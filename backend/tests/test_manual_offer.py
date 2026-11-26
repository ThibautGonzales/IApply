from langchain_core.runnables import RunnableLambda

from app import main
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
