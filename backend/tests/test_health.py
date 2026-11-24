from fastapi.testclient import TestClient

from app import main
from app.main import app

client = TestClient(app)


def test_health_returns_ok_when_database_is_reachable():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_503_when_database_is_unreachable(monkeypatch):
    monkeypatch.setattr(main, "is_database_reachable", lambda: False)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unreachable"}
