import json
from dataclasses import dataclass
from pathlib import Path

import joblib  # type: ignore[import-untyped]
import numpy as np
from numpy.typing import NDArray

from fleet_maintenance.science.data.features import SnapshotDataset
from fleet_maintenance.science.data.preprocessing import Standardizer
from fleet_maintenance.science.prediction.baselines import GradientBoostingRul


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
        transform = json.loads((artifact_dir / "standardizer.json").read_text())
        standardizer = Standardizer(
            tuple(transform["mean"]),
            tuple(transform["scale"]),
            tuple(transform["features"]),
        )
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
