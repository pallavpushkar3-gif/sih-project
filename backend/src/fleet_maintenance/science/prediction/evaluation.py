from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class RegressionMetrics:
    count: int
    mae_cycles: float
    rmse_cycles: float
    asymmetric_score: float

    def as_dict(self) -> dict[str, int | float]:
        return asdict(self)


def regression_metrics(
    targets: NDArray[np.float64], predictions: NDArray[np.float64]
) -> RegressionMetrics:
    if targets.shape != predictions.shape or not targets.size:
        raise ValueError("Targets and predictions must be nonempty and aligned.")
    errors = predictions - targets
    penalties = np.where(errors < 0, np.exp(-errors / 13.0) - 1.0, np.exp(errors / 10.0) - 1.0)
    return RegressionMetrics(
        count=int(targets.size),
        mae_cycles=float(np.mean(np.abs(errors))),
        rmse_cycles=float(np.sqrt(np.mean(np.square(errors)))),
        asymmetric_score=float(np.sum(penalties)),
    )
