"""Conservative FD001 serving eligibility; not a general fault or OOD classifier."""

from typing import Any, cast

import numpy as np


def history_findings(
    rows: list[dict[str, object]],
    minimum: int,
    manifest: dict[str, object],
) -> list[dict[str, str]]:
    def finding(code: str, message: str) -> list[dict[str, str]]:
        return [{"code": code, "severity": "warning", "message": message}]

    if len(rows) < minimum:
        return finding(
            "insufficient_history", f"Provide at least {minimum} consecutive observed cycles."
        )
    if any(value is None for row in rows for value in cast(list[float | None], row["values"])):
        return finding(
            "missing_values",
            "Provide complete supported sensor/settings history; missing data is withheld.",
        )
    values = np.asarray([row["values"] for row in rows], dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 24 or not np.isfinite(values).all():
        return finding(
            "invalid_values", "Provide 24 finite operating settings/sensor values per cycle."
        )
    if np.all(np.ptp(values[-minimum:, 3:], axis=0) == 0):
        return finding(
            "flat_history",
            "All sensor channels are flat; check acquisition before requesting a prediction.",
        )
    bounds = cast(dict[str, Any], manifest.get("operating_settings_bounds", {}))
    if bounds:
        for column, limits in enumerate(bounds["bounds"]):
            if np.any(values[:, column] < limits[0]) or np.any(values[:, column] > limits[1]):
                return finding(
                    "unsupported_conditions",
                    "Operating settings exceed this model's recorded fit-support envelope.",
                )
    elif np.any(np.abs(values[:, 2] - 100.0) > 0.001):
        return finding(
            "unsupported_conditions",
            "Legacy FD001 support requires setting_3 = 100; use a separately supported model.",
        )
    return []
