import pytest
from sqlmodel import select

from app import main
from app.models import JoobleSearch, UserProfile


class FakePlanner:
    """Stands in for `plan_searches()`: one remote search per call, named after the text it got."""

    def __init__(self):
        self.calls = []

    def __call__(self, model, looking_for):
        self.calls.append(looking_for)
        return [JoobleSearch(keywords=looking_for, remote=True)]


@pytest.fixture(autouse=True)
def planner(monkeypatch) -> FakePlanner:
    planner = FakePlanner()
    monkeypatch.setattr(main, "get_chat_model", lambda settings: None)
    monkeypatch.setattr(main, "plan_searches", planner)
    return planner


def test_profile_is_empty_before_the_first_save(client):
    response = client.get("/profile")

    assert response.status_code == 200
    assert response.json()["looking_for"] == ""
    assert "id" not in response.json()


def test_save_replaces_the_text_of_the_only_profile(client, session):
    client.put("/profile", json={"looking_for": "First version"})

    response = client.put("/profile", json={"looking_for": "  Second version  "})

    assert response.status_code == 200
    assert response.json()["looking_for"] == "Second version"
    assert client.get("/profile").json()["looking_for"] == "Second version"
    assert len(session.exec(select(UserProfile)).all()) == 1


def test_both_thresholds_are_saved_with_the_profile(client):
    body = {"looking_for": "AI developer", "min_score_onsite": 55, "min_score_remote": 75}
    response = client.put("/profile", json=body)

    assert (response.json()["min_score_onsite"], response.json()["min_score_remote"]) == (55, 75)
    saved = client.get("/profile").json()
    assert (saved["min_score_onsite"], saved["min_score_remote"]) == (55, 75)


def test_the_thresholds_are_kept_when_they_are_not_sent(client):
    client.put("/profile", json={"looking_for": "AI developer", "min_score_onsite": 55, "min_score_remote": 75})

    response = client.put("/profile", json={"looking_for": "Python developer"})

    assert (response.json()["min_score_onsite"], response.json()["min_score_remote"]) == (55, 75)


def test_a_threshold_outside_0_to_100_is_refused(client):
    for field in ("min_score_onsite", "min_score_remote"):
        response = client.put("/profile", json={"looking_for": "AI developer", field: 101})

        assert response.status_code == 422


def test_the_background_is_empty_before_the_first_save(client):
    assert client.get("/profile").json()["background"] == ""


def test_the_background_is_saved_with_the_profile(client):
    body = {"looking_for": "AI developer", "background": "  5 years of Python at Michelin  "}
    response = client.put("/profile", json=body)

    assert response.json()["background"] == "5 years of Python at Michelin"
    assert client.get("/profile").json()["background"] == "5 years of Python at Michelin"


def test_the_background_is_kept_when_it_is_not_sent(client):
    client.put("/profile", json={"looking_for": "AI developer", "background": "5 years of Python"})

    response = client.put("/profile", json={"looking_for": "Python developer"})

    assert response.json()["background"] == "5 years of Python"


def test_there_are_no_searches_before_the_first_save(client):
    assert client.get("/profile/searches").json() == []


def test_saving_what_i_look_for_replaces_the_searches(client, planner):
    client.put("/profile", json={"looking_for": "First version"})
    client.put("/profile", json={"looking_for": "Second version"})

    searches = client.get("/profile/searches").json()
    assert [(s["keywords"], s["remote"]) for s in searches] == [("Second version", True)]
    assert planner.calls == ["First version", "Second version"]


def test_saving_the_same_text_does_not_call_the_llm_again(client, planner):
    client.put("/profile", json={"looking_for": "AI developer"})

    client.put("/profile", json={"looking_for": " AI developer ", "background": "5 years of Python"})

    assert planner.calls == ["AI developer"]


def test_an_empty_text_clears_the_searches_without_the_llm(client, planner):
    client.put("/profile", json={"looking_for": "AI developer"})

    client.put("/profile", json={"looking_for": "  "})

    assert client.get("/profile/searches").json() == []
    assert planner.calls == ["AI developer"]


def test_nothing_is_saved_when_the_llm_fails(client, monkeypatch):
    client.put("/profile", json={"looking_for": "AI developer"})

    def failing_planner(model, looking_for):
        raise RuntimeError("quota reached")

    monkeypatch.setattr(main, "plan_searches", failing_planner)
    response = client.put("/profile", json={"looking_for": "Python developer", "min_score_onsite": 70})

    assert response.status_code == 400
    assert "quota reached" in response.json()["detail"]
    assert client.get("/profile").json()["looking_for"] == "AI developer"
    assert client.get("/profile").json()["min_score_onsite"] == 50
    assert [s["keywords"] for s in client.get("/profile/searches").json()] == ["AI developer"]
