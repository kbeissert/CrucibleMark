"""
Tiered Scoring Logic
Handles the structured scoring through labeled, standard, advanced, and expert tiers.
"""
from typing import List, Tuple
from ..constants import TIER_THRESHOLDS
from .semantic_matcher import SemanticMatcher


class TieredScoringEngine:
    """Evaluates response against tiered difficulty issues"""

    @staticmethod
    def score_error_detection(
        response_lower: str, config: dict
    ) -> Tuple[float, List[str], List[str], float]:
        """
        Bewertet Issue Detection mit Tiered Difficulty (70 Punkte)
        
        Returns:
            (score, details, violations, max_possible)
        """
        score: float = 0.0
        max_possible: float = 0.0
        details: List[str] = []
        violations: List[str] = []

        # Issues sind direkt in config als labeled_issues, standard_issues, etc.
        tier_configs = {
            "labeled": ("labeled_issues", TIER_THRESHOLDS["labeled"]),
            "standard": ("standard_issues", TIER_THRESHOLDS["standard"]),
            "advanced": ("advanced_issues", TIER_THRESHOLDS["advanced"]),
            "expert": ("expert_issues", TIER_THRESHOLDS["expert"]),
        }

        # Score jede Tier-Kategorie
        for tier_name, (tier_key, default_threshold) in tier_configs.items():
            tier_issues = config.get(tier_key, [])

            if not tier_issues:
                continue

            # Calculate score for this tier
            tier_res = TieredScoringEngine._score_tier_issues(
                response_lower,
                tier_issues,
                default_threshold,
                tier_name.title()
            )
            tier_score, tier_details, tier_violations, tier_max = tier_res

            score += tier_score
            max_possible += tier_max
            details.extend(tier_details)
            violations.extend(tier_violations)

        return round(score, 2), details, violations, max_possible

    @staticmethod
    def _score_tier_issues(
        response_lower: str,
        issues: List[dict],
        min_threshold: float,
        tier_name: str,
    ) -> Tuple[float, List[str], List[str], float]:
        """
        Bewertet eine Tier-Kategorie (z.B. Labeled, Standard, Advanced, Expert)
        """
        tier_score: float = 0.0
        details: List[str] = []
        violations: List[str] = []

        if not issues:
            return 0.0, details, violations, 0.0

        # Berechne max_points für diese Tier (Summe aller Issue-Points)
        tier_max_points = sum(issue.get("points", 0) for issue in issues)

        for issue in issues:
            points = issue.get("points", 0)
            keywords = issue.get("keywords", [])
            issue_name = issue.get("issue", "Unknown Issue")
            severity = issue.get("severity", "medium")

            # Check ob Issue erwähnt wird (delegated to SemanticMatcher)
            found = SemanticMatcher.check_issue_mentioned(
                response_lower,
                keywords,
                tier_name=tier_name,
                min_keyword_threshold=min_threshold
            )

            if found:
                tier_score += points
                details.append(f"✓ [{tier_name}] {issue_name}: +{points}p")
            # Für Critical/High = Violation, sonst nur Details
            elif severity in ["critical", "high"]:
                violations.append(f"✗ [{tier_name}] {issue_name}: -{points}p")
            else:
                details.append(f"○ [{tier_name}] {issue_name}: 0p")

        # Direkter Score ohne Normalisierung (Issue-Points sind bereits korrekt)
        details.append(f"  → {tier_name} Total: {tier_score:.1f}/{tier_max_points}p")

        return round(tier_score, 2), details, violations, tier_max_points
