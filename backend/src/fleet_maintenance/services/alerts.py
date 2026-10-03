from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import Alert, AlertAcknowledgement


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
