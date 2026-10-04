import argparse
import json
from pathlib import Path

from fleet_maintenance.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the implemented FastAPI OpenAPI schema.")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(app.openapi(), indent=2) + "\n")


if __name__ == "__main__":
    main()
