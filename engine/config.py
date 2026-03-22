"""Engine configuration loaded from environment variables."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central settings — all values come from env vars with sane defaults."""

    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "info")

    # Moderation thresholds
    threshold_violence: float = float(os.getenv("THRESHOLD_VIOLENCE", "0.7"))
    threshold_sexual_violence: float = float(os.getenv("THRESHOLD_SEXUAL_VIOLENCE", "0.5"))
    threshold_nsfw: float = float(os.getenv("THRESHOLD_NSFW", "0.6"))
    threshold_deepfake: float = float(os.getenv("THRESHOLD_DEEPFAKE", "0.8"))


settings = Settings()
