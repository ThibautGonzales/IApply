from sqlmodel import select

from app.models import UserProfile


def test_profile_is_empty_before_the_first_save(client):
    response = client.get("/profile")

    assert response.status_code == 200
    assert response.json()["looking_for"] == ""


def test_first_save_creates_the_profile(client, session):
    response = client.put("/profile", json={"looking_for": "  Python backend, remote  "})

    assert response.status_code == 200
    assert response.json()["looking_for"] == "Python backend, remote"
    assert session.get(UserProfile, 1).looking_for == "Python backend, remote"


def test_next_save_replaces_the_text(client, session):
    client.put("/profile", json={"looking_for": "First version"})

    client.put("/profile", json={"looking_for": "Second version"})

    assert client.get("/profile").json()["looking_for"] == "Second version"
    assert len(session.exec(select(UserProfile)).all()) == 1
