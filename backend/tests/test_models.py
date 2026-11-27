from datetime import UTC, datetime

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models import JobOffer, JoobleSearch, LlmSettings, UserProfile
from tests.conftest import ALEMBIC_CONFIG


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


def test_the_profile_exists_empty_from_the_start(session):
    profile = session.get(UserProfile, 1)

    assert profile.looking_for == ""
    assert profile.updated_at is not None


def test_profile_migration_keeps_a_profile_saved_before_it(session):
    # A database that got the table one migration earlier, and where the profile was saved since.
    command.downgrade(ALEMBIC_CONFIG, "d4f6b8c0e2a3")
    session.execute(text("UPDATE user_profile SET looking_for = 'Saved before' WHERE id = 1"))
    session.commit()

    command.upgrade(ALEMBIC_CONFIG, "head")

    assert session.get(UserProfile, 1).looking_for == "Saved before"


def test_the_llm_settings_exist_empty_from_the_start(session):
    settings = session.get(LlmSettings, 1)

    assert settings.provider is None
    assert settings.model is None


def test_a_new_offer_has_no_score_yet(session):
    session.add(make_offer())
    session.commit()

    assert session.get(JobOffer, 1).score is None


def test_both_profile_thresholds_start_at_50(session):
    profile = session.get(UserProfile, 1)

    assert (profile.min_score_onsite, profile.min_score_remote) == (50, 50)


def test_a_profile_left_at_the_first_default_moves_to_50(session):
    # A database that got the threshold column when its default was 70.
    command.downgrade(ALEMBIC_CONFIG, "a7c9e1f3b5d6")
    assert session.execute(text("SELECT min_score FROM user_profile")).scalar() == 70

    command.upgrade(ALEMBIC_CONFIG, "head")

    assert session.execute(text("SELECT min_score_onsite FROM user_profile")).scalar() == 50


def test_the_old_threshold_is_copied_to_both_new_ones(session):
    # A database from before the split, where the user had chosen 65.
    command.downgrade(ALEMBIC_CONFIG, "c9e1a3b5d7f8")
    session.execute(text("UPDATE user_profile SET min_score = 65"))
    session.commit()

    command.upgrade(ALEMBIC_CONFIG, "head")

    thresholds = session.execute(text("SELECT min_score_onsite, min_score_remote FROM user_profile")).one()
    assert tuple(thresholds) == (65, 65)


def test_a_jooble_search_is_saved_local_or_remote(session):
    session.add(JoobleSearch(keywords="développeur full stack", location="Clermont-Ferrand", radius_km=40))
    session.add(JoobleSearch(keywords="développeur IA", remote=True))
    session.commit()

    local, remote = session.exec(select(JoobleSearch).order_by(JoobleSearch.id)).all()
    assert (local.location, local.radius_km, local.remote) == ("Clermont-Ferrand", 40, False)
    assert (remote.location, remote.radius_km, remote.remote) == (None, None, True)
