from crewai import LLM, Agent

import config
from tools import NewsSearchTool


def _llm(model):
    """CrewAI's native OpenAI provider, pointed at either OpenAI itself or Groq's
    OpenAI-compatible endpoint. Never the LiteLLM fallback -- see config.py."""
    kwargs = {
        "model": model,
        "provider": config.LLM_PROVIDER,
        "api_key": config.LLM_API_KEY,
        "temperature": 0,
    }
    # Omitted for OpenAI, which uses the SDK's own endpoint.
    if config.LLM_BASE_URL:
        kwargs["base_url"] = config.LLM_BASE_URL

    return LLM(**kwargs)


def build_agents():
    """Fresh agents per job. These must not be module-level singletons: CrewAI
    mutates agent/task state during a run, so sharing them races across jobs."""
    news_researcher = Agent(
        role="News Researcher",
        goal="Summarize the information from the top three news articles for a given topic.",
        backstory=(
            "With years of experience in journalism, you have a keen eye for identifying newsworthy stories. "
            "Your expertise lies in quickly gathering and summarizing the most relevant and recent information from various sources. "
            "Your dedication to providing accurate and up-to-date news has earned you a reputation as a reliable and thorough researcher."
        ),
        llm=_llm(config.RESEARCH_MODEL),
        tools=[NewsSearchTool()],
        allow_delegation=False,
        verbose=False,
        max_rpm=config.MAX_RPM,
        # One search is enough; more iterations just burn the token budget.
        max_iter=3,
    )

    senior_script_writer = Agent(
        role="Senior Script Writer",
        goal="Write a podcast script based on the provided news summary in the required format and within the specified constraints",
        backstory=(
            "You are an experienced scriptwriter with a talent for creating engaging and informative content. "
            "You simplify complex topics and present them in an entertaining and easily digestible manner. "
            "You direct vocal performances with audio tags, the way a director marks up a screenplay."
        ),
        llm=_llm(config.WRITER_MODEL),
        allow_delegation=False,
        verbose=False,
        max_rpm=config.MAX_RPM,
    )

    return news_researcher, senior_script_writer
