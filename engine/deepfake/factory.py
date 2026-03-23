"""Factory for creating the configured deepfake detector (cached singleton)."""
from __future__ import annotations

import logging

from PIL import Image

from deepfake.base import DeepfakeDetector

logger = logging.getLogger(__name__)

_detector: DeepfakeDetector | None = None


class StubDetector(DeepfakeDetector):
    """Returns a fixed low score — for CI/testing or when no real provider is available."""

    name = "stub"

    def detect(self, face_images: list[Image.Image]) -> list[float]:
        return [0.05] * len(face_images)

    def is_available(self) -> bool:
        return True


def get_detector() -> DeepfakeDetector:
    """Return the configured deepfake detector (cached singleton).

    Reads ``DEEPFAKE_PROVIDER`` from :mod:`config` settings. Falls back to
    :class:`StubDetector` with a warning if the chosen provider is unavailable.
    """
    global _detector
    if _detector is not None:
        return _detector

    from config import settings

    provider = getattr(settings, "deepfake_provider", "stub")

    if provider == "local":
        from deepfake.local_detector import LocalOnnxDetector

        det = LocalOnnxDetector()
    elif provider == "sightengine":
        from deepfake.cloud_sightengine import SightEngineDetector

        det = SightEngineDetector()
    elif provider == "api":
        from deepfake.cloud_generic import GenericApiDetector

        det = GenericApiDetector()
    elif provider == "stub":
        det = StubDetector()
    else:
        logger.warning("Unknown DEEPFAKE_PROVIDER '%s' — falling back to stub", provider)
        det = StubDetector()

    if not det.is_available():
        logger.warning(
            "Deepfake provider '%s' is not available — falling back to stub. "
            "Check configuration and dependencies.",
            det.name,
        )
        det = StubDetector()

    _detector = det
    logger.info("Deepfake detector initialised: %s", det.name)
    return _detector


def reset_detector() -> None:
    """Reset the cached detector (useful for testing)."""
    global _detector
    _detector = None
