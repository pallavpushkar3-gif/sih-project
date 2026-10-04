from dataclasses import dataclass
from statistics import fmean

from fleet_maintenance.services.alert_episodes import EpisodePolicy, EpisodeState, advance
from fleet_maintenance.services.alert_policy import (
    AlertPolicy,
    AlertState,
    QualityState,
    next_alert_state,
    next_threshold_state,
)


@dataclass(frozen=True)
class AlertObservation:
    event_id: str
    cycle: int
    estimate_cycles: float | None
    quality_state: QualityState = "eligible"


@dataclass(frozen=True)
class AlertHistory:
    history_id: str
    observations: tuple[AlertObservation, ...]
    reference_event_cycle: int | None
    censored: bool = False


@dataclass(frozen=True)
class HistoryMetrics:
    history_id: str
    warning_lead_cycles: int | None
    missed_event: bool
    false_alert_episodes: int
    recommendation_changes: int
    duplicate_deliveries: int


@dataclass(frozen=True)
class AggregateMetrics:
    event_count: int
    detected_event_count: int
    missed_events: int
    false_alert_episodes: int
    recommendation_changes: int
    mean_warning_lead_cycles: float | None
    histories: tuple[HistoryMetrics, ...]


def evaluate_history(
    history: AlertHistory,
    policy: AlertPolicy,
    *,
    warning_horizon_cycles: int,
    hysteresis: bool,
    episodes: bool = False,
) -> HistoryMetrics:
    if warning_horizon_cycles <= 0:
        raise ValueError("Warning horizon must be positive.")

    state: AlertState = "normal"
    last_cycle: int | None = None
    seen: dict[str, AlertObservation] = {}
    actionable_cycles: list[int] = []
    false_alert_episodes = 0
    recommendation_changes = 0
    duplicate_deliveries = 0
    actionable = False
    episode_state = EpisodeState()
    window_start = (
        None
        if history.reference_event_cycle is None
        else history.reference_event_cycle - warning_horizon_cycles
    )

    transition = next_alert_state if hysteresis else next_threshold_state
    for observation in history.observations:
        prior = seen.get(observation.event_id)
        if prior is not None:
            if prior != observation:
                raise ValueError(f"Conflicting repeated event {observation.event_id}.")
            duplicate_deliveries += 1
            continue
        if last_cycle is not None and observation.cycle <= last_cycle:
            raise ValueError("New alert observations must be strictly chronological.")
        seen[observation.event_id] = observation
        last_cycle = observation.cycle

        next_state = transition(
            state,
            observation.estimate_cycles,
            observation.quality_state,
            policy,
        )
        if episodes:
            episode_state = advance(
                episode_state,
                observation.cycle,
                observation.estimate_cycles,
                observation.quality_state == "eligible",
                observation.event_id,
                EpisodePolicy(threshold=policy),
            )
            next_state = episode_state.state
        next_actionable = next_state in {"warning", "critical"}
        if next_state != state:
            recommendation_changes += 1
        if next_actionable:
            if (
                history.reference_event_cycle is not None
                and window_start is not None
                and window_start <= observation.cycle <= history.reference_event_cycle
            ):
                actionable_cycles.append(observation.cycle)
            if (
                not actionable
                and not (history.censored and window_start is None)
                and (window_start is None or observation.cycle < window_start)
            ):
                false_alert_episodes += 1
        state = next_state
        actionable = next_actionable

    has_reference_event = history.reference_event_cycle is not None
    missed_event = has_reference_event and not actionable_cycles
    warning_lead = None
    if actionable_cycles and history.reference_event_cycle is not None:
        warning_lead = history.reference_event_cycle - actionable_cycles[0]
    return HistoryMetrics(
        history.history_id,
        warning_lead,
        missed_event,
        false_alert_episodes,
        recommendation_changes,
        duplicate_deliveries,
    )


def aggregate_metrics(histories: tuple[HistoryMetrics, ...]) -> AggregateMetrics:
    event_count = sum(
        item.warning_lead_cycles is not None or item.missed_event for item in histories
    )
    leads = [item.warning_lead_cycles for item in histories if item.warning_lead_cycles is not None]
    return AggregateMetrics(
        event_count=event_count,
        detected_event_count=len(leads),
        missed_events=sum(item.missed_event for item in histories),
        false_alert_episodes=sum(item.false_alert_episodes for item in histories),
        recommendation_changes=sum(item.recommendation_changes for item in histories),
        mean_warning_lead_cycles=fmean(leads) if leads else None,
        histories=histories,
    )


def evaluate_policy(
    histories: tuple[AlertHistory, ...],
    policy: AlertPolicy,
    *,
    warning_horizon_cycles: int,
    hysteresis: bool,
    episodes: bool = False,
) -> AggregateMetrics:
    return aggregate_metrics(
        tuple(
            evaluate_history(
                history,
                policy,
                warning_horizon_cycles=warning_horizon_cycles,
                hysteresis=hysteresis,
                episodes=episodes,
            )
            for history in histories
        )
    )
