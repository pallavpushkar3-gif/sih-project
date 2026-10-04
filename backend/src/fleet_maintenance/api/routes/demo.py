"""Customer rehearsal is deliberately restricted to local demo authentication."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor, require_planner
from fleet_maintenance.api.routes.jobs import serialize
from fleet_maintenance.domain.contracts.api import JobResponse
from fleet_maintenance.domain.contracts.demo import (
    HistoryImport,
    TrialCatalogResponse,
    TrialRequest,
    TrialResponse,
)
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Scenario
from fleet_maintenance.services.approvals import ApprovalConflict
from fleet_maintenance.services.customer_trials import (
    catalog,
    create_trial,
    get_trial,
    trial_planning_snapshot,
)
from fleet_maintenance.services.jobs import submit_job
from fleet_maintenance.settings import get_settings


def local_demo() -> None:
    settings = get_settings()
    if settings.environment != "development" or settings.authentication_mode != "demo":
        raise HTTPException(403, "Customer trials are available only in the local demonstrator.")


router = APIRouter(prefix="/demo", tags=["customer trials"], dependencies=[Depends(local_demo)])


@router.get("/catalog", response_model=TrialCatalogResponse)
def trial_catalog(session: Session = Depends(get_session)) -> TrialCatalogResponse:
    return catalog(session)


@router.get("/trials", response_model=list[TrialResponse])
def trial_list(session: Session = Depends(get_session)) -> list[TrialResponse]:
    return [
        get_trial(session, item.id)
        for item in session.scalars(
            select(Scenario).where(Scenario.id.startswith("trial-")).order_by(Scenario.id)
        )
        if item.assumptions.get("customer_trial")
    ]


@router.get("/trials/{trial_id}", response_model=TrialResponse)
def trial_detail(trial_id: str, session: Session = Depends(get_session)) -> TrialResponse:
    try:
        return get_trial(session, trial_id)
    except LookupError:
        raise HTTPException(404, "Trial not found") from None


@router.post("/trials", response_model=TrialResponse)
def trial_create(
    body: TrialRequest,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> TrialResponse:
    require_planner(actor)
    try:
        return create_trial(session, body, actor.id)
    except ApprovalConflict as exc:
        session.rollback()
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        session.rollback()
        raise HTTPException(422, str(exc)) from exc


@router.post("/trials/{trial_id}/planning", response_model=JobResponse)
def trial_plan(
    trial_id: str, session: Session = Depends(get_session), actor: Actor = Depends(current_actor)
) -> dict[str, object]:
    require_planner(actor)
    try:
        snapshot = trial_planning_snapshot(session, trial_id)
        return serialize(submit_job(session, "planning", snapshot, owner=actor.id))
    except LookupError:
        raise HTTPException(404, "Trial not found") from None
    except (ApprovalConflict, ValueError) as exc:
        session.rollback()
        raise HTTPException(409, str(exc)) from exc


@router.get("/trials/{trial_id}/jobs", response_model=list[JobResponse])
def trial_jobs(trial_id: str, session: Session = Depends(get_session)) -> list[dict[str, object]]:
    from fleet_maintenance.persistence.models import Job

    try:
        trial = get_trial(session, trial_id)
    except LookupError:
        raise HTTPException(404, "Trial not found") from None
    query = (
        select(Job)
        .where(
            or_(
                Job.input_payload["import_id"].as_string() == trial.import_id,
                Job.input_payload["scope_component_id"].as_string() == trial.component_id,
                Job.input_payload["scenario_id"]
                .as_string()
                .in_([trial.baseline_scenario_id, trial.supply_scenario_id]),
            )
        )
        .order_by(Job.created_at.desc(), Job.id.desc())
        .limit(100)
    )
    return [serialize(job) for job in session.scalars(query)]


@router.get("/trials/{trial_id}/history", response_model=HistoryImport)
def trial_history(trial_id: str, session: Session = Depends(get_session)) -> HistoryImport:
    from fleet_maintenance.persistence.models import ImportRecord

    try:
        trial = get_trial(session, trial_id)
    except LookupError:
        raise HTTPException(404, "Trial not found") from None
    record = session.get(ImportRecord, trial.import_id)
    assert record is not None
    return HistoryImport.model_validate(
        {
            "source_version": record.source_version,
            "engine_identity": record.engine_identity,
            "rows": record.rows,
        }
    )
