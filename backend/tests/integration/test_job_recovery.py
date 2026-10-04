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


def test_rejected_attempt_rolls_back_its_pending_plan(isolated_session: Session):
    from fleet_maintenance.services.planning import planning_snapshot

    job = submit_job(isolated_session, "planning", planning_snapshot(isolated_session))
    attempt = claim_job(isolated_session, job.id).attempt
    request_cancellation(isolated_session, job.id)
    plan = propose_plan(
        isolated_session, "unaccepted-plan", commit=False, snapshot=job.input_payload
    )
    with pytest.raises(JobConflict):
        accept_result(isolated_session, job.id, attempt, {"plan_id": plan.id})
    isolated_session.rollback()
    assert isolated_session.get(Plan, "unaccepted-plan") is None


def test_expired_leases_requeue_and_stop_at_attempt_limit(isolated_session: Session, monkeypatch):
    from datetime import timedelta

    from fleet_maintenance.services.jobs import recover_expired
    from fleet_maintenance.settings import get_settings

    monkeypatch.setattr(get_settings(), "job_max_attempts", 2)
    job = submit_job(isolated_session, "planning", {})
    first = claim_job(isolated_session, job.id)
    first.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    isolated_session.commit()
    assert recover_expired(isolated_session) == 1
    assert first.state == "queued"
    second = claim_job(isolated_session, job.id)
    second.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    isolated_session.commit()
    assert recover_expired(isolated_session) == 1
    assert second.state == "failed"
    assert second.result_payload == {"error": "attempt_limit_exceeded"}


def test_attempt_history_retains_recovery_and_authoritative_completion(isolated_session: Session):
    from fleet_maintenance.persistence.models import JobAttempt

    job = submit_job(isolated_session, "planning", {})
    first_number = claim_job(isolated_session, job.id).attempt
    recover_attempt(isolated_session, job.id, first_number)
    second_number = claim_job(isolated_session, job.id).attempt
    with pytest.raises(JobConflict):
        accept_result(isolated_session, job.id, first_number, {"plan_id": "late"})
    isolated_session.rollback()
    accept_result(isolated_session, job.id, second_number, {"plan_id": "current"})
    rows = isolated_session.scalars(
        select(JobAttempt).where(JobAttempt.job_id == job.id).order_by(JobAttempt.number)
    ).all()
    assert [row.number for row in rows] == [1, 2]
    assert [row.state for row in rows] == ["interrupted", "succeeded"]
    assert rows[0].outcome_code == "explicit_recovery"
    assert all(row.worker_id and row.started_at and row.finished_at for row in rows)


def test_expired_cancelled_attempt_retains_its_lease_and_terminal_time(isolated_session: Session):
    from datetime import timedelta

    from fleet_maintenance.persistence.models import JobAttempt
    from fleet_maintenance.services.jobs import recover_expired

    job = submit_job(isolated_session, "planning", {})
    claim_job(isolated_session, job.id)
    request_cancellation(isolated_session, job.id)
    job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    isolated_session.commit()
    assert recover_expired(isolated_session) == 1
    record = isolated_session.get(JobAttempt, f"{job.id}:1")
    assert record is not None and record.state == "cancelled"
    assert record.outcome_code == "cancellation_lease_expired"
    assert record.finished_at is not None and job.finished_at is not None
    assert record.lease_expires_at is not None and job.lease_expires_at is None


def test_replay_never_skips_a_lower_unconfirmed_publication(isolated_session: Session):
    submit_job(isolated_session, "planning", {})
    submit_job(isolated_session, "planning", {})
    rows = isolated_session.scalars(select(OutboxEvent).order_by(OutboxEvent.id)).all()
    rows[1].published_at = datetime.now(UTC)
    isolated_session.commit()
    factory = lambda: Session(isolated_session.bind, expire_on_commit=False)  # noqa: E731
    assert published_after(0, session_factory=factory) == []
    rows[0].published_at = datetime.now(UTC)
    isolated_session.commit()
    assert [row.id for row in published_after(0, session_factory=factory)] == [
        row.id for row in rows
    ]


def test_replay_position_requests_resync_for_missing_and_future_history(isolated_session: Session):
    from sqlalchemy import delete

    from fleet_maintenance.api.routes.events import replay_position

    isolated_session.add(OutboxEvent(id=50, topic="application.job", payload={}))
    isolated_session.commit()
    factory = lambda: Session(isolated_session.bind, expire_on_commit=False)  # noqa: E731
    assert replay_position(20, factory) == (49, "history_gap")
    assert replay_position(60, factory) == (0, "cursor_ahead_of_history")
    assert replay_position(49, factory) == (49, None)
    isolated_session.execute(delete(OutboxEvent))
    isolated_session.commit()
    assert replay_position(50, factory) == (0, "history_unavailable")
