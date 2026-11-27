"""Cover letters: the LLM writes one for an offer, from the user's profile and their own letters.

The LLM gets what the user wrote about themselves (background, what they look for), the letters
they already wrote (their style, and more true facts about them) and the offer text. It answers with the letter as plain
text, in one call: no structured output, the whole answer is the letter.
"""

from langchain_core.language_models import BaseChatModel
from sqlmodel import Session, col, select

from app.models import CoverLetter, CoverLetterExample, JobOffer, UserProfile, utc_now


class MissingOfferTextError(Exception):
    """The offer text was not pasted: a letter written from a title alone would say nothing."""


class MissingBackgroundError(Exception):
    """No background and no letter example: the LLM would have nothing true to say about the user."""


# ---------- Prompt ----------


def describe_offer(offer: JobOffer) -> str:
    details = [offer.title, offer.company, offer.location, offer.contract_type]
    return " | ".join(detail for detail in details if detail) + f"\n{offer.description}"


def describe_examples(examples: list[CoverLetterExample]) -> str:
    if not examples:
        return "They have not given any letter yet: write a sober, classic cover letter."
    return "\n\n".join(f"--- Letter {number} ---\n{example.text}" for number, example in enumerate(examples, 1))


def letter_context(profile: UserProfile, examples: list[CoverLetterExample], offer: JobOffer) -> str:
    """What the LLM must know to write a letter, or to change one (the changes come with the next step)."""
    return (
        "Their background, in their own words. It is true: use it freely.\n"
        f"{profile.background or '(not given)'}\n\n"
        "What they are looking for:\n"
        f"{profile.looking_for}\n\n"
        "Cover letters they already wrote. Follow their style: tone, structure, length, how they\n"
        "open and sign. What these letters say about the job seeker (skills, jobs, projects,\n"
        "results, motivations) is true as well, like their background: reuse it when it fits the\n"
        "offer. Only what they say about the companies they were written for is not to be reused.\n"
        f"{describe_examples(examples)}\n\n"
        "Never claim a skill, a job, a degree or any fact about the job seeker that is neither in\n"
        "their background nor in their letters.\n\n"
        "The job offer:\n"
        f"{describe_offer(offer)}"
    )


def generation_prompt(profile: UserProfile, examples: list[CoverLetterExample], offer: JobOffer) -> str:
    return (
        "You write a cover letter for a job seeker, for the job offer below.\n\n"
        f"{letter_context(profile, examples, offer)}\n\n"
        "Write the letter in the language of the offer. Answer with the text of the letter only, as\n"
        "plain text ready to paste: no Markdown, no comment before or after it. When a detail is not\n"
        "known (the recruiter's name, an address), leave it out rather than inventing it."
    )


# ---------- Reading and saving ----------


def get_letter(session: Session, offer: JobOffer) -> CoverLetter | None:
    return session.exec(select(CoverLetter).where(CoverLetter.job_offer_id == offer.id)).first()


def save_letter(session: Session, offer: JobOffer, text: str) -> CoverLetter:
    """Save the letter of the offer: the first one, or a new text replacing the one there was."""
    letter = get_letter(session, offer) or CoverLetter(job_offer_id=offer.id, text="")
    letter.text = text.strip()
    letter.updated_at = utc_now()
    session.add(letter)
    session.commit()
    session.refresh(letter)
    return letter


# ---------- Writing a letter ----------


def check_can_write(session: Session, offer: JobOffer) -> UserProfile:
    """Refuse before any LLM call (which costs money) when the letter could only be empty talk."""
    if not offer.description:
        raise MissingOfferTextError("Paste the offer text first (View offer).")
    profile = session.get_one(UserProfile, 1)
    # The letter examples say true things about the user too: one of them is enough without a background.
    if not profile.background and session.exec(select(CoverLetterExample)).first() is None:
        raise MissingBackgroundError(
            "Describe your background on the Profile page, or add a letter example, first."
        )
    return profile


def generate_letter(session: Session, model: BaseChatModel, offer: JobOffer) -> CoverLetter:
    """Write a new letter for the offer and save it, replacing the one there was."""
    profile = check_can_write(session, offer)
    examples = list(session.exec(select(CoverLetterExample).order_by(col(CoverLetterExample.id))).all())
    answer = model.invoke(generation_prompt(profile, examples, offer))
    # .text joins the text parts of the answer: some providers send a list of parts, not a string.
    return save_letter(session, offer, answer.text)
