"""
Tests für utils/benchmark_utils.py — Reasoning-Kanal-Rekonstruktion (Kanal-Bias-Fix).

Deckt ab:
    - with_reasoning_channel()  (Materialisierung, Noops, Doppelblock-Schutz)
    - has_reasoning_channel()   (Tag-Familien aus der Strip-SSoT)
    - Judge-Stufe nutzt dieselbe Rekonstruktion (kein Doppelter-Block)
"""

from __future__ import annotations

from utils.benchmark_utils import (
    REASONING_CHANNEL_TAG,
    has_reasoning_channel,
    with_reasoning_channel,
)

THINK = "Zuerst dachte ich 17-9=8. Aber warte, ich lag falsch: all but 9 heißt 9 bleiben."
ANSWER = "Answer: Es sind 9 Schafe übrig."


class TestWithReasoningChannel:
    def test_lagert_separiertes_reasoning_in_die_response(self):
        out = with_reasoning_channel(ANSWER, THINK)
        assert out.startswith(f"<{REASONING_CHANNEL_TAG}>")
        assert THINK in out and out.endswith(ANSWER)

    def test_ohne_reasoning_kanal_unchanged(self):
        assert with_reasoning_channel(ANSWER, None) == ANSWER
        assert with_reasoning_channel(ANSWER, "   ") == ANSWER

    def test_doppelblock_wird_verhindet(self):
        """CoT steht bereits inline im Content-Feld (Qwen3.8-Fall) → kein Voranstellen."""
        inline = f"<thought>\n{THINK}\n</thought>\n\n{ANSWER}"
        assert with_reasoning_channel(inline, THINK) == inline

    def test_alle_tag_familien_erkannt(self):
        for tag in ("think", "thought", "reasoning"):
            assert has_reasoning_channel(f"<{tag}>x</{tag}>") is True
        assert has_reasoning_channel(ANSWER) is False


class TestJudgeUsesSameReconstruction:
    def test_judge_kwargs_nutzen_die_ssot(self):
        """Judge-Stufe und Regel-Stufe müssen identischen Text sehen (kein Drift)."""
        from utils.scoring import judge_evaluator as je

        assert je.with_reasoning_channel is with_reasoning_channel
