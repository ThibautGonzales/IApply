"""Job offer sources.

Every source is a module exposing the same function:

    fetch_jobs(session: Session, since: date) -> list[JobOffer]

It returns the offers published on or after `since`, not yet saved. The session lets a source
read its settings from the database (Jooble: the searches worked out from the profile).
To add a source, write its module and register it in SOURCES.
"""

from collections.abc import Callable
from datetime import date

from sqlmodel import Session

from app.models import JobOffer
from app.sources import jooble

FetchJobs = Callable[[Session, date], list[JobOffer]]

SOURCES: dict[str, FetchJobs] = {
    jooble.SOURCE_NAME: jooble.fetch_jobs,
}
