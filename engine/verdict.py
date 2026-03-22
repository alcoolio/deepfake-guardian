"""Verdict logic — turns raw scores into allow / delete / flag decisions."""

from __future__ import annotations

from typing import Literal

from config import settings
from models import ModerationResult, ModerationScores


def decide(scores: ModerationScores) -> ModerationResult:
    """Apply threshold rules and return the final moderation result."""
    reasons: list[str] = []

    if scores.violence >= settings.threshold_violence:
        reasons.append("violence")
    if scores.sexual_violence >= settings.threshold_sexual_violence:
        reasons.append("sexual_violence")
    if scores.nsfw >= settings.threshold_nsfw:
        reasons.append("nsfw")
    if scores.deepfake_suspect >= settings.threshold_deepfake:
        reasons.append("deepfake_suspect")

    verdict: Literal["allow", "delete", "flag"]
    if reasons:
        verdict = "delete"
    elif any(
        getattr(scores, field) >= 0.4
        for field in ("violence", "sexual_violence", "nsfw", "deepfake_suspect")
    ):
        # Scores are elevated but below delete thresholds → flag for review
        verdict = "flag"
        reasons = [f"elevated_{f}" for f in ("violence", "sexual_violence", "nsfw", "deepfake_suspect")
                    if getattr(scores, f) >= 0.4]
    else:
        verdict = "allow"

    return ModerationResult(verdict=verdict, reasons=reasons, scores=scores)
