"""Entry point for the shared final FD001 evaluation implementation."""

import argparse
import json
from pathlib import Path

from fleet_maintenance.science.prediction.final_evaluation import (
    FinalEvaluationConfig,
    evaluate_final,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a frozen FD001 model on the official final test"
    )
    parser.add_argument("--raw", type=Path, default=Path("data/raw/cmapss"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/models/baseline-v1"))
    parser.add_argument("--policy", type=Path, default=Path("configs/acceptance_proposal.yaml"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/evaluations/final-fd001-v1-shared.json"),
    )
    args = parser.parse_args()
    result = evaluate_final(
        FinalEvaluationConfig(args.raw, args.artifact_dir, args.policy, args.output)
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in [
                    "eligible_count",
                    "capped_primary",
                    "uncapped_secondary",
                    "intervals",
                    "gates",
                    "acceptance",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
