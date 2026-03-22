"""English language pack.

Uses ``facebook/bart-large-mnli`` for zero-shot text classification — the same
model that was previously hard-coded in ``classifiers.py``.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from i18n.base import HarmPattern, Helpline, LanguagePack

logger = logging.getLogger(__name__)

_en_classifier: Any = None


class EnglishPack(LanguagePack):
    lang_code = "en"
    lang_name = "English"

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------

    def detect(self, text: str) -> float:
        """Return probability that *text* is English via langdetect."""
        try:
            from langdetect import detect_langs  # type: ignore[import]

            for lang in detect_langs(text):
                if lang.lang == "en":
                    return float(lang.prob)
        except Exception:
            pass
        return 0.0

    # ------------------------------------------------------------------
    # ML classifier
    # ------------------------------------------------------------------

    def get_classifier(self) -> Any:
        """Return a cached zero-shot classification pipeline (BART MNLI)."""
        global _en_classifier
        if _en_classifier is None:
            try:
                from transformers import pipeline

                _en_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1,  # CPU
                )
                logger.info("English classifier loaded: facebook/bart-large-mnli")
            except Exception:
                logger.warning("Could not load English classifier – using stub scores")
        return _en_classifier

    # ------------------------------------------------------------------
    # Label mapping
    # ------------------------------------------------------------------

    def get_labels(self) -> dict[str, str]:
        """Map BART MNLI output labels to internal category names."""
        return {
            "hate speech": "nsfw",
            "sexual content": "nsfw",
            "violence": "violence",
            "harassment": "cyberbullying",
            "cyberbullying": "cyberbullying",
            "safe": "safe",
        }

    # ------------------------------------------------------------------
    # Harm patterns
    # ------------------------------------------------------------------

    def get_patterns(self) -> list[HarmPattern]:
        """Return English-language cyberbullying and harm patterns."""
        return [
            # Direct threats / suicidal ideation
            HarmPattern(
                pattern=re.compile(
                    r"\b(nobody likes you|you should die|kill yourself|go kill yourself"
                    r"|you're worthless|you are worthless|you don't deserve to live"
                    r"|kys)\b",
                    re.IGNORECASE,
                ),
                category="cyberbullying",
                weight=0.9,
            ),
            # Targeted insults
            HarmPattern(
                pattern=re.compile(
                    r"\b(loser|freak|ugly|fat|stupid|idiot|moron|dumb|retard"
                    r"|pathetic|disgusting)\b.{0,40}\b(you|ur|u|your)\b",
                    re.IGNORECASE,
                ),
                category="cyberbullying",
                weight=0.65,
            ),
            # Exclusion language
            HarmPattern(
                pattern=re.compile(
                    r"\b(no one|nobody|everyone hates|everyone thinks|all of us)\b"
                    r".{0,30}\b(you|ur|u)\b",
                    re.IGNORECASE,
                ),
                category="cyberbullying",
                weight=0.7,
            ),
            # Extortion / coercion
            HarmPattern(
                pattern=re.compile(
                    r"\b(i('ll| will) (send|show|share|post|leak)|if you don't"
                    r"|unless you)\b.{0,50}\b(everyone|all|expose|ruin)\b",
                    re.IGNORECASE,
                ),
                category="cyberbullying",
                weight=0.75,
            ),
        ]

    # ------------------------------------------------------------------
    # Educational messages
    # ------------------------------------------------------------------

    def get_educational_messages(self) -> dict[str, str]:
        return {
            "cyberbullying": (
                "This message may contain cyberbullying. "
                "Be kind and respectful to others online."
            ),
            "violence": "This message contains violent content.",
            "nsfw": "This message contains inappropriate content.",
            "sexual_violence": "This message contains sexual or violent content.",
        }

    # ------------------------------------------------------------------
    # Helplines
    # ------------------------------------------------------------------

    def get_helplines(self) -> list[Helpline]:
        return [
            Helpline(
                name="Crisis Text Line",
                phone="Text HOME to 741741",
                url="https://www.crisistextline.org",
                description="Free, 24/7 crisis support via text.",
            ),
            Helpline(
                name="Cyberbullying Research Center",
                url="https://cyberbullying.org",
                description="Resources and research on cyberbullying prevention.",
            ),
            Helpline(
                name="StopBullying.gov",
                url="https://www.stopbullying.gov",
                description="US government resource on bullying and cyberbullying.",
            ),
        ]
