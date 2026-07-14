import pytest
from pydantic import ValidationError

from schemas import DialogueLine, PodcastScript


def test_accepts_a_line_with_audio_tags():
    line = DialogueLine(
        text="[laughs] That is a great question... [pauses] let me think.",
        voice="Female",
        stability=0.3,
    )
    assert line.stability == 0.3
    assert line.speed is None


def test_stability_defaults_to_midpoint():
    assert DialogueLine(text="hi", voice="Male").stability == 0.5


@pytest.mark.parametrize(
    "field,value",
    [("stability", 1.5), ("stability", -0.1), ("speed", 0.1), ("speed", 3.0)],
)
def test_rejects_out_of_range_values(field, value):
    with pytest.raises(ValidationError):
        DialogueLine(text="hi", voice="Male", **{field: value})


def test_rejects_unknown_voice():
    with pytest.raises(ValidationError):
        DialogueLine(text="hi", voice="Robot")


def test_script_wraps_lines():
    script = PodcastScript(
        lines=[
            {"text": "[curious] So what changed?", "voice": "Male"},
            {"text": "Everything.", "voice": "Female", "stability": 0.7},
        ]
    )
    assert len(script.lines) == 2
    assert script.lines[1].voice == "Female"
