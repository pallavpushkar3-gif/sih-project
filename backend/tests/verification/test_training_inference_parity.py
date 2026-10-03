import numpy as np

from fleet_maintenance.science.data.preprocessing import Standardizer


def test_frozen_transform_replays_identically():
    rows = [{"a": 1.0, "b": 10.0}, {"a": 3.0, "b": 14.0}]
    fitted = Standardizer.fit(rows, ("a", "b"))
    assert np.array_equal(fitted.transform(rows), fitted.transform(rows))
    assert fitted.features == ("a", "b")
