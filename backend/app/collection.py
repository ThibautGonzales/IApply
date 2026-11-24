"""Collect new job offers from every source and save them."""

from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlmodel import Session, func, select

from app.models import JobOffer
from app.sources import SOURCES, FetchJobs

# How far back the very first collection of a source goes.
FIRST_COLLECTION_DAYS = 7


@dataclass
class CollectionResult:
    fetched: int = 0  # offers returned by the sources
    added: int = 0  # offers that were new and got saved
    errors: list[str] = field(default_factory=list)  # one message per failed source


def collect_jobs(session: Session, sources: dict[str, FetchJobs] | None = None) -> CollectionResult:
    """Fetch the offers published since the last collection and save the new ones.

    `sources` defaults to every registered source. A failing source is reported
    in `errors` and does not stop the others.
    """
    result = CollectionResult()
    for name, fetch_jobs in (sources or SOURCES).items():
        try:
            offers = fetch_jobs(collect_since(session, name))
        except Exception as error:
            result.errors.append(f"{name}: {error}")
            continue
        result.fetched += len(offers)
        result.added += save_new_offers(session, name, offers)
    return result


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
