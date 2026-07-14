from typing import Literal, Optional

from pydantic import BaseModel, Field


class DialogueLine(BaseModel):
    """One spoken line of the podcast.

    `text` may embed ElevenLabs v3 audio tags ("[laughs]", "[whispers]", "[curious]")
    which the v3 model performs. They replace the emotion enum the old PlayHT
    integration used. Providers that cannot perform tags strip them instead.
    """

    text: str
    voice: Literal["Male", "Female"]
    stability: float = Field(0.5, ge=0.0, le=1.0)
    # ElevenLabs ignores speed on eleven_v3; it applies on older models and on edge-tts.
    speed: Optional[float] = Field(None, ge=0.7, le=1.2)


class PodcastScript(BaseModel):
    lines: list[DialogueLine]
