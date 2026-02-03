#!/usr/bin/env python3
"""
Integration Tests for Content Transformation v2.0
Tests Phase 2 evaluators (FormatValidator, ToneEvaluator)
"""
import sys
from pathlib import Path

# Add project root to path
# This file is in benchmark_modules/content_transformation/tests/
# We need to go up 3 levels to reach project root (cruciblemark/)
root_dir = Path(__file__).parents[3]
sys.path.insert(0, str(root_dir))

# noqa: E402
from benchmark_modules.content_transformation.core.evaluators import (  # noqa: E402
    FormatValidator,
    ToneEvaluator
)

def test_manual_execution():
    """
    Manual Execution entry point for running this script directly
    """
    print("=" * 60)
    print("Content Transformation v2.0 - Integration Test")
    print("=" * 60)

    # Test 1: Twitter Thread Validator
    print("\n[Test 1] FormatValidator.validate_twitter_thread()")
    thread_valid = "1/3 First tweet\n2/3 Second tweet\n3/3 Final tweet"
    thread_invalid = "1/5 First\n3/5 Third"  # Missing 2, 4, 5

    # Changed to pass config dict instead of kwargs to match implementation
    is_valid, violations = FormatValidator.validate_twitter_thread(thread_valid, config={"min_tweets": 3})
    print(f"  ✓ Valid thread: {is_valid} (expected: True)")
    assert is_valid is True, "Valid thread should pass"

    is_valid, violations = FormatValidator.validate_twitter_thread(thread_invalid, config={"min_tweets": 5})
    print(f"  ✓ Invalid thread: {is_valid} (expected: False)")
    print(f"    Violations: {violations}")
    assert is_valid is False, "Invalid thread should fail"

    # Test 2: JSON Validator
    print("\n[Test 2] FormatValidator.validate_json_structure()")
    json_valid = '{"name": "John", "age": 30}'
    json_invalid = '{"name": "John", "age":}'

    is_valid, violations = FormatValidator.validate_json_structure(json_valid)
    print(f"  ✓ Valid JSON: {is_valid} (expected: True)")
    assert is_valid is True, "Valid JSON should pass"

    is_valid, violations = FormatValidator.validate_json_structure(json_invalid)
    print(f"  ✓ Invalid JSON: {is_valid} (expected: False)")
    assert is_valid is False, "Invalid JSON should fail"

    # Test 3: Landing Page Validator
    print("\n[Test 3] FormatValidator.validate_landing_page_structure()")
    landing_page = """
# Headline: Revolutionary Product
## Subheadline: Transform your workflow
CTA: Sign up now!
"""
    is_valid, violations = FormatValidator.validate_landing_page_structure(landing_page)
    print(f"  ✓ Valid landing page: {is_valid} (expected: True)")
    assert is_valid is True, "Valid landing page should pass"

    # Test 4: Tone Evaluator - Formality
    print("\n[Test 4] ToneEvaluator.measure_formality()")
    formal_text = "Therefore, we hereby recommend the aforementioned solution."
    casual_text = "Hey! This is gonna be awesome, yeah?"

    formality_formal = ToneEvaluator.measure_formality(formal_text)
    formality_casual = ToneEvaluator.measure_formality(casual_text)

    print(f"  ✓ Formal text score: {formality_formal} (expected: > 0.5)")
    print(f"  ✓ Casual text score: {formality_casual} (expected: < 0.5)")
    assert formality_formal > 0.5, f"Formal text should score > 0.5, got {formality_formal}"
    assert formality_casual < 0.5, f"Casual text should score < 0.5, got {formality_casual}"

    # Test 5: Professionalism
    print("\n[Test 5] ToneEvaluator.measure_professionalism()")
    professional_text = "Thank you for your consideration. Please let me know."
    unprofessional_text = "lol whatever, this is stupid"

    prof_score = ToneEvaluator.measure_professionalism(professional_text)
    unprof_score = ToneEvaluator.measure_professionalism(unprofessional_text)

    print(f"  ✓ Professional text: {prof_score} (expected: > 0.5)")
    print(f"  ✓ Unprofessional text: {unprof_score} (expected: < 0.3)")
    assert prof_score > 0.5, f"Professional text should score > 0.5, got {prof_score}"
    assert unprof_score < 0.3, f"Unprofessional text should score < 0.3, got {unprof_score}"

    # Test 6: Spoken Style Detection
    print("\n[Test 6] ToneEvaluator.detect_spoken_style()")
    spoken_text = "So, um, like, you know what I mean? Let me explain."
    written_text = "The implementation requires careful consideration of architectural constraints."

    spoken_metrics = ToneEvaluator.detect_spoken_style(spoken_text)
    written_metrics = ToneEvaluator.detect_spoken_style(written_text)

    print(f"  ✓ Spoken text metrics: {spoken_metrics}")
    print(f"  ✓ Written text metrics: {written_metrics}")
    assert spoken_metrics['questions_count'] > 0, "Spoken text should have questions"

    print("\n" + "=" * 60)
    print("✅ All 6 tests passed! Content Transformation v2.0 ready.")
    print("=" * 60)

if __name__ == "__main__":
    test_manual_execution()
