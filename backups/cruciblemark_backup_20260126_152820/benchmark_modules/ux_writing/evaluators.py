import re
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, Union
from utils.similarity import SemanticSimilarity
from .models import UXCriterion, UXIssue

# Constants
MIN_SENTENCE_LENGTH = 15
SIMILARITY_THRESHOLD = 0.65
MIN_TABLE_COLUMNS = 2
MAX_BUTTON_LENGTH = 50
MAX_STEP_WORDS = 80

class CriterionEvaluator(ABC):
    """Abstract base class for criterion evaluators."""
    
    @abstractmethod
    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        """Returns (score, explanation_string)."""
        pass

class KeywordPresenceEvaluator(CriterionEvaluator):
    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        points = criterion.points
        keywords = criterion.keywords
        # Simple containment check
        found_keywords = [kw for kw in keywords if kw.lower() in response.lower()]
        min_required = criterion.min_keywords

        if len(found_keywords) >= min_required:
            display_kws = ", ".join(found_keywords[:3])
            return (
                points,
                f"✓ {criterion.name}: {len(found_keywords)}/{min_required} ({display_kws}) ({points}p)",
            )
        display_kws = ", ".join(found_keywords) if found_keywords else 'keine'
        return (
            0.0,
            f"✗ {criterion.name}: {len(found_keywords)}/{min_required} ({display_kws})",
        )

class KeywordAbsenceEvaluator(CriterionEvaluator):
    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        points = criterion.points
        forbidden = criterion.forbidden_keywords
        found_forbidden = [kw for kw in forbidden if kw.lower() in response.lower()]
        max_violations = criterion.max_violations

        if len(found_forbidden) <= max_violations:
            return (
                points,
                f"✓ {criterion.name}: Keine verbotenen Begriffe ({points}p)",
            )
        return (
            0.0,
            f"✗ {criterion.name}: Verbotene Begriffe gefunden: {', '.join(found_forbidden)}",
        )

class MarkdownTableEvaluator(CriterionEvaluator):
    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        points = criterion.points
        has_table = "|" in response and "-" in response
        
        # Count rows that look like table rows (have enough pipes)
        # Note: Original code used global MIN_TABLE_COLUMNS
        table_rows = len(
            [
                line
                for line in response.split("\n")
                if line.count("|") >= MIN_TABLE_COLUMNS
            ]
        )
        min_rows = criterion.min_rows

        if has_table and table_rows >= min_rows:
            return points, f"✓ {criterion.name}: {table_rows} Zeilen ({points}p)"
        
        if has_table:
            # Partial credit logic from original code
            partial = (float(table_rows) / min_rows) * points
            return (
                partial,
                f"⚠ {criterion.name}: {table_rows}/{min_rows} Zeilen ({partial:.1f}p)",
            )

        return 0.0, f"✗ {criterion.name}: Keine Tabelle gefunden"

class StructureValidationEvaluator(CriterionEvaluator):
    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        points = criterion.points
        required_structure = criterion.required_structure

        found = [
            elem for elem in required_structure if elem.lower() in response.lower()
        ]

        if len(found) == len(required_structure):
            return (
                points,
                f"✓ {criterion.name}: Alle Strukturelemente vorhanden ({points}p)",
            )

        missing = set(required_structure) - set(found)
        return 0.0, f"✗ {criterion.name}: Fehlende Elemente: {', '.join(missing)}"

class RegexEvaluator(CriterionEvaluator):
    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        points = criterion.points
        
        # Fallback to WCAG pattern if not provided, just like original code
        pattern = criterion.check_pattern or r"\d\.\d\.\d"

        matches = re.findall(pattern, response)
        # Assuming count_unique is True based on original code defaults, 
        # though original code checked a dict key.
        count = len(set(matches))
        min_required = 4 # Default from original code

        if count >= min_required:
            return points, f"✓ {criterion.name}: {count} Treffer ({points}p)"

        partial = (float(count) / min_required) * points
        return (
            partial,
            f"⚠ {criterion.name}: {count}/{min_required} Treffer ({partial:.1f}p)",
        )

class CodeValidationEvaluator(CriterionEvaluator):
    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        points = criterion.points
        required = criterion.required_elements
        min_blocks = criterion.min_code_blocks

        total_found = 0
        found_elements = []

        for elem in required:
            count = response.count(elem)
            if count > 0:
                total_found += count
                found_elements.append(f"{elem}({count}x)")

        if total_found >= min_blocks:
            return (
                points,
                f"✓ {criterion.name}: {total_found} Code-Beispiele ({', '.join(found_elements[:3])}) ({points}p)",
            )

        return (
            0.0,
            f"✗ {criterion.name}: {total_found}/{min_blocks} Code-Beispiele",
        )

class LengthValidationEvaluator(CriterionEvaluator):
    def evaluate(self, response: str, criterion: UXCriterion) -> Tuple[float, str]:
        points = criterion.points
        # Assuming generic param parsing or usage of additional_params if needed
        # but models.py has specific fields for now or we rely on defaults.
        # Original code used hardcoded MAX_BUTTON_LENGTH default
        max_length = MAX_BUTTON_LENGTH 

        button_pattern = r'["\']([^"\']{1,100})["\']'
        buttons = re.findall(button_pattern, response)

        if not buttons:
            return 0.0, f"⚠ {criterion.name}: Keine Button-Labels gefunden"

        too_long = [b for b in buttons if len(b) > max_length]

        if len(too_long) == 0:
            return (
                points,
                f"✓ {criterion.name}: Alle Buttons <{max_length} Zeichen ({points}p)",
            )

        return (
            points * 0.5,
            f"⚠ {criterion.name}: {len(too_long)} Buttons zu lang (z.B. '{too_long[0][:30]}...')",
        )

class IssueEvaluator:
    """Evaluates error detection issues using hybrid matching."""
    
    @staticmethod
    def check_issue_mentioned(response_lower: str, keywords: List[str]) -> bool:
        """
        Prüft ob ein Issue in der Response erwähnt wurde.
        Nutzt Hybrid-Ansatz: String-Matching + Semantic Similarity
        """
        if not keywords:
            return False

        # 1. WCAG Nummer Check (Regex)
        has_wcag_number = any(re.match(r"\d\.\d\.\d", kw) for kw in keywords)
        if has_wcag_number:
            for kw in keywords:
                if re.match(r"\d\.\d\.\d", kw) and kw in response_lower:
                    return True  # Wenn WCAG Nummer im Text vorkommt -> Treffer

        # 2. String Matching (Keyword Count)
        matches = sum(1 for kw in keywords if kw.lower() in response_lower)
        required_ratio = 0.4
        required_matches = max(1, int(len(keywords) * required_ratio))

        if matches >= required_matches:
            return True

        # 3. Semantic Similarity (Fallback)
        query = " ".join(keywords)  # Konstruiere eine Query aus den Keywords

        # Splitte Response in Sätze (grob)
        sentences = [
            s.strip()
            for s in response_lower.split(".")
            if len(s.strip()) > MIN_SENTENCE_LENGTH
        ]

        # Wenn keine Sätze gefunden, nutze Chunks
        if not sentences:
            sentences = [
                response_lower[i : i + 200] for i in range(0, len(response_lower), 200)
            ]

        # Suche besten Match
        # Assuming SemanticSimilarity is available and configured
        try:
             best_score = SemanticSimilarity.find_best_match(query, sentences)
             return best_score > SIMILARITY_THRESHOLD
        except Exception:
             # Fallback if similarity check fails (e.g. model not loaded)
             return False

    @classmethod
    def evaluate(cls, response_lower: str, issue: UXIssue) -> Tuple[float, str, bool]:
        """
        Returns (points_awarded, explanation, is_match).
        """
        matched = cls.check_issue_mentioned(response_lower, issue.keywords)
        
        # If inverse_match is True, we want matched to be False for points
        if issue.inverse_match:
            if not matched:
                return issue.points, f"✓ {issue.issue}: Erfolgreich vermieden ({issue.points}p)", False
            else:
                 return 0.0, f"✗ {issue.issue}: Unerwünscht gefunden", True
        else:
            if matched:
                return issue.points, f"✓ {issue.issue}: Erkannt ({issue.points}p)", True
            else:
                return 0.0, f"✗ {issue.issue}: Nicht erkannt", False

class EvaluatorFactory:
    _evaluators = {
        "keyword_presence": KeywordPresenceEvaluator(),
        "keyword_absence": KeywordAbsenceEvaluator(),
        "markdown_table_validation": MarkdownTableEvaluator(),
        "structure_validation": StructureValidationEvaluator(),
        "regex": RegexEvaluator(),
        "code_validation": CodeValidationEvaluator(),
        "length_validation": LengthValidationEvaluator(),
        # Map readability to keyword presence for now as per original code logic usually
        # but let's see if we need a specific one. 
        # Original code mapped "readability_score" -> score_readability which used kw search
        "readability_score": KeywordPresenceEvaluator(), 
        "readability_mention": KeywordPresenceEvaluator(),
    }

    @classmethod
    def get_evaluator(cls, check_method: str) -> CriterionEvaluator:
        return cls._evaluators.get(check_method, KeywordPresenceEvaluator())

