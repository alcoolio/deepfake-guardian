"""Telegram bot configuration."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    engine_url: str = os.getenv("ENGINE_URL", "http://localhost:8000")
    engine_api_key: str = os.getenv("ENGINE_API_KEY", "")
    log_level: str = os.getenv("LOG_LEVEL", "info")
    # Language for admin notification messages ("en" or "de")
    bot_language: str = os.getenv("BOT_LANGUAGE", "en")


settings = Settings()
