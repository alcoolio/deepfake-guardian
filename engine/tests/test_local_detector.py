"""Tests for the local ONNX deepfake detector."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from deepfake.local_detector import INPUT_SIZE, LocalOnnxDetector, _preprocess, _sigmoid


class TestPreprocess:
    def test_output_shape(self):
        face = Image.new("RGB", (50, 50), color=(128, 128, 128))
        tensor = _preprocess(face)
        assert tensor.shape == (1, 3, INPUT_SIZE, INPUT_SIZE)
        assert tensor.dtype == np.float32

    def test_values_normalised(self):
        face = Image.new("RGB", (10, 10), color=(0, 0, 0))
        tensor = _preprocess(face)
        # Black image: (0/255 - mean) / std — all values should be negative
        assert tensor.max() < 0


class TestSigmoid:
    def test_zero(self):
        assert _sigmoid(0.0) == pytest.approx(0.5)

    def test_large_positive(self):
        assert _sigmoid(10.0) > 0.999

    def test_large_negative(self):
        assert _sigmoid(-10.0) < 0.001


class TestLocalOnnxDetector:
    def test_is_available_false_when_no_model(self):
        with patch("deepfake.local_detector.os.path.isfile", return_value=False):
            det = LocalOnnxDetector()
            assert det.is_available() is False

    def test_is_available_true_when_model_exists(self):
        with patch("deepfake.local_detector.os.path.isfile", return_value=True):
            det = LocalOnnxDetector()
            assert det.is_available() is True

    def test_detect_with_mocked_session(self):
        """When ONNX session works, returns sigmoid of model output."""
        mock_session = MagicMock()
        mock_session.get_inputs.return_value = [MagicMock(name="input")]
        mock_session.get_inputs.return_value[0].name = "input"
        # Model returns logit of 2.0 → sigmoid ≈ 0.88
        mock_session.run.return_value = [np.array([[2.0]])]

        det = LocalOnnxDetector()
        det._session = mock_session

        face = Image.new("RGB", (50, 50))
        scores = det.detect([face])

        assert len(scores) == 1
        assert scores[0] == pytest.approx(_sigmoid(2.0), abs=1e-4)

    def test_detect_fallback_when_session_unavailable(self):
        """When ONNX session fails to load, returns stub scores."""
        det = LocalOnnxDetector()
        det._session = None

        with patch.object(det, "_get_session", return_value=None):
            face = Image.new("RGB", (50, 50))
            scores = det.detect([face])

        assert scores == [0.05]
