from dataclasses import dataclass
from typing import Literal

AlertState = Literal["normal", "warning", "critical", "data_unavailable"]
QualityState = Literal["eligible", "withheld"]


@dataclass(frozen=True)
class AlertPolicy:
    warning_cycles: float = 45.0
    critical_cycles: float = 20.0
    clear_margin_cycles: float = 8.0
    version: str = "demo-v1"


DEFAULT_POLICY = AlertPolicy()


def next_alert_state(
    previous: AlertState,
    estimate_cycles: float | None,
    quality_state: QualityState,
    policy: AlertPolicy = DEFAULT_POLICY,
) -> AlertState:
    if quality_state == "withheld" or estimate_cycles is None:
        return "data_unavailable" if previous == "normal" else previous
    if estimate_cycles <= policy.critical_cycles:
        return "critical"
    if estimate_cycles <= policy.warning_cycles:
        return "warning"
    if (
        previous == "critical"
        and estimate_cycles <= policy.critical_cycles + policy.clear_margin_cycles
    ):
        return "critical"
    if (
        previous == "warning"
        and estimate_cycles <= policy.warning_cycles + policy.clear_margin_cycles
    ):
        return "warning"
    return "normal"


def next_threshold_state(
    previous: AlertState,
    estimate_cycles: float | None,
    quality_state: QualityState,
    policy: AlertPolicy = DEFAULT_POLICY,
) -> AlertState:
    """Evaluate the transparent no-hysteresis comparison policy."""
    if quality_state == "withheld" or estimate_cycles is None:
        return "data_unavailable" if previous in {"normal", "data_unavailable"} else previous
    if estimate_cycles <= policy.critical_cycles:
        return "critical"
    if estimate_cycles <= policy.warning_cycles:
        return "warning"
    return "normal"
