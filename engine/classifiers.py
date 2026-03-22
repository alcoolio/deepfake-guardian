"""Lightweight classifier wrappers.

Each public function accepts raw content and returns a dict of category scores.
The implementations use Hugging Face pipelines where available, falling back to
deterministic stubs so the service always starts — even without a GPU.
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded pipelines (downloaded on first call)
# ---------------------------------------------------------------------------

_text_classifier: Any = None
_image_classifier: Any = None


def _get_text_classifier() -> Any:
    """Return a zero-shot text classification pipeline (cached)."""
    global _text_classifier
    if _text_classifier is None:
        try:
            from transformers import pipeline

            _text_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1,  # CPU
            )
            logger.info("Text classifier loaded: facebook/bart-large-mnli")
        except Exception:
            logger.warning("Could not load text classifier – using stub scores")
    return _text_classifier


def _get_image_classifier() -> Any:
    """Return an image classification pipeline for NSFW/violence (cached)."""
    global _image_classifier
    if _image_classifier is None:
        try:
            from transformers import pipeline

            # Falconsai/nsfw_image_detection is a small, widely-used model
            _image_classifier = pipeline(
                "image-classification",
                model="Falconsai/nsfw_image_detection",
                device=-1,
            )
            logger.info("Image classifier loaded: Falconsai/nsfw_image_detection")
        except Exception:
            logger.warning("Could not load image classifier – using stub scores")
    return _image_classifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def decode_image(image_base64: str | None, image_url: str | None) -> Image.Image | None:
    """Decode a PIL Image from base64 data or fetch from URL."""
    if image_base64:
        data = base64.b64decode(image_base64)
        return Image.open(io.BytesIO(data)).convert("RGB")
    if image_url:
        import httpx

        resp = httpx.get(image_url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    return None


# ---------------------------------------------------------------------------
# Public classifiers
# ---------------------------------------------------------------------------

_TEXT_LABELS = ["hate speech", "sexual content", "violence", "harassment", "safe"]


def classify_text(text: str) -> dict[str, float]:
    """Classify text and return normalised scores.

    Returns dict with keys: violence, sexual_violence, nsfw.
    """
    clf = _get_text_classifier()
    if clf is None:
        return {"violence": 0.0, "sexual_violence": 0.0, "nsfw": 0.0}

    result = clf(text, candidate_labels=_TEXT_LABELS, multi_label=True)
    label_scores: dict[str, float] = dict(zip(result["labels"], result["scores"]))

    return {
        "violence": float(label_scores.get("violence", 0.0)),
        "sexual_violence": float(label_scores.get("sexual content", 0.0)),
        "nsfw": float(
            max(
                label_scores.get("sexual content", 0.0),
                label_scores.get("hate speech", 0.0),
            )
        ),
    }


def classify_image(image: Image.Image) -> dict[str, float]:
    """Classify an image and return normalised scores.

    Returns dict with keys: violence, sexual_violence, nsfw.
    """
    clf = _get_image_classifier()
    if clf is None:
        return {"violence": 0.0, "sexual_violence": 0.0, "nsfw": 0.0}

    results = clf(image)
    label_scores: dict[str, float] = {r["label"].lower(): r["score"] for r in results}
    nsfw_score = float(label_scores.get("nsfw", 0.0))

    return {
        "violence": 0.0,  # This model doesn't detect violence — extend later
        "sexual_violence": nsfw_score * 0.5,  # Rough heuristic
        "nsfw": nsfw_score,
    }


def detect_deepfake_suspect(image: Image.Image) -> float:
    """Detect whether an image may be a deepfake.

    TODO: Replace this stub with a real deepfake detection model, e.g.:
      - Microsoft FaceXRay
      - Sensity deepfake detector
      - A fine-tuned EfficientNet on FaceForensics++
      - Any ONNX / TorchScript model that outputs a probability score

    Current implementation: returns a fixed low score (0.05) so the pipeline
    is wired end-to-end and ready for a real model drop-in.

    Args:
        image: A PIL RGB image.

    Returns:
        A float between 0.0 and 1.0 indicating deepfake likelihood.
    """
    # TODO: Integrate a real deepfake detection model here.
    # The function signature and return type should stay the same.
    _ = np.array(image)  # Placeholder — proves the image is valid
    logger.info("detect_deepfake_suspect called (stub) — returning 0.05")
    return 0.05
