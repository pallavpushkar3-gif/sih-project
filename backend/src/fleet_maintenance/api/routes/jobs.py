from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor, require_planner
from fleet_maintenance.domain.contracts.api import JobResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Job, Scenario
from fleet_maintenance.services.jobs import JobConflict, request_cancellation, submit_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


def serialize(item: Job) -> dict[str, object]:
    return {
        "id": item.id,
        "kind": item.kind,
        "state": item.state,
        "attempt": item.attempt,
        "result": item.result_payload,
    }


@router.get("", response_model=list[JobResponse])
def jobs(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [serialize(item) for item in session.scalars(select(Job)).all()]


@router.get("/{job_id}", response_model=JobResponse)
def job(job_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    j = session.get(Job, job_id)
    if j is None:
        raise HTTPException(404, "Job not found")
    return serialize(j)


@router.post("/planning", response_model=JobResponse)
def submit_planning(
    session: Session = Depends(get_session), actor: Actor = Depends(current_actor)
) -> dict[str, object]:
    require_planner(actor)
    return serialize(submit_job(session, "planning", {}))


@router.post("/simulation/{scenario_id}", response_model=JobResponse)
def submit_simulation(
    scenario_id: str,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    require_planner(actor)
    if session.get(Scenario, scenario_id) is None:
        raise HTTPException(404, "Scenario not found")
    return serialize(submit_job(session, "simulation", {"scenario_id": scenario_id}))


@router.post("/{job_id}/cancellation", response_model=JobResponse)
def cancel(
    job_id: str,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    require_planner(actor)
    try:
        item = request_cancellation(session, job_id)
    except LookupError:
        raise HTTPException(404, "Job not found") from None
    except JobConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    return serialize(item)
