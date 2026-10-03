from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.api import JobResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Job
from fleet_maintenance.services.jobs import JobConflict, request_cancellation

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse])
def jobs(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [
        {
            "id": j.id,
            "kind": j.kind,
            "state": j.state,
            "attempt": j.attempt,
            "result": j.result_payload,
        }
        for j in session.scalars(select(Job)).all()
    ]


@router.get("/{job_id}", response_model=JobResponse)
def job(job_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    j = session.get(Job, job_id)
    if j is None:
        raise HTTPException(404, "Job not found")
    return {
        "id": j.id,
        "kind": j.kind,
        "state": j.state,
        "attempt": j.attempt,
        "result": j.result_payload,
    }


@router.post("/{job_id}/cancellation", response_model=JobResponse)
def cancel(job_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    try:
        item = request_cancellation(session, job_id)
    except LookupError:
        raise HTTPException(404, "Job not found") from None
    except JobConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    return {
        "id": item.id,
        "kind": item.kind,
        "state": item.state,
        "attempt": item.attempt,
        "result": item.result_payload,
    }
