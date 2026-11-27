"""Collect new job offers from every source and save them."""

from dataclasses import dataclass, field
from datetime import date, timedelta

from langchain_core.language_models import BaseChatModel
from sqlmodel import Session, func, select

from app.llm import get_chat_model, get_settings
from app.models import JobOffer
from app.scoring import score_unscored_offers, unscored_offers
from app.sources import SOURCES, FetchJobs

# How far back the very first collection of a source goes.
FIRST_COLLECTION_DAYS = 7


@dataclass
class CollectionResult:
    fetched: int = 0  # offers returned by the sources
    added: int = 0  # offers that were new and got saved
    errors: list[str] = field(default_factory=list)  # one message per failed source
    scored: int = 0  # offers that got a score from the LLM
    scoring_error: str | None = None  # why the offers could not be scored, if they could not


def collect_jobs(
    session: Session, sources: dict[str, FetchJobs] | None = None, model: BaseChatModel | None = None
) -> CollectionResult:
    """Fetch the offers published since the last collection, save the new ones, then score them.

    `sources` defaults to every registered source, and `model` to the LLM chosen on the LLM page.
    A failing source is reported in `errors` and does not stop the others.
    """
    result = CollectionResult()
    for name, fetch_jobs in (sources or SOURCES).items():
        try:
            offers = fetch_jobs(session, collect_since(session, name))
        except Exception as error:
            result.errors.append(f"{name}: {error}")
            continue
        result.fetched += len(offers)
        result.added += save_new_offers(session, name, offers)
    result.scored, result.scoring_error = score_new_offers(session, model)
    return result


def score_new_offers(session: Session, model: BaseChatModel | None) -> tuple[int, str | None]:
    """Score the offers waiting for a score. Returns how many got one, and the error if any.

    Never raises: without an LLM, without a profile or when the provider fails, the collection
    still succeeds, and the offers left unscored (so visible) are tried again at the next one.
    The batches scored before a failure are already saved: counting the offers still waiting
    before and after gives how many got a score, failure or not.
    """
    waiting = len(unscored_offers(session))
    error = None
    try:
        score_unscored_offers(session, model or get_chat_model(get_settings(session)))
    except Exception as exception:
        session.rollback()
        error = str(exception)
    return waiting - len(unscored_offers(session)), error


def collect_since(session: Session, source: str) -> date:
    """Day of the most recent offer already saved for this source.

    Offers of that day are fetched again; the duplicates are skipped when saving.
    """
    latest = session.exec(select(func.max(JobOffer.published_at)).where(JobOffer.source == source)).one()
    if latest is None:
        return date.today() - timedelta(days=FIRST_COLLECTION_DAYS)
    return latest.date()


def save_new_offers(session: Session, source: str, offers: list[JobOffer]) -> int:
    """Save the offers not stored yet and return how many were saved."""
    known_ids = set(session.exec(select(JobOffer.external_id).where(JobOffer.source == source)).all())
    added = 0
    for offer in offers:
        # The same offer can come back from two searches (two keywords) in one collection.
        if offer.external_id in known_ids:
            continue
        known_ids.add(offer.external_id)
        session.add(offer)
        added += 1
    session.commit()
    return added
