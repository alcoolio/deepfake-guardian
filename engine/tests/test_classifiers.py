"""Unit tests for classifier helpers in classifiers.py."""

from __future__ import annotations

import base64
import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from classifiers import classify_image, classify_text, decode_image, detect_deepfake_suspect


def _make_image(width: int = 10, height: int = 10) -> Image.Image:
    return Image.new("RGB", (width, height), color=(128, 64, 32))


class TestDecodeImage:
    def test_decode_from_base64(self):
        img = _make_image()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        result = decode_image(b64, None)
        assert result is not None
        assert result.mode == "RGB"

    def test_decode_returns_none_when_no_input(self):
        result = decode_image(None, None)
        assert result is None

    def test_decode_converts_to_rgb(self):
        # RGBA image should be converted to RGB
        img = Image.new("RGBA", (10, 10), color=(255, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        result = decode_image(b64, None)
        assert result is not None
        assert result.mode == "RGB"


class TestClassifyText:
    def test_returns_zeros_when_classifier_unavailable(self):
        with patch("classifiers._get_text_classifier", return_value=None):
            result = classify_text("hello world")
        assert result == {"violence": 0.0, "sexual_violence": 0.0, "nsfw": 0.0}

    def test_maps_labels_to_scores(self):
        mock_clf = MagicMock(
            return_value={
                "labels": ["violence", "sexual content", "hate speech", "harassment", "safe"],
                "scores": [0.8, 0.6, 0.3, 0.1, 0.05],
            }
        )
        with patch("classifiers._get_text_classifier", return_value=mock_clf):
            result = classify_text("some text")
        assert result["violence"] == pytest.approx(0.8)
        assert result["sexual_violence"] == pytest.approx(0.6)
        # nsfw = max(sexual_content, hate_speech) = max(0.6, 0.3)
        assert result["nsfw"] == pytest.approx(0.6)

    def test_nsfw_uses_max_of_sexual_and_hate(self):
        mock_clf = MagicMock(
            return_value={
                "labels": ["violence", "sexual content", "hate speech", "harassment", "safe"],
                "scores": [0.1, 0.2, 0.9, 0.1, 0.1],
            }
        )
        with patch("classifiers._get_text_classifier", return_value=mock_clf):
            result = classify_text("hateful text")
        # hate speech score (0.9) > sexual content (0.2)
        assert result["nsfw"] == pytest.approx(0.9)


class TestClassifyImage:
    def test_returns_zeros_when_classifier_unavailable(self):
        with patch("classifiers._get_image_classifier", return_value=None):
            result = classify_image(_make_image())
        assert result == {"violence": 0.0, "sexual_violence": 0.0, "nsfw": 0.0}

    def test_extracts_nsfw_score(self):
        mock_clf = MagicMock(
            return_value=[{"label": "nsfw", "score": 0.7}, {"label": "normal", "score": 0.3}]
        )
        with patch("classifiers._get_image_classifier", return_value=mock_clf):
            result = classify_image(_make_image())
        assert result["nsfw"] == pytest.approx(0.7)
        assert result["sexual_violence"] == pytest.approx(0.35)  # nsfw * 0.5
        assert result["violence"] == 0.0  # known stub

    def test_violence_always_zero(self):
        mock_clf = MagicMock(
            return_value=[{"label": "normal", "score": 1.0}]
        )
        with patch("classifiers._get_image_classifier", return_value=mock_clf):
            result = classify_image(_make_image())
        assert result["violence"] == 0.0


class TestDetectDeepfakeSuspect:
    def test_stub_returns_005(self):
        img = _make_image()
        score = detect_deepfake_suspect(img)
        assert score == pytest.approx(0.05)

    def test_accepts_any_pil_image(self):
        for size in [(1, 1), (100, 100), (640, 480)]:
            img = _make_image(*size)
            score = detect_deepfake_suspect(img)
            assert 0.0 <= score <= 1.0
