import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import OutboxEvent
from fleet_maintenance.services.jobs import (
    JobConflict,
    accept_result,
    claim_job,
    confirm_cancellation,
    recover_attempt,
    request_cancellation,
    submit_job,
)


def test_recovery_rejects_late_result_from_old_attempt(isolated_session: Session):
    job = submit_job(isolated_session, "planning", {"input_version": "v1"})
    first = claim_job(isolated_session, job.id)
    first_attempt = first.attempt
    recover_attempt(isolated_session, job.id, first_attempt)
    second = claim_job(isolated_session, job.id)

    with pytest.raises(JobConflict, match="stale"):
        accept_result(isolated_session, job.id, first_attempt, {"plan_id": "old"})

    completed = accept_result(
        isolated_session, job.id, second.attempt, {"plan_id": "authoritative"}
    )
    assert completed.state == "succeeded"
    assert completed.result_payload == {"plan_id": "authoritative"}
    assert isolated_session.scalar(select(func.count(OutboxEvent.id))) == 5


def test_cancellation_request_is_distinct_for_running_job(isolated_session: Session):
    job = submit_job(isolated_session, "simulation", {"scenario_id": "scenario-baseline"})
    running = claim_job(isolated_session, job.id)
    requested = request_cancellation(isolated_session, job.id)
    assert requested.state == "cancellation_requested"

    with pytest.raises(JobConflict, match="stale or ineligible"):
        accept_result(isolated_session, job.id, running.attempt, {"run_id": "late"})

    cancelled = confirm_cancellation(isolated_session, job.id, running.attempt)
    assert cancelled.state == "cancelled"
