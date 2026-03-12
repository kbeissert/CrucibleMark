"""
Error Detection Logic for Code Quality Module.
Handles issue detection, bonus scoring, and violation tracking.
"""

from typing import Any, Dict, List, Tuple, Set


class ErrorDetector:
    """Handles error detection scoring and violation tracking."""

    def __init__(self) -> None:
        self.known_issues_cache: Set[str] = set()

    def score_error_detection(
        self, response: str, response_lower: str, config: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Main error detection scoring method.

        Args:
            response: The original response string (unused in this logic but kept for interface).
            response_lower: Lowercased response for keyword matching.
            config: Configuration dictionary containing issue definitions.

        Returns:
            Tuple of (score, details, violations)
        """
        score = 0.0
        details = []
        violations = []
        max_score = config.get("weight", 0)

        # 1. Identify all found issues once (Performance Optimization)
        found_issues = self._identify_found_issues(response_lower, config)

        # 2. Iterate config to report results (maintaining order)
        for key, issues_list in config.items():
            if (
                key.endswith("_issues")
                and key != "bonus_issues"
                and isinstance(issues_list, list)
            ):
                category_name = key.replace("_issues", "").replace("_", " ").title()

                for issue in issues_list:
                    issue_name = issue.get("issue", "Unknown Issue")
                    points = issue.get("points", 0)
                    extra_info = f" (WCAG {issue['wcag']})" if "wcag" in issue else ""
                    severity = category_name

                    if issue_name in found_issues:
                        score += points
                        details.append(
                            f"✓ {severity} detected: {issue_name}{extra_info}, +{points}p"
                        )
                    elif severity in ["Critical", "Labeled", "Standard"]:
                        prefix = "✗" if severity in ["Critical", "Labeled"] else "~"
                        if severity == "Critical":
                            violations.append(
                                f"{prefix} {severity} missing: {issue_name}{extra_info}, -{points}p"
                            )
                        else:
                            violations.append(
                                f"~ {severity} missing: {issue_name}{extra_info}, -{points}p"
                            )
                    elif severity == "Medium":
                        details.append(f"○ Medium missing: {issue_name}{extra_info}")
                    else:
                        violations.append(
                            f"~ {severity} missing: {issue_name}{extra_info}, -{points}p"
                        )

        # 3. Bonus Scoring
        bonus_score = self.calculate_bonus_score(response_lower, config, details)
        score += bonus_score

        return min(score, max_score), details, violations

    def _identify_found_issues(
        self, text_lower: str, config: Dict[str, Any]
    ) -> Set[str]:
        """
        Scans text for all issue keywords and returns set of found issue names.
        Optimized to single text pass per keyword.
        """
        found = set()
        for key, issues_list in config.items():
            if (
                key.endswith("_issues")
                and key != "bonus_issues"
                and isinstance(issues_list, list)
            ):
                for issue in issues_list:
                    # Check if ANY keyword is present
                    keywords = issue.get("keywords", [])
                    for kw in keywords:
                        if kw.lower() in text_lower:
                            found.add(issue.get("issue"))
                            break  # Found this issue, move to next
        return found

    def check_issue_mentioned(self, text_lower: str, keywords: List[str]) -> bool:
        """Checks if any keyword for an issue is present."""
        if not keywords:
            return False
        for kw in keywords:
            if kw.lower() in text_lower:
                return True
        return False

    def calculate_bonus_score(
        self, response_lower: str, config: Dict[str, Any], details: List[str]
    ) -> float:
        """Calculates bonus points for extra findings."""
        bonus = 0.0
        bonus_issues = config.get("bonus_issues", [])
        for issue in bonus_issues:
            if self.check_issue_mentioned(response_lower, issue.get("keywords", [])):
                points = issue.get("points", 0)
                bonus += points
                details.append(f"★ Bonus found: {issue.get('issue')}, +{points}p")
        return bonus
