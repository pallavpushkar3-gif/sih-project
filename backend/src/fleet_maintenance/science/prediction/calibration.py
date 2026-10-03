import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from fleet_maintenance.science.data.features import build_snapshot_dataset
from fleet_maintenance.science.data.loaders import CmapssTable
from fleet_maintenance.science.data.splitting import EngineSplit
from fleet_maintenance.science.prediction.inference import BaselinePredictor


@dataclass(frozen=True)
class CalibrationResult:
    nominal_coverage: float
    sample_count: int
    residual_quantile_cycles: float
    calibration_coverage: float
    mean_interval_width_cycles: float

    def as_dict(self) -> dict[str, int | float]:
        return asdict(self)


def conformal_quantile(residuals: NDArray[np.float64], nominal_coverage: float) -> float:
    if residuals.ndim != 1 or not residuals.size or (residuals < 0).any():
        raise ValueError("Residuals must be a nonempty one-dimensional nonnegative array.")
    if not 0.0 < nominal_coverage < 1.0:
        raise ValueError("Nominal coverage must be between zero and one.")
    rank = min(len(residuals), math.ceil((len(residuals) + 1) * nominal_coverage))
    return float(np.sort(residuals)[rank - 1])


def calibrate_baseline(
    table: CmapssTable,
    split: EngineSplit,
    artifact_dir: Path,
    *,
    nominal_coverage: float = 0.9,
    target_cap: int = 125,
    minimum_history: int = 30,
    window: int = 30,
    seed: int = 26249,
    provenance: dict[str, str] | None = None,
) -> CalibrationResult:
    predictor = BaselinePredictor.load(artifact_dir)
    calibration = build_snapshot_dataset(
        table,
        split.calibration,
        minimum_history=minimum_history,
        window=window,
        target_cap=target_cap,
        sampling="one_seeded_cutoff_per_engine",
        seed=seed,
    )
    predictions = predictor.predict(calibration)
    residuals = np.abs(calibration.targets - predictions)
    quantile = conformal_quantile(residuals, nominal_coverage)
    lower = np.maximum(predictions - quantile, 0.0)
    upper = predictions + quantile
    covered = (calibration.targets >= lower) & (calibration.targets <= upper)
    result = CalibrationResult(
        nominal_coverage=nominal_coverage,
        sample_count=len(residuals),
        residual_quantile_cycles=quantile,
        calibration_coverage=float(covered.mean()),
        mean_interval_width_cycles=float(np.mean(upper - lower)),
    )
    payload = {
        "version": "validation-v1",
        "method": "split_conformal_symmetric_absolute_residual",
        "model": predictor.manifest["model"],
        "model_artifacts": predictor.manifest["artifacts"],
        "sampling_unit": "one_seeded_cutoff_per_engine",
        "calibration_engines": list(split.calibration),
        "calibration_cutoffs": calibration.cutoffs.tolist(),
        "diagnostic": result.as_dict(),
        "final_test_evaluated": False,
        "provenance": provenance or {},
    }
    (artifact_dir / "calibration.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    return result
