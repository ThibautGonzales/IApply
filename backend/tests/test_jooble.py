import json
from datetime import UTC, date, datetime

import httpx
import pytest

from app.sources import SOURCES, jooble


def make_job(job_id: int) -> dict:
    return {
        "id": job_id,
        "title": "D&eacute;veloppeur <b>full stack</b>",
        "location": "Clermont-Ferrand",
        "snippet": "&nbsp;Vous rejoindrez une <b>équipe</b>...",
        "salary": "",
        "source": "example.fr",
        "type": "CDI",
        "link": f"https://jooble.org/desc/{job_id}",
        "company": "ACME",
        "updated": "2026-11-20T10:31:00.0000000",
    }


@pytest.fixture(autouse=True)
def jooble_env(monkeypatch):
    monkeypatch.setenv("JOOBLE_API_KEY", "test-key")
    monkeypatch.setenv("JOOBLE_KEYWORDS", "full stack;GenAI")


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
    assert offer.salary is None  # empty string from Jooble
    assert offer.contract_type == "CDI"
    assert offer.url == "https://jooble.org/desc/42"
    assert offer.published_at == datetime(2026, 11, 20, 10, 31, tzinfo=UTC)


def test_fetch_jobs_runs_one_search_per_keyword_with_the_right_body():
    requests = []
    client = fake_client({"full stack": [[make_job(1)]], "GenAI": [[make_job(2)]]}, requests)

    offers = jooble.fetch_jobs(date(2026, 11, 23), client)

    assert [o.external_id for o in offers] == ["1", "2"]
    url, body = requests[0]
    assert str(url) == "https://jooble.org/api/test-key"
    assert body["location"] == "Clermont-Ferrand"
    assert body["datecreatedfrom"] == "2026-11-23"


def test_fetch_jobs_reads_next_page_only_when_current_page_is_full():
    requests = []
    full_page = [make_job(i) for i in range(jooble.RESULTS_PER_PAGE)]
    client = fake_client({"full stack": [full_page, [make_job(999)]], "GenAI": [[]]}, requests)

    offers = jooble.fetch_jobs(date(2026, 11, 23), client)

    assert len(offers) == jooble.RESULTS_PER_PAGE + 1
    assert len(requests) == 3  # 2 pages for "full stack", 1 for "GenAI"


def test_fetch_jobs_raises_when_jooble_answers_an_error():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(403)))

    with pytest.raises(httpx.HTTPStatusError):
        jooble.fetch_jobs(date(2026, 11, 23), client)


def test_jooble_is_registered_as_a_source():
    assert SOURCES["jooble"] is jooble.fetch_jobs
