from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app import collection
from app.database import get_session
from app.main import app
from app.models import JobOffer


@pytest.fixture
def client(session):
    """API client whose routes use the test database."""
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_offer(external_id: str, day: int) -> JobOffer:
    return JobOffer(
        source="fake",
        external_id=external_id,
        title=f"Offer {external_id}",
        url=f"https://example.com/{external_id}",
        published_at=datetime(2026, 11, day, tzinfo=UTC),
    )


def test_list_jobs_returns_most_recent_first(client, session):
    session.add_all([make_offer("old", day=20), make_offer("recent", day=23)])
    session.commit()

    response = client.get("/jobs")

    assert response.status_code == 200
    assert [job["external_id"] for job in response.json()] == ["recent", "old"]
    assert response.json()[0]["url"] == "https://example.com/recent"


def test_collect_returns_the_collection_summary(client, monkeypatch):
    monkeypatch.setattr(collection, "SOURCES", {"fake": lambda since: [make_offer("1", day=23)]})

    response = client.post("/jobs/collect")

    assert response.status_code == 200
    assert response.json() == {"fetched": 1, "added": 1, "errors": []}
