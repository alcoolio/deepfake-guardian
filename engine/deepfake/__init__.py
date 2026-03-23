"""Deepfake detection provider package.

Usage::

    from deepfake import get_detector

    detector = get_detector()
    scores = detector.detect(face_images)
"""
from __future__ import annotations

from deepfake.factory import get_detector

__all__ = ["get_detector"]
