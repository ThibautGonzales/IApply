"""Search planning: the LLM works out the Jooble searches of the collection from the profile.

Same approach as `scoring.py`: one prompt, and a structured answer validated by LangChain
(`PlannedSearches`), so we get Python objects, never text to parse.
"""

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from app.models import JoobleSearch

# Each search costs one to five Jooble calls per collection, and the free key allows 100 a day.
MAX_SEARCHES = 6


# ---------- What the LLM must answer (validated by LangChain's structured output) ----------


class PlannedSearch(BaseModel):
    keywords: str = Field(description="A few words typed in the Jooble search box, in French")
    remote: bool = Field(description="true for a search of full remote offers only, anywhere")
    location: str | None = Field(description="City or region of an on-site search, null for a remote one")
    radius_km: int | None = Field(description="Distance around the location in km, null for a remote one")


class PlannedSearches(BaseModel):
    searches: list[PlannedSearch]


# ---------- Prompt ----------


def planning_prompt(looking_for: str) -> str:
    return (
        "You prepare the searches of a job seeker on Jooble, a French job search engine.\n"
        "Here is what they are looking for, in their words:\n"
        f"{looking_for}\n\n"
        f"Give at most {MAX_SEARCHES} searches that, together, find the offers they want.\n"
        "- keywords: a few words, in French, as typed in a job board's search box\n"
        "  (a job title, possibly with a key technology). One idea per search: no lists, no OR.\n"
        "- remote: true only for full remote offers. Such a search has no location nor radius.\n"
        "- location and radius_km: for on-site or hybrid offers, the place they want to work\n"
        "  and how far around it. If they give no distance, choose a reasonable one.\n"
        "If they accept both on-site offers near a place and full remote offers, give the same\n"
        "keywords twice: once with the place, once remote. Fewer searches are better than\n"
        "overlapping ones: each search costs part of a small daily quota."
    )


# ---------- The LLM call ----------


def plan_searches(model: BaseChatModel, looking_for: str) -> list[JoobleSearch]:
    """Ask the LLM for the searches matching `looking_for`. They are not saved here."""
    # json_schema: see `scoring.score_offers()` for why this method is used.
    planner = model.with_structured_output(PlannedSearches, method="json_schema")
    answer = planner.invoke(planning_prompt(looking_for))
    return [to_jooble_search(search) for search in answer.searches[:MAX_SEARCHES]]


def to_jooble_search(search: PlannedSearch) -> JoobleSearch:
    """A remote search keeps no place: the LLM may still give one, which Jooble must not get."""
    if search.remote:
        return JoobleSearch(keywords=search.keywords.strip(), remote=True)
    return JoobleSearch(
        keywords=search.keywords.strip(),
        location=(search.location or "").strip() or None,
        radius_km=search.radius_km,
    )
