from pathlib import Path

import numpy as np
import pytest

from fleet_maintenance.science.data.loaders import load_cmapss_table, load_rul_labels


def write_rows(path: Path, rows: list[list[float]]) -> None:
    np.savetxt(path, np.asarray(rows), fmt="%.6f")


def test_loader_namespaces_engines_and_checks_cycles(tmp_path: Path):
    path = tmp_path / "train_FD001.txt"
    rows = [
        [1, 1, *([0.0] * 24)],
        [1, 2, *([1.0] * 24)],
        [2, 1, *([2.0] * 24)],
    ]
    write_rows(path, rows)
    table = load_cmapss_table(path, "FD001", "train")
    assert table.features.shape == (3, 24)
    assert table.identities[0] == "NASA_CMAPSS:FD001:train:1"
    assert table.identities[-1] == "NASA_CMAPSS:FD001:train:2"


def test_loader_rejects_cycle_gap(tmp_path: Path):
    path = tmp_path / "train_FD001.txt"
    write_rows(path, [[1, 1, *([0.0] * 24)], [1, 3, *([0.0] * 24)]])
    with pytest.raises(ValueError, match="missing, duplicated, or out of order"):
        load_cmapss_table(path, "FD001", "train")


def test_rul_label_count_is_checked(tmp_path: Path):
    path = tmp_path / "RUL_FD001.txt"
    write_rows(path, [[10], [20]])
    with pytest.raises(ValueError, match="Expected 3"):
        load_rul_labels(path, 3)
