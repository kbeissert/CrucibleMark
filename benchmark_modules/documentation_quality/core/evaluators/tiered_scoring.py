"""
Tiered Scoring Engine module.
Handles scoring for tiered error detection (Labeled, Standard, Advanced, Expert).
"""

from typing import List, Tuple
from .semantic_matcher import SemanticMatcher

class TieredScoringEngine:
    """
    Handles scoring for tiered error detection (Labeled, Standard, Advanced, Expert).
    Manages scoring logic including inverse matching and severity penalties.
    """

    def __init__(self, asset_id: str):
        self.asset_id = asset_id

    def score_tier(self, response: str, issues: list[dict],
                   tier_name: str, min_threshold: float) -> Tuple[float, List[str], List[str]]:
        """
        Scores a single tier level (e.g. "Standard Issues").

        Args:
            response: The (lower-cased) response string.
            issues: List of issue definitions for this tier.
            tier_name: Name of the tier (for logging).
            min_threshold: Default keyword match ratio if not specified in issue.

        Returns:
            Tuple containing:
            - tier_score (float)
            - details (list of strings)
            - violations (list of strings)
        """
        tier_score: float = 0.0
        details: List[str] = []
        violations: List[str] = []

        if not issues:
            return 0.0, details, violations

        max_points = sum(issue.get("points", 0) for issue in issues)

        for issue in issues:
            points = issue.get("points", 0)
            keywords = issue.get("keywords", [])
            target_matches = self._calculate_target_matches(
                issue, keywords, min_threshold
            )

            found = SemanticMatcher.check_match(
                response, keywords, target_matches, self.asset_id
            )

            delta, m_type, msg = self._evaluate_issue(issue, found, tier_name, points)

            tier_score += delta
            if m_type == "detail":
                details.append(msg)
            elif m_type == "violation":
                violations.append(msg)

        details.append(f"  → {tier_name} Total: {tier_score:.1f}/{max_points}p")
        return round(tier_score, 2), details, violations

    def _evaluate_issue(self, issue: dict, found: bool,
                        tier_name: str, points: float) -> Tuple[float, str, str]:
        """Evaluates a single issue and determines score impact and message."""
        name = issue.get("issue", "Unknown Issue")
        severity = issue.get("severity", "medium")
        inverse = issue.get("inverse_match", False)

        if inverse:
            if not found:
                return points, "detail", f"✓ [{tier_name}] {name} (Nicht gefunden): +{points}p"
            return 0.0, "violation", f"✗ [{tier_name}] {name} (Unerwünscht gefunden): -{points}p"

        if found:
            return points, "detail", f"✓ [{tier_name}] {name}: +{points}p"

        if severity in ["critical", "high"]:
            return 0.0, "violation", f"✗ [{tier_name}] {name}: -{points}p"

        return 0.0, "detail", f"○ [{tier_name}] {name}: 0p"

    def _calculate_target_matches(self, issue: dict,
                                   keywords: list[str],
                                   min_threshold: float) -> int:
        """Determines the number of keyword matches required."""
        explicit_min = issue.get("min_keywords")
        explicit_ratio = issue.get("required_ratio")

        if explicit_min is not None:
            return int(explicit_min)

        ratio = explicit_ratio if explicit_ratio is not None else min_threshold
        return max(1, int(len(keywords) * ratio))
