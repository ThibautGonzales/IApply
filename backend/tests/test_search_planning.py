from langchain_core.runnables import RunnableLambda

from app.search_planning import MAX_SEARCHES, PlannedSearch, PlannedSearches, plan_searches, planning_prompt


class FakeModel:
    """Stands in for the LLM: records the prompt and answers the given searches."""

    def __init__(self, searches: list[PlannedSearch]):
        self.prompts = []
        self.searches = searches

    def with_structured_output(self, schema, method):
        assert schema is PlannedSearches
        assert method == "json_schema"

        def reply(prompt: str) -> PlannedSearches:
            self.prompts.append(prompt)
            return PlannedSearches(searches=self.searches)

        return RunnableLambda(reply)


def planned(keywords="développeur IA", remote=False, location=None, radius_km=None) -> PlannedSearch:
    return PlannedSearch(keywords=keywords, remote=remote, location=location, radius_km=radius_km)


def test_the_prompt_holds_what_the_user_is_looking_for():
    prompt = planning_prompt("Full stack developer near Clermont-Ferrand, or remote")

    assert "Full stack developer near Clermont-Ferrand, or remote" in prompt
    assert f"at most {MAX_SEARCHES} searches" in prompt


def test_the_planned_searches_become_jooble_searches():
    model = FakeModel([
        planned("développeur full stack", location="Clermont-Ferrand", radius_km=40),
        planned("développeur full stack", remote=True),
    ])

    local, remote = plan_searches(model, "Full stack developer near Clermont-Ferrand, or remote")

    assert (local.keywords, local.location, local.radius_km, local.remote) == (
        "développeur full stack", "Clermont-Ferrand", 40, False
    )
    assert (remote.keywords, remote.location, remote.radius_km, remote.remote) == (
        "développeur full stack", None, None, True
    )
    assert "Full stack developer near Clermont-Ferrand, or remote" in model.prompts[0]


def test_a_remote_search_drops_the_place_the_llm_gave():
    model = FakeModel([planned(remote=True, location="Lyon", radius_km=30)])

    [search] = plan_searches(model, "AI developer, remote")

    assert (search.location, search.radius_km) == (None, None)


def test_the_searches_beyond_the_maximum_are_dropped():
    model = FakeModel([planned(f"keywords {i}", remote=True) for i in range(MAX_SEARCHES + 2)])

    searches = plan_searches(model, "Anything")

    assert len(searches) == MAX_SEARCHES
