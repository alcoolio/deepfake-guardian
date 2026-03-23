"""Tests for cloud-based deepfake detectors."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from deepfake.cloud_generic import GenericApiDetector, _extract_nested
from deepfake.cloud_sightengine import SightEngineDetector


class TestSightEngineDetector:
    def test_is_available_without_credentials(self):
        with patch("config.settings") as mock_settings:
            mock_settings.sightengine_api_user = ""
            mock_settings.sightengine_api_secret = ""
            det = SightEngineDetector()
        assert det.is_available() is False

    def test_is_available_with_credentials(self):
        with patch("config.settings") as mock_settings:
            mock_settings.sightengine_api_user = "user123"
            mock_settings.sightengine_api_secret = "secret456"
            det = SightEngineDetector()
        assert det.is_available() is True

    def test_detect_parses_response(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"deepfake": {"score": 0.85}}
        mock_resp.raise_for_status = MagicMock()

        with patch("config.settings") as mock_settings:
            mock_settings.sightengine_api_user = "user"
            mock_settings.sightengine_api_secret = "secret"
            det = SightEngineDetector()

        with patch("httpx.post", return_value=mock_resp):
            face = Image.new("RGB", (50, 50))
            scores = det.detect([face])

        assert len(scores) == 1
        assert scores[0] == pytest.approx(0.85)

    def test_detect_handles_api_error(self):
        with patch("config.settings") as mock_settings:
            mock_settings.sightengine_api_user = "user"
            mock_settings.sightengine_api_secret = "secret"
            det = SightEngineDetector()

        with patch("httpx.post", side_effect=Exception("timeout")):
            face = Image.new("RGB", (50, 50))
            scores = det.detect([face])

        assert scores == [0.0]


class TestExtractNested:
    def test_simple_path(self):
        assert _extract_nested({"score": 0.9}, "score") == 0.9

    def test_nested_path(self):
        assert _extract_nested({"result": {"score": 0.7}}, "result.score") == 0.7

    def test_missing_key(self):
        assert _extract_nested({"other": 1}, "score") == 0.0

    def test_missing_nested_key(self):
        assert _extract_nested({"result": {}}, "result.score") == 0.0


class TestGenericApiDetector:
    def test_is_available_without_url(self):
        with patch("config.settings") as mock_settings:
            mock_settings.deepfake_api_url = ""
            mock_settings.deepfake_api_key = ""
            mock_settings.deepfake_api_score_path = "score"
            det = GenericApiDetector()
        assert det.is_available() is False

    def test_is_available_with_url(self):
        with patch("config.settings") as mock_settings:
            mock_settings.deepfake_api_url = "http://localhost:9000/detect"
            mock_settings.deepfake_api_key = ""
            mock_settings.deepfake_api_score_path = "score"
            det = GenericApiDetector()
        assert det.is_available() is True

    def test_detect_sends_base64_and_parses_score(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"score": 0.72}
        mock_resp.raise_for_status = MagicMock()

        with patch("config.settings") as mock_settings:
            mock_settings.deepfake_api_url = "http://localhost:9000/detect"
            mock_settings.deepfake_api_key = "mykey"
            mock_settings.deepfake_api_score_path = "score"
            det = GenericApiDetector()

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            face = Image.new("RGB", (50, 50))
            scores = det.detect([face])

        assert len(scores) == 1
        assert scores[0] == pytest.approx(0.72)
        # Verify auth header was sent
        call_kwargs = mock_post.call_args
        assert "Bearer mykey" in str(call_kwargs)
