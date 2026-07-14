import pytest
from crewai import LLM, Agent

from tasks import build_tasks


@pytest.fixture
def agent():
    """A real Agent (Task validates the type), but never invoked - constructing
    an LLM makes no network call, so these tests need no live credentials."""
    return Agent(
        role="Test",
        goal="Test",
        backstory="Test",
        llm=LLM(model="gpt-4o-mini", provider="openai", api_key="test-key"),
    )


def test_build_tasks_keeps_the_topic_placeholder_across_calls(agent):
    """Regression test for the bug that corrupted every job after the first.

    The old code held Task objects as module-level singletons and formatted the
    topic straight into the shared description. Once request #1 replaced
    "{topic}" with its own topic, the placeholder was gone forever, so every
    later job silently regenerated a podcast about the *first* topic.

    Building tasks per job must leave "{topic}" intact for Crew.kickoff() to
    interpolate each time.
    """
    for _ in range(3):
        fetch, write = build_tasks(agent, agent)
        assert "{topic}" in fetch.description
        assert "{topic}" in write.description


def test_build_tasks_returns_independent_objects(agent):
    first_fetch, _ = build_tasks(agent, agent)
    second_fetch, _ = build_tasks(agent, agent)
    assert first_fetch is not second_fetch

    # Mutating one job's task must not leak into the next.
    first_fetch.description = "mutated"
    third_fetch, _ = build_tasks(agent, agent)
    assert "{topic}" in third_fetch.description


def test_writer_task_is_wired_for_structured_output(agent):
    from schemas import PodcastScript

    fetch, write = build_tasks(agent, agent)
    assert write.output_pydantic is PodcastScript
    # The writer must see the researcher's output.
    assert fetch in write.context
