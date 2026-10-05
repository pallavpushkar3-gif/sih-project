import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fleet_maintenance.main import app
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import User
from fleet_maintenance.services.access import passwords
from fleet_maintenance.settings import Settings, get_settings


def tunnel_settings(**overrides):
    values = dict(
        environment="tunnel_demo",
        authentication_mode="session",
        secure_cookies=True,
        database_url="postgresql+psycopg://fleet:unused@postgres/fleet_public_demo",
        auto_create_schema=False,
        auto_seed_demo=False,
        allowed_origins=["https://frontend.example"],
        cookie_samesite="none",
    )
    return Settings(**(values | overrides))


@pytest.mark.parametrize(
    "overrides",
    [
        {"authentication_mode": "demo"},
        {"secure_cookies": False},
        {"auto_seed_demo": True},
        {"auto_create_schema": True},
        {"database_url": "postgresql+psycopg://fleet:unused@postgres/fleet"},
        {"allowed_origins": ["http://frontend.example"]},
    ],
)
def test_tunnel_refuses_unsafe_configuration(overrides):
    with pytest.raises(ValueError):
        tunnel_settings(**overrides)


@pytest.mark.parametrize("same_site", ["strict", "none"])
def test_tunnel_session_cookie_origin_csrf_and_revocation(
    isolated_session: Session,
    monkeypatch,
    same_site,
):
    settings = get_settings()
    monkeypatch.setattr(settings, "authentication_mode", "session")
    monkeypatch.setattr(settings, "cookie_samesite", same_site)
    monkeypatch.setattr(settings, "secure_cookies", True)
    monkeypatch.setattr(settings, "allowed_origins", ["https://frontend.example"])
    user = isolated_session.get(User, "demo-supervisor")
    user.password_hash = passwords.hash("Synthetic-demo-password")
    isolated_session.commit()

    def override():
        yield isolated_session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app, base_url="https://backend.example") as client:
            assert (
                client.get("/api/fleet", headers={"X-Demo-Role": "supervisor"}).status_code == 401
            )
            credentials = {"user_id": user.id, "password": "Synthetic-demo-password"}
            assert client.post("/api/access/session", json=credentials).status_code == 403
            response = client.post(
                "/api/access/session",
                json=credentials,
                headers={"Origin": "https://frontend.example"},
            )
            assert response.status_code == 200
            cookie = response.headers["set-cookie"].lower()
            assert f"samesite={same_site}" in cookie
            assert "secure" in cookie and "httponly" in cookie and "path=/api" in cookie
            assert client.get("/api/access/session").json()["authentication"] == "server session"
            assert client.delete("/api/access/session").status_code == 403
            token = response.json()["csrf_token"]
            headers = {"X-CSRF-Token": token, "Origin": "https://untrusted.example"}
            assert client.delete("/api/access/session", headers=headers).status_code == 403
            headers["Origin"] = "https://frontend.example"
            assert client.delete("/api/access/session", headers=headers).status_code == 204
            assert client.get("/api/access/session").status_code == 401
    finally:
        app.dependency_overrides.pop(get_session, None)
