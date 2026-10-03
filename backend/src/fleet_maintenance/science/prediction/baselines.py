from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import GradientBoostingRegressor  # type: ignore[import-untyped]


@dataclass
class GradientBoostingRul:
    model: GradientBoostingRegressor

    @classmethod
    def fit(
        cls, features: NDArray[np.float64], targets: NDArray[np.float64], seed: int
    ) -> "GradientBoostingRul":
        model = GradientBoostingRegressor(
            random_state=seed,
            n_estimators=250,
            learning_rate=0.04,
            max_depth=3,
            loss="huber",
        )
        model.fit(features, targets)
        return cls(model)

    def predict(self, features: NDArray[np.float64]) -> NDArray[np.float64]:
        predictions = np.asarray(self.model.predict(features), dtype=np.float64)
        return np.maximum(predictions, 0.0)
