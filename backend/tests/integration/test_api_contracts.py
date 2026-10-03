from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.main import app
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Job, Plan, SimulationRun


def test_core_api_contracts_are_connected():
    with TestClient(app) as client:
        assert client.get("/api/health/ready").status_code == 200
        fleet = client.get("/api/fleet").json()
        assert fleet and fleet[0]["provenance"] == "synthetic"
        detail = client.get("/api/components/cmp-eng-01").json()
        assert detail["assessment"]["estimate_cycles"] is None
        assert detail["assessment"]["state"] == "unavailable"


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
                client.post(
                    "/api/scenarios/scenario-baseline/runs", headers=headers
                ).status_code
                == 403
            )
            assert client.post("/api/jobs/planning", headers=headers).status_code == 403
    finally:
        app.dependency_overrides.pop(get_session, None)
    isolated_session.expire_all()
    assert isolated_session.scalar(select(func.count(Plan.id))) == before["plans"]
    assert isolated_session.scalar(select(func.count(SimulationRun.id))) == before["runs"]
    assert isolated_session.scalar(select(func.count(Job.id))) == before["jobs"]
