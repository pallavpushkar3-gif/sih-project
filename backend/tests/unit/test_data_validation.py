from fleet_maintenance.science.data.validation import assessment_state, validate_history


def test_valid_history_is_eligible():
    findings = validate_history(
        [
            {"cycle": 1, "sensor_2": 10.0},
            {"cycle": 2, "sensor_2": 11.0},
        ]
    )
    assert findings == []
    assert assessment_state(findings) == "eligible"


def test_non_integral_cycle_and_non_finite_sensor_are_withheld():
    findings = validate_history([{"cycle": 1.5, "sensor_2": float("nan")}])
    assert {item.code for item in findings} == {"invalid_cycle", "invalid_sensor"}
    assert assessment_state(findings) == "withheld"
