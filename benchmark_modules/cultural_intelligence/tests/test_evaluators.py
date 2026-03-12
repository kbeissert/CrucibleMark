import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from benchmark_modules.cultural_intelligence.core.evaluators import (
    LanguageProficiencyEvaluator,
    CulturalFitEvaluator,
    RegionalConsistencyValidator,
    FormalityScorer,
)


def test_language_proficiency():
    response = "Das ist nicht für uns, sondern für sie noch wichtig."
    criteria = [
        {
            "name": "German Words",
            "points": 10,
            "check_method": "german_word_count",
            "min_count": 3,
        }
    ]
    result = LanguageProficiencyEvaluator.score_proficiency(response, criteria)
    assert result["score"] == 10
    # Note: formality might be "informal" or "neutral" depending on markers found,
    # but "sie" is in FORMAL_MARKERS['pronouns'], so it should detect formality if logic holds.
    # Let's check what logic expects.
    # FORMAL_MARKERS["pronouns"] = ["sie", "ihnen"...]
    # "sie" is in response (lowercase).
    # So it should be formal.
    assert result["metadata"]["formality_level"] == "formal"
    print("✓ LanguageProficiencyEvaluator test passed")


def test_cultural_fit():
    response = "Bitte schön! Vielen Dank für Ihre Hilfe. Das ist sehr freundlich."
    criteria = [
        {
            "name": "Politeness",
            "points": 10,
            "check_method": "politeness_count",
            "min_count": 2,
        }
    ]
    result = CulturalFitEvaluator.score_cultural_fit(response, criteria)
    assert result["score"] == 10
    assert result["metadata"]["politeness_marker_count"] >= 2
    print("✓ CulturalFitEvaluator test passed")


def test_regional_consistency():
    # Consistent (only DE terms)
    response = "Das Brötchen schmeckt lecker. Moin!"
    result = RegionalConsistencyValidator.validate_consistency(response)
    assert result["is_consistent"] is True
    assert result["dominant_region"] == "de"

    # Inconsistent (DE + AT)
    response_mix = "Das Brötchen und die Semmel schmecken gut."
    result_mix = RegionalConsistencyValidator.validate_consistency(response_mix)
    assert result_mix["is_consistent"] is False
    assert len(result_mix["violations"]) > 0
    print("✓ RegionalConsistencyValidator test passed")


def test_formality_scorer():
    # Very formal
    response_formal = "Sehr geehrte Damen und Herren, wir möchten Ihnen mitteilen."
    result_formal = FormalityScorer.calculate_formality(response_formal)
    assert result_formal["formality_level"] in ["formal", "very_formal"]
    assert result_formal["formality_score"] > 0.6

    # Informal
    response_informal = "Hallo, wie geht es dir? Willst du kommen?"
    result_informal = FormalityScorer.calculate_formality(response_informal)
    assert result_informal["formality_level"] in ["informal", "very_informal"]
    assert result_informal["formality_score"] < 0.4
    print("✓ FormalityScorer test passed")


if __name__ == "__main__":
    test_language_proficiency()
    test_cultural_fit()
    test_regional_consistency()
    test_formality_scorer()
    print("\nAll evaluator tests passed!")
