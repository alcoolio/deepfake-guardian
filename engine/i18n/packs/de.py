"""German language pack.

Uses ``ml6team/distilbert-base-german-cased-toxic-comments`` for multi-label
toxic-comment classification.  The model outputs scores for the labels
``toxic``, ``severe_toxic``, ``obscene``, ``threat``, ``insult``,
``identity_hate``, and ``neutral``; these are mapped to our internal
categories via :meth:`get_labels`.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from i18n.base import HarmPattern, Helpline, LanguagePack

logger = logging.getLogger(__name__)

_de_classifier: Any = None


class GermanPack(LanguagePack):
    lang_code = "de"
    lang_name = "Deutsch"

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------

    def detect(self, text: str) -> float:
        """Return probability that *text* is German via langdetect."""
        try:
            from langdetect import detect_langs  # type: ignore[import]

            for lang in detect_langs(text):
                if lang.lang == "de":
                    return float(lang.prob)
        except Exception:
            pass
        return 0.0

    # ------------------------------------------------------------------
    # ML classifier
    # ------------------------------------------------------------------

    def get_classifier(self) -> Any:
        """Return a cached German toxic-comment classification pipeline."""
        global _de_classifier
        if _de_classifier is None:
            try:
                from transformers import pipeline

                _de_classifier = pipeline(
                    "text-classification",
                    model="ml6team/distilbert-base-german-cased-toxic-comments",
                    device=-1,  # CPU
                    top_k=None,  # return all label scores
                )
                logger.info(
                    "German classifier loaded: "
                    "ml6team/distilbert-base-german-cased-toxic-comments"
                )
            except Exception:
                logger.warning("Could not load German classifier – using stub scores")
        return _de_classifier

    # ------------------------------------------------------------------
    # Label mapping
    # ------------------------------------------------------------------

    def get_labels(self) -> dict[str, str]:
        """Map German model output labels to internal category names."""
        return {
            "threat": "violence",
            "obscene": "nsfw",
            "insult": "cyberbullying",
            "identity_hate": "cyberbullying",
            "toxic": "cyberbullying",
            "severe_toxic": "cyberbullying",
            "neutral": "safe",
        }

    # ------------------------------------------------------------------
    # Harm patterns
    # ------------------------------------------------------------------

    def get_patterns(self) -> list[HarmPattern]:
        """Return German-language cyberbullying and harm patterns."""
        return [
            # Direct threats / Todesdrohungen
            HarmPattern(
                pattern=re.compile(
                    r"\b(du solltest (sterben|tot sein|verschwinden)"
                    r"|ich bringe dich um"
                    r"|du bist es nicht wert zu leben"
                    r"|niemand mag dich"
                    r"|alle hassen dich"
                    r"|keiner will dich"
                    r"|hör auf zu leben)\b",
                    re.IGNORECASE,
                ),
                category="cyberbullying",
                weight=0.9,
            ),
            # Ausgrenzung (exclusion)
            HarmPattern(
                pattern=re.compile(
                    r"\b(keiner mag dich|niemand mag dich|du gehörst nicht dazu"
                    r"|du bist nicht willkommen|wir wollen dich nicht"
                    r"|du bist ausgeschlossen)\b",
                    re.IGNORECASE,
                ),
                category="cyberbullying",
                weight=0.8,
            ),
            # Gezielte Beleidigungen (targeted insults)
            HarmPattern(
                pattern=re.compile(
                    r"\b(du bist so (hässlich|dumm|fett|bescheuert|blöd|eklig"
                    r"|widerlich|unnötig|nutzlos))\b",
                    re.IGNORECASE,
                ),
                category="cyberbullying",
                weight=0.7,
            ),
            # Erpressung (extortion)
            HarmPattern(
                pattern=re.compile(
                    r"\b(ich zeig das allen|ich schick das an|ich poste das"
                    r"|wenn du nicht|sonst zeige ich|ich mach dich fertig)\b",
                    re.IGNORECASE,
                ),
                category="cyberbullying",
                weight=0.75,
            ),
            # Doxxing indicators (German address/phone patterns)
            HarmPattern(
                pattern=re.compile(
                    r"\b(deine adresse ist|ich weiß wo du wohnst"
                    r"|ich kenne deine nummer)\b",
                    re.IGNORECASE,
                ),
                category="cyberbullying",
                weight=0.85,
            ),
        ]

    # ------------------------------------------------------------------
    # Educational messages
    # ------------------------------------------------------------------

    def get_educational_messages(self) -> dict[str, str]:
        return {
            "cyberbullying": (
                "Diese Nachricht könnte Cybermobbing enthalten. "
                "Bitte geh respektvoll miteinander um."
            ),
            "violence": "Diese Nachricht enthält gewalttätige Inhalte.",
            "nsfw": "Diese Nachricht enthält unangemessene Inhalte.",
            "sexual_violence": "Diese Nachricht enthält sexuelle oder gewalttätige Inhalte.",
        }

    # ------------------------------------------------------------------
    # Helplines
    # ------------------------------------------------------------------

    def get_helplines(self) -> list[Helpline]:
        return [
            Helpline(
                name="Nummer gegen Kummer",
                phone="116 111",
                url="https://www.nummergegenkummer.de",
                description="Kostenlose Beratung für Kinder und Jugendliche, Mo–Sa 14–20 Uhr.",
            ),
            Helpline(
                name="Telefonseelsorge",
                phone="0800 111 0 111",
                url="https://www.telefonseelsorge.de",
                description="Kostenlos, 24/7, anonym.",
            ),
            Helpline(
                name="Jugendnotmail",
                url="https://www.jugendnotmail.de",
                description="Online-Beratung per E-Mail für Jugendliche in Krisen.",
            ),
            Helpline(
                name="Klicksafe",
                url="https://www.klicksafe.de",
                description="EU-Initiative für mehr Sicherheit im Internet.",
            ),
        ]
