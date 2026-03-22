"""Verdict logic — turns raw scores into allow / delete / flag decisions."""

from __future__ import annotations

from typing import Literal

from config import settings
from models import ModerationResult, ModerationScores

# Fields checked for the "flag" (elevated but below delete threshold) condition
_FLAG_FIELDS = ("violence", "sexual_violence", "nsfw", "deepfake_suspect", "cyberbullying")

# Score at or above which a field is considered "elevated" (→ flag)
_FLAG_THRESHOLD = 0.4


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
    if scores.cyberbullying >= settings.threshold_cyberbullying:
        reasons.append("cyberbullying")

    verdict: Literal["allow", "delete", "flag"]
    if reasons:
        verdict = "delete"
    elif any(getattr(scores, field) >= _FLAG_THRESHOLD for field in _FLAG_FIELDS):
        # Scores are elevated but below delete thresholds → flag for review
        verdict = "flag"
        reasons = [
            f"elevated_{f}" for f in _FLAG_FIELDS if getattr(scores, f) >= _FLAG_THRESHOLD
        ]
    else:
        verdict = "allow"

    return ModerationResult(verdict=verdict, reasons=reasons, scores=scores, language=None)
