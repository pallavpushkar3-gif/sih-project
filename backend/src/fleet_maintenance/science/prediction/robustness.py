import hashlib
from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import NDArray

from fleet_maintenance.science.data.features import SnapshotDataset, build_snapshot_dataset
from fleet_maintenance.science.data.loaders import CmapssTable
from fleet_maintenance.science.data.robustness import InterventionSpec, prepare_intervention
from fleet_maintenance.science.data.splitting import EngineSplit
from fleet_maintenance.science.prediction.evaluation import regression_metrics
from fleet_maintenance.science.prediction.inference import BaselinePredictor


@dataclass(frozen=True)
class RobustnessMetrics:
    name: str
    kind: str
    sample_count: int
    withheld_count: int
    withholding_rate: float
    modified_values: int
    missing_values: int
    missing_mask_sha256: str
    mae_cycles: float | None
    rmse_cycles: float | None
    asymmetric_score: float | None
    interval_coverage: float | None
    mean_interval_width_cycles: float | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _subset(dataset: SnapshotDataset, eligible: NDArray[np.bool_]) -> SnapshotDataset:
    return SnapshotDataset(
        tuple(
            identity for identity, keep in zip(dataset.engine_ids, eligible, strict=True) if keep
        ),
        dataset.cutoffs[eligible],
        dataset.values[eligible],
        dataset.targets[eligible],
    )


def evaluate_intervention(
    table: CmapssTable,
    split: EngineSplit,
    predictor: BaselinePredictor,
    spec: InterventionSpec,
    *,
    calibration_quantile: float,
    target_cap: int,
    minimum_history: int,
    window: int,
    seed: int,
    maximum_missing_fraction: float,
    maximum_contiguous_missing_cycles: int,
) -> RobustnessMetrics:
    clean = build_snapshot_dataset(
        table,
        split.validation,
        minimum_history=minimum_history,
        window=window,
        target_cap=target_cap,
        sampling="one_seeded_cutoff_per_engine",
        seed=seed,
    )
    prepared = prepare_intervention(
        table,
        fit_engine_ids=split.fit,
        evaluation_engine_ids=clean.engine_ids,
        cutoffs=clean.cutoffs,
        window=window,
        maximum_missing_fraction=maximum_missing_fraction,
        maximum_contiguous_missing_cycles=maximum_contiguous_missing_cycles,
        spec=spec,
        seed=seed,
    )
    changed = build_snapshot_dataset(
        prepared.table,
        split.validation,
        minimum_history=minimum_history,
        window=window,
        target_cap=target_cap,
        sampling="one_seeded_cutoff_per_engine",
        seed=seed,
    )
    if (
        changed.engine_ids != clean.engine_ids
        or not np.array_equal(changed.cutoffs, clean.cutoffs)
        or not np.array_equal(changed.targets, clean.targets)
    ):
        raise ValueError("Intervention changed evaluation sampling or targets.")

    eligible = np.logical_not(np.asarray(prepared.withheld, dtype=np.bool_))
    eligible_count = int(eligible.sum())
    sample_count = len(clean.targets)
    withheld_count = sample_count - eligible_count
    withholding_rate = 1.0 - eligible_count / sample_count
    missing_values = int(prepared.missing_mask.sum())
    missing_mask_sha256 = hashlib.sha256(prepared.missing_mask.tobytes()).hexdigest()
    if not eligible_count:
        return RobustnessMetrics(
            name=spec.name,
            kind=spec.kind,
            sample_count=sample_count,
            withheld_count=withheld_count,
            withholding_rate=withholding_rate,
            modified_values=prepared.modified_values,
            missing_values=missing_values,
            missing_mask_sha256=missing_mask_sha256,
            mae_cycles=None,
            rmse_cycles=None,
            asymmetric_score=None,
            interval_coverage=None,
            mean_interval_width_cycles=None,
        )

    evaluated = _subset(changed, eligible)
    predictions = predictor.predict(evaluated)
    metrics = regression_metrics(evaluated.targets, predictions)
    lower = np.maximum(0.0, predictions - calibration_quantile)
    upper = np.minimum(float(target_cap), predictions + calibration_quantile)
    coverage = np.mean((evaluated.targets >= lower) & (evaluated.targets <= upper))
    return RobustnessMetrics(
        name=spec.name,
        kind=spec.kind,
        sample_count=sample_count,
        withheld_count=withheld_count,
        withholding_rate=withholding_rate,
        modified_values=prepared.modified_values,
        missing_values=missing_values,
        missing_mask_sha256=missing_mask_sha256,
        mae_cycles=metrics.mae_cycles,
        rmse_cycles=metrics.rmse_cycles,
        asymmetric_score=metrics.asymmetric_score,
        interval_coverage=float(coverage),
        mean_interval_width_cycles=float(np.mean(upper - lower)),
    )
