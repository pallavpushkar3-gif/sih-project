from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor, require_engineer
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.services.approvals import ApprovalConflict
from fleet_maintenance.services.assessments import register_model
from fleet_maintenance.services.imports import import_history
from fleet_maintenance.services.jobs import submit_job

router = APIRouter(tags=["evidence"])


class HistoryRow(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    cycle: int = Field(strict=True, ge=1)
    values: list[FiniteFloat | None] = Field(min_length=24, max_length=24)


class HistoryImport(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_version: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    engine_identity: str = Field(
        pattern=r"^NASA_CMAPSS:FD001:(train|test):[1-9][0-9]*$", max_length=120
    )
    rows: list[HistoryRow] = Field(min_length=1, max_length=10000)
    previous_id: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def consecutive(self) -> "HistoryImport":
        if [row.cycle for row in self.rows] != list(range(1, len(self.rows) + 1)):
            raise ValueError("Cycles must start at one and be consecutive and ordered")
        return self


class Registration(BaseModel):
    version: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    directory: str = Field(min_length=1, max_length=240)


class AssessmentRequest(BaseModel):
    import_id: str = Field(min_length=1, max_length=64)
    model_id: str = Field(min_length=1, max_length=64)
    cutoff_cycle: int = Field(strict=True, ge=1)


@router.post("/components/{component_id}/imports")
def import_component(
    component_id: str,
    body: HistoryImport,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    require_engineer(actor)
    try:
        record = import_history(
            session,
            component_id,
            body.source_version,
            body.engine_identity,
            [row.model_dump() for row in body.rows],
            body.previous_id,
            actor.id,
        )
        return {
            "id": record.id,
            "source_version": record.source_version,
            "sha256": record.sha256,
            "rows": len(record.rows),
            "previous_id": record.previous_id,
        }
    except LookupError:
        raise HTTPException(404, "Component not found") from None
    except ApprovalConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/models/registrations")
def model_registration(
    body: Registration,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    if actor.role != "administrator":
        raise HTTPException(403, "Administrator role required")
    try:
        record = register_model(session, body.version, body.directory, actor.id)
        return {"id": record.id, "hashes": record.hashes, "scientific_release": "not_qualified"}
    except (ValueError, OSError, KeyError) as exc:
        raise HTTPException(422, "Artifact directory or manifest is invalid") from exc
    except ApprovalConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/jobs/assessment")
def submit_assessment(
    body: AssessmentRequest,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    require_engineer(actor)
    from fleet_maintenance.persistence.models import ImportRecord, ModelRegistration

    history = session.get(ImportRecord, body.import_id)
    if history is None or session.get(ModelRegistration, body.model_id) is None:
        raise HTTPException(404, "Import or model not found")
    if body.cutoff_cycle > len(history.rows):
        raise HTTPException(422, "Cutoff outside imported history")
    job = submit_job(session, "assessment", body.model_dump(), owner=actor.id)
    from fleet_maintenance.api.routes.jobs import serialize

    return serialize(job)
