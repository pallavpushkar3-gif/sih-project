from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import Alert, AlertAcknowledgement, Assessment


def acknowledge_alert(session: Session, alert_id: str, actor: str) -> Alert:
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise LookupError(alert_id)
    existing = session.scalar(
        select(AlertAcknowledgement).where(
            AlertAcknowledgement.alert_id == alert_id,
            AlertAcknowledgement.actor == actor,
        )
    )
    if existing is None:
        try:
            with session.begin_nested():
                session.add(AlertAcknowledgement(alert_id=alert_id, actor=actor))
                session.flush()
        except IntegrityError:
            # The unique constraint makes concurrent repeats converge on one review row.
            pass
    alert.acknowledged_by = actor
    session.commit()
    session.refresh(alert)
    return alert


def current_alerts(session: Session) -> list[Alert]:
    from fleet_maintenance.persistence.models import Assessment

    rows = session.scalars(
        select(Alert)
        .outerjoin(Assessment, Assessment.id == Alert.assessment_id)
        .order_by(Assessment.created_at.desc().nulls_last(), Alert.id.desc())
    ).all()
    latest: dict[str, Alert] = {}
    for alert in rows:
        latest.setdefault(alert.component_id, alert)
    return [latest[key] for key in sorted(latest)]


def record_assessment_alert(session: Session, assessment: Assessment) -> None:
    """Only a current cutoff may change the live policy state; old replay stays historical."""
    import uuid
    from dataclasses import asdict

    from fleet_maintenance.persistence.models import Component, ImportRecord, OutboxEvent
    from fleet_maintenance.services.alert_episodes import EpisodeState, advance

    component = session.scalar(
        select(Component).where(Component.id == assessment.component_id).with_for_update()
    )
    assert component is not None
    latest = session.scalar(
        select(ImportRecord)
        .where(ImportRecord.component_id == component.id)
        .order_by(ImportRecord.created_at.desc(), ImportRecord.id.desc())
        .limit(1)
    )
    if (
        latest is None
        or latest.id != assessment.input_version
        or assessment.cutoff_cycle != component.current_cycle
    ):
        return
    previous = next(
        (alert for alert in current_alerts(session) if alert.component_id == component.id), None
    )
    from typing import Any, cast

    prior = (
        EpisodeState(**cast(dict[str, Any], previous.policy_context.get("episode", {})))
        if previous and previous.policy_context
        else EpisodeState(
            state=cast(Any, previous.state),
            episode_id=f"legacy-concern:{previous.id}"
            if previous.state in {"warning", "critical"}
            else None,
        )
        if previous
        else EpisodeState()
    )
    eligible = assessment.state == "available"
    identifier = f"alert-{uuid.uuid5(uuid.NAMESPACE_URL, assessment.id + 'demo-v2').hex}"
    episode = advance(
        prior,
        assessment.cutoff_cycle or 0,
        assessment.estimate_cycles,
        eligible,
        f"episode-{uuid.uuid5(uuid.NAMESPACE_URL, assessment.id + 'demo-v2').hex}",
    )
    if session.get(Alert, identifier) is None:
        session.add(
            Alert(
                id=identifier,
                component_id=component.id,
                state=episode.state,
                reason="Configured demonstration policy on current cycles; "
                + (
                    "assessment withheld, concern retained."
                    if not eligible
                    else "point estimate evaluated against 45/20-cycle thresholds."
                ),
                policy_version="demo-v2",
                assessment_id=assessment.id,
                episode_id=episode.episode_id,
                policy_context={
                    "episode": asdict(episode),
                    "unit": "cycles",
                    "persistence_samples": 2,
                    "cooldown_cycles": 10,
                    "freshness_cycles": 10,
                    "qualification": "demonstration settings",
                },
            )
        )

        if episode.episode_id and (
            prior.episode_id != episode.episode_id or prior.state != episode.state
        ):
            session.add(
                OutboxEvent(
                    topic="application.alert",
                    payload={
                        "event_type": "alert.review_required",
                        "component_id": component.id,
                        "assessment_id": assessment.id,
                        "episode_id": episode.episode_id,
                        "policy_version": "demo-v2",
                        "state": episode.state,
                        "next_action": "Review evidence; request a fresh resource-aware proposal",
                    },
                )
            )
