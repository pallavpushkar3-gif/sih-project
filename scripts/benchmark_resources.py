import argparse
import json
from pathlib import Path

from fleet_maintenance.verification.resource_benchmark import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure bounded resource-aware scheduling fixtures"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"acceptance": result["acceptance"]}))


if __name__ == "__main__":
    main()
