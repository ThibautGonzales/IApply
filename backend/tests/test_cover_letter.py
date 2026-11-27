from datetime import UTC, datetime

from langchain_core.language_models import FakeListChatModel

from app import main
from app.cover_letter import generation_prompt
from app.models import CoverLetterExample, JobOffer, UserProfile

LETTER = "Madame, Monsieur,\n\nVotre offre de développeur Python..."


def make_offer(session, description: str | None = "Nous recherchons un développeur Python...") -> JobOffer:
    offer = JobOffer(
        source="manual",
        external_id="1",
        title="Développeur Python",
        company="Acme",
        url="https://example.com/1",
        description=description,
        published_at=datetime(2026, 11, 27, tzinfo=UTC),
    )
    session.add(offer)
    session.commit()
    return offer


def fill_profile(session, background: str = "5 ans de Python chez Michelin") -> None:
    profile = session.get_one(UserProfile, 1)
    profile.looking_for = "Développeur Python, Clermont-Ferrand"
    profile.background = background
    session.add(profile)
    session.commit()


def fake_llm(monkeypatch, answer: str = LETTER) -> None:
    monkeypatch.setattr(main, "get_chat_model", lambda settings: FakeListChatModel(responses=[answer]))


# ---------- Prompt ----------


def test_the_prompt_holds_the_profile_the_examples_and_the_offer(session):
    fill_profile(session)
    offer = make_offer(session)
    examples = [CoverLetterExample(title="Letter for Michelin, 2025", text="Ma lettre pour Michelin")]

    prompt = generation_prompt(session.get_one(UserProfile, 1), examples, offer)

    for expected in [
        "5 ans de Python chez Michelin",
        "Clermont-Ferrand",
        "Ma lettre pour Michelin",
        "Acme",
        "Nous recherchons un développeur Python",
    ]:
        assert expected in prompt
    assert "Letter for Michelin, 2025" not in prompt  # the title is only for the user


def test_without_examples_the_prompt_asks_for_a_classic_letter(session):
    fill_profile(session)
    prompt = generation_prompt(session.get_one(UserProfile, 1), [], make_offer(session))

    assert "classic cover letter" in prompt


# ---------- Routes ----------


def test_there_is_no_letter_before_one_is_generated(client, session):
    offer = make_offer(session)

    assert client.get(f"/jobs/{offer.id}/cover-letter").status_code == 404


def test_a_generated_letter_is_saved_and_can_be_read_again(client, session, monkeypatch):
    fill_profile(session)
    offer = make_offer(session)
    fake_llm(monkeypatch, f"  {LETTER}  ")

    response = client.post(f"/jobs/{offer.id}/cover-letter")

    assert response.status_code == 200
    assert response.json()["text"] == LETTER
    assert client.get(f"/jobs/{offer.id}/cover-letter").json()["text"] == LETTER


def test_generating_again_replaces_the_letter(client, session, monkeypatch):
    fill_profile(session)
    offer = make_offer(session)
    fake_llm(monkeypatch, "First letter")
    first_id = client.post(f"/jobs/{offer.id}/cover-letter").json()["id"]
    fake_llm(monkeypatch, "Second letter")

    response = client.post(f"/jobs/{offer.id}/cover-letter")

    assert (response.json()["id"], response.json()["text"]) == (first_id, "Second letter")


def test_no_letter_without_the_offer_text(client, session, monkeypatch):
    fill_profile(session)
    offer = make_offer(session, description=None)
    fake_llm(monkeypatch)

    response = client.post(f"/jobs/{offer.id}/cover-letter")

    assert response.status_code == 400
    assert "offer text" in response.json()["detail"]


def test_no_letter_without_the_background(client, session, monkeypatch):
    fill_profile(session, background="")
    offer = make_offer(session)
    fake_llm(monkeypatch)

    response = client.post(f"/jobs/{offer.id}/cover-letter")

    assert response.status_code == 400
    assert "background" in response.json()["detail"]


def test_no_letter_without_an_llm(client, session):
    fill_profile(session)
    offer = make_offer(session)

    response = client.post(f"/jobs/{offer.id}/cover-letter")

    assert response.status_code == 400
    assert "LLM page" in response.json()["detail"]


def test_the_letter_can_be_changed_by_hand(client, session, monkeypatch):
    fill_profile(session)
    offer = make_offer(session)
    fake_llm(monkeypatch)
    client.post(f"/jobs/{offer.id}/cover-letter")

    response = client.put(f"/jobs/{offer.id}/cover-letter", json={"text": "My own version"})

    assert response.status_code == 200
    assert client.get(f"/jobs/{offer.id}/cover-letter").json()["text"] == "My own version"


def test_a_letter_cannot_be_changed_before_it_is_generated(client, session):
    offer = make_offer(session)

    assert client.put(f"/jobs/{offer.id}/cover-letter", json={"text": "My own version"}).status_code == 404
