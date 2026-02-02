import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from benchmark_modules.cultural_intelligence.core.evaluators import CulturalIntelligenceEvaluator

def test_legacy_asset_dispatch():
    """Test that legacy assets (v1.0) are correctly dispatched to LegacyEvaluator."""
    # Note: LegacyEvaluator logic relies on specific IDs (e.g. cultural_intel_004)
    # to choose a scoring method. Arbitrary IDs return 0 score.
    legacy_asset = {
        "id": "cultural_intel_004",  # Using a known ID (Formal/Informal)
        "scoring": {
            "total_points": 100,
            "criteria": [
                {"name": "German Usage", "points": 30, "keywords": ["deutsch"]}
            ]
        }
    }
    
    evaluator = CulturalIntelligenceEvaluator(legacy_asset)
    # "Das ist ein Test." contains no "Sie/Ihnen" -> hits strict check (+2) -> score > 0
    response = "Das ist ein Test auf Deutsch."
    
    result = evaluator.score_response(response)
    
    # Should NOT be 0 (bug would cause this)
    assert result["total_score"] > 0, f"Legacy asset returned 0 score. Result: {result}"
    
    # Legacy output does not contain "status" key in v1 logic, it just returns scores.
    # So we remove checking for 'status' == 'success'
    # assert result["status"] == "success"
    
    print(f"✓ Legacy asset score: {result['total_score']}/100")

def test_v2_asset_dispatch():
    """Test that v2 assets are correctly dispatched to new evaluators."""
    v2_asset = {
        "id": "test_v2",
        "scoring": {
            "total_points": 100,
            "language_proficiency": {
                "weight": 40,
                "criteria": [
                    # Check for words in GERMAN_WORD_MARKERS (der, die, das, etc.)
                    {"name": "German Words", "points": 20, "check_method": "german_word_count", "min_count": 1}
                ]
            },
            "cultural_fit": {
                "weight": 30,
                "criteria": []
            },
            "solution_quality": {
                "weight": 30,
                "criteria": []
            }
        }
    }
    
    evaluator = CulturalIntelligenceEvaluator(v2_asset)
    # Include markers from constants.py (der, die, das, aber, und...)
    response = "Das ist der Test für die neue Logik in aber einer anderen Form."
    
    result = evaluator.score_response(response)
    
    assert result["total_score"] > 0, f"v2 asset returned 0 score. Result: {result}"
    assert "formality" in result["metadata"]  # v2-specific metadata
    print(f"✓ v2 asset score: {result['total_score']}/100")

if __name__ == "__main__":
    test_legacy_asset_dispatch()
    test_v2_asset_dispatch()
    print("\n✅ Legacy compatibility tests passed!")
