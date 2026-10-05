"""Package retained model/sample bytes, or bootstrap an isolated public installation."""

import argparse
import json
from pathlib import Path

from fleet_maintenance.persistence.database import SessionLocal
from fleet_maintenance.services.demo_bundle import install_bundle, package_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("package")
    pack.add_argument("--model", type=Path, required=True)
    pack.add_argument("--sample", type=Path, required=True)
    pack.add_argument("--output", type=Path, required=True)
    install = commands.add_parser("install")
    install.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "package":
        print(json.dumps({"sha256": package_bundle(args.model, args.sample, args.output)}))
    else:
        with SessionLocal() as session:
            install_bundle(session, args.bundle)
        print("Verified model and simulated history installed; synthetic records initialized.")


if __name__ == "__main__":
    main()
