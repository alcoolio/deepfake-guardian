"""HTTP client for the moderation engine API."""

from __future__ import annotations

import base64
from typing import Any

import httpx
import structlog

from config import settings

logger = structlog.get_logger()

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=settings.engine_url, timeout=60)
    return _client


async def moderate_text(text: str) -> dict[str, Any]:
    """Send text to the engine for moderation."""
    resp = await _get_client().post("/moderate_text", json={"text": text})
    resp.raise_for_status()
    return resp.json()


async def moderate_image(image_bytes: bytes) -> dict[str, Any]:
    """Send a base64-encoded image to the engine for moderation."""
    b64 = base64.b64encode(image_bytes).decode()
    resp = await _get_client().post("/moderate_image", json={"image_base64": b64})
    resp.raise_for_status()
    return resp.json()


async def moderate_video(video_bytes: bytes) -> dict[str, Any]:
    """Send a base64-encoded video to the engine for moderation."""
    b64 = base64.b64encode(video_bytes).decode()
    resp = await _get_client().post("/moderate_video", json={"video_base64": b64})
    resp.raise_for_status()
    return resp.json()
