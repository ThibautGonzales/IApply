from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime, Text, UniqueConstraint, false
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class JobOffer(SQLModel, table=True):
    """A job offer collected from an external source (Jooble today, others later)."""

    __tablename__ = "job_offer"
    # The same offer can come back in several collections: this makes the
    # database refuse the duplicate instead of storing it twice.
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: int | None = Field(default=None, primary_key=True)
    source: str = Field(max_length=50)  # e.g. "jooble"
    external_id: str = Field(max_length=100)  # the offer's id in its source
    title: str = Field(max_length=300)
    company: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    salary: str | None = Field(default=None, max_length=200)  # free text, as given by the source
    contract_type: str | None = Field(default=None, max_length=100)
    # The full offer text, pasted by the user. Empty until then: the sources don't give it.
    description: str | None = Field(default=None, sa_type=Text)
    url: str = Field(sa_type=Text)  # direct link to the original posting
    # True for a full remote offer. server_default fills the rows saved before this column existed.
    remote: bool = Field(default=False, sa_column_kwargs={"server_default": false()})
    # Hidden offers leave the list. A flag, not a delete: a deleted offer would come back
    # at the next collection.
    hidden: bool = Field(default=False, sa_column_kwargs={"server_default": false()})
    published_at: datetime = Field(sa_type=DateTime(timezone=True), index=True)
    collected_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))


class ApplicationStatus(StrEnum):
    """Where an application stands. Stored as plain text in `Application.status`."""

    WAITING = "waiting"  # waiting for an answer
    INTERVIEW = "interview"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    CLOSED = "closed"  # closed without answer


class Application(SQLModel, table=True):
    """An application sent for an offer. Kept apart from `JobOffer` so the tracking has its own data."""

    __tablename__ = "application"

    id: int | None = Field(default=None, primary_key=True)
    # unique: one application per offer.
    job_offer_id: int = Field(foreign_key="job_offer.id", unique=True)
    status: str = Field(default=ApplicationStatus.WAITING, max_length=50)
    applied_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    # Last time something happened (status change or "I got news"): used to close an
    # application after a month without news.
    last_news_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))


class UserProfile(SQLModel, table=True):
    """What the user is looking for, as plain text. One user, so one row (id 1), created by a migration."""

    __tablename__ = "user_profile"

    id: int | None = Field(default=None, primary_key=True)
    # Free text: job, technologies, location, contract... Used later to filter the offers.
    looking_for: str = Field(default="", sa_type=Text)
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))


class LlmSettings(SQLModel, table=True):
    """The LLM chosen on the LLM page. One row (id 1), created by a migration.

    The API key is a secret: it is never stored here but in a local `.env` file (see `app/llm.py`).
    """

    __tablename__ = "llm_settings"

    id: int | None = Field(default=None, primary_key=True)
    provider: str | None = Field(default=None, max_length=50)  # a key of `llm.PROVIDERS`, e.g. "anthropic"
    model: str | None = Field(default=None, max_length=200)  # None means the provider's default model


class ApplicationWithJob(SQLModel):
    """What the tracking page receives: an application and its offer, in one object."""

    id: int
    status: str
    applied_at: datetime
    last_news_at: datetime
    job: JobOffer


class StatusChange(SQLModel):
    """Body of `PUT /applications/{id}/status`. An unknown status is refused by FastAPI (422)."""

    status: ApplicationStatus


class DescriptionChange(SQLModel):
    """Body of `PUT /jobs/{id}/description`: the offer text pasted by the user."""

    description: str


class ProfileChange(SQLModel):
    """Body of `PUT /profile`: what the user is looking for."""

    looking_for: str
