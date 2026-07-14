import importlib

import pytest

import config
from agents import _llm as build_llm


@pytest.mark.parametrize("model", [config.RESEARCH_MODEL, config.WRITER_MODEL])
def test_llm_routes_through_a_native_provider_not_litellm(model):
    """Guards both LLM backends.

    CrewAI's agent executor tags system messages with a `cache_breakpoint` key.
    Only native providers strip it before sending; the LiteLLM fallback path
    leaks it into the payload and a strict API rejects the request outright with
    "property 'cache_breakpoint' is unsupported".

    So the LLM must resolve to a native provider class. `crewai.llm.LLM` is the
    LiteLLM wrapper - seeing it here means we silently regressed.
    """
    llm = build_llm(model)
    assert type(llm).__name__ != "LLM", "fell back to LiteLLM; requests will be rejected"
    assert type(llm).__module__.startswith("crewai.llms.providers")


def test_backend_selects_a_coherent_key_and_endpoint():
    """Each backend must line up: OpenAI talks to its own endpoint with an OpenAI
    key; Groq talks to its OpenAI-compatible endpoint with a Groq key."""
    if config.LLM_BACKEND == "openai":
        assert config.LLM_BASE_URL is None  # the SDK's default endpoint
        assert config.LLM_KEY_NAME == "OPENAI_API_KEY"
    else:
        assert "groq.com" in config.LLM_BASE_URL
        assert config.LLM_KEY_NAME == "GROQ_API_KEY"


def test_rejects_an_unknown_backend(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "bedrock")
    with pytest.raises(ValueError, match="LLM_BACKEND"):
        importlib.reload(config)
    monkeypatch.delenv("LLM_BACKEND")
    importlib.reload(config)


def test_refusal_is_caught_rather_than_synthesized():
    """A safety-trained model can return its refusal *as* the script. We must not
    turn that into audio of a model apologizing."""
    from schemas import PodcastScript
    from script_generator import _is_refusal

    refusal = PodcastScript(
        lines=[{"text": "I'm sorry, but I can't provide that.", "voice": "Male"}]
    )
    real = PodcastScript(
        lines=[
            {"text": "[curious] So what changed?", "voice": "Male"},
            {"text": "The EU AI Act took effect.", "voice": "Female"},
            {"text": "[laughs] Finally!", "voice": "Male"},
        ]
    )

    assert _is_refusal(refusal)
    assert not _is_refusal(real)
