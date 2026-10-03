from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.main import app
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Alert, AlertAcknowledgement


def test_acknowledgement_is_idempotent_and_does_not_resolve_alert(
    isolated_session: Session,
) -> None:
    def override_session() -> Generator[Session, None, None]:
        yield isolated_session

    app.dependency_overrides[get_session] = override_session
    headers = {"X-Demo-Role": "engineer", "X-Demo-User": "demo-engineer"}
    try:
        with TestClient(app) as client:
            first = client.post(
                "/api/alerts/alert-quality-01/acknowledgements", headers=headers
            )
            repeated = client.post(
                "/api/alerts/alert-quality-01/acknowledgements", headers=headers
            )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert first.status_code == repeated.status_code == 200
    assert repeated.json()["state"] == "data_unavailable"
    assert repeated.json()["acknowledged_by"] == "demo-engineer"
    assert len(repeated.json()["acknowledgements"]) == 1
    assert isolated_session.scalar(select(func.count(AlertAcknowledgement.id))) == 1
    assert isolated_session.get(Alert, "alert-quality-01").state == "data_unavailable"


def test_viewer_cannot_acknowledge_alert(isolated_session: Session) -> None:
    def override_session() -> Generator[Session, None, None]:
        yield isolated_session

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/alerts/alert-quality-01/acknowledgements",
                headers={"X-Demo-Role": "viewer", "X-Demo-User": "demo-viewer"},
            )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 403
    assert isolated_session.scalar(select(func.count(AlertAcknowledgement.id))) == 0
