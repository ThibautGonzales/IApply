from datetime import UTC, date, datetime, timedelta

from app.collection import FIRST_COLLECTION_DAYS, collect_jobs, collect_since
from app.models import Application, JobOffer, UserProfile
from tests.test_scoring import FakeModel, scores_of


def make_offer(external_id: str, day: int = 20, source: str = "fake") -> JobOffer:
    return JobOffer(
        source=source,
        external_id=external_id,
        title=f"Offer {external_id}",
        url=f"https://example.com/{external_id}",
        published_at=datetime(2026, 11, day, 9, 0, tzinfo=UTC),
    )


def test_first_collection_goes_back_a_few_days(session):
    assert collect_since(session, "fake") == date.today() - timedelta(days=FIRST_COLLECTION_DAYS)


def test_next_collection_starts_on_the_day_of_the_latest_offer(session):
    session.add_all([make_offer("1", day=20), make_offer("2", day=22), make_offer("3", day=23, source="other")])
    session.commit()

    assert collect_since(session, "fake") == date(2026, 11, 22)


def test_collect_saves_only_new_offers(session):
    session.add(make_offer("already-saved"))
    session.commit()
    received_since = []

    def fake_source(since: date) -> list[JobOffer]:
        received_since.append(since)
        # "dup" comes back twice, as it would from two keyword searches.
        return [make_offer("already-saved"), make_offer("new"), make_offer("dup"), make_offer("dup")]

    result = collect_jobs(session, {"fake": fake_source})

    assert received_since == [date(2026, 11, 20)]
    assert (result.fetched, result.added, result.errors) == (4, 2, [])
    assert len(session.exec(JobOffer.__table__.select()).all()) == 3


def test_a_failing_source_does_not_stop_the_others(session):
    def broken_source(since: date) -> list[JobOffer]:
        raise RuntimeError("quota reached")

    result = collect_jobs(session, {"broken": broken_source, "fake": lambda since: [make_offer("1")]})

    assert result.added == 1
    assert result.errors == ["broken: quota reached"]


def describe_profile(session, text: str = "Full stack and AI developer") -> None:
    session.get(UserProfile, 1).looking_for = text
    session.commit()


def test_new_offers_are_scored_after_the_collection(session):
    describe_profile(session)
    model = FakeModel(lambda prompt: scores_of(*[(i, 70) for i in range(1, 10) if f"[{i}]" in prompt]))

    result = collect_jobs(session, {"fake": lambda since: [make_offer("a"), make_offer("b")]}, model)

    assert (result.scored, result.scoring_error) == (2, None)
    assert "Full stack and AI developer" in model.prompts[0]
    assert [offer.score for offer in session.exec(JobOffer.__table__.select()).all()] == [70, 70]


def test_only_offers_of_the_list_without_a_score_are_sent(session):
    describe_profile(session)
    scored, hidden, applied, waiting = (make_offer(name) for name in ["scored", "hidden", "applied", "waiting"])
    scored.score = 80
    hidden.hidden = True
    session.add_all([scored, hidden, applied, waiting])
    session.commit()
    session.add(Application(job_offer_id=applied.id))
    session.commit()
    model = FakeModel(lambda prompt: scores_of())

    collect_jobs(session, {}, model)

    assert "Offer waiting" in model.prompts[0]
    assert all(f"Offer {name}" not in model.prompts[0] for name in ["scored", "hidden", "applied"])


def test_without_a_profile_the_offers_are_saved_but_not_scored(session):
    model = FakeModel(lambda prompt: scores_of())

    result = collect_jobs(session, {"fake": lambda since: [make_offer("a")]}, model)

    assert result.added == 1
    assert result.scored == 0
    assert "Profile page" in result.scoring_error
    assert model.prompts == []


def test_a_failing_llm_does_not_fail_the_collection(session):
    describe_profile(session)

    def broken(prompt):
        raise RuntimeError("invalid x-api-key")

    result = collect_jobs(session, {"fake": lambda since: [make_offer("a")]}, FakeModel(broken))

    assert result.added == 1
    assert result.scoring_error == "invalid x-api-key"
    assert session.exec(JobOffer.__table__.select()).one().score is None


def test_the_batches_scored_before_a_failure_are_kept(session):
    describe_profile(session)
    session.add_all([make_offer(str(i)) for i in range(25)])  # 2 batches: 20 + 5
    session.commit()

    def first_batch_only(prompt):
        if "[21]" in prompt:  # the second batch
            raise RuntimeError("overloaded")
        return scores_of(*[(i, 60) for i in range(1, 21)])

    result = collect_jobs(session, {}, FakeModel(first_batch_only))

    assert (result.scored, result.scoring_error) == (20, "overloaded")
    scores = [offer.score for offer in session.exec(JobOffer.__table__.select()).all()]
    assert scores.count(60) == 20
    assert scores.count(None) == 5
