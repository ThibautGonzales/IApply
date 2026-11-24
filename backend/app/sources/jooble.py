"""Jooble source: https://jooble.org/api/about

The API takes a POST with a JSON body and answers {"totalCount": ..., "jobs": [...]}.
"""

import html
import os
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime

import httpx

from app.models import JobOffer

SOURCE_NAME = "jooble"
RESULTS_PER_PAGE = 50
# Keeps the number of calls low: the free key allows 100 calls a day.
MAX_PAGES_PER_SEARCH = 5


class JoobleError(Exception):
    """Jooble answered an error (bad key, wrong host, quota reached...)."""


@dataclass
class JoobleSettings:
    api_key: str
    host: str
    keywords: list[str]
    location: str
    radius_km: str


def load_settings() -> JoobleSettings:
    """Read the Jooble settings from the environment (see .env.example)."""
    api_key = os.environ.get("JOOBLE_API_KEY")
    if not api_key:
        raise JoobleError("JOOBLE_API_KEY is not set (see .env.example)")
    keywords = os.environ.get("JOOBLE_KEYWORDS", "développeur full stack;développeur IA;GenAI")
    return JoobleSettings(
        api_key=api_key,
        host=os.environ.get("JOOBLE_HOST", "fr.jooble.org"),
        keywords=[k.strip() for k in keywords.split(";") if k.strip()],
        location=os.environ.get("JOOBLE_LOCATION", "Clermont-Ferrand"),
        radius_km=os.environ.get("JOOBLE_RADIUS_KM", "40"),
    )


def fetch_jobs(since: date, client: httpx.Client | None = None) -> list[JobOffer]:
    """Return the Jooble offers published since `since`, for every configured keyword."""
    if client is None:
        with httpx.Client(timeout=30) as client:
            return fetch_jobs(since, client)

    settings = load_settings()
    offers: list[JobOffer] = []
    for keywords in settings.keywords:
        offers += _search(client, settings, keywords, since)
    return offers


def _search(client: httpx.Client, settings: JoobleSettings, keywords: str, since: date) -> list[JobOffer]:
    """Run one search, page by page, until a page comes back incomplete."""
    offers: list[JobOffer] = []
    for page in range(1, MAX_PAGES_PER_SEARCH + 1):
        body = {
            "keywords": keywords,
            "location": settings.location,
            "radius": settings.radius_km,
            "datecreatedfrom": since.isoformat(),  # "YYYY-MM-DD"
            "page": str(page),
            "ResultOnPage": str(RESULTS_PER_PAGE),
        }
        response = client.post(f"https://{settings.host}/api/{settings.api_key}", json=body)
        if response.is_error:
            # Not raise_for_status(): its message contains the URL, and so the API key.
            raise JoobleError(f"Jooble answered HTTP {response.status_code} on {settings.host}")
        jobs = response.json().get("jobs", [])
        offers += [to_job_offer(job) for job in jobs]
        if len(jobs) < RESULTS_PER_PAGE:
            break
    return offers


def to_job_offer(job: dict) -> JobOffer:
    """Convert one Jooble result into our JobOffer model."""
    return JobOffer(
        source=SOURCE_NAME,
        external_id=str(job["id"]),
        title=_clean(job["title"]),
        company=job.get("company") or None,
        location=job.get("location") or None,
        salary=job.get("salary") or None,
        contract_type=job.get("type") or None,
        description=_clean(job.get("snippet") or "") or None,
        url=job["link"],
        published_at=_parse_date(job["updated"]),
    )


def _clean(text: str) -> str:
    """Jooble returns HTML fragments (<b>, &nbsp;...): keep the plain text only."""
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _parse_date(value: str) -> datetime:
    """Jooble dates look like "2026-11-20T10:31:00.0000000", without a time zone: assume UTC."""
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
