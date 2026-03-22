"""Telegram bot configuration."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    engine_url: str = os.getenv("ENGINE_URL", "http://localhost:8000")
    log_level: str = os.getenv("LOG_LEVEL", "info")


settings = Settings()
