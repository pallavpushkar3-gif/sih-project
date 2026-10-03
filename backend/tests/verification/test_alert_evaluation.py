import pytest

from fleet_maintenance.science.alerts.evaluation import (
    AlertHistory,
    AlertObservation,
    evaluate_history,
    evaluate_policy,
)
from fleet_maintenance.services.alert_policy import AlertPolicy

POLICY = AlertPolicy(warning_cycles=45, critical_cycles=20, clear_margin_cycles=8)


def test_hysteresis_reduces_changes_without_changing_detection() -> None:
    history = AlertHistory(
        "jitter",
        (
            AlertObservation("a", 40, 60),
            AlertObservation("b", 55, 44),
            AlertObservation("c", 60, 47),
            AlertObservation("d", 65, 44),
            AlertObservation("e", 70, 48),
            AlertObservation("f", 80, 19),
        ),
        reference_event_cycle=100,
    )

    baseline = evaluate_policy((history,), POLICY, warning_horizon_cycles=45, hysteresis=False)
    candidate = evaluate_policy((history,), POLICY, warning_horizon_cycles=45, hysteresis=True)

    assert baseline.missed_events == candidate.missed_events == 0
    assert baseline.mean_warning_lead_cycles == candidate.mean_warning_lead_cycles == 45
    assert baseline.recommendation_changes == 5
    assert candidate.recommendation_changes == 2


def test_repeated_delivery_is_deduplicated_and_withheld_does_not_clear() -> None:
    warning = AlertObservation("warning", 55, 44)
    history = AlertHistory(
        "delivery",
        (
            warning,
            warning,
            AlertObservation("withheld", 60, None, "withheld"),
        ),
        reference_event_cycle=100,
    )

    result = evaluate_history(history, POLICY, warning_horizon_cycles=45, hysteresis=True)

    assert result.duplicate_deliveries == 1
    assert result.recommendation_changes == 1
    assert result.warning_lead_cycles == 45


def test_out_of_order_and_conflicting_repeated_events_are_rejected() -> None:
    out_of_order = AlertHistory(
        "order",
        (AlertObservation("a", 2, 50), AlertObservation("b", 1, 40)),
        None,
    )
    conflicting = AlertHistory(
        "repeat",
        (AlertObservation("a", 1, 50), AlertObservation("a", 1, 40)),
        None,
    )

    with pytest.raises(ValueError, match="strictly chronological"):
        evaluate_history(out_of_order, POLICY, warning_horizon_cycles=45, hysteresis=True)
    with pytest.raises(ValueError, match="Conflicting repeated event"):
        evaluate_history(conflicting, POLICY, warning_horizon_cycles=45, hysteresis=True)
