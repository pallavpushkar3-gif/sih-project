"""Training-mean interventions explain model sensitivity, never mechanical causation."""

from collections.abc import Callable
from typing import cast

import numpy as np
from numpy.typing import NDArray

PredictionFunction = Callable[[NDArray[np.float64]], NDArray[np.float64]]


def feature_sensitivities(
    predict: PredictionFunction, standardized: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Return f(x)-f(x with feature j set to its fitted mean), in target units."""
    if standardized.ndim != 1 or not standardized.size or not np.isfinite(standardized).all():
        raise ValueError("Sensitivity requires one finite nonempty feature vector")
    original = np.asarray(predict(standardized[None, :]), dtype=np.float64)
    interventions = np.repeat(standardized[None, :], standardized.size, axis=0)
    np.fill_diagonal(interventions, 0.0)
    altered = np.asarray(predict(interventions), dtype=np.float64)
    if original.shape != (1,) or altered.shape != (standardized.size,):
        raise ValueError("Sensitivity predictions must match the intervention rows")
    if not np.isfinite(original).all() or not np.isfinite(altered).all():
        raise ValueError("Sensitivity predictions must be finite")
    return cast(NDArray[np.float64], original[0] - altered)


def explanation_evidence(
    predict: PredictionFunction, standardized: NDArray[np.float64], features: tuple[str, ...]
) -> dict[str, object]:
    if len(features) != standardized.size or len(set(features)) != len(features):
        raise ValueError("Sensitivity feature names must be unique and aligned")
    differences = feature_sensitivities(predict, standardized)
    ranked = sorted(
        zip(features, differences.tolist(), strict=True),
        key=lambda pair: abs(pair[1]),
        reverse=True,
    )[:10]
    return {
        "state": "available",
        "method": "one_feature_at_training_mean_sensitivity",
        "version": "training-mean-sensitivity-v1",
        "reference": "Each feature independently replaced by its fit-engine training mean",
        "contributions": [
            {"feature": name, "difference_cycles": difference} for name, difference in ranked
        ],
        "limitations": (
            "Noncausal sensitivity; correlated inputs limit interpretation. "
            "Contributions are not additive. Single-feature replacements may be off-distribution."
        ),
    }
