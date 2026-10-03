import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import Job, OutboxEvent


class JobConflict(Exception):
    pass


def _event(session: Session, job: Job, event_type: str) -> None:
    session.add(
        OutboxEvent(
            topic="application.job",
            payload={
                "event_type": event_type,
                "job_id": job.id,
                "kind": job.kind,
                "state": job.state,
                "attempt": job.attempt,
            },
        )
    )


def submit_job(session: Session, kind: str, input_payload: dict[str, object]) -> Job:
    job = Job(
        id=f"job-{uuid.uuid4().hex}",
        kind=kind,
        state="queued",
        attempt=0,
        input_payload=input_payload,
    )
    session.add(job)
    _event(session, job, "job.queued")
    session.commit()
    session.refresh(job)
    return job


def claim_job(session: Session, job_id: str) -> Job:
    job = session.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if job is None:
        raise LookupError(job_id)
    if job.state != "queued":
        raise JobConflict(f"Job {job_id} is not queued.")
    job.attempt += 1
    job.state = "running"
    _event(session, job, "job.running")
    session.commit()
    session.refresh(job)
    return job


def accept_result(
    session: Session, job_id: str, attempt: int, result_payload: dict[str, object]
) -> Job:
    job = session.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if job is None:
        raise LookupError(job_id)
    if job.state != "running" or job.attempt != attempt:
        raise JobConflict("The result belongs to a stale or ineligible attempt.")
    job.result_payload = result_payload
    job.state = "succeeded"
    _event(session, job, "job.succeeded")
    session.commit()
    session.refresh(job)
    return job


def fail_attempt(session: Session, job_id: str, attempt: int, code: str) -> Job:
    job = session.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if job is None:
        raise LookupError(job_id)
    if job.state not in {"running", "cancellation_requested"} or job.attempt != attempt:
        raise JobConflict("The failure belongs to a stale or ineligible attempt.")
    job.result_payload = {"error": code}
    job.state = "failed"
    _event(session, job, "job.failed")
    session.commit()
    session.refresh(job)
    return job


def request_cancellation(session: Session, job_id: str) -> Job:
    job = session.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if job is None:
        raise LookupError(job_id)
    if job.state == "queued":
        job.state = "cancelled"
        _event(session, job, "job.cancelled")
    elif job.state == "running":
        job.state = "cancellation_requested"
        _event(session, job, "job.cancellation_requested")
    elif job.state not in {"cancellation_requested", "cancelled"}:
        raise JobConflict(f"Terminal job in state {job.state} cannot be cancelled.")
    session.commit()
    session.refresh(job)
    return job


def confirm_cancellation(session: Session, job_id: str, attempt: int) -> Job:
    job = session.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if job is None:
        raise LookupError(job_id)
    if job.state != "cancellation_requested" or job.attempt != attempt:
        raise JobConflict("Cancellation confirmation is stale or ineligible.")
    job.state = "cancelled"
    _event(session, job, "job.cancelled")
    session.commit()
    session.refresh(job)
    return job


def recover_attempt(session: Session, job_id: str, attempt: int) -> Job:
    job = session.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if job is None:
        raise LookupError(job_id)
    if job.state != "running" or job.attempt != attempt:
        raise JobConflict("Only the current running attempt can be recovered.")
    job.state = "queued"
    _event(session, job, "job.requeued")
    session.commit()
    session.refresh(job)
    return job
