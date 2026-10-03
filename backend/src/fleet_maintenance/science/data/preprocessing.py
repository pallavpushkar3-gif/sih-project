from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Standardizer:
    mean: tuple[float, ...]
    scale: tuple[float, ...]
    features: tuple[str, ...]

    @classmethod
    def fit(cls, rows: list[dict[str, float]], features: tuple[str, ...]) -> "Standardizer":
        matrix = np.asarray([[row[name] for name in features] for row in rows], dtype=float)
        mean = matrix.mean(axis=0)
        scale = matrix.std(axis=0)
        scale[scale == 0] = 1.0
        return cls(tuple(mean.tolist()), tuple(scale.tolist()), features)

    def transform(self, rows: list[dict[str, float]]) -> NDArray[np.float64]:
        matrix = np.asarray([[row[name] for name in self.features] for row in rows], dtype=float)
        result: NDArray[np.float64] = (matrix - np.asarray(self.mean)) / np.asarray(self.scale)
        return result
