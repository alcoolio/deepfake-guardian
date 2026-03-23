"""HTTP client for the moderation engine API.

Includes exponential-backoff retry on transient network errors and 5xx responses
so the bot degrades gracefully when the engine is temporarily unavailable.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx
import structlog

from config import settings

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Retry configuration
# ---------------------------------------------------------------------------
# Maximum number of additional attempts after the first failure.
_MAX_RETRIES = 3
# Backoff factor in seconds (1 → waits 1s, 2s, 4s).
_BACKOFF_FACTOR = 1.0

# HTTP status codes that warrant an automatic retry.
_RETRY_STATUS_CODES = {500, 502, 503, 504}

# ---------------------------------------------------------------------------
# HTTP client (lazy singleton)
# ---------------------------------------------------------------------------
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        headers = {}
        if settings.engine_api_key:
            headers["X-API-Key"] = settings.engine_api_key
        _client = httpx.AsyncClient(
            base_url=settings.engine_url,
            timeout=60,
            headers=headers,
        )
    return _client


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------

async def _post_with_retry(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST *payload* to *path*, retrying on transient failures."""
    import asyncio

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            resp = await _get_client().post(path, json=payload)
            if resp.status_code in _RETRY_STATUS_CODES:
                raise httpx.HTTPStatusError(
                    f"Server error {resp.status_code}",
                    request=resp.request,
                    response=resp,
                )
            resp.raise_for_status()
            return resp.json()
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                wait = _BACKOFF_FACTOR * (2 ** attempt)
                logger.warning(
                    "engine_request_retry",
                    path=path,
                    attempt=attempt + 1,
                    wait_seconds=wait,
                    error=str(exc),
                )
                await asyncio.sleep(wait)

    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Public API — moderation
# ---------------------------------------------------------------------------

async def moderate_text(
    text: str,
    user_id: str | None = None,
    group_id: str | None = None,
) -> dict[str, Any]:
    """Send text to the engine for moderation."""
    payload: dict[str, Any] = {"text": text, "platform": "telegram"}
    if user_id:
        payload["user_id"] = user_id
    if group_id:
        payload["group_id"] = group_id
    return await _post_with_retry("/moderate_text", payload)


async def moderate_image(
    image_bytes: bytes,
    user_id: str | None = None,
    group_id: str | None = None,
) -> dict[str, Any]:
    """Send a base64-encoded image to the engine for moderation."""
    b64 = base64.b64encode(image_bytes).decode()
    payload: dict[str, Any] = {"image_base64": b64, "platform": "telegram"}
    if user_id:
        payload["user_id"] = user_id
    if group_id:
        payload["group_id"] = group_id
    return await _post_with_retry("/moderate_image", payload)


async def moderate_video(
    video_bytes: bytes,
    user_id: str | None = None,
    group_id: str | None = None,
) -> dict[str, Any]:
    """Send a base64-encoded video to the engine for moderation."""
    b64 = base64.b64encode(video_bytes).decode()
    payload: dict[str, Any] = {"video_base64": b64, "platform": "telegram"}
    if user_id:
        payload["user_id"] = user_id
    if group_id:
        payload["group_id"] = group_id
    return await _post_with_retry("/moderate_video", payload)


# ---------------------------------------------------------------------------
# Public API — GDPR
# ---------------------------------------------------------------------------

async def gdpr_delete_request(user_id: str) -> dict[str, Any]:
    """Submit an Article 17 erasure request for a Telegram user."""
    return await _post_with_retry(
        "/gdpr/delete_request",
        {"user_id": user_id, "platform": "telegram", "notes": "requested via /delete_my_data"},
    )


async def gdpr_export(user_id: str) -> dict[str, Any]:
    """Fetch all stored data for a Telegram user (Article 15)."""
    return await _post_with_retry(
        "/gdpr/export",
        {"user_id": user_id, "platform": "telegram"},
    )


# ---------------------------------------------------------------------------
# Public API — warnings
# ---------------------------------------------------------------------------

async def record_warning(
    user_id: str,
    group_id: str,
    reasons: list[str],
) -> dict[str, Any]:
    """Record a violation for a user in a group; returns the escalation action."""
    return await _post_with_retry(
        "/warnings/record",
        {
            "user_id": user_id,
            "group_id": group_id,
            "platform": "telegram",
            "reasons": reasons,
        },
    )
