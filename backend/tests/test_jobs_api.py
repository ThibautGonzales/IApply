from datetime import UTC, datetime, timedelta

from sqlmodel import select

from app import collection
from app.models import Application, JobOffer, UserProfile, utc_now


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
    body = response.json()
    assert (body["fetched"], body["added"], body["errors"]) == (1, 1, [])
    # No LLM chosen in the tests: the collection succeeds, the offer stays unscored.
    assert body["scored"] == 0
    assert "LLM page" in body["scoring_error"]


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



def scored_offer(external_id: str, score: int | None, day: int = 20) -> JobOffer:
    offer = make_offer(external_id, day)
    offer.score = score
    return offer


def test_offers_under_the_threshold_leave_the_list(client, session):
    session.add_all([scored_offer("yes", 50), scored_offer("no", 49)])
    session.commit()

    response = client.get("/jobs")

    assert [job["external_id"] for job in response.json()] == ["yes"]


def test_the_threshold_comes_from_the_profile(client, session):
    session.add_all([scored_offer("high", 80), scored_offer("middle", 60)])
    session.get(UserProfile, 1).min_score_onsite = 70
    session.commit()

    response = client.get("/jobs")

    assert [job["external_id"] for job in response.json()] == ["high"]


def test_remote_offers_have_their_own_threshold(client, session):
    remote_ok, remote_low = scored_offer("remote-ok", 80), scored_offer("remote-low", 60)
    remote_ok.remote = remote_low.remote = True
    session.add_all([remote_ok, remote_low, scored_offer("onsite-ok", 40), scored_offer("onsite-low", 30)])
    profile = session.get(UserProfile, 1)
    profile.min_score_onsite, profile.min_score_remote = 40, 70
    session.commit()

    response = client.get("/jobs")

    assert [job["external_id"] for job in response.json()] == ["remote-ok", "onsite-ok"]


def test_unscored_offers_come_first_then_the_highest_scores(client, session):
    session.add_all([
        scored_offer("65", 65, day=23),
        scored_offer("90-old", 90, day=20),
        scored_offer("90-recent", 90, day=22),
        scored_offer("unscored", None, day=21),
    ])
    session.commit()

    response = client.get("/jobs")

    assert [job["external_id"] for job in response.json()] == ["unscored", "90-recent", "90-old", "65"]


def test_a_restored_offer_stays_in_the_list_whatever_its_score(client, session):
    restored = scored_offer("restored", 10)
    restored.restored = True
    session.add_all([restored, scored_offer("rejected", 10)])
    session.commit()

    response = client.get("/jobs")

    assert [job["external_id"] for job in response.json()] == ["restored"]


# ---------- Rejected offers ----------


def recent_offer(external_id: str, score: int | None = None, days_ago: int = 1) -> JobOffer:
    """The rejected page depends on today's date, so these offers are dated from now."""
    offer = scored_offer(external_id, score)
    offer.published_at = utc_now() - timedelta(days=days_ago)
    return offer


def rejected_ids(client) -> list[str]:
    return [job["external_id"] for job in client.get("/jobs/rejected").json()]


def test_rejected_lists_the_hidden_and_the_under_threshold_offers(client, session):
    hidden = recent_offer("hidden", 90)
    hidden.hidden = True
    session.add_all([hidden, recent_offer("low", 10), recent_offer("good", 80), recent_offer("unscored")])
    session.commit()

    assert rejected_ids(client) == ["hidden", "low"]


def test_rejected_uses_the_threshold_of_each_offer(client, session):
    remote_low, remote_ok = recent_offer("remote-low", 60), recent_offer("remote-ok", 80)
    remote_low.remote = remote_ok.remote = True
    session.add_all([remote_low, remote_ok, recent_offer("onsite-low", 30), recent_offer("onsite-ok", 40)])
    profile = session.get(UserProfile, 1)
    profile.min_score_onsite, profile.min_score_remote = 40, 70
    session.commit()

    assert rejected_ids(client) == ["remote-low", "onsite-low"]


def test_rejected_leaves_out_restored_applied_and_old_offers(client, session):
    restored, applied = recent_offer("restored", 10), recent_offer("applied", 10)
    restored.restored = True
    session.add_all([restored, applied, recent_offer("old", 10, days_ago=8)])
    session.commit()
    session.add(Application(job_offer_id=applied.id))
    session.commit()

    assert rejected_ids(client) == []


def test_restore_brings_a_hidden_or_low_score_offer_back_to_the_list(client, session):
    hidden, low = recent_offer("hidden", 10), recent_offer("low", 10)
    hidden.hidden = True
    session.add_all([hidden, low])
    session.commit()

    for offer in (hidden, low):
        assert client.post(f"/jobs/{offer.id}/restore").status_code == 204

    assert rejected_ids(client) == []
    assert sorted(job["external_id"] for job in client.get("/jobs").json()) == ["hidden", "low"]
    session.refresh(low)
    assert low.score == 10  # the score is kept: only the flag changes


def test_restore_unknown_offer_returns_404(client):
    assert client.post("/jobs/999/restore").status_code == 404
