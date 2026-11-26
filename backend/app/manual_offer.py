"""Offers added by hand: the user pastes the text of an offer found elsewhere (LinkedIn...).

The LLM reads the text and fills the offer fields. Nothing is saved here: the user checks the
fields first, then saves the offer.
"""

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

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
