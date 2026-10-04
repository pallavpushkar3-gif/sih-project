from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.main import app
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Job, Plan, SimulationRun


def test_core_api_contracts_are_connected(isolated_session: Session):
    def override_session() -> Generator[Session, None, None]:
        yield isolated_session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        assert client.get("/api/health/ready").status_code == 200
        fleet = client.get("/api/fleet").json()
        assert fleet and fleet[0]["provenance"] == "synthetic"
        detail = client.get("/api/components/cmp-eng-01").json()
        assert detail["assessment"]["estimate_cycles"] is None
        assert detail["assessment"]["state"] == "unavailable"
    app.dependency_overrides.pop(get_session, None)


def test_viewer_cannot_mutate_plans_scenarios_or_jobs(isolated_session: Session):
    def override_session() -> Generator[Session, None, None]:
        yield isolated_session

    app.dependency_overrides[get_session] = override_session
    before = {
        "plans": isolated_session.scalar(select(func.count(Plan.id))),
        "runs": isolated_session.scalar(select(func.count(SimulationRun.id))),
        "jobs": isolated_session.scalar(select(func.count(Job.id))),
    }
    try:
        with TestClient(app) as client:
            headers = {"X-Demo-Role": "viewer", "X-Demo-User": "demo-viewer"}
            assert client.post("/api/plans/proposals", headers=headers).status_code == 403
            assert (
                client.post("/api/scenarios/scenario-baseline/runs", headers=headers).status_code
                == 403
            )
            assert client.post("/api/jobs/planning", headers=headers).status_code == 403
    finally:
        app.dependency_overrides.pop(get_session, None)
    isolated_session.expire_all()
    assert isolated_session.scalar(select(func.count(Plan.id))) == before["plans"]
    assert isolated_session.scalar(select(func.count(SimulationRun.id))) == before["runs"]
    assert isolated_session.scalar(select(func.count(Job.id))) == before["jobs"]


def test_unavailable_explanation_metadata_does_not_hide_valid_assessment(isolated_session: Session):
    from fleet_maintenance.persistence.models import Assessment

    assessment = Assessment(
        id="valid-estimate-no-explanation",
        component_id="cmp-eng-01",
        state="available",
        estimate_cycles=50,
        lower_cycles=20,
        upper_cycles=80,
        model_version="test-model",
        input_version="test-input",
        cutoff_cycle=31,
        quality_findings=[],
        evidence={"explanation": {"state": "unavailable", "reason": "intervention failed"}},
    )
    isolated_session.add(assessment)
    isolated_session.commit()

    def override_session():
        yield isolated_session

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            result = client.get("/api/assessments/" + assessment.id)
            assert result.status_code == 200
            body = result.json()
            assert body["state"] == "available" and body["estimate_cycles"] == 50
            assert body["explanation"]["state"] == "unavailable"
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_inspection_context_is_read_only_and_component_scoped(isolated_session: Session):
    from fleet_maintenance.persistence.models import MaintenanceTask, Part

    def override_session():
        yield isolated_session

    tasks = isolated_session.scalars(select(MaintenanceTask)).all()
    stock = {
        part.id: (part.on_hand, part.version) for part in isolated_session.scalars(select(Part))
    }
    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            response = client.get("/api/components/cmp-eng-01/maintenance")
            assert response.status_code == 200
            body = response.json()
            assert body["component_id"] == "cmp-eng-01" and body["slot_duration_hours"] == 8
            expected = [task.id for task in tasks if task.component_id == "cmp-eng-01"]
            assert sorted(task["id"] for task in body["tasks"]) == sorted(expected)
            for task in body["tasks"]:
                if task["part_id"]:
                    assert task["part_available"] == stock[task["part_id"]][0]
            assert client.get("/api/components/missing/maintenance").status_code == 404
    finally:
        app.dependency_overrides.pop(get_session, None)
    assert stock == {
        part.id: (part.on_hand, part.version) for part in isolated_session.scalars(select(Part))
    }


def test_part_delay_revision_preserves_parent_and_saved_run(isolated_session: Session):
    from fleet_maintenance.persistence.models import Scenario

    def override_session():
        yield isolated_session

    parent = isolated_session.get(Scenario, "scenario-baseline")
    assert parent is not None
    before = dict(parent.assumptions)
    body = {
        "name": "Synthetic delayed supply",
        "expected_version": parent.version,
        "horizon_hours": 24,
        "aircraft_count": 2,
        "maintenance_capacity": 1,
        "maintenance_events": [[2, 3], [4, 2]],
        "part_available_hours": 8,
    }
    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            baseline = client.post("/api/scenarios/scenario-baseline/runs").json()
            revision = client.post("/api/scenarios/scenario-baseline/revisions", json=body)
            assert revision.status_code == 200
            alternative = client.post("/api/scenarios/" + revision.json()["id"] + "/runs").json()
            assert alternative["metrics"]["part_wait_hours"] == 10
            assert alternative["availability"] < baseline["availability"]
            assert parent.assumptions == before
            assert client.post(
                "/api/scenarios/scenario-baseline/revisions",
                json={**body, "part_available_hours": 24},
            ).status_code == 422
            assert client.post(
                "/api/scenarios/scenario-baseline/revisions",
                json={**body, "expected_version": 999},
            ).status_code == 409
            saved = client.get("/api/scenarios/runs/all").json()
            assert next(run for run in saved if run["id"] == baseline["id"]) == baseline
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_plan_commitment_retains_approval_reservations_and_work(isolated_session: Session):
    from fleet_maintenance.services.approvals import approve_plan
    from fleet_maintenance.services.inspection import plan_commitment
    from fleet_maintenance.services.planning import propose_plan

    plan = propose_plan(isolated_session)
    assert plan_commitment(isolated_session, plan.id)["reservations"] == []
    approve_plan(isolated_session, plan.id, "demo-supervisor")
    before = plan_commitment(isolated_session, plan.id)
    assert len(before["reservations"]) == 2
    assert len(before["work"]) == 2
    assert plan_commitment(isolated_session, plan.id) == before

    def override_session():
        yield isolated_session

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            result = client.get(f"/api/plans/{plan.id}/commitment")
            assert result.status_code == 200
            assert result.json()["plan_id"] == plan.id
            assert len(result.json()["reservations"]) == 2
            assert client.get("/api/plans/missing/commitment").status_code == 404
    finally:
        app.dependency_overrides.pop(get_session, None)
