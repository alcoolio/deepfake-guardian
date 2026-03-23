"""Shared face extraction using MediaPipe FaceDetection.

Extracts face crops from images for downstream deepfake detection.
"""
from __future__ import annotations

import logging
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)

_face_detector: Any = None

# Minimum face size relative to image dimensions (skip tiny/background faces)
MIN_FACE_RATIO = 0.03
# Padding around face bounding box (fraction of bbox size)
FACE_PADDING = 0.2


def _get_face_detector() -> Any:
    """Return a cached MediaPipe FaceDetection instance."""
    global _face_detector
    if _face_detector is None:
        try:
            import mediapipe as mp

            _face_detector = mp.solutions.face_detection.FaceDetection(
                model_selection=0,  # 0 = short-range (<2m), 1 = full-range
                min_detection_confidence=0.5,
            )
            logger.info("MediaPipe FaceDetection loaded")
        except Exception:
            logger.warning("Could not load MediaPipe FaceDetection")
    return _face_detector


def extract_faces(image: Image.Image) -> list[Image.Image]:
    """Detect faces in an image and return cropped face images.

    Args:
        image: A PIL RGB image.

    Returns:
        List of cropped face PIL images. Empty list if no faces found or
        if MediaPipe is unavailable.
    """
    import numpy as np

    detector = _get_face_detector()
    if detector is None:
        return []

    img_array = np.array(image)
    h, w = img_array.shape[:2]
    min_face_pixels = min(h, w) * MIN_FACE_RATIO

    results = detector.process(img_array)
    if not results.detections:
        return []

    faces: list[Image.Image] = []
    for detection in results.detections:
        bbox = detection.location_data.relative_bounding_box

        # Convert relative coordinates to absolute pixels
        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        bw = int(bbox.width * w)
        bh = int(bbox.height * h)

        # Skip tiny faces
        if bw < min_face_pixels or bh < min_face_pixels:
            continue

        # Add padding
        pad_x = int(bw * FACE_PADDING)
        pad_y = int(bh * FACE_PADDING)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(w, x + bw + pad_x)
        y2 = min(h, y + bh + pad_y)

        face_crop = image.crop((x1, y1, x2, y2))
        faces.append(face_crop)

    logger.debug("Extracted %d face(s) from image (%dx%d)", len(faces), w, h)
    return faces
