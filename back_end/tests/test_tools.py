import requests

import config
from tools import NewsSearchTool


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_formats_articles_compactly(monkeypatch):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **kw: FakeResponse(
            {
                "news": [
                    {
                        "title": "EU AI Act enforced",
                        "source": "Reuters",
                        "date": "1d ago",
                        "snippet": "Guidelines took effect.",
                    }
                ]
            }
        ),
    )

    out = NewsSearchTool()._run("AI regulation")

    assert "EU AI Act enforced" in out
    assert "Reuters" in out
    assert "Guidelines took effect." in out


def test_truncates_long_snippets(monkeypatch):
    """Groq's free tier caps at 8k tokens/minute, so research context stays small."""
    monkeypatch.setattr(config, "MAX_SNIPPET_CHARS", 20)
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **kw: FakeResponse({"news": [{"title": "T", "snippet": "x" * 5000}]}),
    )

    assert len(NewsSearchTool()._run("topic")) < 200


def test_caps_the_number_of_articles(monkeypatch):
    monkeypatch.setattr(config, "NEWS_RESULTS", 2)
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **kw: FakeResponse(
            {"news": [{"title": f"Article {i}", "snippet": "s"} for i in range(10)]}
        ),
    )

    out = NewsSearchTool()._run("topic")

    assert "Article 1" in out
    assert "Article 5" not in out


def test_takes_exactly_one_argument():
    """Groq rejects tool calls with unknown arguments. SerperDevTool advertised
    extra params ("num", "type") that the model would emit, breaking the call."""
    assert set(NewsSearchTool().args_schema.model_fields) == {"search_query"}


def test_reports_search_failure_without_crashing(monkeypatch):
    def boom(*a, **kw):
        raise requests.RequestException("connection reset")

    monkeypatch.setattr(requests, "post", boom)

    assert "Search failed" in NewsSearchTool()._run("topic")


def test_handles_no_results(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: FakeResponse({"news": []}))
    assert "No recent news" in NewsSearchTool()._run("obscure topic")
