from datetime import UTC, datetime

from langchain_core.language_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from app import main
from app.cover_letter import LetterChanges, Replacement, apply_replacements, generation_prompt
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


def test_the_prompt_says_the_letters_are_true_facts_too(session):
    fill_profile(session)
    prompt = generation_prompt(session.get_one(UserProfile, 1), [], make_offer(session))

    one_line = prompt.replace("\n", " ")  # the prompt is cut in lines: compare without them
    assert "is true as well, like their background" in one_line
    assert "neither in their background nor in their letters" in one_line


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


def test_a_letter_example_is_enough_without_the_background(client, session, monkeypatch):
    fill_profile(session, background="")
    client.post("/letter-examples", json={"title": "Michelin", "text": "J'ai 5 ans de Python..."})
    offer = make_offer(session)
    fake_llm(monkeypatch)

    assert client.post(f"/jobs/{offer.id}/cover-letter").status_code == 200


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


# ---------- Changing a letter ----------


class FakeReviser:
    """Stands in for the LLM when a letter is changed: records each prompt, answers the given replacements."""

    def __init__(self, replacements: list[Replacement]):
        self.prompts = []
        self.replacements = replacements

    def with_structured_output(self, schema, method):
        assert schema is LetterChanges
        assert method == "json_schema"

        def reply(prompt: str) -> LetterChanges:
            self.prompts.append(prompt)
            return LetterChanges(replacements=self.replacements)

        return RunnableLambda(reply)


def test_replacements_found_once_are_applied_in_order():
    text, failed = apply_replacements(
        "I like Python. I like Java.",
        [Replacement(old="Python", new="Go"), Replacement(old="Go.", new="Go and Rust.")],
    )

    assert (text, failed) == ("I like Go and Rust. I like Java.", [])


def test_a_replacement_not_found_or_found_twice_fails_and_changes_nothing():
    missing = Replacement(old="Kotlin", new="Rust")
    twice = Replacement(old="I like", new="I love")
    empty = Replacement(old="", new="Hello")

    text, failed = apply_replacements("I like Python. I like Java.", [missing, twice, empty])

    assert (text, failed) == ("I like Python. I like Java.", [missing, twice, empty])


def test_an_empty_new_text_deletes_the_passage():
    text, _ = apply_replacements("Hello. Useless sentence. Bye.", [Replacement(old=" Useless sentence.", new="")])

    assert text == "Hello. Bye."


def make_letter(client, session, monkeypatch) -> JobOffer:
    fill_profile(session)
    offer = make_offer(session)
    fake_llm(monkeypatch, "Old letter")
    client.post(f"/jobs/{offer.id}/cover-letter")
    return offer


def test_the_revise_route_applies_the_changes_to_the_page_text_and_saves_it(client, session, monkeypatch):
    offer = make_letter(client, session, monkeypatch)
    reviser = FakeReviser([Replacement(old="Python", new="Go"), Replacement(old="Kotlin", new="Rust")])
    monkeypatch.setattr(main, "get_chat_model", lambda settings: reviser)

    # The page sends its own text: here changed by hand ("Old" became "My") and not saved yet.
    body = {"text": "My letter about Python", "instructions": "Talk about Go instead"}
    response = client.post(f"/jobs/{offer.id}/cover-letter/revise", json=body)

    assert response.status_code == 200
    assert response.json()["letter"]["text"] == "My letter about Go"
    assert response.json()["failed"] == [{"old": "Kotlin", "new": "Rust"}]
    assert client.get(f"/jobs/{offer.id}/cover-letter").json()["text"] == "My letter about Go"
    for expected in ["My letter about Python", "Talk about Go instead", "5 ans de Python chez Michelin", "Acme"]:
        assert expected in reviser.prompts[0]


def test_a_letter_cannot_be_revised_before_it_is_generated(client, session):
    offer = make_offer(session)

    body = {"text": "A letter", "instructions": "Shorter"}
    assert client.post(f"/jobs/{offer.id}/cover-letter/revise", json=body).status_code == 404


def test_revising_without_instructions_is_refused(client, session, monkeypatch):
    offer = make_letter(client, session, monkeypatch)

    body = {"text": "A letter", "instructions": ""}
    assert client.post(f"/jobs/{offer.id}/cover-letter/revise", json=body).status_code == 422
