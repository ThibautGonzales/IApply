from datetime import UTC, datetime

from langchain_core.runnables import RunnableLambda

from app import main
from app.models import JobOffer
from app.manual_offer import ExtractedOffer, extract_offer, extraction_prompt

PASTED_TEXT = "Développeur Python - Acme - Lyon - CDI - 45 k€ - Nous recherchons..."

EXTRACTED = ExtractedOffer(
    title="Développeur Python",
    company="Acme",
    location="Lyon",
    contract_type="CDI",
    salary="45 k€",
    remote=False,
)


class FakeModel:
    """Stands in for the LLM: records each prompt and answers with the given offer."""

    def __init__(self, answer: ExtractedOffer):
        self.prompts = []
        self.answer = answer

    def with_structured_output(self, schema, method):
        assert schema is ExtractedOffer
        assert method == "json_schema"

        def reply(prompt: str) -> ExtractedOffer:
            self.prompts.append(prompt)
            return self.answer

        return RunnableLambda(reply)


def test_the_prompt_holds_the_pasted_text():
    assert PASTED_TEXT in extraction_prompt(PASTED_TEXT)


def test_extract_offer_returns_the_fields_read_by_the_llm():
    model = FakeModel(EXTRACTED)

    assert extract_offer(model, PASTED_TEXT) == EXTRACTED
    assert PASTED_TEXT in model.prompts[0]


def test_the_extract_route_returns_the_fields(client, monkeypatch):
    monkeypatch.setattr(main, "get_chat_model", lambda settings: FakeModel(EXTRACTED))

    response = client.post("/jobs/manual/extract", json={"text": PASTED_TEXT})

    assert response.status_code == 200
    assert response.json() == EXTRACTED.model_dump()


def test_the_extract_route_saves_nothing(client, monkeypatch):
    monkeypatch.setattr(main, "get_chat_model", lambda settings: FakeModel(EXTRACTED))

    client.post("/jobs/manual/extract", json={"text": PASTED_TEXT})

    assert client.get("/jobs").json() == []


def test_the_extract_route_fails_without_an_llm(client):
    response = client.post("/jobs/manual/extract", json={"text": PASTED_TEXT})

    assert response.status_code == 400
    assert "LLM page" in response.json()["detail"]


def test_an_empty_text_is_refused(client):
    assert client.post("/jobs/manual/extract", json={"text": ""}).status_code == 422


# ---------- Saving the checked offer ----------

NEW_OFFER = {
    "url": "https://www.linkedin.com/jobs/view/123",
    "title": "Développeur Python",
    "company": "Acme",
    "location": "Lyon",
    "contract_type": "CDI",
    "salary": None,
    "remote": True,
    "description": PASTED_TEXT,
}


def test_the_checked_offer_is_saved_as_a_manual_offer(client):
    response = client.post("/jobs/manual", json=NEW_OFFER)

    assert response.status_code == 201
    offer = response.json()
    assert offer["source"] == "manual"
    assert (offer["title"], offer["company"], offer["remote"]) == ("Développeur Python", "Acme", True)
    assert offer["description"] == PASTED_TEXT
    assert offer["url"] == NEW_OFFER["url"]
    assert offer["score"] is None


def test_a_manual_offer_comes_first_in_the_list(client, session):
    session.add(
        JobOffer(
            source="jooble",
            external_id="1",
            title="Scored offer",
            url="https://example.com/1",
            score=95,
            published_at=datetime(2026, 11, 25, tzinfo=UTC),
        )
    )
    session.commit()

    client.post("/jobs/manual", json=NEW_OFFER)

    assert [job["title"] for job in client.get("/jobs").json()] == ["Développeur Python", "Scored offer"]


def test_the_same_link_cannot_be_added_twice(client):
    client.post("/jobs/manual", json=NEW_OFFER)

    response = client.post("/jobs/manual", json=NEW_OFFER | {"url": f"  {NEW_OFFER['url']} "})

    assert response.status_code == 409
    assert len(client.get("/jobs").json()) == 1


def test_an_offer_without_a_title_or_a_link_is_refused(client):
    assert client.post("/jobs/manual", json=NEW_OFFER | {"title": ""}).status_code == 422
    assert client.post("/jobs/manual", json=NEW_OFFER | {"url": ""}).status_code == 422
