"""Run a separately retrained, engine-disjoint internal simulated benchmark."""

import argparse
import json
from pathlib import Path

from fleet_maintenance.science.prediction.lifecycle_release import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/cmapss"))
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/lifecycle_release.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_experiment(args.raw, args.artifact_dir, args.config, args.output)
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "version",
                    "prediction",
                    "constant_baseline",
                    "interval_coverage",
                    "mean_interval_width_cycles",
                    "promotion",
                    "qualification",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
