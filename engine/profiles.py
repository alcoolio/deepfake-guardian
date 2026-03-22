"""Moderation threshold profiles.

Profiles let operators choose a pre-configured strictness level instead of
tuning individual thresholds.  Individual env-var overrides still take
precedence (handled in :class:`~config.Settings`).

Available profiles:

* ``minors_strict`` — lowest thresholds; suitable for groups with minors
  where zero-tolerance is appropriate.
* ``default`` — balanced thresholds matching the original v0.1.0 values.
* ``permissive`` — higher thresholds; fewer interventions for adult
  communities where some rough language is acceptable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThresholdProfile:
    """Immutable set of delete-thresholds for all moderation categories."""

    violence: float
    sexual_violence: float
    nsfw: float
    deepfake: float
    cyberbullying: float


PROFILES: dict[str, ThresholdProfile] = {
    "minors_strict": ThresholdProfile(
        violence=0.5,
        sexual_violence=0.3,
        nsfw=0.4,
        deepfake=0.6,
        cyberbullying=0.4,
    ),
    "default": ThresholdProfile(
        violence=0.7,
        sexual_violence=0.5,
        nsfw=0.6,
        deepfake=0.8,
        cyberbullying=0.6,
    ),
    "permissive": ThresholdProfile(
        violence=0.85,
        sexual_violence=0.7,
        nsfw=0.75,
        deepfake=0.9,
        cyberbullying=0.8,
    ),
}


def get_profile(name: str) -> ThresholdProfile:
    """Return the named profile, falling back to ``"default"`` if not found."""
    return PROFILES.get(name, PROFILES["default"])
