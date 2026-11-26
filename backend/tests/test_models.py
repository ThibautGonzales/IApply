from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import JobOffer, UserProfile


def make_offer(**overrides) -> JobOffer:
    values = {
        "source": "jooble",
        "external_id": "123",
        "title": "Full stack developer",
        "url": "https://example.com/offer/123",
        "published_at": datetime(2026, 11, 24, tzinfo=UTC),
    }
    return JobOffer(**(values | overrides))


def test_job_offer_is_saved_with_collection_date(session):
    session.add(make_offer())
    session.commit()

    saved = session.get(JobOffer, 1)
    assert saved.title == "Full stack developer"
    assert saved.collected_at is not None


def test_same_offer_from_same_source_is_refused(session):
    session.add(make_offer())
    session.commit()

    session.add(make_offer(title="Same offer, collected again"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_same_id_from_another_source_is_accepted(session):
    session.add(make_offer())
    session.add(make_offer(source="adzuna"))
    session.commit()


def test_user_profile_is_saved_with_update_date(session):
    session.add(UserProfile(looking_for="Python backend developer, Lyon or remote"))
    session.commit()

    saved = session.get(UserProfile, 1)
    assert saved.looking_for == "Python backend developer, Lyon or remote"
    assert saved.updated_at is not None
