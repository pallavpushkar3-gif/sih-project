from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from fleet_maintenance.science.data.loaders import CmapssTable

InterventionKind = Literal[
    "clean", "random_missing", "contiguous_outage", "sensor_noise", "regime_shift"
]


@dataclass(frozen=True)
class InterventionSpec:
    name: str
    kind: InterventionKind
    rate: float = 0.0
    length_cycles: int = 0
    feature: str | None = None
    scale: float = 0.0


@dataclass(frozen=True)
class PreparedIntervention:
    table: CmapssTable
    missing_mask: NDArray[np.bool_]
    modified_values: int
    withheld: tuple[bool, ...]


def _engine_number(identity: str) -> int:
    return int(identity.rsplit(":", 1)[1])


def _longest_run(values: NDArray[np.bool_]) -> int:
    longest = current = 0
    for value in values:
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest


def prepare_intervention(
    table: CmapssTable,
    *,
    fit_engine_ids: tuple[str, ...],
    evaluation_engine_ids: tuple[str, ...],
    cutoffs: NDArray[np.int64],
    window: int,
    maximum_missing_fraction: float,
    maximum_contiguous_missing_cycles: int,
    spec: InterventionSpec,
    seed: int,
) -> PreparedIntervention:
    if len(evaluation_engine_ids) != len(cutoffs):
        raise ValueError("Evaluation engines and cutoffs must align.")
    if not 0 <= maximum_missing_fraction <= 1:
        raise ValueError("Maximum missing fraction must be between zero and one.")

    fit_numbers = {_engine_number(identity) for identity in fit_engine_ids}
    evaluation_numbers = {_engine_number(identity) for identity in evaluation_engine_ids}
    fit_rows = np.isin(table.engine_numbers, list(fit_numbers))
    evaluation_rows = np.isin(table.engine_numbers, list(evaluation_numbers))
    if not fit_rows.any() or not evaluation_rows.any():
        raise ValueError("Fit and evaluation histories must both be present.")

    values = table.features.copy()
    missing = np.zeros(values.shape, dtype=np.bool_)
    fit_values = table.features[fit_rows]
    medians = np.median(fit_values, axis=0)
    deviations = np.std(fit_values, axis=0)
    minimums = np.min(fit_values, axis=0)
    maximums = np.max(fit_values, axis=0)
    sensor_columns = np.arange(3, values.shape[1])
    generator = np.random.default_rng(seed)

    if spec.kind == "random_missing":
        candidates = np.ix_(evaluation_rows, sensor_columns)
        selected = generator.random(values[candidates].shape) < spec.rate
        missing[candidates] = selected
    elif spec.kind == "contiguous_outage":
        if spec.feature not in table.feature_names:
            raise ValueError(f"Unknown outage feature: {spec.feature}")
        column = table.feature_names.index(spec.feature)
        for identity, cutoff in zip(evaluation_engine_ids, cutoffs, strict=True):
            engine = _engine_number(identity)
            affected = (
                (table.engine_numbers == engine)
                & (table.cycles <= cutoff)
                & (table.cycles > cutoff - spec.length_cycles)
            )
            missing[affected, column] = True
    elif spec.kind == "sensor_noise":
        rows = np.flatnonzero(evaluation_rows)
        noise = generator.normal(
            0.0,
            deviations[sensor_columns] * spec.scale,
            size=(len(rows), len(sensor_columns)),
        )
        values[np.ix_(rows, sensor_columns)] += noise
    elif spec.kind == "regime_shift":
        rows = np.flatnonzero(evaluation_rows)
        setting_columns = np.arange(min(3, values.shape[1]))
        shifted = values[np.ix_(rows, setting_columns)] + (
            deviations[setting_columns] * spec.scale
        )
        values[np.ix_(rows, setting_columns)] = np.clip(
            shifted, minimums[setting_columns], maximums[setting_columns]
        )
    elif spec.kind != "clean":
        raise ValueError(f"Unsupported intervention kind: {spec.kind}")

    values[missing] = np.broadcast_to(medians, values.shape)[missing]
    withheld: list[bool] = []
    for identity, cutoff in zip(evaluation_engine_ids, cutoffs, strict=True):
        engine = _engine_number(identity)
        indices = np.flatnonzero(
            (table.engine_numbers == engine) & (table.cycles <= cutoff)
        )[-window:]
        window_missing = missing[indices]
        fraction = float(window_missing.mean())
        longest = max(
            (_longest_run(window_missing[:, column]) for column in range(values.shape[1])),
            default=0,
        )
        withheld.append(
            fraction > maximum_missing_fraction
            or longest > maximum_contiguous_missing_cycles
        )

    if spec.kind in {"random_missing", "contiguous_outage"}:
        modified_values = int(missing.sum())
    else:
        modified_values = int(np.count_nonzero(values != table.features))
    return PreparedIntervention(
        CmapssTable(
            table.identities,
            table.engine_numbers.copy(),
            table.cycles.copy(),
            values,
            table.feature_names,
        ),
        missing,
        modified_values,
        tuple(withheld),
    )
