"""Install already fitted/calibrated local artifacts and a labelled validation history.

Run in the API environment with access to its DB/artifact volume. No training or test
labels are used here. Source weights, transforms and manifest are verified by registration.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from fleet_maintenance.persistence.database import SessionLocal
from fleet_maintenance.services.assessments import register_model
from fleet_maintenance.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("artifacts/models/customer-trial-v1"))
    parser.add_argument("--raw", type=Path, default=Path("data/raw/cmapss/train_FD001.txt"))
    args = parser.parse_args()
    settings = get_settings()
    if settings.environment != "development" or settings.authentication_mode != "demo":
        raise RuntimeError("Install customer data only in the local demonstrator")
    manifest = json.loads((args.model / "manifest.json").read_text())
    identity = "NASA_CMAPSS:FD001:train:1"
    if identity not in manifest["validation_engines"] or identity in manifest["fit_engines"]:
        raise RuntimeError("Demo sample must be a held-out validation engine")
    rows = []
    for line in args.raw.read_text().splitlines():
        columns = [float(value) for value in line.split()]
        if int(columns[0]) == 1 and int(columns[1]) <= 180:
            rows.append({"cycle": int(columns[1]), "values": columns[2:]})
    source_hash = hashlib.sha256(args.raw.read_bytes()).hexdigest()
    if source_hash != manifest["provenance"]["training_source_sha256"]:
        raise RuntimeError("Sample dataset does not match fitted artifact provenance")
    destination = settings.artifact_root / "customer-trial-v1"
    if destination.resolve() != args.model.resolve():
        destination.mkdir(parents=True, exist_ok=True)
        for name in (
            "model.joblib",
            "standardizer.json",
            "manifest.json",
            "calibration.json",
        ):
            target = destination / name
            contents = (args.model / name).read_bytes()
            if target.exists() and target.read_bytes() != contents:
                raise RuntimeError(
                    "Installed model differs; choose a new version rather than overwrite"
                )
            if not target.exists():
                shutil.copyfile(args.model / name, target)
    with SessionLocal() as session:
        registration = register_model(
            session, "customer-trial-v1", "customer-trial-v1", "demo-administrator"
        )
    sample = {
        "source_sha256": source_hash,
        "simulated": True,
        "partition": "validation",
        "history": {
            "source_version": "customer-trial-validation-v1",
            "engine_identity": identity,
            "rows": rows,
        },
    }
    sample_path = settings.artifact_root / "customer-trial-sample.json"
    sample_path.write_text(json.dumps(sample, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "model_id": registration.id,
                "sample_cycles": len(rows),
                "source_sha256": source_hash,
                "scientific_release": "not_qualified",
            }
        )
    )


if __name__ == "__main__":
    main()
