"""Tests for face extraction using MediaPipe."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from deepfake.face_extractor import extract_faces


def _make_image(w: int = 100, h: int = 100) -> Image.Image:
    return Image.new("RGB", (w, h), color=(128, 128, 128))


class TestExtractFaces:
    def test_returns_empty_when_detector_unavailable(self):
        with patch("deepfake.face_extractor._get_face_detector", return_value=None):
            result = extract_faces(_make_image())
        assert result == []

    def test_returns_empty_when_no_detections(self):
        mock_det = MagicMock()
        mock_results = MagicMock()
        mock_results.detections = None
        mock_det.process.return_value = mock_results

        with patch("deepfake.face_extractor._get_face_detector", return_value=mock_det):
            result = extract_faces(_make_image())
        assert result == []

    def test_returns_face_crops(self):
        """When mediapipe finds a face, returns a cropped PIL image."""
        mock_det = MagicMock()

        # Simulate a detection with relative bounding box
        mock_bbox = MagicMock()
        mock_bbox.xmin = 0.2
        mock_bbox.ymin = 0.2
        mock_bbox.width = 0.5
        mock_bbox.height = 0.5

        mock_detection = MagicMock()
        mock_detection.location_data.relative_bounding_box = mock_bbox

        mock_results = MagicMock()
        mock_results.detections = [mock_detection]
        mock_det.process.return_value = mock_results

        with patch("deepfake.face_extractor._get_face_detector", return_value=mock_det):
            result = extract_faces(_make_image(200, 200))

        assert len(result) == 1
        assert isinstance(result[0], Image.Image)

    def test_skips_tiny_faces(self):
        """Faces smaller than MIN_FACE_RATIO are skipped."""
        mock_det = MagicMock()

        # Very small face (1% of image)
        mock_bbox = MagicMock()
        mock_bbox.xmin = 0.5
        mock_bbox.ymin = 0.5
        mock_bbox.width = 0.01
        mock_bbox.height = 0.01

        mock_detection = MagicMock()
        mock_detection.location_data.relative_bounding_box = mock_bbox

        mock_results = MagicMock()
        mock_results.detections = [mock_detection]
        mock_det.process.return_value = mock_results

        with patch("deepfake.face_extractor._get_face_detector", return_value=mock_det):
            result = extract_faces(_make_image(100, 100))

        assert len(result) == 0
