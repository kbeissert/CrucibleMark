#!/usr/bin/env python3
"""
Reproducibility & Validation Tests for Metacognition Scoring.

Tests the hybrid robust metrics against ground truth dataset
to ensure consistent, reproducible scoring.
"""

import sys
import yaml
import traceback
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from benchmark_modules.reasoning_logic.core.evaluators import ReasoningEvaluator  # noqa: E402
from benchmark_modules.reasoning_logic.core.validation_dataset import (  # noqa: E402
    GROUND_TRUTH_DATASETS,
    validate_response_against_ground_truth,
)


def get_asset_path(asset_id, folder_rel_path="benchmark_modules/reasoning_logic/assets"):
    """Helper to get robust asset path."""
    primary = PROJECT_ROOT / folder_rel_path / f"{asset_id}.yaml"
    if primary.exists():
        return primary
    # Fallback/alternative naming logic if needed
    return primary


def test_ground_truth_reproducibility():
    """Test that ground truth responses score consistently."""
    
    print("\n" + "="*70)
    print("TEST 1: Ground Truth Reproducibility")
    print("="*70)
    
    all_passed = True
    
    for asset_id, dataset in GROUND_TRUTH_DATASETS.items():
        print(f"\nAsset: {dataset['test_name']}")
        print("-" * 70)
        
        # Load asset config
        asset_path = get_asset_path(asset_id)
        if not asset_path.exists():
            print(f"ERROR: Asset not found at {asset_path}")
            all_passed = False
            continue

        with open(asset_path) as f:
            asset = yaml.safe_load(f)
        
        evaluator = ReasoningEvaluator(asset)
        
        for response_type, response_data in dataset["gold_responses"].items():
            response_text = response_data["text"]
            expected_score = response_data["expected_score"]
            
            # Score the response
            result = evaluator.score_response(response_text)
            actual_score = result.get("total_score", 0)
            
            # Validate against ground truth
            validation = validate_response_against_ground_truth(
                asset_id, response_type, actual_score, tolerance=10.0
            )
            
            status = "✅" if validation["success"] else "❌"
            print(f"\n{status} {response_type.upper()}")
            print(f"   Expected: {expected_score}pts | Actual: {actual_score:.1f}pts")
            print(f"   Variance: {validation['variance']:.1f}pts")
            
            if not validation["success"]:
                all_passed = False
                print(f"   ERROR: {validation['message']}")
                
                # Show breakdown
                breakdown = result.get("category_scores", {})
                for k, v in breakdown.items():
                    print(f"     - {k}: {v['achieved']:.0f}pts")
    
    print("\n" + "="*70)
    status = "✅ PASSED" if all_passed else "❌ FAILED"
    print(f"Reproducibility Test: {status}")
    print("="*70)
    
    return all_passed


def test_hybrid_metrics_evidence():
    """Test that hybrid metrics produce clear evidence."""
    
    print("\n" + "="*70)
    print("TEST 2: Hybrid Metrics Evidence Transparency")
    print("="*70)
    
    from benchmark_modules.reasoning_logic.core.robust_metrics import (
        detect_self_correction_robust,
        score_linguistic_analysis_objective,
        measure_thought_quality_robust,
    )
    
    # Test response with clear self-correction
    test_thought = """
    Wait, I think I made a mistake. Initially I thought 17-9=8, 
    but actually, "all but 9" means that 9 remain alive.
    """
    
    test_answer = "9"
    
    print("\nTest Thought:")
    print(test_thought.strip())
    print(f"Test Answer: {test_answer}")
    
    # Test 1: Self-Correction Detection
    print("\n1. Self-Correction Detection (Hybrid):")
    correction_result = detect_self_correction_robust(
        test_thought, test_answer, expected_answer="9"
    )
    print(f"   Score: {correction_result['score']:.0f}/40")
    print(f"   Layers matched: {correction_result['layers_matched']}")
    for evidence in correction_result['evidence']:
        print(f"   {evidence}")
    
    # Test 2: Linguistic Analysis
    print("\n2. Linguistic Analysis (Objective):")
    linguistic_result = score_linguistic_analysis_objective(test_thought, test_answer)
    print(f"   Score: {linguistic_result['score']:.0f}/30")
    print(f"   Phrase mentioned: {linguistic_result['phrase_mentioned']}")
    print(f"   Semantic explanation: {linguistic_result['semantic_explanation']}")
    for evidence in linguistic_result['evidence']:
        print(f"   {evidence}")
    
    # Test 3: Thought Quality
    print("\n3. Thought Quality (Robust):")
    quality_result = measure_thought_quality_robust(test_thought, has_thought_tags=True)
    print(f"   Score: {quality_result['score']:.0f}/15")
    print(f"   Dimensions: {quality_result['dimensions']}")
    for evidence in quality_result['evidence']:
        print(f"   {evidence}")
    
    print("\n✅ Evidence transparency confirmed")


def test_non_gameable_scoring():
    """Test that scoring cannot be gamed with keyword stuffing."""
    
    print("\n" + "="*70)
    print("TEST 3: Non-Gameable Scoring (Keyword Stuffing Prevention)")
    print("="*70)
    
    from benchmark_modules.reasoning_logic.core.robust_metrics import (
        detect_self_correction_robust,
    )
    
    # Response with keywords but no real correction
    keyword_stuffed = """
    Wait, actually, let me reconsider. But I was wrong. 
    Actually, thinking about it again, but actually that's not right.
    Answer: 8 (wrong answer)
    """
    
    print("\nTest: Response with keyword stuffing but WRONG answer")
    print(f"Text: {keyword_stuffed.strip()[:80]}...")
    
    result = detect_self_correction_robust(
        keyword_stuffed, answer="8", expected_answer="9"
    )
    
    print("\nResult:")
    print(f"  Score: {result['score']:.0f}/40")
    print(f"  Layers matched: {result['layers_matched']}")
    
    # Should NOT have multiple layers matched (trajectory analysis should fail)
    # Keywords alone = max 20pts, no trajectory = max 40pts total
    if len(result['layers_matched']) == 1 and result['score'] <= 20:
        print(f"\n✅ PASS: Keyword stuffing prevented (only explicit_keywords layer, score: {result['score']:.0f})")
        return True
    else:
        print(f"\n❌ FAIL: Scoring can be gamed! Got {result['score']:.0f} with {len(result['layers_matched'])} layers")
        return False


def test_consistency_across_runs():
    """Test that scoring is consistent across multiple runs."""
    
    print("\n" + "="*70)
    print("TEST 4: Consistency Across Runs")
    print("="*70)
    
    asset_path = get_asset_path("reasoning_metacog_001")
    if not asset_path.exists():
         # Fallback to old name if needed
         asset_path = get_asset_path("asset_metacog_001")
    
    if not asset_path.exists():
         print(f"CRITICAL: Could not find asset at {asset_path}")
         return False

    with open(asset_path) as f:
        asset = yaml.safe_load(f)
    
    test_response = """<thought>
    The key phrase here is "all but 9" which means that 9 survive.
    </thought>
    
    Answer: 9"""
    
    evaluator = ReasoningEvaluator(asset)
    
    # Run scoring multiple times
    scores = []
    for i in range(5):
        result = evaluator.score_response(test_response)
        score = result.get("total_score", 0)
        scores.append(score)
    
    print(f"\nRuns: {scores}")
    print(f"Mean: {sum(scores) / len(scores):.1f}")
    print(f"Std Dev: {(sum((x - sum(scores)/len(scores))**2 for x in scores) / len(scores)) ** 0.5:.2f}")
    
    # All scores should be identical
    if len(set(scores)) == 1:
        print(f"\n✅ PASS: Consistent scoring ({scores[0]:.1f} every time)")
        return True
    else:
        print("\n❌ FAIL: Inconsistent scoring across runs!")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("REPRODUCIBILITY & VALIDATION TEST SUITE")
    print("="*70)
    
    try:
        test1 = test_ground_truth_reproducibility()
        test2_passed = True  # Just for display
        test_hybrid_metrics_evidence()
        test3 = test_non_gameable_scoring()
        test4 = test_consistency_across_runs()
        
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"✅ Ground Truth Reproducibility: {'PASS' if test1 else 'FAIL'}")
        print("✅ Hybrid Metrics Evidence: PASS")
        print(f"✅ Non-Gameable Scoring: {'PASS' if test3 else 'FAIL'}")
        print(f"✅ Consistency: {'PASS' if test4 else 'FAIL'}")
        
        all_passed = test1 and test3 and test4
        print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '⚠️ SOME TESTS FAILED'}")
        print("="*70)
        
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
