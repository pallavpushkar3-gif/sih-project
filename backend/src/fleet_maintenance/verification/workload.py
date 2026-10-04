"""Bounded concurrent reads while real durable jobs run in an isolated demo stack."""

import json
import platform
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from fleet_maintenance.artifacts.storage import sha256


def run_workload(base_url: str, config_path: Path, output: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text())
    count = config["concurrent_readers"]
    requests = config["requests_per_reader"]
    if not 1 <= count <= 100 or not 1 <= requests <= 1000:
        raise ValueError("Diagnostic workload must be bounded to 100 readers / 1000 requests")
    barrier = threading.Barrier(count + 1)
    submitted_ids: set[str] = set()
    headers = {"X-Demo-Role": "supervisor", "X-Demo-User": "workload-diagnostic"}

    def request(path: str, method: str = "GET") -> tuple[float, int, Any]:
        started = time.perf_counter()
        req = urllib.request.Request(base_url.rstrip("/") + path, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=config["timeout_seconds"]) as response:
                return time.perf_counter() - started, response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return time.perf_counter() - started, exc.code, None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return time.perf_counter() - started, 0, None

    def reader(index: int) -> list[dict[str, Any]]:
        barrier.wait(timeout=15)
        rows = []
        for position in range(requests):
            path = config["read_paths"][(position + index) % len(config["read_paths"])]
            latency, status, body = request(path)
            active = (
                [
                    item["id"]
                    for item in body
                    if item["id"] in submitted_ids and item["state"] in {"queued", "running"}
                ]
                if path == "/jobs" and isinstance(body, list)
                else []
            )
            rows.append(
                {
                    "path": path,
                    "latency_seconds": latency,
                    "status": status,
                    "observed_active_job_ids": active,
                }
            )
        return rows

    def jobs() -> list[dict[str, Any]]:
        # Queue the specified jobs together before releasing concurrent readers.
        submitted = []
        for path in config["job_paths"]:
            latency, status, body = request(path, "POST")
            if isinstance(body, dict) and "id" in body:
                submitted_ids.add(body["id"])
            submitted.append(
                {"path": path, "submission_seconds": latency, "status": status, "body": body}
            )
        barrier.wait(timeout=15)
        deadline = time.monotonic() + config["maximum_job_wait_seconds"]
        for item in submitted:
            body = item["body"]
            if not isinstance(body, dict) or "id" not in body:
                item["outcome"] = "submission_failed"
                continue
            started = time.monotonic()
            while time.monotonic() < deadline:
                _, status, state = request("/jobs/" + body["id"])
                if status == 200 and state["state"] in {"succeeded", "failed", "cancelled"}:
                    item["outcome"] = state["state"]
                    item["result"] = state
                    break
                time.sleep(0.1)
            else:
                item["outcome"] = "timeout"
            item["observed_wait_seconds"] = time.monotonic() - started
        return submitted

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=count + 1) as pool:
        readers = [pool.submit(reader, index) for index in range(count)]
        job_future = pool.submit(jobs)
        rows = [row for future in readers for row in future.result()]
        job_rows = job_future.result()
    durations = [row["latency_seconds"] for row in rows]
    summary = {}
    for path in config["read_paths"]:
        values = [row["latency_seconds"] for row in rows if row["path"] == path]
        summary[path] = {
            "count": len(values),
            "p95_seconds": float(np.quantile(values, 0.95)),
            "p99_seconds": float(np.quantile(values, 0.99)),
        }
    result = {
        "configuration": config,
        "configuration_sha256": sha256(config_path),
        "client_environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "elapsed_seconds": time.perf_counter() - started,
        "requests": len(rows),
        "failed_requests": sum(row["status"] != 200 for row in rows),
        "p95_seconds": float(np.quantile(durations, 0.95)),
        "p99_seconds": float(np.quantile(durations, 0.99)),
        "per_route": summary,
        "read_samples_observing_active_jobs": sum(
            bool(row["observed_active_job_ids"]) for row in rows
        ),
        "benchmark_module_sha256": sha256(Path(__file__)),
        "jobs": job_rows,
        "responses": rows,
        "acceptance": "diagnostic_only_no_frozen_workload_or_latency_budget",
        "limitations": (
            "HTTP client concurrency is not browser interaction latency. "
            "Existing small demo records; no large-fleet throughput "
            "or production session load claim."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return result
