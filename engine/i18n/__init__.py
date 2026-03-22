"""i18n framework for language-aware content moderation.

Usage:
    from i18n.registry import LanguageRegistry
    from i18n.detector import detect_language

    lang_code = detect_language(text)
    pack = LanguageRegistry.get(lang_code)
"""

from __future__ import annotations
