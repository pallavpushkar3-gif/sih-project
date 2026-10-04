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
    from typing import cast

    from fleet_maintenance.persistence.models import Component, ImportRecord
    from fleet_maintenance.services.alert_policy import DEFAULT_POLICY, AlertState, next_alert_state

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
    prior = cast(AlertState, previous.state if previous else "normal")
    eligible = assessment.state == "available"
    state = next_alert_state(
        prior, assessment.estimate_cycles, "eligible" if eligible else "withheld"
    )
    identifier = (
        f"alert-{uuid.uuid5(uuid.NAMESPACE_URL, assessment.id + DEFAULT_POLICY.version).hex}"
    )
    if session.get(Alert, identifier) is None:
        session.add(
            Alert(
                id=identifier,
                component_id=component.id,
                state=state,
                reason="Configured demonstration policy on current cycles; "
                + (
                    "assessment withheld, concern retained."
                    if not eligible
                    else "point estimate evaluated against 45/20-cycle thresholds."
                ),
                policy_version=DEFAULT_POLICY.version,
                assessment_id=assessment.id,
            )
        )
