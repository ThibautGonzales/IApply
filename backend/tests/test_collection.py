from datetime import UTC, date, datetime, timedelta

from app.collection import FIRST_COLLECTION_DAYS, collect_jobs, collect_since
from app.models import JobOffer


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
