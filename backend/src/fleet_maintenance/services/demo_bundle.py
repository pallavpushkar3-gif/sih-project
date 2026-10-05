"""Offline trusted model/sample packaging; never accepts browser model uploads."""

import hashlib
import io
import json
import shutil
import tarfile
import tempfile
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session

from fleet_maintenance.artifacts.storage import sha256
from fleet_maintenance.domain.contracts.health import HistoryImport
from fleet_maintenance.science.prediction.inference import BaselinePredictor, predict_history
from fleet_maintenance.services.assessments import register_model
from fleet_maintenance.services.records import seed_demo
from fleet_maintenance.settings import get_settings

MODEL_FILES = ("model.joblib", "standardizer.json", "manifest.json", "calibration.json")
SAMPLE = "customer-trial-sample.json"
FILES = (*MODEL_FILES, SAMPLE)


def validate_directory(directory: Path) -> None:
    BaselinePredictor.load(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    sample = json.loads((directory / SAMPLE).read_text())
    history = HistoryImport.model_validate(sample["history"])
    if sample.get("simulated") is not True or sample.get("partition") != "validation":
        raise ValueError("Bundle must contain labelled simulated validation history")
    if history.engine_identity not in manifest["validation_engines"] or (
        history.engine_identity in manifest["fit_engines"]
    ):
        raise ValueError("Sample must be a validation engine, outside model fit")
    if sample["source_sha256"] != manifest["provenance"]["training_source_sha256"]:
        raise ValueError("Sample provenance does not match the fitted model")
    # Reuse serving calibration/transform checks before installing any bytes.
    predict_history(
        directory,
        np.asarray([row.values for row in history.rows], dtype=float),
        int(manifest["minimum_history_cycles"]),
    )


def package_bundle(model: Path, sample: Path, output: Path) -> str:
    if output.exists():
        raise ValueError("Choose a new bundle path; existing bytes are retained")
    with tempfile.TemporaryDirectory(prefix="fleet-bundle-") as temp:
        directory = Path(temp)
        for name in MODEL_FILES:
            shutil.copyfile(model / name, directory / name)
        shutil.copyfile(sample, directory / SAMPLE)
        validate_directory(directory)
        manifest = {name: sha256(directory / name) for name in FILES}
        output.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(output, "w:gz") as archive:
            metadata = json.dumps({"version": "public-demo-v1", "files": manifest}).encode()
            info = tarfile.TarInfo("bundle.json")
            info.size = len(metadata)
            archive.addfile(info, io.BytesIO(metadata))
            for name in FILES:
                archive.add(directory / name, arcname=name)
    output.chmod(0o600)
    return sha256(output)


def install_bundle(session: Session, bundle: Path) -> None:
    settings = get_settings()
    if settings.environment != "tunnel_demo" or settings.authentication_mode != "session":
        raise ValueError("Bundle bootstrap requires the isolated public demo configuration")
    settings.artifact_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".bundle-", dir=settings.artifact_root) as temp:
        directory = Path(temp)
        with tarfile.open(bundle, "r:gz") as archive:
            members = archive.getmembers()
            if len(members) != len(FILES) + 1 or {m.name for m in members} != {
                *FILES,
                "bundle.json",
            }:
                raise ValueError("Bundle contains unexpected or duplicate paths")
            for member in members:
                if not member.isfile() or member.size > 50_000_000:
                    raise ValueError("Bundle must contain bounded regular files")
                stream = archive.extractfile(member)
                assert stream is not None
                (directory / member.name).write_bytes(stream.read())
        metadata = json.loads((directory / "bundle.json").read_text())
        if metadata.get("version") != "public-demo-v1" or set(metadata["files"]) != set(FILES):
            raise ValueError("Unsupported bundle manifest")
        for name in FILES:
            if (
                hashlib.sha256((directory / name).read_bytes()).hexdigest()
                != metadata["files"][name]
            ):
                raise ValueError("Bundle checksum mismatch")
        validate_directory(directory)
        target = settings.artifact_root / "customer-trial-v1"
        # Check every immutable existing byte before making any installation change.
        for name in MODEL_FILES:
            if (target / name).exists() and (target / name).read_bytes() != (
                directory / name
            ).read_bytes():
                raise ValueError("Installed model differs; use a new evaluated version")
        installed_sample = settings.artifact_root / SAMPLE
        if (
            installed_sample.exists()
            and installed_sample.read_bytes() != (directory / SAMPLE).read_bytes()
        ):
            raise ValueError("Installed sample differs; existing evidence is immutable")
        target.mkdir(exist_ok=True)
        for name in MODEL_FILES:
            if not (target / name).exists():
                shutil.copyfile(directory / name, target / name)
        if not installed_sample.exists():
            shutil.copyfile(directory / SAMPLE, installed_sample)
    register_model(session, "customer-trial-v1", "customer-trial-v1", "deployment-bootstrap")
    seed_demo(session)
