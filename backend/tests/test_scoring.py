from datetime import UTC, datetime

from langchain_core.runnables import RunnableLambda

from app.models import JobOffer
from app.scoring import OfferScore, OfferScores, score_offers, scoring_prompt


def make_offer(offer_id: int, **overrides) -> JobOffer:
    values = {
        "id": offer_id,
        "source": "jooble",
        "external_id": str(offer_id),
        "title": f"Offer {offer_id}",
        "url": f"https://example.com/{offer_id}",
        "published_at": datetime(2026, 11, 24, tzinfo=UTC),
    }
    return JobOffer(**(values | overrides))


class FakeModel:
    """Stands in for the LLM: records each prompt and answers with the given function."""

    def __init__(self, answer):
        self.prompts = []
        self.answer = answer

    def with_structured_output(self, schema):
        assert schema is OfferScores

        def reply(prompt: str) -> OfferScores:
            self.prompts.append(prompt)
            return self.answer(prompt)

        return RunnableLambda(reply)


def scores_of(*pairs: tuple[int, int]) -> OfferScores:
    return OfferScores(scores=[OfferScore(id=offer_id, score=score) for offer_id, score in pairs])


def test_the_prompt_holds_the_profile_and_one_line_per_offer():
    offers = [
        make_offer(1, title="Python developer", company="Acme", location="Lyon", remote=True),
        make_offer(2, title="Data engineer", description="Full text pasted by the user"),
    ]

    prompt = scoring_prompt("AI developer, remote", offers)

    assert "AI developer, remote" in prompt
    assert "[1] Python developer | Acme | Lyon | full remote" in prompt
    assert "[2] Data engineer\nFull text pasted by the user" in prompt


def test_offers_are_sent_by_batches_of_20():
    offers = [make_offer(i) for i in range(1, 46)]
    model = FakeModel(lambda prompt: scores_of())

    score_offers(model, "AI developer", offers)

    assert len(model.prompts) == 3  # 20 + 20 + 5


def test_the_scores_of_every_batch_are_returned_by_offer_id():
    offers = [make_offer(i) for i in range(1, 23)]
    model = FakeModel(lambda prompt: scores_of(*[(i, 50) for i in range(1, 23) if f"[{i}]" in prompt]))

    scores = score_offers(model, "AI developer", offers)

    assert scores == {i: 50 for i in range(1, 23)}


def test_a_forgotten_offer_gets_no_score_and_an_invented_id_is_ignored():
    offers = [make_offer(1), make_offer(2)]
    model = FakeModel(lambda prompt: scores_of((1, 80), (99, 10)))

    scores = score_offers(model, "AI developer", offers)

    assert scores == {1: 80}
