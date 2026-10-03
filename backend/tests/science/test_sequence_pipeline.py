import json
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from fleet_maintenance.science.data.features import build_sequence_dataset  # noqa: E402
from fleet_maintenance.science.data.loaders import CmapssTable  # noqa: E402
from fleet_maintenance.science.data.splitting import EngineSplit  # noqa: E402
from fleet_maintenance.science.prediction.evaluation import regression_metrics  # noqa: E402
from fleet_maintenance.science.prediction.sequence import RulLstm, SequenceRul  # noqa: E402
from fleet_maintenance.science.prediction.sequence_training import train_sequence  # noqa: E402


def _table() -> CmapssTable:
    engines = np.repeat(np.arange(1, 5), 7).astype(np.int64)
    cycles = np.tile(np.arange(1, 8), 4).astype(np.int64)
    features = np.column_stack((engines, cycles, engines + cycles)).astype(np.float64)
    identities = tuple(f"NASA_CMAPSS:FD001:train:{engine}" for engine in engines)
    return CmapssTable(identities, engines, cycles, features, ("engine", "cycle", "sum"))


@pytest.mark.science
def test_saved_sequence_model_replays_validation_predictions(tmp_path: Path) -> None:
    table = _table()
    split = EngineSplit(
        fit=("NASA_CMAPSS:FD001:train:1", "NASA_CMAPSS:FD001:train:2"),
        validation=("NASA_CMAPSS:FD001:train:3",),
        calibration=("NASA_CMAPSS:FD001:train:4",),
    )
    result = train_sequence(
        table,
        split,
        tmp_path,
        target_cap=5,
        window=3,
        seed=11,
        hidden_size=4,
        epochs=1,
        batch_size=4,
    )
    saved = torch.load(tmp_path / "model.pt", weights_only=True)
    replay = RulLstm(saved["feature_count"], saved["hidden_size"])
    replay.load_state_dict(saved["state_dict"])
    predictor = SequenceRul(replay.eval())
    transform = json.loads((tmp_path / "standardizer.json").read_text())
    validation = build_sequence_dataset(
        table,
        split.validation,
        window=3,
        target_cap=5,
        sampling="one_seeded_cutoff_per_engine",
        seed=11,
    )
    values = (validation.values - np.asarray(transform["mean"])) / np.asarray(
        transform["scale"]
    )
    replay_metrics = regression_metrics(validation.targets, predictor.predict(values))

    assert replay_metrics.as_dict() == result.validation.as_dict()
    assert result.artifact_manifest["final_test_evaluated"] is False
