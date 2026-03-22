"""Language detection router.

Iterates enabled language packs and returns the code of the pack with the
highest confidence score.  Falls back to ``"en"`` when detection fails or
returns no strong signal.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """Detect the language of *text* using enabled language packs.

    Returns the ``lang_code`` of the best-matching pack, or ``"en"`` as a
    safe fallback.
    """
    # Import here to avoid circular imports at module level
    from config import settings
    from i18n.registry import LanguageRegistry

    enabled = LanguageRegistry.get_enabled(settings.enabled_languages)
    if not enabled:
        return "en"

    best_code = "en"
    best_score = 0.0

    for pack in enabled:
        try:
            score = pack.detect(text)
            if score > best_score:
                best_score = score
                best_code = pack.lang_code
        except Exception:
            logger.warning("Language detection failed for pack '%s'", pack.lang_code)

    return best_code
