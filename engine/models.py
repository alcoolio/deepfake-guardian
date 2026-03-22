"""Pydantic models for API request / response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Plain text to moderate")
    language: str | None = Field(
        None, description="Optional language hint (ISO 639-1, e.g. 'en', 'de')"
    )


class ImageRequest(BaseModel):
    image_base64: str | None = Field(None, description="Base64-encoded image data")
    image_url: str | None = Field(None, description="Public URL of the image")


class VideoRequest(BaseModel):
    video_base64: str | None = Field(None, description="Base64-encoded video data")
    video_url: str | None = Field(None, description="Public URL of the video")


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class ModerationScores(BaseModel):
    violence: float = Field(0.0, ge=0.0, le=1.0)
    sexual_violence: float = Field(0.0, ge=0.0, le=1.0)
    nsfw: float = Field(0.0, ge=0.0, le=1.0)
    deepfake_suspect: float = Field(0.0, ge=0.0, le=1.0)
    cyberbullying: float = Field(0.0, ge=0.0, le=1.0)


class ModerationResult(BaseModel):
    verdict: Literal["allow", "delete", "flag"]
    reasons: list[str] = Field(default_factory=list)
    scores: ModerationScores = Field(default_factory=ModerationScores)  # type: ignore[arg-type]
    language: str | None = Field(None, description="Detected language code (ISO 639-1)")
