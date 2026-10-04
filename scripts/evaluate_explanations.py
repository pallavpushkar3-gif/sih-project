"""Entry point for validation-only model sensitivity diagnostics."""

import argparse
import json
from pathlib import Path

from fleet_maintenance.science.prediction.explanation_evaluation import (
    evaluate_explanations,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/cmapss"))
    parser.add_argument(
        "--artifact-dir", type=Path, default=Path("artifacts/models/baseline-v1")
    )
    parser.add_argument(
        "--config", type=Path, default=Path("configs/explanation_evaluation.yaml")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/evaluations/explanations-validation-v1.json"),
    )
    args = parser.parse_args()
    result = evaluate_explanations(
        args.raw, args.artifact_dir, args.config, args.output
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "acceptance",
                    "engine_count",
                    "max_repeat_difference_cycles",
                    "max_intervention_error_cycles",
                    "summary",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
