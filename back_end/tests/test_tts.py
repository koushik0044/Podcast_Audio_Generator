import pytest

from schemas import DialogueLine
from tts import FallbackTTS, TTSProvider, TTSUnavailableError, strip_audio_tags


class StubProvider(TTSProvider):
    def __init__(self, name, raises=None):
        self.name = name
        self.calls = 0
        self._raises = raises

    def synthesize(self, line):
        self.calls += 1
        if self._raises:
            raise self._raises
        return b"audio-from-" + self.name.encode()


@pytest.fixture
def line():
    return DialogueLine(text="[laughs] Hello there", voice="Male")


def test_strip_audio_tags_removes_tags_and_tidies_spacing():
    assert strip_audio_tags("[laughs] Hello [pauses] there") == "Hello there"
    assert strip_audio_tags("No tags here") == "No tags here"


def test_uses_primary_when_it_works(line):
    primary, fallback = StubProvider("elevenlabs"), StubProvider("edge-tts")
    tts = FallbackTTS(primary, fallback)

    assert tts.synthesize(line) == b"audio-from-elevenlabs"
    assert fallback.calls == 0
    assert not tts.degraded


def test_falls_back_on_quota_error_instead_of_failing(line):
    primary = StubProvider("elevenlabs", raises=TTSUnavailableError("429 quota exceeded"))
    fallback = StubProvider("edge-tts")
    tts = FallbackTTS(primary, fallback)

    assert tts.synthesize(line) == b"audio-from-edge-tts"
    assert tts.degraded
    assert tts.name == "edge-tts"


def test_stays_degraded_and_stops_retrying_the_dead_provider(line):
    primary = StubProvider("elevenlabs", raises=TTSUnavailableError("429"))
    fallback = StubProvider("edge-tts")
    tts = FallbackTTS(primary, fallback)

    for _ in range(3):
        tts.synthesize(line)

    # Primary is tried once, then abandoned for the rest of the job.
    assert primary.calls == 1
    assert fallback.calls == 3


def test_quota_error_notifies_once(line):
    alerts = []
    primary = StubProvider("elevenlabs", raises=TTSUnavailableError("429"))
    tts = FallbackTTS(primary, StubProvider("edge-tts"), on_quota_error=alerts.append)

    for _ in range(3):
        tts.synthesize(line)

    assert len(alerts) == 1


def test_non_quota_errors_still_propagate(line):
    primary = StubProvider("elevenlabs", raises=RuntimeError("connection reset"))
    tts = FallbackTTS(primary, StubProvider("edge-tts"))

    with pytest.raises(RuntimeError):
        tts.synthesize(line)
