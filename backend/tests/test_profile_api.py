from sqlmodel import select

from app.models import UserProfile


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
