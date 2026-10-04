import numpy as np
import pytest

from fleet_maintenance.science.data.loaders import CmapssTable
from fleet_maintenance.science.data.robustness import InterventionSpec, prepare_intervention


def _table() -> CmapssTable:
    engines = np.repeat(np.asarray([1, 2]), 10).astype(np.int64)
    cycles = np.tile(np.arange(1, 11), 2).astype(np.int64)
    features = np.column_stack(
        (cycles, cycles * 2, cycles * 3, engines + cycles, engines - cycles)
    ).astype(np.float64)
    identities = tuple(f"NASA_CMAPSS:FD001:train:{engine}" for engine in engines)
    return CmapssTable(
        identities,
        engines,
        cycles,
        features,
        ("setting_1", "setting_2", "setting_3", "sensor_1", "sensor_2"),
    )


@pytest.mark.science
def test_contiguous_outage_is_imputed_but_withheld_and_fit_rows_are_unchanged() -> None:
    table = _table()
    result = prepare_intervention(
        table,
        fit_engine_ids=("NASA_CMAPSS:FD001:train:1",),
        evaluation_engine_ids=("NASA_CMAPSS:FD001:train:2",),
        cutoffs=np.asarray([10], dtype=np.int64),
        window=5,
        maximum_missing_fraction=0.5,
        maximum_contiguous_missing_cycles=2,
        spec=InterventionSpec("outage", "contiguous_outage", length_cycles=3, feature="sensor_1"),
        seed=7,
    )

    assert result.modified_values == 3
    assert result.withheld == (True,)
    assert np.array_equal(result.table.features[:10], table.features[:10])
    assert np.isfinite(result.table.features).all()


@pytest.mark.science
def test_random_missingness_is_seeded_and_retains_provenance_mask() -> None:
    arguments = {
        "fit_engine_ids": ("NASA_CMAPSS:FD001:train:1",),
        "evaluation_engine_ids": ("NASA_CMAPSS:FD001:train:2",),
        "cutoffs": np.asarray([10], dtype=np.int64),
        "window": 5,
        "maximum_missing_fraction": 1.0,
        "maximum_contiguous_missing_cycles": 5,
        "spec": InterventionSpec("missing", "random_missing", rate=0.5),
        "seed": 11,
    }
    first = prepare_intervention(_table(), **arguments)
    replay = prepare_intervention(_table(), **arguments)

    assert np.array_equal(first.missing_mask, replay.missing_mask)
    assert first.modified_values > 0
    assert first.withheld == (False,)
