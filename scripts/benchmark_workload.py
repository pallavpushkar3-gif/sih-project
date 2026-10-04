"""Entry point for an isolated local demo workload diagnostic."""

import argparse
import json
from pathlib import Path

from fleet_maintenance.verification.workload import run_workload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8080/api")
    parser.add_argument(
        "--config", type=Path, default=Path("configs/workload_diagnostic.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/benchmarks/workload-local-v1.json"),
    )
    args = parser.parse_args()
    result = run_workload(args.base_url, args.config, args.output)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "requests",
                    "failed_requests",
                    "p95_seconds",
                    "p99_seconds",
                    "per_route",
                    "jobs",
                    "acceptance",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
