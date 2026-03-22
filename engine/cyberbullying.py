"""Cross-language cyberbullying detection.

Combines language-specific patterns from the active :class:`~i18n.base.LanguagePack`
with a set of language-agnostic structural patterns.

The resulting score is merged with the ML cyberbullying label score in
:func:`~classifiers.classify_text` using a max() operation: whichever signal
is stronger wins.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from i18n.base import LanguagePack

# ---------------------------------------------------------------------------
# Cross-language structural patterns (language-agnostic)
# ---------------------------------------------------------------------------

_STRUCTURAL_PATTERNS: list[tuple[re.Pattern, float]] = [  # type: ignore[type-arg]
    # Three or more @mentions in a single message → pile-on / coordinated harassment
    (re.compile(r"(@\w+\s*){3,}", re.IGNORECASE), 0.5),
    # All-caps shouting directed at someone (at least 5 uppercase words)
    (re.compile(r"(\b[A-Z]{3,}\b\s*){5,}"), 0.4),
    # Repetition of the same insult-word 3+ times in a row
    (re.compile(r"\b(\w{3,})\b(?:\W+\1\b){2,}", re.IGNORECASE), 0.45),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_cyberbullying(text: str, lang_pack: "LanguagePack | None") -> float:
    """Calculate a cyberbullying score from pattern matching alone.

    This function is **not** a standalone classifier — it is called inside
    :func:`~classifiers.classify_text` to *boost* the ML model's cyberbullying
    label score when explicit patterns are detected.

    Args:
        text: The raw message text to inspect.
        lang_pack: The active language pack (may be ``None`` for graceful fallback).

    Returns:
        A float in ``[0.0, 1.0]``.  Returns ``0.0`` if no pattern matches.
    """
    best_score = 0.0

    # 1. Language-specific patterns
    if lang_pack is not None:
        try:
            for harm in lang_pack.get_patterns():
                if harm.category == "cyberbullying" and harm.pattern.search(text):
                    best_score = max(best_score, harm.weight)
        except Exception:
            pass  # never let pattern matching crash the pipeline

    # 2. Cross-language structural patterns
    for pattern, weight in _STRUCTURAL_PATTERNS:
        if pattern.search(text):
            best_score = max(best_score, weight)

    return best_score
