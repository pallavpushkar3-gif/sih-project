from fleet_maintenance.services.alert_episodes import EpisodeState, advance


def test_episode_persistence_identity_and_withholding():
    initial = advance(EpisodeState(), 30, 44, True, "first")
    assert initial.episode_id is None
    assert advance(initial, 30, 44, True, "duplicate") == initial
    active = advance(initial, 35, 43, True, "second")
    assert active.episode_id == "second"
    withheld = advance(active, 40, None, False, "missing")
    assert withheld.state == "warning" and withheld.episode_id == active.episode_id
    critical = advance(withheld, 45, 19, True, "escalation")
    assert critical.episode_id == active.episode_id


def test_clear_and_cooldown_do_not_suppress_critical():
    active = advance(EpisodeState(), 30, 19, True, "episode")
    cleared = advance(active, 35, 70, True, "clear")
    assert cleared.state == "normal" and cleared.episode_id is None
    pending = advance(cleared, 36, 44, True, "pending")
    cooldown = advance(pending, 37, 44, True, "new")
    assert cooldown.episode_id is None
    assert advance(cooldown, 38, 19, True, "critical").episode_id == "critical"


def test_corrected_cutoff_can_escalate_without_counting_as_persistence():
    pending = advance(EpisodeState(), 35, 44, True, "pending")
    assert advance(pending, 35, 43, True, "corrected").pending_samples == 1
    urgent = advance(pending, 35, 18, True, "corrected-critical")
    assert urgent.state == "critical" and urgent.episode_id == "corrected-critical"
    assert advance(urgent, 35, 80, True, "correction").episode_id == urgent.episode_id


def test_censored_future_is_not_counted_as_verified_false_alarm():
    from fleet_maintenance.science.alerts.evaluation import (
        AlertHistory,
        AlertObservation,
        evaluate_history,
    )
    from fleet_maintenance.services.alert_policy import AlertPolicy

    observed = AlertHistory("truncated", (AlertObservation("observed", 30, 18),), None, True)
    result = evaluate_history(
        observed, AlertPolicy(), warning_horizon_cycles=45, hysteresis=True, episodes=True
    )
    assert result.false_alert_episodes == 0
    assert not result.missed_event
