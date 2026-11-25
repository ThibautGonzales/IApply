from datetime import UTC, datetime

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
    description: str | None = Field(default=None, sa_type=Text)
    url: str = Field(sa_type=Text)  # direct link to the original posting
    # True for a full remote offer. server_default fills the rows saved before this column existed.
    remote: bool = Field(default=False, sa_column_kwargs={"server_default": false()})
    # Hidden offers leave the list. A flag, not a delete: a deleted offer would come back
    # at the next collection.
    hidden: bool = Field(default=False, sa_column_kwargs={"server_default": false()})
    published_at: datetime = Field(sa_type=DateTime(timezone=True), index=True)
    collected_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))


class Application(SQLModel, table=True):
    """An application sent for an offer. Kept apart from `JobOffer` so the tracking has its own data."""

    __tablename__ = "application"

    id: int | None = Field(default=None, primary_key=True)
    # unique: one application per offer.
    job_offer_id: int = Field(foreign_key="job_offer.id", unique=True)
    status: str = Field(default="waiting", max_length=50)  # the other statuses come with the tracking page
    applied_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    # Used to close an application after a month without news.
    status_changed_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
