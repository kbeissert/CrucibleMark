from typing import Any, Dict, List, Tuple
import re

from utils.similarity import SemanticSimilarity
from .constants import (
    ERROR_INVALID_RESPONSE,
    ERROR_TEST_FAILED,
)

class CodeQualityEvaluator:
    """
    Evaluator class for Code Quality benchmarks.
    Encapsulates all scoring logic (Error Detection, Solution Quality, Formatting, Expertise).
    """

    def __init__(self, asset: Dict[str, Any]):
        self.asset = asset
        self.similarity_engine = SemanticSimilarity()

    def _evaluate_criterion_dispatch(
        self, criterion: Dict[str, Any], response: str, response_lower: str
    ) -> Tuple[float, str]:
        """Zentraler Dispatcher für alle Check-Methoden."""
        method = criterion.get("check_method")

        if not isinstance(method, str):
            return 0.0, ""

        dispatch_map = {
            "regex": lambda: self._score_pattern_match(response, criterion),
            "keyword_presence": lambda: self._score_keyword_presence(
                response_lower, criterion
            ),
            "code_validation": lambda: self._score_code_validation(response, criterion),
            "markdown_table_validation": lambda: self._score_table_criterion(
                response, criterion
            ),
            "list_detection": lambda: self._score_keyword_presence(
                response_lower, criterion
            ),
            "semantic_similarity": lambda: self._score_semantic_similarity(
                response, criterion
            ),
        }

        handler = dispatch_map.get(method)
        if handler:
            return handler()

        return 0.0, ""

    def _score_generic_category(
        self, response: str, response_lower: str, config: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """Generische Iteration über Kriterien."""
        score = 0.0
        details = []
        for criterion in config.get("criteria", []):
            delta, detail = self._evaluate_criterion_dispatch(
                criterion, response, response_lower
            )
            score += delta
            if detail:
                details.append(detail)
        return round(score, 2), details

    def _process_category_result(
        self,
        category_key: str,
        score: float,
        cat_details: List[str],
        weight: int,
        results: Dict[str, Any],
    ) -> None:
        """Updates the results dictionary with the score and details for a specific category."""
        results["category_scores"][category_key] = {
            "achieved": score,
            "max": weight,
        }
        results["details"].extend(cat_details)
        results["total_achieved"] += score

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Facade Method: Main Scoring Logic
        """
        # Clean reasoning tags (e.g. DeepSeek <think>) before scoring
        clean_response = self._clean_reasoning_tags(response)

        if not clean_response or clean_response.startswith("ERROR:"):
            return {
                "status": "error",
                "total_score": 0,
                "max_score": 100,
                "category_scores": {},
                "details": [ERROR_INVALID_RESPONSE],
                "violations": [ERROR_TEST_FAILED],
            }

        scoring_config = self.asset["scoring"]
        total_possible = scoring_config.get("total_points", 100)

        results = {
            "category_scores": {},
            "details": [],
            "violations": [],
            "total_achieved": 0.0,
        }

        response_lower = clean_response.lower()

        # 1. Error Detection (Handled specifically due to violations logic)
        ed_conf = scoring_config.get("error_detection", {})
        ed_score, ed_details, ed_violations = self._score_error_detection(
            clean_response, response_lower, ed_conf
        )
        self._process_category_result(
            "error_detection", ed_score, ed_details, ed_conf.get("weight", 0), results
        )
        results["violations"].extend(ed_violations)

        # 2. Generic Categories (Solution Quality, Formatting, Expertise)
        generic_categories = ["solution_quality", "formatting", "expertise"]
        for cat in generic_categories:
            if cat not in scoring_config:
                if cat == "expertise":  # Explicitly handle optional expertise
                    results["category_scores"][cat] = {"achieved": 0, "max": 0}
                continue

            cat_conf = scoring_config.get(cat, {})
            score, cat_details = self._score_generic_category(
                clean_response, response_lower, cat_conf
            )
            self._process_category_result(
                cat, score, cat_details, cat_conf.get("weight", 0), results
            )

        return {
            "status": "success",
            "total_score": round(results["total_achieved"], 2),
            "max_score": total_possible,
            "category_scores": results["category_scores"],
            "details": results["details"],
            "violations": results["violations"],
        }

    def _clean_reasoning_tags(self, response: str) -> str:
        """Removes <think>...</think> blocks from DeepSeek models."""
        return re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()

    def _score_error_detection(
        self, response: str, response_lower: str, config: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Scoring strategy for Error Detection."""
        score = 0.0
        details = []
        violations = []
        max_score = config.get("weight", 0)

        # Dynamic Issue Iteration
        for key, issues_list in config.items():
            if (
                key.endswith("_issues")
                and key != "bonus_issues"
                and isinstance(issues_list, list)
            ):
                category_name = key.replace("_issues", "").replace("_", " ").title()

                for issue in issues_list:
                    severity = category_name
                    found = self._check_issue_mentioned(
                        response_lower, issue.get("keywords", [])
                    )

                    points = issue.get("points", 0)
                    extra_info = f" (WCAG {issue['wcag']})" if "wcag" in issue else ""
                    issue_name = issue.get("issue", "Unknown Issue")

                    if found:
                        score += points
                        details.append(
                            f"✓ {severity} erkannt: {issue_name}{extra_info}, +{points}p"
                        )
                    elif severity in ["Critical", "Labeled", "Standard"]:
                        prefix = "✗" if severity in ["Critical", "Labeled"] else "~"
                        # violations vs items
                        if severity == "Critical":
                            violations.append(f"{prefix} {severity} fehlt: {issue_name}{extra_info}, -{points}p")
                        else:
                            violations.append(f"~ {severity} fehlt: {issue_name}{extra_info}, -{points}p")
                    elif severity == "Medium":
                        details.append(f"○ Medium fehlt: {issue_name}{extra_info}")
                    else:
                        violations.append(f"~ {severity} fehlt: {issue_name}{extra_info}, -{points}p")

        # Bonus Scoring
        bonus_score = self._calculate_bonus_score(response_lower, config, details)
        score += bonus_score

        return min(score, max_score), details, violations

    def _check_issue_mentioned(self, text_lower: str, keywords: List[str]) -> bool:
        """Checks if any keyword for an issue is present in the text."""
        if not keywords:
            return False
        for kw in keywords:
            if kw.lower() in text_lower:
                return True
        return False

    def _calculate_bonus_score(
        self, response_lower: str, config: Dict[str, Any], details: List[str]
    ) -> float:
        """Calculates bonus points."""
        bonus = 0.0
        bonus_issues = config.get("bonus_issues", [])
        for issue in bonus_issues:
            if self._check_issue_mentioned(response_lower, issue.get("keywords", [])):
                points = issue.get("points", 0)
                bonus += points
                details.append(f"★ Bonus gefunden: {issue.get('issue')}, +{points}p")
        return bonus

    # -- Helper Methods --

    def _score_pattern_match(self, text: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        pattern = criterion.get("pattern", "")
        points = criterion.get("points", 0)
        negate = criterion.get("negate", False)

        found = bool(re.search(pattern, text, re.MULTILINE | re.IGNORECASE))
        if negate:
            if not found:
                return points, f"✓ {criterion.get('description')}: Kein unerwünschtes Muster gefunden"
            return 0.0, f"✗ {criterion.get('description')}: Unerwünschtes Muster gefunden"
        if found:
            return points, f"✓ {criterion.get('description')}"
        return 0.0, f"✗ {criterion.get('description')} nicht gefunden"

    def _score_code_validation(self, text: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        # Minimal implementation based on typical checks
        required_elements = criterion.get("required_elements", [])
        points = criterion.get("points", 0)
        missing = [el for el in required_elements if el not in text]
        if not missing:
            return points, f"✓ {criterion.get('description')}"
        return 0.0, f"✗ {criterion.get('description')}: Fehlende Elemente: {', '.join(missing)}"

    def _score_keyword_presence(self, text_lower: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        keywords = [k.lower() for k in criterion.get("keywords", [])]
        points = criterion.get("points", 0)
        found = any(k in text_lower for k in keywords)
        if found:
            return points, f"✓ {criterion.get('description')}"
        return 0.0, f"✗ {criterion.get('description')} (-{points}p)"

    def _score_table_criterion(self, text: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        # Simple table detection - counting pipes
        lines = text.split('\n')
        table_lines = [line for line in lines if '|' in line and len(line.split('|')) > 2]
        points = criterion.get("points", 0)
        if len(table_lines) >= criterion.get("min_rows", 3):
            return points, f"✓ {criterion.get('description')}"
        return 0.0, "✗ Tabelle nicht erkannt oder zu klein"

    def _score_semantic_similarity(self, text: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        reference = criterion.get("reference_text", "")
        threshold = criterion.get("threshold", 0.7)
        points = criterion.get("points", 0)
        score = self.similarity_engine.calculate_similarity(text, reference)
        if score >= threshold:
            return points, f"✓ Inhaltliche Übereinstimmung ({score:.2f})"
        return 0.0, f"✗ Inhalt weicht ab ({score:.2f} < {threshold})"

