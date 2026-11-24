import json
from datetime import UTC, date, datetime

import httpx
import pytest

from app.sources import SOURCES, jooble


def make_job(job_id: int) -> dict:
    return {
        "id": job_id,
        "title": "D&eacute;veloppeur <b>full stack</b>",
        "location": "Saint-Jacques-de-la-Lande &amp; co",
        "snippet": "&nbsp;Vous rejoindrez une <b>équipe</b>...",
        "salary": "",
        "source": "example.fr",
        "type": "CDI",
        "link": f"https://fr.jooble.org/desc/{job_id}",
        "company": "ACME",
        "updated": "2026-11-20T10:31:00.0000000",
    }


@pytest.fixture(autouse=True)
def jooble_env(monkeypatch):
    monkeypatch.setenv("JOOBLE_API_KEY", "test-key")
    monkeypatch.setenv("JOOBLE_KEYWORDS", "full stack;GenAI")
    monkeypatch.setenv("JOOBLE_INCLUDE_REMOTE", "false")  # remote searches have their own tests


def fake_client(pages_by_keywords: dict[str, list[list[dict]]], requests: list) -> httpx.Client:
    """An httpx client that answers like Jooble, without any network call."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append((request.url, body))
        pages = pages_by_keywords[body["keywords"]]
        page_index = int(body["page"]) - 1
        jobs = pages[page_index] if page_index < len(pages) else []
        return httpx.Response(200, json={"totalCount": 0, "jobs": jobs})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_to_job_offer_converts_and_cleans_a_jooble_result():
    offer = jooble.to_job_offer(make_job(42))

    assert offer.source == "jooble"
    assert offer.external_id == "42"
    assert offer.title == "Développeur full stack"
    assert offer.description == "Vous rejoindrez une équipe..."
    assert offer.location == "Saint-Jacques-de-la-Lande & co"
    assert offer.salary is None  # empty string from Jooble
    assert offer.contract_type == "CDI"
    assert offer.url == "https://fr.jooble.org/desc/42"
    assert offer.published_at == datetime(2026, 11, 20, 10, 31, tzinfo=UTC)


def test_fetch_jobs_runs_one_search_per_keyword_with_the_right_body():
    requests = []
    client = fake_client({"full stack": [[make_job(1)]], "GenAI": [[make_job(2)]]}, requests)

    offers = jooble.fetch_jobs(date(2026, 11, 20), client)

    assert [o.external_id for o in offers] == ["1", "2"]
    url, body = requests[0]
    assert str(url) == "https://fr.jooble.org/api/test-key"
    assert body["location"] == "Clermont-Ferrand"
    assert body["datecreatedfrom"] == "2026-11-20"


def test_fetch_jobs_reads_next_page_only_when_current_page_is_full():
    requests = []
    full_page = [make_job(i) for i in range(jooble.RESULTS_PER_PAGE)]
    client = fake_client({"full stack": [full_page, [make_job(999)]], "GenAI": [[]]}, requests)

    offers = jooble.fetch_jobs(date(2026, 11, 20), client)

    assert len(offers) == jooble.RESULTS_PER_PAGE + 1
    assert len(requests) == 3  # 2 pages for "full stack", 1 for "GenAI"


def test_fetch_jobs_raises_when_jooble_answers_an_error():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(403)))

    with pytest.raises(jooble.JoobleError) as error:
        jooble.fetch_jobs(date(2026, 11, 20), client)
    assert "test-key" not in str(error.value)


def test_jooble_is_registered_as_a_source():
    assert SOURCES["jooble"] is jooble.fetch_jobs


def test_fetch_jobs_drops_offers_older_than_since_even_if_jooble_returns_them():
    old_job = make_job(1) | {"updated": "2026-07-02T00:00:00.0000000"}
    client = fake_client({"full stack": [[old_job, make_job(2)]], "GenAI": [[]]}, [])

    offers = jooble.fetch_jobs(date(2026, 11, 20), client)

    assert [o.external_id for o in offers] == ["2"]


def test_remote_searches_are_added_when_enabled(monkeypatch):
    monkeypatch.setenv("JOOBLE_INCLUDE_REMOTE", "true")

    searches = jooble.build_searches(jooble.load_settings())

    assert [(s.keywords, s.location, s.radius_km) for s in searches] == [
        ("full stack", "Clermont-Ferrand", "40"),
        ("GenAI", "Clermont-Ferrand", "40"),
        ("full stack", "Télétravail", ""),
        ("GenAI", "Télétravail", ""),
    ]


def test_remote_search_sends_no_radius(monkeypatch):
    monkeypatch.setenv("JOOBLE_INCLUDE_REMOTE", "true")
    monkeypatch.setenv("JOOBLE_KEYWORDS", "full stack")
    requests = []
    client = fake_client({"full stack": [[]]}, requests)

    jooble.fetch_jobs(date(2026, 11, 20), client)

    assert requests[1][1]["location"] == "Télétravail"
    assert "radius" not in requests[1][1]


def test_offers_are_flagged_remote_by_search_or_location():
    assert jooble.to_job_offer(make_job(1)).remote is False
    assert jooble.to_job_offer(make_job(1), from_remote_search=True).remote is True
    assert jooble.to_job_offer(make_job(1) | {"location": "Télétravail"}).remote is True


def test_offer_found_by_local_and_remote_search_is_kept_once_as_remote(monkeypatch):
    monkeypatch.setenv("JOOBLE_INCLUDE_REMOTE", "true")
    monkeypatch.setenv("JOOBLE_KEYWORDS", "full stack")
    # The fake client answers by keywords only, so both searches return job 1.
    client = fake_client({"full stack": [[make_job(1)]]}, [])

    offers = jooble.fetch_jobs(date(2026, 11, 20), client)

    assert len(offers) == 1
    assert offers[0].remote is True
