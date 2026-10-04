"""Fault injection against compose.verify.yaml only; never the user's live stack."""

import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path

COMPOSE = ["docker", "compose", "-f", "compose.verify.yaml"]
BASE = "http://127.0.0.1:18000/api"


def compose(*args: str) -> str:
    return subprocess.check_output([*COMPOSE, *args], text=True).strip()


def api(path: str, body: object | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def wait_job(identifier: str, state: str, timeout: int = 80) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = api("/jobs/" + identifier)
        if job["state"] == state:
            return job
        if job["state"] == "failed":
            raise RuntimeError(job)
        time.sleep(0.25)
    raise RuntimeError(f"Job {identifier} did not reach {state}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    records: dict[str, object] = {}
    # Broker outage plus dispatcher restart: a committed job survives both outages.
    compose("stop", "rabbitmq")
    try:
        queued = api("/jobs/planning", {})
        time.sleep(1)
        assert api("/jobs/" + queued["id"])["state"] == "queued"
        compose("stop", "outbox")
    finally:
        compose("start", "rabbitmq")
    compose("start", "outbox")
    records["broker_dispatcher_restart"] = wait_job(queued["id"], "succeeded")
    # Redelivery duplicates use the actual installed Celery producer/consumer.
    compose(
        "exec",
        "-T",
        "api",
        "python",
        "-c",
        "from fleet_maintenance.workers.celery_app import app; "
        f"app.send_task('jobs.execute',args=[{queued['id']!r}]); "
        f"app.send_task('jobs.execute',args=[{queued['id']!r}])",
    )
    time.sleep(2)
    duplicate = api("/jobs/" + queued["id"])
    assert duplicate == records["broker_dispatcher_restart"]
    records["duplicate_delivery"] = duplicate
    # Publish-confirm/DB-mark crash window: publish the real pending outbox row,
    # then throw before the transaction commits. Restart must safely republish.
    compose("stop", "outbox")
    unmarked = api("/jobs/planning", {})
    code = """
from fleet_maintenance.persistence.database import SessionLocal
from fleet_maintenance.workers.outbox_dispatcher import dispatch_one, publish_to_broker
def publish_then_crash(event):
    publish_to_broker(event)
    raise RuntimeError('verification: interrupted before dispatch mark')
try:
    assert dispatch_one(SessionLocal, publish_then_crash)
except RuntimeError:
    print('confirmed publication; mark transaction rolled back')
"""
    compose("exec", "-T", "api", "python", "-c", code)
    compose("start", "outbox")
    records["publish_mark_crash"] = wait_job(unmarked["id"], "succeeded")
    # Terminate a worker after a real claim, before calculation acceptance. Delay
    # is a test-only fault hook; the production solver/result protocol is unchanged.
    compose("stop", "worker")
    code = (
        "import time; from fleet_maintenance.workers import job_tasks as j; "
        "from fleet_maintenance.workers.celery_app import app; original=j.solve; "
        "j.solve=lambda source:(time.sleep(20),original(source))[1]; "
        "app.worker_main(['worker','--loglevel=WARNING','--concurrency=1',"
        "'--without-mingle','--without-gossip'])"
    )
    compose(
        "run",
        "-d",
        "--name",
        "fleet-release-fault-worker",
        "worker",
        "python",
        "-c",
        code,
    )
    try:
        running_cancel = api("/jobs/planning", {})
        wait_job(running_cancel["id"], "running")
        assert (
            api("/jobs/" + running_cancel["id"] + "/cancellation", {})["state"]
            == "cancellation_requested"
        )
        records["running_cancellation"] = wait_job(running_cancel["id"], "cancelled")
        lost = api("/jobs/planning", {})
        first = wait_job(lost["id"], "running")
        subprocess.check_call(["docker", "kill", "--signal", "KILL", "fleet-release-fault-worker"])
        compose("start", "worker")
        recovered = wait_job(lost["id"], "succeeded")
        assert recovered["attempt"] > first["attempt"]
        records["worker_loss"] = {
            "first": first,
            "recovered": recovered,
            "attempts": api("/jobs/" + lost["id"] + "/attempts"),
        }
        count = compose(
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "fleet",
            "-d",
            "fleet",
            "-Atc",
            f"SELECT count(*) FROM plans WHERE id='plan-for-{lost['id']}'",
        )
        assert count == "1"
        code = f"""
from fleet_maintenance.persistence.database import SessionLocal
from fleet_maintenance.services.jobs import accept_result, JobConflict
with SessionLocal() as session:
    try:
        accept_result(session, {lost["id"]!r}, {first["attempt"]}, {{'plan_id':'obsolete'}})
    except JobConflict:
        session.rollback()
        print('obsolete result rejected')
    else:
        raise AssertionError('obsolete result was accepted')
"""
        compose("exec", "-T", "api", "python", "-c", code)
        assert api("/jobs/" + lost["id"]) == recovered
        records["stale_result_rejected"] = recovered
    finally:
        subprocess.run(["docker", "rm", "-f", "fleet-release-fault-worker"], check=False)
        compose("start", "worker")
    compose("stop", "worker")
    try:
        cancelled = api("/jobs/planning", {})
        terminal = api("/jobs/" + cancelled["id"] + "/cancellation", {})
        assert terminal["state"] == "cancelled"
    finally:
        compose("start", "worker")
    time.sleep(2)
    assert api("/jobs/" + cancelled["id"])["state"] == "cancelled"
    records["queued_cancellation"] = terminal
    # A dropped stream resumes from its last persisted, confirmed event ID.
    with urllib.request.urlopen(BASE + "/events", timeout=5) as response:
        cursor = next(
            int(line.decode().split(":", 1)[1]) for line in response if line.startswith(b"id:")
        )
    req = urllib.request.Request(BASE + "/events", headers={"Last-Event-ID": str(cursor)})
    with urllib.request.urlopen(req, timeout=5) as response:
        resumed = next(
            int(line.decode().split(":", 1)[1]) for line in response if line.startswith(b"id:")
        )
    assert resumed > cursor
    records["stream_reconnect"] = {"last": cursor, "resumed": resumed}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "checks": records,
                "elapsed_seconds": time.monotonic() - started,
                "scope": "isolated local demonstrator",
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"passed": list(records)}))


if __name__ == "__main__":
    main()
