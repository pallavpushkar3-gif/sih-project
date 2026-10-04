"""A causal episode policy; repeated identical cutoffs do not supply persistence."""

from dataclasses import dataclass, replace

from fleet_maintenance.services.alert_policy import AlertPolicy, AlertState, next_alert_state


@dataclass(frozen=True)
class EpisodePolicy:
    version: str = "demo-v2"
    threshold: AlertPolicy = AlertPolicy(version="demo-v2")
    persistence_samples: int = 2
    cooldown_cycles: int = 10
    freshness_cycles: int = 10


@dataclass(frozen=True)
class EpisodeState:
    state: AlertState = "normal"
    episode_id: str | None = None
    pending_samples: int = 0
    last_cycle: int | None = None
    closed_cycle: int | None = None
    opened_cycle: int | None = None


def advance(
    previous: EpisodeState,
    cycle: int,
    estimate: float | None,
    eligible: bool,
    identity: str,
    policy: EpisodePolicy = EpisodePolicy(),
) -> EpisodeState:
    if previous.last_cycle is not None and cycle <= previous.last_cycle:
        # Corrections are not new persistence samples. A corrected current snapshot can
        # nevertheless escalate an urgent concern; it cannot retroactively clear one.
        if (
            cycle == previous.last_cycle
            and eligible
            and estimate is not None
            and (estimate <= policy.threshold.critical_cycles)
        ):
            return replace(
                previous,
                state="critical",
                episode_id=previous.episode_id or identity,
                opened_cycle=previous.opened_cycle or cycle,
            )
        return previous
    if not eligible or estimate is None:
        return replace(
            previous,
            state=previous.state if previous.episode_id else "data_unavailable",
            last_cycle=cycle,
        )  # Missing evidence cannot resolve an open concern.
    if previous.last_cycle is not None and cycle - previous.last_cycle > policy.freshness_cycles:
        previous = replace(previous, pending_samples=0)
    next_state = next_alert_state(previous.state, estimate, "eligible", policy.threshold)
    count = previous.pending_samples + 1 if next_state in {"warning", "critical"} else 0
    if next_state == "critical" or (
        next_state == "warning"
        and (previous.episode_id is not None or count >= policy.persistence_samples)
    ):
        if (
            previous.closed_cycle is not None
            and cycle - previous.closed_cycle < policy.cooldown_cycles
            and next_state != "critical"
        ):
            return replace(previous, last_cycle=cycle, pending_samples=count)
        return replace(
            previous,
            state=next_state,
            episode_id=previous.episode_id or identity,
            last_cycle=cycle,
            pending_samples=count,
            opened_cycle=previous.opened_cycle if previous.episode_id else cycle,
        )
    if next_state == "warning":
        return replace(previous, state="normal", last_cycle=cycle, pending_samples=count)
    return EpisodeState(
        state=next_state,
        last_cycle=cycle,
        closed_cycle=cycle if previous.episode_id else previous.closed_cycle,
    )
