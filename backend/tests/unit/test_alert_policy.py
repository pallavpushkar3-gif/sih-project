from fleet_maintenance.services.alert_policy import AlertPolicy, next_alert_state


def test_hysteresis_prevents_warning_flap():
    policy = AlertPolicy(warning_cycles=45, clear_margin_cycles=8)
    assert next_alert_state("warning", 50, "eligible", policy) == "warning"
    assert next_alert_state("warning", 54, "eligible", policy) == "normal"


def test_withheld_does_not_clear_active_alert():
    assert next_alert_state("critical", None, "withheld") == "critical"
