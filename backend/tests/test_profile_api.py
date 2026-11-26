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


def test_the_threshold_is_saved_with_the_profile(client):
    response = client.put("/profile", json={"looking_for": "AI developer", "min_score": 55})

    assert response.json()["min_score"] == 55
    assert client.get("/profile").json()["min_score"] == 55


def test_the_threshold_is_kept_when_it_is_not_sent(client):
    client.put("/profile", json={"looking_for": "AI developer", "min_score": 55})

    response = client.put("/profile", json={"looking_for": "Python developer"})

    assert response.json()["min_score"] == 55


def test_a_threshold_outside_0_to_100_is_refused(client):
    response = client.put("/profile", json={"looking_for": "AI developer", "min_score": 101})

    assert response.status_code == 422
