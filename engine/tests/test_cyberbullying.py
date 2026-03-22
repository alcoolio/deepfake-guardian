"""Tests for the cyberbullying pattern-based scorer."""

from __future__ import annotations

import pytest

from cyberbullying import score_cyberbullying
from i18n.registry import LanguageRegistry


@pytest.fixture(autouse=True)
def reset_registry():
    LanguageRegistry.reset()
    yield
    LanguageRegistry.reset()


class TestScoreCyberbullying:
    def test_benign_text_returns_zero(self):
        result = score_cyberbullying("Hello! How are you doing today?", None)
        assert result == pytest.approx(0.0)

    def test_none_pack_returns_zero_for_benign_text(self):
        result = score_cyberbullying("Good morning, have a nice day!", None)
        assert result == pytest.approx(0.0)

    def test_english_direct_threat_triggers(self):
        LanguageRegistry.discover()
        pack = LanguageRegistry.get("en")
        result = score_cyberbullying("nobody likes you, you should die", pack)
        assert result >= 0.6

    def test_english_exclusion_triggers(self):
        LanguageRegistry.discover()
        pack = LanguageRegistry.get("en")
        result = score_cyberbullying("nobody likes you at all", pack)
        assert result > 0.0

    def test_english_kys_triggers(self):
        LanguageRegistry.discover()
        pack = LanguageRegistry.get("en")
        result = score_cyberbullying("kys loser", pack)
        assert result >= 0.6

    def test_german_threat_triggers(self):
        LanguageRegistry.discover()
        pack = LanguageRegistry.get("de")
        result = score_cyberbullying("keiner mag dich, du solltest sterben", pack)
        assert result >= 0.6

    def test_german_exclusion_triggers(self):
        LanguageRegistry.discover()
        pack = LanguageRegistry.get("de")
        result = score_cyberbullying("du gehörst nicht dazu", pack)
        assert result > 0.0

    def test_german_extortion_triggers(self):
        LanguageRegistry.discover()
        pack = LanguageRegistry.get("de")
        result = score_cyberbullying("ich zeig das allen wenn du nicht", pack)
        assert result > 0.0

    def test_structural_multiple_mentions(self):
        """Three or more @mentions in one message = potential pile-on."""
        result = score_cyberbullying("@alice @bob @charlie you're all losers", None)
        assert result > 0.0

    def test_score_is_bounded(self):
        LanguageRegistry.discover()
        pack = LanguageRegistry.get("en")
        result = score_cyberbullying("kill yourself nobody likes you loser freak", pack)
        assert 0.0 <= result <= 1.0

    def test_exception_in_pack_patterns_handled_gracefully(self):
        """A broken pack must not crash the cyberbullying scorer."""
        from unittest.mock import MagicMock

        broken_pack = MagicMock()
        broken_pack.get_patterns.side_effect = RuntimeError("simulated failure")
        result = score_cyberbullying("some text", broken_pack)
        assert result == pytest.approx(0.0)
