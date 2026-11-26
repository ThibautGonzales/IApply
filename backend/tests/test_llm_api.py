import pytest
from langchain_core.language_models import FakeListChatModel

from app import llm, main


@pytest.fixture(autouse=True)
def env_file(tmp_path, monkeypatch):
    """Each test gets its own .env file, in a temporary folder: the real key is never touched."""
    path = tmp_path / "data" / ".env"
    monkeypatch.setattr(llm, "ENV_PATH", path)
    return path


def test_nothing_is_chosen_at_first(client):
    response = client.get("/llm")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] is None
    assert body["model"] is None
    assert body["api_key_hint"] is None
    assert [p["id"] for p in body["providers"]] == ["openai", "anthropic", "google_genai", "mistralai"]


def test_the_key_goes_to_the_env_file_and_only_its_end_comes_back(client, session, env_file):
    response = client.put("/llm", json={"api_key": "  sk-ant-secret-1234  "})

    body = response.json()
    assert body["api_key_hint"] == "…1234"
    assert "sk-ant-secret-1234" not in response.text
    assert 'LLM_API_KEY' in env_file.read_text()
    assert "sk-ant-secret-1234" in env_file.read_text()
    # The provider is guessed from the key, and its default model is used.
    assert body["provider"] == "anthropic"
    assert body["model"] == "claude-haiku-5-5"


def test_the_key_never_reaches_the_database(client, session):
    client.put("/llm", json={"api_key": "sk-ant-secret-1234"})

    settings = llm.get_settings(session)
    assert "sk-ant-secret-1234" not in str(settings.model_dump())


def test_a_typed_model_replaces_the_default_until_it_is_emptied(client):
    client.put("/llm", json={"provider": "mistralai", "model": " mistral-large-latest "})
    assert client.get("/llm").json()["model"] == "mistral-large-latest"

    response = client.put("/llm", json={"model": ""})

    assert response.json()["model"] == "mistral-small-latest"


def test_changing_provider_forgets_the_model_of_the_old_one(client):
    client.put("/llm", json={"provider": "openai", "model": "gpt-5"})

    response = client.put("/llm", json={"provider": "anthropic"})

    assert response.json()["model"] == "claude-haiku-5-5"


def test_an_unknown_provider_is_refused(client):
    response = client.put("/llm", json={"provider": "unknown"})

    assert response.status_code == 400


def test_the_test_button_fails_without_a_key(client):
    client.put("/llm", json={"provider": "anthropic"})

    response = client.post("/llm/test")

    assert response.status_code == 400


def test_the_test_button_succeeds_when_the_model_answers(client, monkeypatch):
    monkeypatch.setattr(main, "get_chat_model", lambda settings: FakeListChatModel(responses=["OK"]))

    response = client.post("/llm/test")

    assert response.status_code == 200
