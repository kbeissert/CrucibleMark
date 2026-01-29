"""Standard scorers for generic assets."""

from difflib import SequenceMatcher
from typing import Any, cast

from ..constants import (
    BONUS_CONSISTENCY,
    CORRECTION_INDICATORS,
    MATCH_THRESHOLD_WEAK,
    MAX_SCORE,
    MIN_WORD_LENGTH,
    REASONING_INDICATORS,
    SOLUTION_KEYWORDS_OPTIONS,
    SOLUTION_KEYWORDS_STEPS,
    SOLUTION_WEIGHT_OPTIONS,
    SOLUTION_WEIGHT_STEPS,
    SOLUTION_WEIGHT_STRUCTURE,
    STRUCTURE_KEYWORDS,
    WEIGHT_CONSISTENCY,
    WEIGHT_ERROR_DETECTION,
    WEIGHT_SOLUTION_QUALITY,
)
from ..structure_analysis import contains_any


def score_similarity_fallback(
    response: str, asset: dict[str, Any]
) -> tuple[float, dict[str, Any], list[str]]:
    """Fallback for puzzles like River Crossing using sequence matcher."""
    expected = asset.get("expected_output", "")
    if isinstance(expected, dict):
        expected = str(expected)

    sim = SequenceMatcher(None, response.strip(), expected.strip()).ratio()

    total_score = sim * MAX_SCORE
    score_breakdown = {"logic": {"score": total_score, "weight": MAX_SCORE}}
    details = [f"Logic Match: {total_score:.1f}%"]

    return total_score, score_breakdown, details


def score_standard_asset(
    response: str, required_findings: list[str], asset: dict[str, Any]
) -> tuple[float, dict[str, Any], list[str]]:
    """Score 5A, 5B using finding keywords."""
    resp_lower = response.lower()
    details = []
    score_breakdown: dict[str, Any] = {}
    total_score = 0.0

    # 1. Error Detection (Match Keywords)
    error_score = _measure_error_detection(
        resp_lower, required_findings, asset,
    )

    error_max = float(WEIGHT_ERROR_DETECTION)
    if error_cfg := asset.get("scoring", {}).get("error_detection"):
        error_max = float(error_cfg.get("points", error_max))

    score_breakdown["error_detection"] = error_score
    total_score += error_score
    details.append(f"Error Detection: {error_score:.1f}/{error_max}")

    # 2. Solution Quality (Structure)
    quality_score = _measure_solution_quality(resp_lower, asset)
    score_breakdown["solution_quality"] = quality_score
    total_score += quality_score
    details.append(f"Solution Quality: {quality_score:.1f}")

    # 3. Consistency and Finalize
    return _measure_consistency_and_return_full(
        total_score, score_breakdown, details, response, asset,
    )


def _measure_error_detection(
    resp_lower: str, required_findings: list[str], asset: dict[str, Any]
) -> float:
    """Calculate error detection score based on keyword matches."""
    matches = 0
    for finding in required_findings:
        keywords = [w.lower() for w in finding.split() if len(w) >= MIN_WORD_LENGTH]
        if not keywords:
            continue

        found_words = sum(1 for w in keywords if w in resp_lower)
        if found_words / len(keywords) >= MATCH_THRESHOLD_WEAK:
            matches += 1

    error_cfg = cast(
        "dict[str, Any]", asset.get("scoring", {}).get("error_detection", {}),
    )
    error_max = float(error_cfg.get("points", WEIGHT_ERROR_DETECTION))

    if matches >= len(required_findings):
        return error_max
    return (matches / len(required_findings)) * error_max


def _measure_solution_quality(
    resp_lower: str, asset: dict[str, Any]
) -> float:
    """Calculate solution quality score based on structure patterns."""
    qual_cfg = cast(
        "dict[str, Any]", asset.get("scoring", {}).get("solution_quality", {}),
    )
    quality_max = float(qual_cfg.get("points", WEIGHT_SOLUTION_QUALITY))
    quality_score = 0.0

    if contains_any(resp_lower, STRUCTURE_KEYWORDS):
        quality_score += quality_max * SOLUTION_WEIGHT_STRUCTURE
    if contains_any(resp_lower, SOLUTION_KEYWORDS_OPTIONS):
        quality_score += quality_max * SOLUTION_WEIGHT_OPTIONS
    if contains_any(resp_lower, SOLUTION_KEYWORDS_STEPS):
        quality_score += quality_max * SOLUTION_WEIGHT_STEPS

    return min(quality_score, quality_max)


def _measure_consistency_and_return_full(
    total_score: float,
    score_breakdown: dict[str, Any],
    details: list[str],
    response: str,
    asset: dict[str, Any],
) -> tuple[float, dict[str, Any], list[str]]:
    """Measure consistency, add it to totals, and return final standard result."""
    const_cfg = cast(
        "dict[str, Any]", asset.get("scoring", {}).get("consistency", {}),
    )
    const_max = float(const_cfg.get("points", WEIGHT_CONSISTENCY))
    sc, _ = score_consistency(response, {"points": const_max})

    score_breakdown["consistency"] = sc
    total_score += sc
    details.append(f"Consistency: {sc:.1f}/{const_max}")

    return total_score, score_breakdown, details


def score_consistency(
    response: str, config: dict[str, Any]
) -> tuple[float, list[str]]:
    """Evaluate consistency for reasoning tests."""
    score = 0.0
    details: list[str] = []
    max_points = float(config.get("points", WEIGHT_CONSISTENCY))

    resp_lower = response.lower()

    has_reasoning = contains_any(resp_lower, REASONING_INDICATORS)
    has_correction = contains_any(resp_lower, CORRECTION_INDICATORS)

    if has_reasoning and has_correction:
        score = max_points
        details.append(
            f"✓ Konsistenz: Reasoning und Korrektur vorhanden (+{score}p)",
        )
    elif has_reasoning or has_correction:
        score = max_points / 2
        details.append(
            f"~ Teilweise konsistent: Reasoning/Korrektur gefunden ({score}p)",
        )
    else:
        details.append("✗ Inkonsistent: Kein Reasoning-Prozess erkennbar")

    return score, details
