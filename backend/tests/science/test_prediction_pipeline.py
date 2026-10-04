import json
from pathlib import Path

import joblib
import numpy as np
import pytest

from fleet_maintenance.science.data.features import build_snapshot_dataset
from fleet_maintenance.science.data.loaders import CmapssTable
from fleet_maintenance.science.data.splitting import EngineSplit
from fleet_maintenance.science.prediction.calibration import (
    calibrate_baseline,
    conformal_quantile,
)
from fleet_maintenance.science.prediction.evaluation import regression_metrics
from fleet_maintenance.science.prediction.training import train_baseline


def _table(engine_count: int = 6, cycle_count: int = 8) -> CmapssTable:
    engines = np.repeat(np.arange(1, engine_count + 1), cycle_count).astype(np.int64)
    cycles = np.tile(np.arange(1, cycle_count + 1), engine_count).astype(np.int64)
    features = np.column_stack(
        [
            engines.astype(np.float64),
            cycles.astype(np.float64),
            (engines + cycles).astype(np.float64),
        ]
    )
    identities = tuple(f"NASA_CMAPSS:FD001:train:{engine}" for engine in engines)
    return CmapssTable(identities, engines, cycles, features, ("engine", "cycle", "sum"))


@pytest.mark.science
def test_snapshot_sampling_is_engine_separated_and_reproducible() -> None:
    table = _table()
    ids = tuple(f"NASA_CMAPSS:FD001:train:{engine}" for engine in (1, 2, 3))
    first = build_snapshot_dataset(
        table,
        ids,
        minimum_history=3,
        window=3,
        target_cap=5,
        sampling="one_seeded_cutoff_per_engine",
        seed=17,
    )
    replay = build_snapshot_dataset(
        table,
        ids,
        minimum_history=3,
        window=3,
        target_cap=5,
        sampling="one_seeded_cutoff_per_engine",
        seed=17,
    )

    assert first.engine_ids == ids
    assert np.array_equal(first.cutoffs, replay.cutoffs)
    assert np.array_equal(first.values, replay.values)
    assert np.array_equal(first.targets, replay.targets)
    assert np.all(first.targets == np.minimum(5, 8 - first.cutoffs))


@pytest.mark.science
def test_regression_metrics_reject_misaligned_values_and_penalize_late_predictions() -> None:
    with pytest.raises(ValueError, match="nonempty and aligned"):
        regression_metrics(np.asarray([1.0]), np.asarray([], dtype=np.float64))

    late = regression_metrics(np.asarray([20.0]), np.asarray([10.0]))
    early = regression_metrics(np.asarray([10.0]), np.asarray([20.0]))
    assert late.mae_cycles == early.mae_cycles == 10.0
    assert late.asymmetric_score < early.asymmetric_score


@pytest.mark.science
def test_conformal_quantile_uses_finite_sample_higher_rank() -> None:
    residuals = np.asarray([1.0, 2.0, 3.0, 4.0])
    assert conformal_quantile(residuals, 0.75) == 4.0
    with pytest.raises(ValueError, match="between zero and one"):
        conformal_quantile(residuals, 1.0)


@pytest.mark.science
def test_baseline_artifact_replays_training_transform_at_inference(tmp_path: Path) -> None:
    table = _table()
    split = EngineSplit(
        fit=tuple(f"NASA_CMAPSS:FD001:train:{engine}" for engine in (1, 2, 3, 4)),
        validation=("NASA_CMAPSS:FD001:train:5",),
        calibration=("NASA_CMAPSS:FD001:train:6",),
    )
    result = train_baseline(
        table,
        split,
        tmp_path,
        target_cap=5,
        minimum_history=3,
        window=3,
        seed=23,
    )

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    saved_model = joblib.load(tmp_path / "model.joblib")
    validation = build_snapshot_dataset(
        table,
        split.validation,
        minimum_history=3,
        window=3,
        target_cap=5,
        sampling="one_seeded_cutoff_per_engine",
        seed=23,
    )
    transform = json.loads((tmp_path / "standardizer.json").read_text())
    scaled = (validation.values - np.asarray(transform["mean"])) / np.asarray(transform["scale"])
    replay_metrics = regression_metrics(validation.targets, saved_model.predict(scaled))

    assert replay_metrics.as_dict() == result.validation.as_dict()
    assert manifest["validation_metrics"] == result.validation.as_dict()
    assert manifest["final_test_evaluated"] is False
    assert manifest["calibration_engines"] == list(split.calibration)

    calibration = calibrate_baseline(
        table,
        split,
        tmp_path,
        nominal_coverage=0.5,
        target_cap=5,
        minimum_history=3,
        window=3,
        seed=23,
    )
    calibration_manifest = json.loads((tmp_path / "calibration.json").read_text())
    assert calibration.sample_count == 1
    assert calibration.calibration_coverage == 1.0
    assert calibration_manifest["final_test_evaluated"] is False
    assert calibration_manifest["model_artifacts"] == manifest["artifacts"]


@pytest.mark.science
def test_serving_cutoff_excludes_future_and_rejects_tampered_artifacts(tmp_path: Path) -> None:
    from fleet_maintenance.science.prediction.inference import BaselinePredictor, predict_history

    table = _table()
    split = EngineSplit(
        fit=tuple(f"NASA_CMAPSS:FD001:train:{engine}" for engine in (1, 2, 3, 4)),
        validation=("NASA_CMAPSS:FD001:train:5",),
        calibration=("NASA_CMAPSS:FD001:train:6",),
    )
    train_baseline(table, split, tmp_path, target_cap=5, minimum_history=3, window=3, seed=23)
    calibrate_baseline(
        table,
        split,
        tmp_path,
        nominal_coverage=0.5,
        target_cap=5,
        minimum_history=3,
        window=3,
        seed=23,
    )
    history = table.features[table.engine_numbers == 5].copy()
    before = predict_history(tmp_path, history, 4)
    history[4:] += 100000
    after = predict_history(tmp_path, history, 4)
    assert before == after
    model_path = tmp_path / "model.joblib"
    model_path.write_bytes(model_path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="hash mismatch"):
        BaselinePredictor.load(tmp_path)


@pytest.mark.science
def test_explanation_failure_preserves_valid_prediction(tmp_path: Path, monkeypatch) -> None:
    from fleet_maintenance.science.prediction import inference

    table = _table()
    split = EngineSplit(
        fit=tuple(f"NASA_CMAPSS:FD001:train:{engine}" for engine in (1, 2, 3, 4)),
        validation=("NASA_CMAPSS:FD001:train:5",),
        calibration=("NASA_CMAPSS:FD001:train:6",),
    )
    train_baseline(table, split, tmp_path, target_cap=5, minimum_history=3, window=3, seed=23)
    calibrate_baseline(
        table,
        split,
        tmp_path,
        nominal_coverage=0.5,
        target_cap=5,
        minimum_history=3,
        window=3,
        seed=23,
    )
    history = table.features[table.engine_numbers == 5]
    before = inference.predict_history(tmp_path, history, 4)

    def fail(*args):
        raise ValueError("Invalid intervention outputs")

    monkeypatch.setattr(inference, "explanation_evidence", fail)
    after = inference.predict_history(tmp_path, history, 4)
    assert after.estimate_cycles == before.estimate_cycles
    assert (after.lower_cycles, after.upper_cycles) == (before.lower_cycles, before.upper_cycles)
    assert after.evidence["explanation"]["state"] == "unavailable"
