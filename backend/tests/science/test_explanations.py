import numpy as np
import pytest

from fleet_maintenance.science.prediction.explanations import (
    explanation_evidence,
    feature_sensitivities,
)


def test_sensitivities_match_analytic_linear_reference_and_preserve_inputs():
    coefficients = np.asarray([2.0, -3.0, 0.0])
    vector = np.asarray([4.0, 5.0, 7.0])
    before = vector.copy()

    def predict(rows):
        return rows @ coefficients + 11.0

    np.testing.assert_allclose(feature_sensitivities(predict, vector), [8.0, -15.0, 0.0])
    np.testing.assert_array_equal(vector, before)
    evidence = explanation_evidence(predict, vector, ("a", "b", "c"))
    assert evidence["contributions"][0] == {"feature": "b", "difference_cycles": -15.0}
    assert "not additive" in evidence["limitations"]


def test_sensitivity_rejects_invalid_intervention_outputs():
    vector = np.asarray([1.0, 2.0])
    with pytest.raises(ValueError, match="finite"):
        feature_sensitivities(lambda rows: np.full(len(rows), np.nan), vector)
    with pytest.raises(ValueError, match="match"):
        feature_sensitivities(lambda rows: np.ones(1), vector)
    with pytest.raises(ValueError, match="unique"):
        explanation_evidence(lambda rows: rows.sum(axis=1), vector, ("a", "a"))
