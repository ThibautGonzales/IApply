"""Jooble source: https://jooble.org/api/about

The API takes a POST with a JSON body and answers {"totalCount": ..., "jobs": [...]}.
"""

import html
import os
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime

import httpx
from sqlmodel import Session

from app.models import JobOffer, JoobleSearch
from app.search_planning import saved_searches

SOURCE_NAME = "jooble"
RESULTS_PER_PAGE = 50
# Keeps the number of calls low: the free key allows 100 calls a day.
MAX_PAGES_PER_SEARCH = 5


class JoobleError(Exception):
    """Jooble answered an error (bad key, wrong host, quota reached...), or there is nothing to search."""


# Jooble lists full remote offers under this location.
REMOTE_LOCATION = "Télétravail"


@dataclass
class JoobleSettings:
    api_key: str
    host: str


def load_settings() -> JoobleSettings:
    """Read the API key and host from the environment (see .env.example).

    What to search for is not set here: it comes from the profile (`JoobleSearch`).
    """
    api_key = os.environ.get("JOOBLE_API_KEY")
    if not api_key:
        raise JoobleError("JOOBLE_API_KEY is not set (see .env.example)")
    return JoobleSettings(api_key=api_key, host=os.environ.get("JOOBLE_HOST", "fr.jooble.org"))


def load_searches(session: Session) -> list[JoobleSearch]:
    searches = saved_searches(session)
    if not searches:
        raise JoobleError("No search yet: set up the LLM, then describe what you are looking for on the Profile page")
    return searches


def search_body(search: JoobleSearch) -> dict[str, str]:
    """The part of the request body that says what to look for, and where."""
    if search.remote:
        return {"keywords": search.keywords, "location": REMOTE_LOCATION}
    body = {"keywords": search.keywords, "location": search.location or ""}
    if search.radius_km is not None:
        body["radius"] = str(search.radius_km)
    return body


def fetch_jobs(session: Session, since: date, client: httpx.Client | None = None) -> list[JobOffer]:
    """Return the Jooble offers published since `since`, for every search worked out from the profile."""
    if client is None:
        with httpx.Client(timeout=30) as client:
            return fetch_jobs(session, since, client)

    settings = load_settings()
    offers_by_id: dict[str, JobOffer] = {}
    for search in load_searches(session):
        for offer in _search(client, settings, search, since):
            # An offer found by both a local and a remote search is kept once, as remote.
            if offer.external_id in offers_by_id:
                offers_by_id[offer.external_id].remote |= offer.remote
            else:
                offers_by_id[offer.external_id] = offer
    return list(offers_by_id.values())


def _search(client: httpx.Client, settings: JoobleSettings, search: JoobleSearch, since: date) -> list[JobOffer]:
    """Run one search, page by page, until a page comes back incomplete."""
    offers: list[JobOffer] = []
    for page in range(1, MAX_PAGES_PER_SEARCH + 1):
        body = search_body(search) | {
            "datecreatedfrom": since.isoformat(),  # "YYYY-MM-DD"
            "page": str(page),
            "ResultOnPage": str(RESULTS_PER_PAGE),
        }
        response = client.post(f"https://{settings.host}/api/{settings.api_key}", json=body)
        if response.is_error:
            # Not raise_for_status(): its message contains the URL, and so the API key.
            raise JoobleError(f"Jooble answered HTTP {response.status_code} on {settings.host}")
        jobs = response.json().get("jobs", [])
        # Jooble treats `datecreatedfrom` as a hint and can still return months-old
        # offers, so we filter on the publication date ourselves.
        page_offers = [to_job_offer(job, search.remote) for job in jobs]
        offers += [offer for offer in page_offers if offer.published_at.date() >= since]
        if len(jobs) < RESULTS_PER_PAGE:
            break
    return offers


def to_job_offer(job: dict, from_remote_search: bool = False) -> JobOffer:
    """Convert one Jooble result into our JobOffer model."""
    location = _clean(job.get("location") or "") or None
    return JobOffer(
        source=SOURCE_NAME,
        external_id=str(job["id"]),
        title=_clean(job["title"]),
        company=_clean(job.get("company") or "") or None,
        location=location,
        salary=job.get("salary") or None,
        contract_type=job.get("type") or None,
        # No description: Jooble only gives a ~290 character snippet, too short to be useful.
        # The user pastes the full offer later (PUT /jobs/{id}/description).
        url=job["link"],
        published_at=_parse_date(job["updated"]),
        # A local search can also return remote offers: Jooble then gives "Télétravail" as location.
        remote=from_remote_search or "télétravail" in (location or "").lower(),
    )


def _clean(text: str) -> str:
    """Jooble returns HTML fragments (<b>, &nbsp;...): keep the plain text only."""
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _parse_date(value: str) -> datetime:
    """Jooble dates look like "2026-11-20T10:31:00.0000000", without a time zone: assume UTC."""
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
