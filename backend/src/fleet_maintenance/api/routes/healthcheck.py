from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.api import HealthResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import (
    Alert,
    Job,
    JobAttempt,
    MaintenanceResource,
    PartArrival,
    User,
)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_model=HealthResponse)
def ready(session: Session = Depends(get_session)) -> dict[str, str]:
    try:
        session.execute(text("select 1"))
        session.execute(select(Job.owner).limit(1))
        session.execute(select(JobAttempt.id).limit(1))
        session.execute(select(PartArrival.id).limit(1))
        session.execute(select(User.password_hash).limit(1))
        session.execute(select(MaintenanceResource.id).limit(1))
        session.execute(select(Alert.episode_id).limit(1))
    except Exception as exc:
        raise HTTPException(503, "database unavailable") from exc
    return {"status": "ready", "database": "ok"}
