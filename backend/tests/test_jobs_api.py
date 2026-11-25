from datetime import UTC, datetime

from sqlmodel import select

from app import collection
from app.models import Application, JobOffer


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


def test_hide_removes_the_offer_from_the_list(client, session):
    kept, hidden = make_offer("kept", day=20), make_offer("hidden", day=23)
    session.add_all([kept, hidden])
    session.commit()

    response = client.post(f"/jobs/{hidden.id}/hide")

    assert response.status_code == 204
    assert [job["external_id"] for job in client.get("/jobs").json()] == ["kept"]
    session.refresh(hidden)
    assert hidden.hidden is True  # still in the database, so a collection skips it


def test_hide_unknown_offer_returns_404(client, session):
    assert client.post("/jobs/999/hide").status_code == 404


def test_apply_creates_an_application_and_removes_the_offer_from_the_list(client, session):
    kept, applied = make_offer("kept", day=20), make_offer("applied", day=23)
    session.add_all([kept, applied])
    session.commit()

    response = client.post(f"/jobs/{applied.id}/apply")

    assert response.status_code == 200
    assert response.json()["job_offer_id"] == applied.id
    assert response.json()["status"] == "waiting"
    assert [job["external_id"] for job in client.get("/jobs").json()] == ["kept"]


def test_apply_twice_keeps_a_single_application(client, session):
    offer = make_offer("1", day=23)
    session.add(offer)
    session.commit()

    first = client.post(f"/jobs/{offer.id}/apply").json()
    second = client.post(f"/jobs/{offer.id}/apply").json()

    assert first["id"] == second["id"]
    assert len(session.exec(select(Application)).all()) == 1


def test_apply_to_unknown_offer_returns_404(client, session):
    assert client.post("/jobs/999/apply").status_code == 404


def test_change_description_saves_the_pasted_text(client, session):
    offer = make_offer("1", day=23)
    session.add(offer)
    session.commit()

    response = client.put(f"/jobs/{offer.id}/description", json={"description": "  Full offer text\n"})

    assert response.status_code == 200
    assert response.json()["description"] == "Full offer text"
    session.refresh(offer)
    assert offer.description == "Full offer text"


def test_change_description_with_an_empty_text_clears_it(client, session):
    offer = make_offer("1", day=23)
    offer.description = "Old text"
    session.add(offer)
    session.commit()

    response = client.put(f"/jobs/{offer.id}/description", json={"description": "   "})

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_change_description_of_unknown_offer_returns_404(client):
    assert client.put("/jobs/999/description", json={"description": "x"}).status_code == 404
