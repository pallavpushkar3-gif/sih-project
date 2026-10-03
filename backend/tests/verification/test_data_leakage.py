from fleet_maintenance.science.data.splitting import assert_disjoint, split_engines


def test_engine_partitions_are_disjoint_and_deterministic():
    ids = [f"FD001:train:{n}" for n in range(100)]
    first = split_engines(ids)
    second = split_engines(ids)
    assert first == second
    assert_disjoint(first)
    assert len(first.fit) == 70 and len(first.validation) == 15 and len(first.calibration) == 15


def test_duplicate_engine_identity_is_rejected_before_split():
    import pytest

    with pytest.raises(ValueError, match="unique"):
        split_engines(["FD001:train:1", "FD001:train:1"])
