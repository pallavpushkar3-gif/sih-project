from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.api import HealthResponse
from fleet_maintenance.persistence.database import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_model=HealthResponse)
def ready(session: Session = Depends(get_session)) -> dict[str, str]:
    try:
        session.execute(text("select 1"))
    except Exception as exc:
        raise HTTPException(503, "database unavailable") from exc
    return {"status": "ready", "database": "ok"}
