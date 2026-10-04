from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fleet_maintenance.main import app
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import ImportRecord
from fleet_maintenance.settings import Settings, get_settings


def test_import_resource_permissions_and_stream_denial(isolated_session: Session, monkeypatch):
    def override() -> Generator[Session, None, None]:
        yield isolated_session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            assert (
                client.put(
                    "/api/resources/new",
                    json={
                        "kind": "crew",
                        "label": "New crew",
                        "capabilities": ["engine"],
                        "available": [[0, 14]],
                    },
                    headers={"X-Demo-Role": "planner"},
                ).status_code
                == 403
            )
            body = {
                "source_version": "bad",
                "engine_identity": "NASA_CMAPSS:FD001:train:1",
                "csv_text": "cycle,wrong\n1,2\n",
            }
            assert (
                client.post(
                    "/api/components/cmp-eng-01/imports/csv",
                    json=body,
                    headers={"X-Demo-Role": "planner"},
                ).status_code
                == 403
            )
            assert (
                client.post(
                    "/api/components/cmp-eng-01/imports/csv",
                    json=body,
                    headers={"X-Demo-Role": "engineer"},
                ).status_code
                == 422
            )
            assert isolated_session.get(ImportRecord, "bad") is None
            monkeypatch.setattr(get_settings(), "authentication_mode", "session")
            for endpoint in ("/api/events", "/api/jobs", "/api/resources", "/api/demo/catalog"):
                assert client.get(endpoint, headers={"X-Demo-Role": "supervisor"}).status_code in {
                    401,
                    403,
                }
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_request_stream_limit_precedes_parsing(monkeypatch):
    monkeypatch.setattr(get_settings(), "maximum_request_bytes", 1024)
    with TestClient(app) as client:
        response = client.post("/api/plans/proposals", content=iter([b"x" * 600, b"x" * 600]))
        assert response.status_code == 413
        assert "exceeds limit" in response.json()["detail"]


def test_no_unsupported_shared_deployment():
    with pytest.raises(ValueError, match="single-agency"):
        Settings(deployment_scope="multi_agency")
