from datetime import UTC, datetime

from app.models import Application, JobOffer


def make_application(session, external_id: str, day: int) -> Application:
    """Save an offer and an application to it, made on the given day of November 2026."""
    offer = JobOffer(
        source="fake",
        external_id=external_id,
        title=f"Offer {external_id}",
        url=f"https://example.com/{external_id}",
        published_at=datetime(2026, 11, 1, tzinfo=UTC),
    )
    session.add(offer)
    session.commit()
    applied_at = datetime(2026, 11, day, tzinfo=UTC)
    application = Application(job_offer_id=offer.id, applied_at=applied_at, last_news_at=applied_at)
    session.add(application)
    session.commit()
    return application


def test_list_applications_returns_most_recent_first_with_their_offer(client, session):
    make_application(session, "old", day=20)
    make_application(session, "recent", day=23)

    response = client.get("/applications")

    assert response.status_code == 200
    applications = response.json()
    assert [application["job"]["external_id"] for application in applications] == ["recent", "old"]
    assert applications[0]["status"] == "waiting"
    assert applications[0]["job"]["url"] == "https://example.com/recent"


def test_list_applications_is_empty_without_applications(client, session):
    assert client.get("/applications").json() == []


def test_change_status_updates_the_status_and_the_last_news(client, session):
    application = make_application(session, "1", day=20)

    response = client.put(f"/applications/{application.id}/status", json={"status": "interview"})

    assert response.status_code == 200
    assert response.json()["status"] == "interview"
    assert response.json()["job"]["external_id"] == "1"
    session.refresh(application)
    assert application.last_news_at > application.applied_at


def test_change_status_refuses_an_unknown_status(client, session):
    application = make_application(session, "1", day=20)

    response = client.put(f"/applications/{application.id}/status", json={"status": "maybe"})

    assert response.status_code == 422


def test_news_updates_the_last_news_but_keeps_the_status(client, session):
    application = make_application(session, "1", day=20)

    response = client.post(f"/applications/{application.id}/news")

    assert response.status_code == 200
    assert response.json()["status"] == "waiting"
    session.refresh(application)
    assert application.last_news_at > application.applied_at


def test_unknown_application_returns_404(client, session):
    assert client.post("/applications/999/news").status_code == 404
    assert client.put("/applications/999/status", json={"status": "closed"}).status_code == 404
