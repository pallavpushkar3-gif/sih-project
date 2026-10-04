from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.main import app
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import (
    ImportRecord,
    MaintenanceTask,
    Part,
    Plan,
    User,
    WorkRecord,
)
from fleet_maintenance.services.access import passwords
from fleet_maintenance.services.approvals import ApprovalConflict, approve_plan
from fleet_maintenance.services.imports import import_history
from fleet_maintenance.services.planning import propose_plan
from fleet_maintenance.services.reservations import update_work
from fleet_maintenance.settings import Settings, get_settings


def test_work_releases_unstarted_stock_and_consumes_completed_stock(isolated_session: Session):
    plan = propose_plan(isolated_session)
    approve_plan(isolated_session, plan.id, "supervisor")
    works = list(isolated_session.scalars(select(WorkRecord).order_by(WorkRecord.task_id)).all())
    cancelled, completed = works
    cancelled_task = isolated_session.get(MaintenanceTask, cancelled.task_id)
    completed_task = isolated_session.get(MaintenanceTask, completed.task_id)
    assert cancelled_task and completed_task
    cancelled_part = isolated_session.get(Part, cancelled_task.required_part_id)
    completed_part = isolated_session.get(Part, completed_task.required_part_id)
    assert cancelled_part and completed_part
    before_free = cancelled_part.on_hand
    update_work(isolated_session, cancelled.id, "cancel", 1, "supervisor", "Cancelled before work")
    assert cancelled_part.on_hand == before_free + 1
    assert cancelled_task.status == "open"
    update_work(isolated_session, completed.id, "start", 1, "supervisor", "Started")
    before_completion = completed_part.on_hand
    update_work(isolated_session, completed.id, "complete", 2, "supervisor", "Completed")
    assert completed.consumed_quantity == 1 and completed_part.on_hand == before_completion
    with pytest.raises(ApprovalConflict):
        update_work(isolated_session, completed.id, "complete", 2, "supervisor", "Retry")


def test_second_proposal_cannot_commit_same_tasks(isolated_session: Session):
    first, second = propose_plan(isolated_session), propose_plan(isolated_session)
    approve_plan(isolated_session, first.id, "supervisor")
    with pytest.raises(ApprovalConflict):
        approve_plan(isolated_session, second.id, "supervisor")
    assert isolated_session.scalar(select(func.count(WorkRecord.id))) == 2


def test_import_replay_and_explicit_correction(isolated_session: Session):
    rows: list[dict[str, object]] = [{"cycle": 1, "values": [1.0] * 24}]
    record = import_history(
        isolated_session, "cmp-eng-01", "v1", "NASA_CMAPSS:FD001:train:1", rows, None, "engineer"
    )
    assert (
        import_history(
            isolated_session, "cmp-eng-01", "v1", record.engine_identity, rows, None, "engineer"
        ).id
        == record.id
    )
    with pytest.raises(ApprovalConflict):
        import_history(
            isolated_session, "cmp-eng-01", "v2", record.engine_identity, rows, None, "engineer"
        )
    corrected = import_history(
        isolated_session, "cmp-eng-01", "v2", record.engine_identity, rows, record.id, "engineer"
    )
    assert corrected.previous_id == record.id
    assert isolated_session.scalar(select(func.count(ImportRecord.id))) == 2


def test_session_login_csrf_role_denial_and_logout(
    isolated_session: Session, monkeypatch: pytest.MonkeyPatch
):
    settings = get_settings()
    monkeypatch.setattr(settings, "authentication_mode", "session")
    user = isolated_session.get(User, "demo-planner")
    assert user
    user.password_hash = passwords.hash("a-test-password-long-enough")
    isolated_session.commit()

    def override() -> Generator[Session, None, None]:
        yield isolated_session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            assert (
                client.get("/api/fleet", headers={"X-Demo-Role": "supervisor"}).status_code == 401
            )
            origin = {"Origin": "http://localhost:5173"}
            response = client.post(
                "/api/access/session",
                json={"user_id": user.id, "password": "a-test-password-long-enough"},
                headers=origin,
            )
            assert response.status_code == 200
            assert "HttpOnly" in response.headers["set-cookie"]
            assert client.get("/api/fleet").status_code == 200
            assert client.post("/api/plans/proposals", headers=origin).status_code == 403
            headers = {**origin, "X-CSRF-Token": response.json()["csrf_token"]}
            proposal = client.post("/api/plans/proposals", headers=headers)
            assert proposal.status_code == 200
            assert (
                client.post(
                    f"/api/plans/{proposal.json()['id']}/approve", headers=headers
                ).status_code
                == 403
            )
            assert isolated_session.get(Plan, proposal.json()["id"]).status == "proposed"
            assert client.delete("/api/access/session", headers=headers).status_code == 204
            assert client.get("/api/fleet").status_code == 401
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_production_rejects_demo_defaults():
    with pytest.raises(ValueError, match="session authentication"):
        Settings(environment="production")


def test_workspace_fixture_is_atomic_replayable_and_checks_relationships(isolated_session: Session):
    from fleet_maintenance.domain.contracts.records import WorkspaceFixture
    from fleet_maintenance.services.workspace import import_fixture

    body = WorkspaceFixture.model_validate(
        {
            "source_version": "fixture-new-v1",
            "provenance": "synthetic",
            "scheduling_unit": "8_hour_slots",
            "aircraft": [{"id": "new-ac", "tail_number": "SYN-NEW", "label": "Synthetic fixture"}],
            "components": [
                {"id": "new-component", "aircraft_id": "new-ac", "serial_number": "SYN-NEW-ENG"}
            ],
            "parts": [{"id": "new-kit", "name": "Synthetic kit", "on_hand": 2}],
            "tasks": [
                {
                    "id": "new-task",
                    "component_id": "new-component",
                    "title": "Fixture inspection",
                    "duration_slots": 2,
                    "deadline_slot": 8,
                    "required_part_id": "new-kit",
                    "required_part_quantity": 1,
                }
            ],
        }
    )
    counts = import_fixture(isolated_session, body, "administrator")
    assert counts == {"aircraft": 1, "components": 1, "parts": 1, "tasks": 1}
    assert import_fixture(isolated_session, body, "administrator") == counts
    bad = WorkspaceFixture.model_validate(
        {
            "source_version": "fixture-bad-v1",
            "provenance": "synthetic",
            "scheduling_unit": "8_hour_slots",
            "parts": [{"id": "rollback-kit", "name": "Must roll back", "on_hand": 1}],
            "tasks": [
                {
                    "id": "bad-task",
                    "component_id": "unknown-component",
                    "title": "Invalid relationship",
                    "duration_slots": 2,
                    "deadline_slot": 8,
                }
            ],
        }
    )
    with pytest.raises(ValueError, match="unknown component"):
        import_fixture(isolated_session, bad, "administrator")
    assert isolated_session.get(Part, "rollback-kit") is None
    assert isolated_session.get(MaintenanceTask, "bad-task") is None
