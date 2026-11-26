"""Offer scoring: the LLM gives each offer a relevance score from 0 to 100 against the profile.

Offers are sent by batches in one prompt each, one line per offer, and the LLM must answer
with a structured list of (id, score) only: no explanation, so few output tokens are spent.
LangChain turns `OfferScores` into a JSON schema sent to the provider, then validates the
answer against it: we get Python objects, never text to parse.
"""

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from app.models import JobOffer

BATCH_SIZE = 20


# ---------- What the LLM must answer (validated by LangChain's structured output) ----------


class OfferScore(BaseModel):
    id: int = Field(description="The offer number given in the list")
    score: int = Field(ge=0, le=100, description="0 = unrelated, 100 = exactly what is looked for")


class OfferScores(BaseModel):
    scores: list[OfferScore]


# ---------- Prompt ----------


def describe(offer: JobOffer) -> str:
    """One line per offer with what we know of it; the pasted text when there is one."""
    details = [offer.title, offer.company, offer.location, offer.contract_type]
    if offer.remote:
        details.append("full remote")
    line = f"[{offer.id}] " + " | ".join(detail for detail in details if detail)
    if offer.description:
        line += f"\n{offer.description}"
    return line


def scoring_prompt(looking_for: str, offers: list[JobOffer]) -> str:
    offer_lines = "\n\n".join(describe(offer) for offer in offers)
    return (
        "You sort job offers for a job seeker. Here is what they are looking for, in their words.\n"
        "It may hold several wishes, from the ideal job to jobs they would also accept:\n"
        f"{looking_for}\n\n"
        "Give each offer below a score from 0 to 100, with the offer's number as id:\n"
        "- 80 to 100: the job they would love, matching their main wish.\n"
        "- 50 to 79: a job they are looking for too, matching a wish they would also accept,\n"
        "  or only part of their main wish. The closer to the main wish, the higher.\n"
        "- under 50: not really what they are looking for. The further from it, the lower.\n"
        "50 is the line between yes and no. The scores also rank the offers from the most to the\n"
        "least interesting, so give different scores to offers that are not equally interesting.\n"
        "Most offers only show a title, a company, a location and a contract: judge on what you see.\n\n"
        f"{offer_lines}"
    )


# ---------- The LLM calls ----------


def batches(offers: list[JobOffer], size: int = BATCH_SIZE) -> list[list[JobOffer]]:
    return [offers[i : i + size] for i in range(0, len(offers), size)]


def score_offers(model: BaseChatModel, looking_for: str, offers: list[JobOffer]) -> dict[int, int]:
    """Score the offers, one LLM call per batch, and return {offer id: score}.

    An offer the LLM forgot gets no score (it stays unscored); an id it invented is ignored.
    """
    # json_schema: the provider's own structured output, which constrains the answer to the schema
    # while it is generated. The four providers support it, and on the newest Claude models the
    # default method (a forced tool call) is not forced anymore and could come back without scores.
    scorer = model.with_structured_output(OfferScores, method="json_schema")
    known_ids = {offer.id for offer in offers}
    scores = {}
    for batch in batches(offers):
        answer = scorer.invoke(scoring_prompt(looking_for, batch))
        scores |= {item.id: item.score for item in answer.scores if item.id in known_ids}
    return scores
