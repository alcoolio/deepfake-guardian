"""Shared pytest fixtures for the engine test suite."""

from __future__ import annotations

import base64
import io
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Ensure no API_KEY is set during tests by default so auth is disabled
os.environ.setdefault("API_KEY", "")


@pytest.fixture()
def client():
    """Return a TestClient with ML classifiers mocked out (fast, no GPU needed)."""
    with (
        patch("classifiers._get_text_classifier") as mock_text_clf,
        patch("classifiers._get_image_classifier") as mock_img_clf,
    ):
        # Text classifier returns safe scores
        mock_text_clf.return_value = MagicMock(
            return_value={
                "labels": ["violence", "sexual content", "hate speech", "harassment", "safe"],
                "scores": [0.01, 0.01, 0.01, 0.01, 0.96],
            }
        )
        # Image classifier returns safe NSFW score
        mock_img_clf.return_value = MagicMock(
            return_value=[{"label": "normal", "score": 0.98}, {"label": "nsfw", "score": 0.02}]
        )

        from main import app

        yield TestClient(app)


@pytest.fixture()
def client_with_key(monkeypatch):
    """Return a TestClient with API_KEY authentication enabled."""
    monkeypatch.setenv("API_KEY", "test-secret-key")

    with (
        patch("classifiers._get_text_classifier") as mock_text_clf,
        patch("classifiers._get_image_classifier") as mock_img_clf,
    ):
        mock_text_clf.return_value = MagicMock(
            return_value={
                "labels": ["violence", "sexual content", "hate speech", "harassment", "safe"],
                "scores": [0.01, 0.01, 0.01, 0.01, 0.96],
            }
        )
        mock_img_clf.return_value = MagicMock(
            return_value=[{"label": "normal", "score": 0.98}, {"label": "nsfw", "score": 0.02}]
        )

        # Reload settings so the new env var is picked up

        import config as config_module

        config_module.settings.api_key = "test-secret-key"

        from main import app

        yield TestClient(app)

        # Restore
        config_module.settings.api_key = ""


@pytest.fixture()
def small_image_b64() -> str:
    """Return a tiny 10×10 red PNG as a base64 string."""
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
