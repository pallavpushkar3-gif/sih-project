import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from numpy.typing import NDArray

from fleet_maintenance.science.data.features import build_sequence_dataset
from fleet_maintenance.science.data.loaders import CmapssTable
from fleet_maintenance.science.data.splitting import EngineSplit
from fleet_maintenance.science.prediction.evaluation import RegressionMetrics, regression_metrics
from fleet_maintenance.science.prediction.sequence import SequenceRul


@dataclass(frozen=True)
class SequenceTrainingResult:
    validation: RegressionMetrics
    artifact_manifest: dict[str, object]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fit_transform(
    values: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    mean = values.reshape(-1, values.shape[2]).mean(axis=0)
    scale = values.reshape(-1, values.shape[2]).std(axis=0)
    scale[scale == 0] = 1.0
    return mean, scale


def train_sequence(
    table: CmapssTable,
    split: EngineSplit,
    artifact_dir: Path,
    *,
    target_cap: int = 125,
    window: int = 30,
    seed: int = 26249,
    hidden_size: int = 32,
    epochs: int = 8,
    batch_size: int = 128,
    learning_rate: float = 0.001,
    provenance: dict[str, str] | None = None,
) -> SequenceTrainingResult:
    fit = build_sequence_dataset(
        table,
        split.fit,
        window=window,
        target_cap=target_cap,
        sampling="all",
        seed=seed,
    )
    validation = build_sequence_dataset(
        table,
        split.validation,
        window=window,
        target_cap=target_cap,
        sampling="one_seeded_cutoff_per_engine",
        seed=seed,
    )
    mean, scale = _fit_transform(fit.values)
    fit_values = (fit.values - mean) / scale
    validation_values = (validation.values - mean) / scale
    model = SequenceRul.fit(
        fit_values,
        fit.targets,
        seed=seed,
        hidden_size=hidden_size,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
    )
    predictions = model.predict(validation_values)
    metrics = regression_metrics(validation.targets, predictions)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / "model.pt"
    transform_path = artifact_dir / "standardizer.json"
    torch.save(
        {
            "state_dict": model.model.state_dict(),
            "feature_count": fit.values.shape[2],
            "hidden_size": hidden_size,
        },
        model_path,
    )
    transform_path.write_text(
        json.dumps(
            {"features": table.feature_names, "mean": mean.tolist(), "scale": scale.tolist()},
            indent=2,
        )
        + "\n"
    )
    manifest: dict[str, object] = {
        "model": "lstm_sequence_regressor",
        "version": "validation-v1",
        "dataset": "NASA_CMAPSS_FD001",
        "target": {"unit": "cycles", "cap": target_cap},
        "sequence_window_cycles": window,
        "feature_order": list(table.feature_names),
        "fit_engines": list(split.fit),
        "validation_engines": list(split.validation),
        "calibration_engines": list(split.calibration),
        "validation_cutoffs": validation.cutoffs.tolist(),
        "validation_metrics": metrics.as_dict(),
        "training": {
            "hidden_size": hidden_size,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
        },
        "seed": seed,
        "artifacts": {
            "model.pt": _hash(model_path),
            "standardizer.json": _hash(transform_path),
        },
        "final_test_evaluated": False,
        "provenance": provenance or {},
    }
    (artifact_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return SequenceTrainingResult(metrics, manifest)
