import json
from dataclasses import dataclass
from pathlib import Path

import joblib  # type: ignore[import-untyped]
import numpy as np
from numpy.typing import NDArray

from fleet_maintenance.artifacts.storage import verify_hashes
from fleet_maintenance.science.data.features import SnapshotDataset
from fleet_maintenance.science.data.preprocessing import Standardizer
from fleet_maintenance.science.prediction.baselines import GradientBoostingRul
from fleet_maintenance.science.prediction.explanations import explanation_evidence


@dataclass(frozen=True)
class BaselinePredictor:
    model: GradientBoostingRul
    standardizer: Standardizer
    manifest: dict[str, object]

    @classmethod
    def load(cls, artifact_dir: Path) -> "BaselinePredictor":
        manifest = json.loads((artifact_dir / "manifest.json").read_text())
        if manifest.get("model") != "gradient_boosting_regressor":
            raise ValueError("Artifact is not a supported baseline model.")
        verify_hashes(artifact_dir, manifest["artifacts"])
        transform = json.loads((artifact_dir / "standardizer.json").read_text())
        standardizer = Standardizer(
            tuple(transform["mean"]),
            tuple(transform["scale"]),
            tuple(transform["features"]),
        )
        if (list(standardizer.features) != manifest["feature_order"]
                or len(standardizer.mean) != len(standardizer.features)
                or len(standardizer.scale) != len(standardizer.features)
                or not np.isfinite(standardizer.mean).all()
                or not np.isfinite(standardizer.scale).all()
                or np.any(np.asarray(standardizer.scale) <= 0)):
            raise ValueError("Transform features/finite scales do not match the model manifest")
        model = joblib.load(artifact_dir / "model.joblib")
        if not isinstance(model, GradientBoostingRul):
            raise TypeError("Baseline artifact contains an unexpected model type.")
        return cls(model, standardizer, manifest)

    def predict(self, dataset: SnapshotDataset) -> NDArray[np.float64]:
        rows = [
            dict(zip(self.standardizer.features, row, strict=True))
            for row in dataset.values.tolist()
        ]
        return self.model.predict(self.standardizer.transform(rows))


@dataclass(frozen=True)
class HistoryPrediction:
    estimate_cycles: float
    lower_cycles: float
    upper_cycles: float
    evidence: dict[str, object]


def predict_history(
    directory: Path, history: NDArray[np.float64], cutoff: int
) -> HistoryPrediction:
    """Shared serving transformation; only observations through the cutoff are used."""
    import math

    from fleet_maintenance.science.data.features import snapshot_features

    predictor = BaselinePredictor.load(directory)
    if cutoff < int(str(predictor.manifest["minimum_history_cycles"])) or cutoff > len(history):
        raise ValueError("History does not support the requested cutoff")
    values = snapshot_features(
        history[:cutoff], cutoff, int(str(predictor.manifest["feature_window_cycles"]))
    )
    dataset = SnapshotDataset(
        ("serving",),
        np.asarray([cutoff], dtype=np.int64),
        values[None, :],
        np.zeros(1, dtype=np.float64),
    )
    estimate = float(predictor.predict(dataset)[0])
    calibration = json.loads((directory / "calibration.json").read_text())
    if calibration["model_artifacts"] != predictor.manifest["artifacts"]:
        raise ValueError("Calibration does not match the fitted model")
    quantile = float(calibration["diagnostic"]["residual_quantile_cycles"])
    if not math.isfinite(estimate) or estimate < 0 or not math.isfinite(quantile) or quantile < 0:
        raise ValueError("Model produced an invalid estimate or interval")
    feature_rows = [dict(zip(predictor.standardizer.features, values.tolist(), strict=True))]
    standardized = predictor.standardizer.transform(feature_rows)
    try:
        explanation = explanation_evidence(
            predictor.model.predict, standardized[0], predictor.standardizer.features
        )
    except (ValueError, ArithmeticError):
        explanation = {
            "state": "unavailable",
            "method": "one_feature_at_training_mean_sensitivity",
            "version": "training-mean-sensitivity-v1",
            "reason": "Feature sensitivity could not be calculated reliably",
        }
    evidence: dict[str, object] = {
        "calibration": calibration["diagnostic"],
        "feature_order": predictor.standardizer.features,
        "feature_values": values.tolist(),
        "explanation": explanation,
    }
    return HistoryPrediction(estimate, max(0.0, estimate - quantile), estimate + quantile, evidence)
