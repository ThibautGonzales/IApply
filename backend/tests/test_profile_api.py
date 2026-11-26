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
