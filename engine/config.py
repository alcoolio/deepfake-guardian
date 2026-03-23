"""Engine configuration loaded from environment variables.

Moderation thresholds are initialised from the active
:data:`~profiles.PROFILES` entry so that ``MODERATION_PROFILE=minors_strict``
changes all thresholds at once.  Individual env vars (``THRESHOLD_VIOLENCE``
etc.) can still override a single threshold within a profile.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central settings — all values come from env vars with sane defaults."""

    def __init__(self) -> None:
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.log_level: str = os.getenv("LOG_LEVEL", "info")

        # API authentication — leave empty to disable (dev/local only)
        self.api_key: str = os.getenv("API_KEY", "")

        # Rate limiting (requests per minute per IP on moderation endpoints)
        self.rate_limit: str = os.getenv("RATE_LIMIT", "60/minute")

        # i18n — comma-separated list of enabled language codes
        self.enabled_languages: list[str] = [
            lang.strip()
            for lang in os.getenv("ENABLED_LANGUAGES", "en,de").split(",")
            if lang.strip()
        ]

        # Moderation profile — sets default thresholds; individual env vars override
        self.moderation_profile: str = os.getenv("MODERATION_PROFILE", "default")

        from profiles import get_profile

        profile = get_profile(self.moderation_profile)

        self.threshold_violence: float = float(
            os.getenv("THRESHOLD_VIOLENCE", str(profile.violence))
        )
        self.threshold_sexual_violence: float = float(
            os.getenv("THRESHOLD_SEXUAL_VIOLENCE", str(profile.sexual_violence))
        )
        self.threshold_nsfw: float = float(
            os.getenv("THRESHOLD_NSFW", str(profile.nsfw))
        )
        self.threshold_deepfake: float = float(
            os.getenv("THRESHOLD_DEEPFAKE", str(profile.deepfake))
        )
        self.threshold_cyberbullying: float = float(
            os.getenv("THRESHOLD_CYBERBULLYING", str(profile.cyberbullying))
        )

        # GDPR / persistence
        self.database_url: str = os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./deepfake_guardian.db"
        )
        # Secret salt for SHA-256 ID hashing — change in production
        self.gdpr_salt: str = os.getenv("GDPR_SALT", "change-me-in-production")
        # How many days moderation events are kept before automatic deletion
        self.data_retention_days: int = int(os.getenv("DATA_RETENTION_DAYS", "30"))


settings = Settings()
