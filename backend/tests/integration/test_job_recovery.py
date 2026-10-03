from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.api.routes.events import encode_event, published_after
from fleet_maintenance.persistence.models import OutboxEvent, Plan, SimulationRun
from fleet_maintenance.services.jobs import (
    JobConflict,
    accept_result,
    claim_job,
    confirm_cancellation,
    fail_attempt,
    recover_attempt,
    request_cancellation,
    submit_job,
)
from fleet_maintenance.services.planning import propose_plan
from fleet_maintenance.services.scenarios import run_saved_scenario
from fleet_maintenance.workers.outbox_dispatcher import dispatch_one


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


def test_failed_attempt_records_bounded_error(isolated_session: Session):
    job = submit_job(isolated_session, "unsupported", {})
    running = claim_job(isolated_session, job.id)
    failed = fail_attempt(isolated_session, job.id, running.attempt, "unsupported_job_kind")
    assert failed.state == "failed"
    assert failed.result_payload == {"error": "unsupported_job_kind"}


def test_outbox_marks_only_confirmed_publication(isolated_session: Session):
    submit_job(isolated_session, "planning", {})
    factory = lambda: Session(isolated_session.bind, expire_on_commit=False)  # noqa: E731

    def fail(_: OutboxEvent) -> None:
        raise RuntimeError("broker unavailable")

    with pytest.raises(RuntimeError, match="broker unavailable"):
        dispatch_one(factory, fail)
    isolated_session.expire_all()
    event = isolated_session.scalar(select(OutboxEvent).order_by(OutboxEvent.id.desc()))
    assert event is not None and event.published_at is None

    assert dispatch_one(factory, lambda _: None) is True
    isolated_session.expire_all()
    event = isolated_session.scalar(select(OutboxEvent).order_by(OutboxEvent.id.desc()))
    assert event is not None and event.published_at is not None


def test_job_effect_records_are_idempotent(isolated_session: Session):
    first_plan = propose_plan(isolated_session, "plan-for-job-fixed")
    repeated_plan = propose_plan(isolated_session, "plan-for-job-fixed")
    first_run = run_saved_scenario(
        isolated_session, "scenario-baseline", run_id="sim-for-job-fixed"
    )
    repeated_run = run_saved_scenario(
        isolated_session, "scenario-baseline", run_id="sim-for-job-fixed"
    )
    assert repeated_plan.id == first_plan.id
    assert repeated_run.id == first_run.id
    assert isolated_session.get(Plan, first_plan.id) is not None
    assert isolated_session.get(SimulationRun, first_run.id) is not None


def test_event_replay_uses_published_cursor_order(isolated_session: Session):
    submit_job(isolated_session, "planning", {})
    event = isolated_session.scalar(select(OutboxEvent).order_by(OutboxEvent.id.desc()))
    assert event is not None
    assert event.payload["state"] == "queued"
    assert event.payload["attempt"] == 0
    event.published_at = datetime.now(UTC)
    isolated_session.commit()
    factory = lambda: Session(isolated_session.bind, expire_on_commit=False)  # noqa: E731

    rows = published_after(event.id - 1, session_factory=factory)
    assert [row.id for row in rows] == [event.id]
    encoded = encode_event(rows[0])
    assert f"id: {event.id}\n" in encoded
    assert "event: job.queued\n" in encoded
    assert published_after(event.id, session_factory=factory) == []
