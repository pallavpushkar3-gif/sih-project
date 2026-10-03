from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.api import AlertResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
def list_alerts(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [
        {
            "id": a.id,
            "component_id": a.component_id,
            "state": a.state,
            "reason": a.reason,
            "policy_version": a.policy_version,
            "assessment_id": a.assessment_id,
            "acknowledged_by": a.acknowledged_by,
        }
        for a in session.scalars(select(Alert)).all()
    ]
