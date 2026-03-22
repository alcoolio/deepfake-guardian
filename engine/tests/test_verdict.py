"""Unit tests for verdict.py — the threshold-based decision engine."""

from __future__ import annotations

import pytest

from models import ModerationScores
from verdict import decide


class TestDecideAllow:
    def test_all_zeros(self):
        scores = ModerationScores(violence=0.0, sexual_violence=0.0, nsfw=0.0, deepfake_suspect=0.0)
        result = decide(scores)
        assert result.verdict == "allow"
        assert result.reasons == []

    def test_all_below_flag_threshold(self):
        scores = ModerationScores(violence=0.1, sexual_violence=0.2, nsfw=0.3, deepfake_suspect=0.1)
        result = decide(scores)
        assert result.verdict == "allow"
        assert result.reasons == []


class TestDecideFlag:
    def test_violence_elevated(self):
        # 0.4 is exactly the flag threshold — should flag but not delete (delete is 0.7)
        scores = ModerationScores(violence=0.4, sexual_violence=0.0, nsfw=0.0, deepfake_suspect=0.0)
        result = decide(scores)
        assert result.verdict == "flag"
        assert "elevated_violence" in result.reasons

    def test_nsfw_elevated(self):
        scores = ModerationScores(violence=0.0, sexual_violence=0.0, nsfw=0.5, deepfake_suspect=0.0)
        result = decide(scores)
        assert result.verdict == "flag"
        assert "elevated_nsfw" in result.reasons

    def test_multiple_elevated(self):
        scores = ModerationScores(violence=0.5, sexual_violence=0.4, nsfw=0.0, deepfake_suspect=0.0)
        result = decide(scores)
        assert result.verdict == "flag"
        assert "elevated_violence" in result.reasons
        assert "elevated_sexual_violence" in result.reasons

    def test_just_below_delete_threshold(self):
        # Default violence threshold is 0.7 — 0.69 should flag, not delete
        scores = ModerationScores(violence=0.69, sexual_violence=0.0, nsfw=0.0, deepfake_suspect=0.0)
        result = decide(scores)
        assert result.verdict == "flag"


class TestDecideDelete:
    def test_violence_at_threshold(self):
        scores = ModerationScores(violence=0.7, sexual_violence=0.0, nsfw=0.0, deepfake_suspect=0.0)
        result = decide(scores)
        assert result.verdict == "delete"
        assert "violence" in result.reasons

    def test_sexual_violence_at_threshold(self):
        # Default threshold is 0.5
        scores = ModerationScores(violence=0.0, sexual_violence=0.5, nsfw=0.0, deepfake_suspect=0.0)
        result = decide(scores)
        assert result.verdict == "delete"
        assert "sexual_violence" in result.reasons

    def test_nsfw_at_threshold(self):
        # Default threshold is 0.6
        scores = ModerationScores(violence=0.0, sexual_violence=0.0, nsfw=0.6, deepfake_suspect=0.0)
        result = decide(scores)
        assert result.verdict == "delete"
        assert "nsfw" in result.reasons

    def test_deepfake_at_threshold(self):
        # Default threshold is 0.8
        scores = ModerationScores(violence=0.0, sexual_violence=0.0, nsfw=0.0, deepfake_suspect=0.8)
        result = decide(scores)
        assert result.verdict == "delete"
        assert "deepfake_suspect" in result.reasons

    def test_multiple_reasons(self):
        scores = ModerationScores(violence=0.9, sexual_violence=0.8, nsfw=0.0, deepfake_suspect=0.0)
        result = decide(scores)
        assert result.verdict == "delete"
        assert "violence" in result.reasons
        assert "sexual_violence" in result.reasons

    def test_scores_preserved_in_result(self):
        scores = ModerationScores(violence=0.75, sexual_violence=0.0, nsfw=0.0, deepfake_suspect=0.0)
        result = decide(scores)
        assert result.scores.violence == pytest.approx(0.75)
        assert result.verdict == "delete"
