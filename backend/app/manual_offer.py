"""Offers added by hand: the user pastes the text of an offer found elsewhere (LinkedIn...).

The LLM reads the text and fills the offer fields. Nothing is saved here: the user checks the
fields first, then saves the offer.

These offers are never scored: the user added them, so they want to see them. Unscored, they
stay at the top of the list, where the user handles them first.
"""

from uuid import uuid4

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.models import JobOffer, ManualOfferCreate, utc_now

# The `source` of the offers added by hand.
MANUAL_SOURCE = "manual"


class ExtractedOffer(BaseModel):
    """What the LLM must answer: the offer fields, read from the pasted text.

    No default values: every field is required in the schema, which some providers ask for in
    structured output. The LLM answers null for what the text does not say.
    """

    title: str = Field(description="The job title")
    company: str | None = Field(description="The hiring company, null if not given")
    location: str | None = Field(description="Where the job is (city, area), null if not given")
    contract_type: str | None = Field(description="The contract (CDI, CDD, freelance...), null if not given")
    salary: str | None = Field(description="The salary as written in the text, null if not given")
    remote: bool = Field(description="True only for a full remote job")


def extraction_prompt(text: str) -> str:
    return (
        "Here is the text of a job offer, copied from a job board.\n"
        "Fill in the offer fields from it. Keep the words and the language of the text,\n"
        "and answer null for a field the text does not give: never guess.\n\n"
        f"{text}"
    )


def extract_offer(model: BaseChatModel, text: str) -> ExtractedOffer:
    """Ask the LLM for the offer fields. Same structured output as the scoring (`app/scoring.py`)."""
    extractor = model.with_structured_output(ExtractedOffer, method="json_schema")
    return extractor.invoke(extraction_prompt(text))


class DuplicateOfferError(Exception):
    """An offer with the same link was already added by hand."""


def save_manual_offer(session: Session, new_offer: ManualOfferCreate) -> JobOffer:
    """Save the offer checked by the user. The same link cannot be added twice."""
    url = new_offer.url.strip()
    already_added = select(JobOffer).where(JobOffer.source == MANUAL_SOURCE, JobOffer.url == url)
    if session.exec(already_added).first() is not None:
        raise DuplicateOfferError("This offer was already added.")
    offer = JobOffer(
        **new_offer.model_dump(exclude={"url", "description"}),
        url=url,
        description=new_offer.description.strip() or None,
        source=MANUAL_SOURCE,
        external_id=uuid4().hex,  # a manual offer has no id in a source: a random one keeps it unique
        published_at=utc_now(),  # a date read in the text would not be reliable
    )
    session.add(offer)
    session.commit()
    session.refresh(offer)
    return offer
