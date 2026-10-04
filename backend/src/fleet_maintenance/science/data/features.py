import random
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fleet_maintenance.science.data.loaders import CmapssTable


@dataclass(frozen=True)
class SnapshotDataset:
    engine_ids: tuple[str, ...]
    cutoffs: NDArray[np.int64]
    values: NDArray[np.float64]
    targets: NDArray[np.float64]


@dataclass(frozen=True)
class SequenceDataset:
    engine_ids: tuple[str, ...]
    cutoffs: NDArray[np.int64]
    values: NDArray[np.float64]
    targets: NDArray[np.float64]


def _engine_number(identity: str) -> int:
    return int(identity.rsplit(":", 1)[1])


def snapshot_features(history: NDArray[np.float64], cycle: int, window: int) -> NDArray[np.float64]:
    if window <= 0 or cycle < 1 or history.ndim != 2 or not len(history):
        raise ValueError(
            "Snapshot requires nonempty two-dimensional history and positive window/cycle"
        )
    if not np.isfinite(history).all():
        raise ValueError("Snapshot history must be finite")
    recent = history[-window:]
    mean = recent.mean(axis=0)
    if len(recent) == 1:
        slope = np.zeros(recent.shape[1], dtype=np.float64)
    else:
        x = np.arange(len(recent), dtype=np.float64)
        centered = x - x.mean()
        slope = (centered[:, None] * (recent - recent.mean(axis=0))).sum(axis=0)
        slope /= np.square(centered).sum()
    return np.concatenate((history[-1], mean, slope, np.asarray([float(cycle)])))


def snapshot_feature_names(feature_names: tuple[str, ...]) -> tuple[str, ...]:
    return (
        *(f"current_{name}" for name in feature_names),
        *(f"mean_{name}" for name in feature_names),
        *(f"slope_{name}" for name in feature_names),
        "current_cycle",
    )


def build_snapshot_dataset(
    table: CmapssTable,
    engine_ids: tuple[str, ...],
    *,
    minimum_history: int,
    window: int,
    target_cap: int,
    sampling: str,
    seed: int,
) -> SnapshotDataset:
    rows: list[NDArray[np.float64]] = []
    targets: list[float] = []
    selected_ids: list[str] = []
    cutoffs: list[int] = []
    generator = random.Random(seed)
    for identity in engine_ids:
        engine = _engine_number(identity)
        mask = table.engine_numbers == engine
        history = table.features[mask]
        cycles = table.cycles[mask]
        if len(cycles) < minimum_history:
            continue
        indices: Iterable[int]
        if sampling == "all":
            indices = range(minimum_history - 1, len(cycles))
        elif sampling == "one_seeded_cutoff_per_engine":
            indices = (generator.randrange(minimum_history - 1, len(cycles)),)
        else:
            raise ValueError(f"Unsupported snapshot sampling policy: {sampling}")
        maximum_cycle = int(cycles[-1])
        for index in indices:
            cutoff = int(cycles[index])
            rows.append(snapshot_features(history[: index + 1], cutoff, window))
            targets.append(float(min(target_cap, maximum_cycle - cutoff)))
            selected_ids.append(identity)
            cutoffs.append(cutoff)
    if not rows:
        raise ValueError("No eligible engine snapshots were produced.")
    return SnapshotDataset(
        tuple(selected_ids),
        np.asarray(cutoffs, dtype=np.int64),
        np.vstack(rows),
        np.asarray(targets, dtype=np.float64),
    )


def build_sequence_dataset(
    table: CmapssTable,
    engine_ids: tuple[str, ...],
    *,
    window: int,
    target_cap: int,
    sampling: str,
    seed: int,
) -> SequenceDataset:
    if window <= 0:
        raise ValueError("Sequence window must be positive.")
    rows: list[NDArray[np.float64]] = []
    targets: list[float] = []
    selected_ids: list[str] = []
    cutoffs: list[int] = []
    generator = random.Random(seed)
    for identity in engine_ids:
        engine = _engine_number(identity)
        mask = table.engine_numbers == engine
        history = table.features[mask]
        cycles = table.cycles[mask]
        if len(cycles) < window:
            continue
        indices: Iterable[int]
        if sampling == "all":
            indices = range(window - 1, len(cycles))
        elif sampling == "one_seeded_cutoff_per_engine":
            indices = (generator.randrange(window - 1, len(cycles)),)
        else:
            raise ValueError(f"Unsupported sequence sampling policy: {sampling}")
        maximum_cycle = int(cycles[-1])
        for index in indices:
            cutoff = int(cycles[index])
            rows.append(history[index - window + 1 : index + 1])
            targets.append(float(min(target_cap, maximum_cycle - cutoff)))
            selected_ids.append(identity)
            cutoffs.append(cutoff)
    if not rows:
        raise ValueError("No eligible engine sequences were produced.")
    return SequenceDataset(
        tuple(selected_ids),
        np.asarray(cutoffs, dtype=np.int64),
        np.stack(rows),
        np.asarray(targets, dtype=np.float64),
    )
