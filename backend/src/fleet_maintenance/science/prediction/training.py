import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import joblib  # type: ignore[import-untyped]
import numpy as np
from numpy.typing import NDArray

from fleet_maintenance.science.data.features import (
    build_snapshot_dataset,
    snapshot_feature_names,
)
from fleet_maintenance.science.data.loaders import CmapssTable
from fleet_maintenance.science.data.preprocessing import Standardizer
from fleet_maintenance.science.data.splitting import EngineSplit
from fleet_maintenance.science.prediction.baselines import GradientBoostingRul
from fleet_maintenance.science.prediction.evaluation import RegressionMetrics, regression_metrics


@dataclass(frozen=True)
class BaselineTrainingResult:
    validation: RegressionMetrics
    artifact_manifest: dict[str, object]


def _rows(values: NDArray[np.float64], names: tuple[str, ...]) -> list[dict[str, float]]:
    return [dict(zip(names, row, strict=True)) for row in values.tolist()]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def train_baseline(
    table: CmapssTable,
    split: EngineSplit,
    artifact_dir: Path,
    *,
    target_cap: int = 125,
    minimum_history: int = 30,
    window: int = 30,
    seed: int = 26249,
    provenance: dict[str, str] | None = None,
) -> BaselineTrainingResult:
    fit = build_snapshot_dataset(
        table,
        split.fit,
        minimum_history=minimum_history,
        window=window,
        target_cap=target_cap,
        sampling="all",
        seed=seed,
    )
    validation = build_snapshot_dataset(
        table,
        split.validation,
        minimum_history=minimum_history,
        window=window,
        target_cap=target_cap,
        sampling="one_seeded_cutoff_per_engine",
        seed=seed,
    )
    names = snapshot_feature_names(table.feature_names)
    standardizer = Standardizer.fit(_rows(fit.values, names), names)
    fit_values = standardizer.transform(_rows(fit.values, names))
    validation_values = standardizer.transform(_rows(validation.values, names))
    model = GradientBoostingRul.fit(fit_values, fit.targets, seed)
    predictions = model.predict(validation_values)
    metrics = regression_metrics(validation.targets, predictions)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / "model.joblib"
    transform_path = artifact_dir / "standardizer.json"
    joblib.dump(model, model_path)
    transform_path.write_text(
        json.dumps(
            {"features": names, "mean": standardizer.mean, "scale": standardizer.scale},
            indent=2,
        )
        + "\n"
    )
    manifest: dict[str, object] = {
        "model": "gradient_boosting_regressor",
        "version": "validation-v1",
        "dataset": "NASA_CMAPSS_FD001",
        "target": {"unit": "cycles", "cap": target_cap},
        "minimum_history_cycles": minimum_history,
        "feature_window_cycles": window,
        "feature_order": list(names),
        "fit_engines": list(split.fit),
        "validation_engines": list(split.validation),
        "calibration_engines": list(split.calibration),
        "validation_cutoffs": validation.cutoffs.tolist(),
        "validation_metrics": metrics.as_dict(),
        "seed": seed,
        "artifacts": {
            "model.joblib": _hash(model_path),
            "standardizer.json": _hash(transform_path),
        },
        "final_test_evaluated": False,
        "provenance": provenance or {},
    }
    if table.feature_names[:3] == ("setting_1", "setting_2", "setting_3"):
        fit_numbers = [int(identity.rsplit(":", 1)[1]) for identity in split.fit]
        settings = table.features[np.isin(table.engine_numbers, fit_numbers), :3]
        low, high = settings.min(axis=0), settings.max(axis=0)
        padding = np.maximum(0.001, (high - low) * 0.05)
        manifest["operating_settings_bounds"] = {
            "method": "fit-min-max-plus-5pct-range-or-0.001-demo-envelope-v1",
            "bounds": np.column_stack((low - padding, high + padding)).tolist(),
            "qualification": "conservative demonstration envelope; no general OOD guarantee",
        }
    (artifact_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return BaselineTrainingResult(metrics, manifest)
