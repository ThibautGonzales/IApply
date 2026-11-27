def add(client, title: str, text: str = "Dear Sir or Madam, ..."):
    return client.post("/letter-examples", json={"title": title, "text": text})


def test_there_is_no_example_at_first(client):
    assert client.get("/letter-examples").json() == []


def test_added_examples_are_listed_in_the_order_they_were_added(client):
    response = add(client, "  Data engineer at Michelin  ", "  First letter  ")
    add(client, "Python developer at OVH")

    assert response.status_code == 201
    assert (response.json()["title"], response.json()["text"]) == ("Data engineer at Michelin", "First letter")
    titles = [example["title"] for example in client.get("/letter-examples").json()]
    assert titles == ["Data engineer at Michelin", "Python developer at OVH"]


def test_an_example_without_title_or_text_is_refused(client):
    assert add(client, "", "Some text").status_code == 422
    assert add(client, "A title", "").status_code == 422


def test_an_example_can_be_changed(client):
    example_id = add(client, "Old title").json()["id"]

    response = client.put(f"/letter-examples/{example_id}", json={"title": "New title", "text": "New text"})

    assert response.status_code == 200
    saved = client.get("/letter-examples").json()
    assert [(example["title"], example["text"]) for example in saved] == [("New title", "New text")]


def test_an_example_can_be_deleted(client):
    kept_id = add(client, "Kept").json()["id"]
    deleted_id = add(client, "Deleted").json()["id"]

    response = client.delete(f"/letter-examples/{deleted_id}")

    assert response.status_code == 204
    assert [example["id"] for example in client.get("/letter-examples").json()] == [kept_id]


def test_an_unknown_example_is_not_found(client):
    assert client.put("/letter-examples/999", json={"title": "A", "text": "B"}).status_code == 404
    assert client.delete("/letter-examples/999").status_code == 404
