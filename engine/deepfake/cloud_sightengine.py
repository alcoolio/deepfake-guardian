"""SightEngine cloud-based deepfake detector.

Sends face crops to the SightEngine API for deepfake analysis.

.. warning::

    Using this provider means face image data is sent to a third-party service.
    For GDPR-sensitive deployments (especially with minors), prefer the ``local``
    provider which keeps all data on-device.
"""
from __future__ import annotations

import io
import logging

from PIL import Image

from deepfake.base import DeepfakeDetector

logger = logging.getLogger(__name__)

_SIGHTENGINE_URL = "https://api.sightengine.com/1.0/check.json"


class SightEngineDetector(DeepfakeDetector):
    """Deepfake detector using the SightEngine cloud API."""

    name = "sightengine"

    def __init__(self) -> None:
        from config import settings

        self._api_user = getattr(settings, "sightengine_api_user", "")
        self._api_secret = getattr(settings, "sightengine_api_secret", "")

        if self.is_available():
            logger.warning(
                "GDPR notice: SightEngine deepfake provider is active. "
                "Face images will be sent to the SightEngine API."
            )

    def detect(self, face_images: list[Image.Image]) -> list[float]:
        """Send each face crop to SightEngine and return deepfake scores."""
        import httpx

        scores: list[float] = []
        for face in face_images:
            try:
                buf = io.BytesIO()
                face.save(buf, format="JPEG", quality=90)
                buf.seek(0)

                resp = httpx.post(
                    _SIGHTENGINE_URL,
                    data={
                        "models": "deepfake",
                        "api_user": self._api_user,
                        "api_secret": self._api_secret,
                    },
                    files={"media": ("face.jpg", buf, "image/jpeg")},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

                # SightEngine returns {"type_1_score": 0.xx} for deepfake model
                score = float(data.get("deepfake", {}).get("score", 0.0))
                scores.append(score)
            except Exception:
                logger.exception("SightEngine API call failed for face crop")
                scores.append(0.0)

        return scores

    def is_available(self) -> bool:
        """Available only when both API credentials are configured."""
        return bool(self._api_user and self._api_secret)
