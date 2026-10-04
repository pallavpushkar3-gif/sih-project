from fleet_maintenance.science.data.eligibility import history_findings


def history():
    return [
        {"cycle": cycle, "values": [0.0, 0.0, 100.0] + [float(cycle)] * 21}
        for cycle in range(1, 31)
    ]


def test_flat_missing_short_and_out_of_regime_are_withheld():
    assert not history_findings(history(), 30, {})
    assert history_findings(history()[:29], 30, {})[0]["code"] == "insufficient_history"
    missing = history()
    missing[0]["values"][4] = None
    assert history_findings(missing, 30, {})[0]["code"] == "missing_values"
    shifted = history()
    shifted[-1]["values"][2] = 60
    assert history_findings(shifted, 30, {})[0]["code"] == "unsupported_conditions"
    flat = [{"cycle": cycle, "values": [0.0, 0.0, 100.0] + [1.0] * 21} for cycle in range(1, 31)]
    assert history_findings(flat, 30, {})[0]["code"] == "flat_history"
