from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.main import app
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import (
    AuditEvent,
    MaintenanceTask,
    OutboxEvent,
    Part,
    Plan,
    Reservation,
    ResourceBooking,
    ResourceSlot,
    WorkRecord,
)
from fleet_maintenance.services.planning import propose_plan


@pytest.mark.parametrize(
    "endpoint",
    ["/plans/{id}/approve", "/plans/{id}/revisions", "/plans/proposals", "/jobs/planning"],
)
def test_legacy_active_work_returns_conflict_without_effects(
    isolated_session: Session, endpoint: str,
):
    session = isolated_session
    candidate = propose_plan(session)
    assignment = candidate.assignments[0]
    task = session.get(MaintenanceTask, assignment["task_id"])
    assert task
    task.status = "approved"
    # Reproduce an approved pre-resource plan, not an invalid new booking.
    legacy = Plan(
        id="legacy-approved",
        status="approved",
        solver_status="optimal",
        input_version="legacy-version",
        assignments=[{key: assignment[key] for key in ("task_id", "start", "end")}],
        approved_at=datetime.now(UTC),
        approved_by="legacy-supervisor",
    )
    session.add(legacy)
    session.flush()
    session.add(WorkRecord(id="legacy-work", plan_id=legacy.id, task_id=task.id))
    session.commit()
    models = (Plan, Reservation, ResourceBooking, ResourceSlot, WorkRecord, AuditEvent, OutboxEvent)
    before = [session.scalar(select(func.count()).select_from(model)) for model in models]
    stock = {part.id: (part.on_hand, part.version) for part in session.scalars(select(Part))}

    def override() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            for _ in range(2):
                response = client.post(
                    "/api" + endpoint.format(id=candidate.id),
                    headers={"X-Demo-Role": "supervisor"},
                )
                assert response.status_code == 409
                assert "Active legacy work has no crew/bay booking" in response.json()["detail"]
                assert "Reconcile or finish" in response.json()["detail"]
            # Already accepted legacy decisions still have idempotent retrieval.
            assert client.post(
                "/api/plans/legacy-approved/approve",
                headers={"X-Demo-Role": "supervisor"},
            ).status_code == 200
    finally:
        app.dependency_overrides.pop(get_session, None)
        session.rollback()
    assert [session.scalar(select(func.count()).select_from(model)) for model in models] == before
    after_stock = {part.id: (part.on_hand, part.version) for part in session.scalars(select(Part))}
    assert after_stock == stock
    assert session.get(Plan, candidate.id).status == "proposed"
    assert session.get(WorkRecord, "legacy-work").status == "approved"


def test_empty_proposal_cannot_commit(isolated_session: Session):
    session = isolated_session
    for task in session.scalars(select(MaintenanceTask)):
        task.status = "completed"
    session.commit()
    plan = propose_plan(session)
    assert not plan.assignments

    def override() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/plans/{plan.id}/approve", headers={"X-Demo-Role": "supervisor"},
            )
            assert response.status_code == 409
            assert "no scheduled work" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_session, None)
        session.rollback()
    assert session.get(Plan, plan.id).status == "proposed"
    assert session.scalar(select(func.count(WorkRecord.id))) == 0
    assert session.scalar(select(func.count(Reservation.id))) == 0
