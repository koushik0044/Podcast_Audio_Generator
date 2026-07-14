import logging
import os

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

import config

logger = logging.getLogger(__name__)

SERPER_URL = "https://google.serper.dev/news"


class NewsSearchInput(BaseModel):
    search_query: str = Field(description="The topic to search recent news for.")


class NewsSearchTool(BaseTool):
    """Compact news search, replacing SerperDevTool + ScrapeWebsiteTool.

    Two reasons this is hand-rolled rather than the stock crewai_tools pair:

    1. Tokens. Groq's free tier allows 8k tokens/MINUTE, and an agentic loop
       resends the whole conversation on every iteration. Scraping full article
       bodies blows that budget in a single turn and the run dies on a 429.
       Serper's headline + snippet is enough to summarize a news story from, at
       a fraction of the tokens.

    2. Schema strictness. Groq validates tool-call arguments against the schema
       and rejects unknown ones. SerperDevTool's description advertises extra
       parameters ("num", "type"), so the model would emit them and Groq would
       reject the call with "additionalProperties not allowed". This tool takes
       exactly one argument, so there is nothing to get wrong.
    """

    name: str = "search_recent_news"
    description: str = (
        "Search recent news articles for a topic. "
        "Takes a single argument, search_query. "
        "Returns the top headlines with a short snippet and source for each."
    )
    args_schema: type[BaseModel] = NewsSearchInput

    def _run(self, search_query: str) -> str:
        api_key = os.environ.get("SERPER_API_KEY")
        if not api_key:
            return "Search unavailable: SERPER_API_KEY is not set."

        try:
            response = requests.post(
                SERPER_URL,
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": search_query, "num": config.NEWS_RESULTS},
                timeout=20,
            )
            response.raise_for_status()
            articles = response.json().get("news", [])[: config.NEWS_RESULTS]
        except requests.RequestException as exc:
            logger.warning("news search failed for %r: %s", search_query, exc)
            return f"Search failed: {exc}"

        if not articles:
            return f"No recent news found for '{search_query}'."

        lines = []
        for i, a in enumerate(articles, 1):
            snippet = (a.get("snippet") or "").strip()[: config.MAX_SNIPPET_CHARS]
            lines.append(
                f"{i}. {a.get('title', 'Untitled')}\n"
                f"   Source: {a.get('source', 'unknown')} ({a.get('date', 'n/a')})\n"
                f"   {snippet}"
            )

        logger.info("news search %r returned %d articles", search_query, len(articles))
        return "\n\n".join(lines)
