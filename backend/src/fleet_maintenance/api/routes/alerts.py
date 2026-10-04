from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor, require_engineer
from fleet_maintenance.domain.contracts.api import AlertResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Alert, AlertAcknowledgement
from fleet_maintenance.services.alerts import acknowledge_alert, current_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


def serialize(session: Session, alert: Alert) -> dict[str, object]:
    acknowledgements = session.scalars(
        select(AlertAcknowledgement)
        .where(AlertAcknowledgement.alert_id == alert.id)
        .order_by(AlertAcknowledgement.created_at)
    ).all()
    return {
        "id": alert.id,
        "component_id": alert.component_id,
        "state": alert.state,
        "reason": alert.reason,
        "policy_version": alert.policy_version,
        "assessment_id": alert.assessment_id,
        "acknowledged_by": alert.acknowledged_by,
        "acknowledgements": [
            {"actor": item.actor, "created_at": item.created_at} for item in acknowledgements
        ],
    }


@router.get("", response_model=list[AlertResponse])
def list_alerts(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [serialize(session, alert) for alert in current_alerts(session)]


@router.post("/{alert_id}/acknowledgements", response_model=AlertResponse)
def acknowledge(
    alert_id: str,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    require_engineer(actor)
    try:
        alert = acknowledge_alert(session, alert_id, actor.id)
    except LookupError:
        raise HTTPException(404, "Alert not found") from None
    return serialize(session, alert)


@router.get("/history/{component_id}", response_model=list[AlertResponse])
def history(component_id: str, session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [
        serialize(session, alert)
        for alert in session.scalars(select(Alert).where(Alert.component_id == component_id)).all()
    ]
