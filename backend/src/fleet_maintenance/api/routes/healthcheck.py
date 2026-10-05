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
from fleet_maintenance.settings import get_settings

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
    if get_settings().environment == "tunnel_demo":
        from fleet_maintenance.artifacts.storage import artifact_directory, verify_hashes
        from fleet_maintenance.persistence.models import ModelRegistration
        from fleet_maintenance.services.customer_trials import MODEL_ID, catalog

        try:
            if not catalog(session).available:
                raise ValueError("Missing public demo bundle")
            model = session.get(ModelRegistration, MODEL_ID)
            assert model is not None
            verify_hashes(
                artifact_directory(get_settings().artifact_root, model.artifact_directory),
                model.hashes,
            )
        except Exception as exc:
            raise HTTPException(503, "Demo model/history bundle is unavailable") from exc
    return {"status": "ready", "database": "ok"}
