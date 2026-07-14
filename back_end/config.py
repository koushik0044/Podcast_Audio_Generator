import os

from dotenv import load_dotenv

load_dotenv()

# --- LLM ---------------------------------------------------------------------
#
# Two backends, selected by LLM_BACKEND. Defaults to openai when an OpenAI key is
# present, otherwise groq.
#
#   openai - paid, but generous rate limits. A podcast is ~10-20k tokens, well
#            under a cent on gpt-4o-mini. This is the reliable option.
#   groq   - free, but the free tier allows only 8k tokens/MINUTE and 200k/day.
#            An agent loop resends its whole conversation each iteration, so that
#            budget goes fast and jobs die on 429s.
#
# Both go through CrewAI's *native* OpenAI provider (Groq via its
# OpenAI-compatible endpoint), never the LiteLLM fallback. That is deliberate:
# CrewAI's agent executor tags system messages with a `cache_breakpoint` key, and
# only the native providers strip it before the request
# (crewai/llms/base_llm.py). The LiteLLM path leaks it into the payload and a
# strict API rejects the call with "property 'cache_breakpoint' is unsupported".
# Passing provider= explicitly also skips CrewAI's model-name validation, which
# would otherwise reject a non-OpenAI model name under the "openai" provider.

GROQ_DEFAULTS = {
    "base_url": "https://api.groq.com/openai/v1",
    # gpt-oss-120b is the only Groq free-tier model that satisfies both agents:
    # llama-3.3-70b emits malformed tool calls (breaking the researcher) and does
    # not support the json_schema response format (breaking the writer's
    # structured output).
    "research_model": "openai/gpt-oss-120b",
    "writer_model": "openai/gpt-oss-120b",
    "max_rpm": 20,
    "news_results": 4,
    "max_snippet_chars": 300,
}

OPENAI_DEFAULTS = {
    "base_url": None,  # the SDK's own default endpoint
    "research_model": "gpt-4o-mini",  # cheap, and calls tools reliably
    "writer_model": "gpt-4o",  # better prose; it is the one creative step
    "max_rpm": 60,
    # Rate limits are not the binding constraint here, so the researcher can
    # afford a richer view of the news than Groq's 8k-tokens/minute allowed.
    "news_results": 6,
    "max_snippet_chars": 600,
}

LLM_BACKEND = os.environ.get(
    "LLM_BACKEND", "openai" if os.environ.get("OPENAI_API_KEY") else "groq"
).lower()

if LLM_BACKEND not in ("openai", "groq"):
    raise ValueError(f"LLM_BACKEND must be 'openai' or 'groq', got {LLM_BACKEND!r}")

_defaults = OPENAI_DEFAULTS if LLM_BACKEND == "openai" else GROQ_DEFAULTS

LLM_PROVIDER = "openai"  # the CrewAI provider class, not the vendor
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", _defaults["base_url"])
LLM_API_KEY = os.environ.get(
    "OPENAI_API_KEY" if LLM_BACKEND == "openai" else "GROQ_API_KEY"
)

RESEARCH_MODEL = os.environ.get("RESEARCH_MODEL", _defaults["research_model"])
WRITER_MODEL = os.environ.get("WRITER_MODEL", _defaults["writer_model"])

MAX_RPM = int(os.environ.get("MAX_RPM", _defaults["max_rpm"]))
NEWS_RESULTS = int(os.environ.get("NEWS_RESULTS", _defaults["news_results"]))
MAX_SNIPPET_CHARS = int(
    os.environ.get("MAX_SNIPPET_CHARS", _defaults["max_snippet_chars"])
)

# TTS
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "elevenlabs")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_MODEL_ID = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_v3")
# Defaults are stock ElevenLabs voices. List your own with GET /v1/voices.
ELEVENLABS_VOICE_MALE = os.environ.get("ELEVENLABS_VOICE_MALE", "nPczCjzI2devNBz1zQrb")
ELEVENLABS_VOICE_FEMALE = os.environ.get("ELEVENLABS_VOICE_FEMALE", "EXAVITQu4vr4xnSDxMaL")
EDGE_VOICE_MALE = os.environ.get("EDGE_VOICE_MALE", "en-US-GuyNeural")
EDGE_VOICE_FEMALE = os.environ.get("EDGE_VOICE_FEMALE", "en-US-JennyNeural")

# Alerting. Optional: with no RESEND_API_KEY the app runs fine and just logs instead.
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
ALERT_EMAIL_FROM = os.environ.get("ALERT_EMAIL_FROM", "PAG <onboarding@resend.dev>")
ALERT_EMAIL_TO = os.environ.get("ALERT_EMAIL_TO")

# Job store
AUDIO_ROOT = os.environ.get("AUDIO_ROOT", "/tmp/pag_audio")
JOB_TTL_SECONDS = int(os.environ.get("JOB_TTL_SECONDS", "3600"))
MAX_JOBS = int(os.environ.get("MAX_JOBS", "50"))

# CORS
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]

# Keys required for the pipeline to run at all. The LLM key depends on the backend.
LLM_KEY_NAME = "OPENAI_API_KEY" if LLM_BACKEND == "openai" else "GROQ_API_KEY"
REQUIRED_KEYS = (LLM_KEY_NAME, "SERPER_API_KEY")


def missing_required_keys():
    """Names of required env vars that are unset, so startup can fail loudly."""
    return [k for k in REQUIRED_KEYS if not os.environ.get(k)]
