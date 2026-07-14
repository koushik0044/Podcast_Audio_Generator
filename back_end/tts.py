import asyncio
import logging
import re

import config
from schemas import DialogueLine

logger = logging.getLogger(__name__)

# ElevenLabs v3 audio tags, e.g. "[laughs]", "[whispers]". Providers that cannot
# perform them must strip them, or they get read aloud as literal text.
AUDIO_TAG_RE = re.compile(r"\[[^\]\n]{1,40}\]")


def strip_audio_tags(text: str) -> str:
    return re.sub(r"\s{2,}", " ", AUDIO_TAG_RE.sub("", text)).strip()


class TTSUnavailableError(Exception):
    """Provider rejected us for auth, permission, or quota reasons - all of which
    are worth degrading to the free voice over rather than failing the job."""


class TTSProvider:
    name = "base"

    def synthesize(self, line: DialogueLine) -> bytes:
        raise NotImplementedError


class ElevenLabsTTS(TTSProvider):
    name = "elevenlabs"

    def __init__(self):
        from elevenlabs import ElevenLabs

        if not config.ELEVENLABS_API_KEY:
            raise TTSUnavailableError("ELEVENLABS_API_KEY is not set")
        self._client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
        self._model_id = config.ELEVENLABS_MODEL_ID

    def synthesize(self, line: DialogueLine) -> bytes:
        from elevenlabs.core import ApiError

        voice_id = (
            config.ELEVENLABS_VOICE_MALE
            if line.voice == "Male"
            else config.ELEVENLABS_VOICE_FEMALE
        )
        settings = {"stability": line.stability, "similarity_boost": 0.75}
        # eleven_v3 rejects speed; its pacing comes from audio tags instead.
        if line.speed is not None and self._model_id != "eleven_v3":
            settings["speed"] = line.speed

        try:
            chunks = self._client.text_to_speech.convert(
                voice_id=voice_id,
                model_id=self._model_id,
                output_format="mp3_44100_128",
                text=line.text,
                voice_settings=settings,
            )
            return b"".join(chunks)
        except ApiError as exc:
            status = getattr(exc, "status_code", None)
            if status in (401, 403, 429):
                raise TTSUnavailableError(f"ElevenLabs returned {status}: {exc}") from exc
            raise


class EdgeTTS(TTSProvider):
    """Free fallback. No API key, no quota. Cannot perform audio tags, so it
    strips them and approximates delivery with rate only."""

    name = "edge-tts"

    def synthesize(self, line: DialogueLine) -> bytes:
        import edge_tts

        text = strip_audio_tags(line.text)
        if not text:
            raise ValueError("nothing left to speak after stripping audio tags")

        voice = (
            config.EDGE_VOICE_MALE if line.voice == "Male" else config.EDGE_VOICE_FEMALE
        )
        # edge-tts wants a relative percentage, e.g. "-10%".
        rate = f"{round(((line.speed or 1.0) - 1.0) * 100):+d}%"

        async def _run() -> bytes:
            audio = bytearray()
            async for chunk in edge_tts.Communicate(text, voice, rate=rate).stream():
                if chunk["type"] == "audio":
                    audio.extend(chunk["data"])
            return bytes(audio)

        return asyncio.run(_run())


class FallbackTTS(TTSProvider):
    """Runs `primary`, and on a quota error switches permanently to `fallback`
    for the rest of the job rather than failing it.

    ElevenLabs' free tier is only ~10k characters/month, so a public demo will
    exhaust it. Degrading to a free voice beats returning an error.
    """

    def __init__(self, primary: TTSProvider, fallback: TTSProvider, on_quota_error=None):
        self._primary = primary
        self._fallback = fallback
        self._on_quota_error = on_quota_error
        self._degraded = False

    @property
    def name(self) -> str:
        return self._fallback.name if self._degraded else self._primary.name

    @property
    def degraded(self) -> bool:
        return self._degraded

    def synthesize(self, line: DialogueLine) -> bytes:
        if self._degraded:
            return self._fallback.synthesize(line)

        try:
            return self._primary.synthesize(line)
        except TTSUnavailableError as exc:
            logger.warning(
                "%s unavailable (%s); falling back to %s for the rest of this job",
                self._primary.name,
                exc,
                self._fallback.name,
            )
            self._degraded = True
            if self._on_quota_error:
                self._on_quota_error(exc)
            return self._fallback.synthesize(line)


def build_tts(on_quota_error=None) -> TTSProvider:
    """Provider chosen by TTS_PROVIDER. Defaults to ElevenLabs with an edge-tts
    safety net; an unset/invalid ElevenLabs key degrades instead of crashing."""
    if config.TTS_PROVIDER == "edge-tts":
        return EdgeTTS()

    try:
        primary = ElevenLabsTTS()
    except TTSUnavailableError as exc:
        logger.warning("ElevenLabs unavailable (%s); using edge-tts", exc)
        return EdgeTTS()

    return FallbackTTS(primary, EdgeTTS(), on_quota_error=on_quota_error)
