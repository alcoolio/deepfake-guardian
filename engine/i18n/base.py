"""Abstract base class for language packs.

Every language pack lives in ``engine/i18n/packs/<lang_code>.py`` and
subclasses :class:`LanguagePack`.  The registry auto-discovers all subclasses,
so adding a new language requires only that one new file.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class HarmPattern:
    """A compiled regex pattern associated with a harm category."""

    pattern: re.Pattern  # type: ignore[type-arg]
    category: str  # "cyberbullying", "violence", "nsfw", …
    weight: float = 1.0  # score contribution when pattern matches (0.0–1.0)


@dataclass
class Helpline:
    """A local support or counselling resource."""

    name: str
    phone: str | None = None
    url: str | None = None
    description: str = ""


class LanguagePack(ABC):
    """Abstract base for a language-specific moderation pack.

    Subclasses must set the class attributes :attr:`lang_code` and
    :attr:`lang_name`, then implement all abstract methods.
    """

    lang_code: str  # ISO 639-1 code, e.g. "en", "de"
    lang_name: str  # Human-readable name, e.g. "English", "Deutsch"

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------

    @abstractmethod
    def detect(self, text: str) -> float:
        """Return confidence (0.0–1.0) that *text* is written in this language."""
        ...

    # ------------------------------------------------------------------
    # ML classification
    # ------------------------------------------------------------------

    @abstractmethod
    def get_classifier(self) -> Any:
        """Return a lazy-loaded Hugging Face pipeline for this language.

        May return ``None`` if the model could not be loaded — callers must
        handle that case gracefully.
        """
        ...

    @abstractmethod
    def get_labels(self) -> dict[str, str]:
        """Map model output labels to internal category names.

        Internal categories: ``"violence"``, ``"sexual_violence"``,
        ``"nsfw"``, ``"cyberbullying"``, ``"safe"``.

        Example::

            {"hate speech": "nsfw", "harassment": "cyberbullying", "safe": "safe"}
        """
        ...

    # ------------------------------------------------------------------
    # Pattern-based detection
    # ------------------------------------------------------------------

    @abstractmethod
    def get_patterns(self) -> list[HarmPattern]:
        """Return language-specific harm patterns (compiled regexes)."""
        ...

    # ------------------------------------------------------------------
    # Educational content & resources
    # ------------------------------------------------------------------

    @abstractmethod
    def get_educational_messages(self) -> dict[str, str]:
        """Return educational feedback texts keyed by internal category name."""
        ...

    @abstractmethod
    def get_helplines(self) -> list[Helpline]:
        """Return local support and counselling resources for this language."""
        ...
