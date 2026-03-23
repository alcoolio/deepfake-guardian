"""Abstract base class for deepfake detection providers."""
from __future__ import annotations

from abc import ABC, abstractmethod

from PIL import Image


class DeepfakeDetector(ABC):
    """Abstract base for deepfake detection providers.

    Each provider receives pre-cropped face images and returns a score
    per face indicating the likelihood of being a deepfake (0.0–1.0).
    """

    name: str

    @abstractmethod
    def detect(self, face_images: list[Image.Image]) -> list[float]:
        """Score each face crop for deepfake likelihood.

        Args:
            face_images: List of cropped face PIL images (RGB).

        Returns:
            List of floats 0.0–1.0, one per face.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this detector is properly configured and ready."""
        ...
