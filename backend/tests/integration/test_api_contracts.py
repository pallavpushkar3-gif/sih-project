from fastapi.testclient import TestClient

from fleet_maintenance.main import app


def test_core_api_contracts_are_connected():
    with TestClient(app) as client:
        assert client.get("/api/health/ready").status_code == 200
        fleet = client.get("/api/fleet").json()
        assert fleet and fleet[0]["provenance"] == "synthetic"
        detail = client.get("/api/components/cmp-eng-01").json()
        assert detail["assessment"]["estimate_cycles"] is None
        assert detail["assessment"]["state"] == "unavailable"
