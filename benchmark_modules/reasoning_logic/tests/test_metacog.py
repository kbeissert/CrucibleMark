#!/usr/bin/env python3
"""
Functional tests for reasoning_logic metacognition tier.
"""

from benchmark_modules.reasoning_logic.core.evaluators import (
    ReasoningEvaluator,
    calculate_rci,
    classify_model,
)


def test_parse_thought_tags() -> None:
    """Test thought tag parsing."""
    test_asset = {
        "metadata": {"id": "reasoning_metacog_001", "scoring_version": 2.0},
        "expected_output": {"correct_answer": "9"},
    }
    evaluator = ReasoningEvaluator(test_asset)

    test_response = "<thought>\nWait, let me reconsider. First, I thought 17-9=8.\nBut actually, all but 9 die means 9 survive.\n</thought>\n\nAnswer: 9"

    parsed = evaluator.parse_thought_tags(test_response)
    assert parsed["has_thought_tags"] is True
    assert parsed["thought_length"] > 10
    assert "9" in parsed["answer_content"]
    print("✅ Parse Test passed")


def test_self_correction_detection() -> None:
    """Test self-correction keyword detection."""
    from benchmark_modules.reasoning_logic.core.structure_analysis import (
        detect_self_correction,
    )

    thought_with_correction = "Wait, actually I realized my mistake. Let me reconsider."
    has_correction = detect_self_correction(thought_with_correction)
    assert has_correction is True
    print("✅ Self-Correction Detection test passed")


def test_rci_calculation() -> None:
    """Test RCI calculation."""
    tier1_2_scores = [70.0, 80.0, 75.0, 85.0]
    tier3_scores = [80.0, 85.0, 75.0, 90.0, 88.0]

    rci = calculate_rci(tier1_2_scores, tier3_scores)
    assert 0 <= rci <= 100
    assert 75 < rci < 85  # Expected range for these scores
    print(f"✅ RCI Calculation test passed (RCI: {rci:.1f})")


def test_classification() -> None:
    """Test model classification."""
    test_cases = [
        (40, "Non-Thinking Model"),
        (60, "Basic Thinking Model"),
        (75, "Thinking Model"),
        (88, "Deep Thinking Model"),
    ]

    for rci, expected_class in test_cases:
        classification = classify_model(rci)
        assert classification == expected_class, (
            f"Expected {expected_class}, got {classification}"
        )
    print("✅ Classification test passed")


def test_metacog_001_scoring() -> None:
    """Test METACOG_001 scoring function."""
    from benchmark_modules.reasoning_logic.core.scorers.tier3.metacog_001_sheep import (
        score_metacog_001,
    )

    test_response = "<thought>\nWait, I initially thought 17-9=8, but actually all but 9 die means 9 survive.\n</thought>\n\nAnswer: 9"

    total_score, breakdown, details = score_metacog_001(test_response)
    assert total_score > 0
    assert "self_correction" in breakdown
    assert "output_correctness" in breakdown
    print(f"✅ METACOG_001 Scoring test passed (Score: {total_score:.1f})")


if __name__ == "__main__":
    test_parse_thought_tags()
    test_self_correction_detection()
    test_rci_calculation()
    test_classification()
    test_metacog_001_scoring()
    print("\n🎉 All functional tests passed!")


def test_kanal_bias_fix_tier3_bekommt_denktext() -> None:
    """R1-Fall: Reasoning im separaten Kanal darf in Tier 3 nicht wie Nicht-Denker wirken.

    Vor dem Fix sah der Regel-Scorer nur den kurzen sichtbaren Text → alle
    Denkblock-Dimensionen (Self-Correction 40, Linguistic Analysis 30) = 0.
    """
    from utils.benchmark_utils import with_reasoning_channel

    think = ("Zuerst dachte ich, 17 minus 9 sind 8. Aber warte, ich lag falsch: "
             "'all but 9 die' heißt, alle außer 9 sterben — also bleiben 9 übrig. "
             "Ich prüfe nochmal: die 8 toten Schafe sind nicht die Antwort.")
    answer = "Answer: Es sind 9 Schafe übrig."
    asset = {
        "metadata": {"id": "reasoning_metacog_001", "scoring_version": 2.0},
        "expected_output": {"correct_answer": "9"},
    }
    plain = ReasoningEvaluator(asset).score_response(answer)["total_score"]
    channeled = ReasoningEvaluator(asset).score_response(
        with_reasoning_channel(answer, think)
    )["total_score"]
    assert channeled > plain, "separierter Reasoning-Kanal muss in Tier 3 zählen"
    print(f"✅ Kanal-Bias-Fix: plain={plain} → mit Kanal={channeled}")


def test_kanal_bias_fix_tier1_2_bleibt_unveraendert() -> None:
    """Tier 1/2 strippen Denkblöcke bewusst — der Fix darf dort keine Keywords liefern."""
    from utils.benchmark_utils import with_reasoning_channel

    think = "Der Cache wird reduziert und die Performance verbessert sich, faster lookups."
    answer = "Der Fehler liegt in der Indentation innerhalb des if-Blocks."
    for asset_id in ("reasoning_5b_001", "reasoning_5c_001"):
        asset = {
            "metadata": {"id": asset_id, "scoring_version": 2.0},
            "expected_output": {},
        }
        plain = ReasoningEvaluator(asset).score_response(answer)["total_score"]
        channeled = ReasoningEvaluator(asset).score_response(
            with_reasoning_channel(answer, think)
        )["total_score"]
        assert plain == channeled, f"{asset_id}: Tier-1/2-Durchgang muss identisch bleiben"
    print("✅ Tier 1/2 unverändert (Strip-Verhalten bleibt dominant)")
