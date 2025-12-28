#!/usr/bin/env python3
"""
UX Writing & Microcopy Test Module
Erweiterte Version mit vollständigem Scoring für UX Writing Dimensionen
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re
import time

# Ensure root directory is in sys.path for imports
# Path: benchmark_modules/ux_writing/test.py -> .../llm-test
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmark_modules.base_test import BaseTest  # noqa: E402
from utils.similarity import SemanticSimilarity  # noqa: E402

# ============================================================
# Constants for scoring thresholds
# ============================================================

MIN_TABLE_COLUMNS = 2  # Minimum pipes for table detection
DEFAULT_MIN_TABLE_ROWS = 6  # Default minimum rows for complete table
DEFAULT_MIN_KEYWORDS = 2  # Default minimum keywords to match
MAX_BUTTON_LENGTH = 50  # Max characters for button labels
MAX_STEP_WORDS = 80  # Max words per onboarding step
FLESCH_TARGET_MIN = 60  # Minimum Flesch Reading Ease score


class UXWritingTest(BaseTest):
    """
    Test-Modul für UX Writing & Microcopy

    Features:
    - Verständlichkeit (Flesch-Reading-Ease, Klarheit)
    - Tonalität (Kontext-Anpassung, Empathie)
    - Länge & Prägnanz (Button-Limits, Mobile-First)
    - A11y-Konformität (ARIA-Labels, Screen-Reader)
    """

    def execute(self, model: str, llm_client, provider: str = "ollama") -> Dict:
        """
        Führt UX-Writing-Test aus

        Args:
            model: LLM-Modell (z.B. qwen2.5:14b)
            llm_client: LLMClient-Instanz
            provider: Provider (ollama, mistral, anthropic, openai)

        Returns:
            Dict mit raw_response, execution_time, tokens_used, metadata
        """
        prompt = self.asset["prompt"]

        # 1. Requirements injizieren
        if "{requirements}" in prompt and "requirements" in self.asset:
            req_list = self.asset["requirements"]
            if isinstance(req_list, list):
                req_text = "\n".join([f"- {r}" for r in req_list])
            else:
                req_text = str(req_list)
            prompt = prompt.replace("{requirements}", req_text)

        # 2. Input Text injizieren
        if "{input_text}" in prompt and "input_text" in self.asset:
            prompt = prompt.replace("{input_text}", self.asset["input_text"])

        # Context hinzufügen falls vorhanden
        if "context" in self.asset:
            full_prompt = f"{self.asset['context']}\n\n{prompt}"
        else:
            full_prompt = prompt

        # LLM Query
        start = time.time()
        try:
            response = llm_client.query(model, full_prompt, provider=provider)
            elapsed = time.time() - start

            # Token-Approximation (Wörter * 1.3)
            approx_tokens = len(response.split()) * 1.3

            return {
                "raw_response": response,
                "execution_time": elapsed,
                "tokens_used": approx_tokens,
                "metadata": {
                    "model": model,
                    "asset_id": self.asset["metadata"]["id"],
                    "prompt_length": len(full_prompt),
                },
            }
        except Exception as e:
            return {
                "raw_response": f"ERROR: {str(e)}",
                "execution_time": 0.0,
                "tokens_used": 0,
                "metadata": {"model": model, "error": str(e)},
            }

    def score_response(self, response: str) -> Dict:
        """
        Bewertet UX-Writing-Antwort nach Asset-Scoring-Kriterien

        Scoring-Kategorien:
        1. Problem-Erkennung (30-35 Punkte) - Tiered Difficulty
        2. Lösungs-Qualität (30-40 Punkte) - Verständlichkeit, Tonalität
        3. Formatierung (10-20 Punkte) - Struktur, A11y
        4. Fachkompetenz (15-20 Punkte) - UX-Writing-Prinzipien

        Returns:
            Dict mit total_score, category_scores, details, violations
        """
        if not response or response.startswith("ERROR"):
            return {
                "status": "error",
                "total_score": 0,
                "max_score": 100,
                "category_scores": {},
                "details": ["Keine gültige Response erhalten"],
                "violations": ["Test konnte nicht ausgeführt werden"],
            }

        scoring_config = self.asset["scoring"]
        total_possible = scoring_config["total_points"]

        category_scores = {}
        details = []
        violations = []
        total_achieved = 0

        response_lower = response.lower()

        # ============================================================
        # KATEGORIE 1: Problem-Erkennung (30-35 Punkte)
        # ============================================================

        ed_score, ed_details, ed_violations = self.score_error_detection(
            response, response_lower, scoring_config["error_detection"]
        )
        category_scores["error_detection"] = {
            "achieved": ed_score,
            "max": scoring_config["error_detection"]["weight"],
        }
        details.extend(ed_details)
        violations.extend(ed_violations)
        total_achieved += ed_score

        # ============================================================
        # KATEGORIE 2: Lösungs-Qualität (30-40 Punkte)
        # ============================================================

        sq_score, sq_details = self.score_solution_quality(
            response, response_lower, scoring_config["solution_quality"]
        )
        category_scores["solution_quality"] = {
            "achieved": sq_score,
            "max": scoring_config["solution_quality"]["weight"],
        }
        details.extend(sq_details)
        total_achieved += sq_score

        # ============================================================
        # KATEGORIE 3: Formatierung (10-20 Punkte)
        # ============================================================

        fmt_score, fmt_details = self.score_formatting(
            response, response_lower, scoring_config["formatting"]
        )
        category_scores["formatting"] = {
            "achieved": fmt_score,
            "max": scoring_config["formatting"]["weight"],
        }
        details.extend(fmt_details)
        total_achieved += fmt_score

        # ============================================================
        # KATEGORIE 4: Fachkompetenz (15-20 Punkte)
        # ============================================================

        if "expertise" in scoring_config:
            exp_score, exp_details = self.score_expertise(
                response, response_lower, scoring_config["expertise"]
            )
            category_scores["expertise"] = {
                "achieved": exp_score,
                "max": scoring_config["expertise"]["weight"],
            }
            details.extend(exp_details)
            total_achieved += exp_score
        else:
            category_scores["expertise"] = {"achieved": 0, "max": 0}

        return {
            "status": "success",
            "total_score": round(total_achieved, 2),
            "max_score": total_possible,
            "category_scores": category_scores,
            "details": details,
            "violations": violations,
        }

    # ============================================================
    # HELPER METHODS: Error Detection
    # ============================================================

    def check_and_score_issue(
        self, response_lower: str, issue: Dict, severity: str
    ) -> Tuple[float, Optional[str], Optional[str]]:
        """
        Hilfsfunktion: Prüft ein einzelnes Issue und gibt Score/Details zurück.

        Returns:
            (score_delta, detail_msg, violation_msg)
        """
        found = self.check_issue_mentioned(response_lower, issue["keywords"])
        extra_info = f" (WCAG {issue['wcag']})" if "wcag" in issue else ""
        extra_info += (
            f" (Compliance: {issue['compliance_risk']})"
            if "compliance_risk" in issue
            else ""
        )

        if found:
            detail = f"✓ {severity} erkannt: {issue['issue']}{extra_info} ({issue['points']}p)"
            return issue["points"], detail, None
        elif severity == "Medium":
            detail = f"⚠ {severity} fehlt: {issue['issue']}{extra_info}"
            return 0, detail, None
        else:
            violation_prefix = "🔴 CRITICAL" if severity == "Critical" else "⚠️ HIGH"
            violation = f"{violation_prefix}: {severity} fehlt: {issue['issue']}{extra_info} (-{issue['points']}p)"
            return 0, None, violation

    def calculate_bonus_score(
        self, response_lower: str, config: Dict, details: List[str]
    ) -> int:
        """Berechnet Bonus-Punkte für zusätzlich gefundene Issues."""
        bonus_count = 0
        bonus_max = config.get("max_bonus", 5)
        bonus_issues = config.get("bonus_issues", [])

        for bonus_issue in bonus_issues:
            keywords = bonus_issue.lower().split()[:3]
            if any(kw in response_lower for kw in keywords):
                bonus_count += 1
                if bonus_count <= bonus_max:
                    details.append(
                        f"✓ Bonus: {bonus_issue} (+{config.get('bonus_points_each', 1)}p)"
                    )

        if bonus_count > 0:
            details.append(
                f"🎁 Bonus Total: {min(bonus_count, bonus_max)} Issues gefunden"
            )

        return min(bonus_count, bonus_max) * config.get("bonus_points_each", 1)

    def score_error_detection(
        self, response: str, response_lower: str, config: Dict
    ) -> Tuple[int, List[str], List[str]]:
        """
        Bewertet Problem-Erkennung (30-35 Punkte)
        Tiered: Labeled → Standard → Advanced → Expert

        Returns:
            (score, details_list, violations_list)
        """
        score = 0
        details = []
        violations = []
        max_score = config["weight"]

        # Iterate through all issue categories
        for key, issues_list in config.items():
            if (
                key.endswith("_issues")
                and key != "bonus_issues"
                and isinstance(issues_list, list)
            ):
                # Derive category name (e.g. "labeled_issues" -> "Labeled")
                category_name = key.replace("_issues", "").replace("_", " ").title()

                for issue in issues_list:
                    delta, detail, violation = self.check_and_score_issue(
                        response_lower, issue, category_name
                    )
                    score += delta
                    if detail:
                        details.append(detail)
                    if violation:
                        violations.append(violation)

        # BONUS Issues
        bonus_score = self.calculate_bonus_score(response_lower, config, details)
        score += bonus_score

        # Cap bei max_score
        score = min(score, max_score)

        return score, details, violations

    # ============================================================
    # HELPER METHODS: Solution Quality
    # ============================================================

    def score_pattern_match(self, response: str, criterion: Dict) -> Tuple[float, str]:
        """
        Hilfsfunktion: Bewertet Pattern-basierte Kriterien (Keyword-Präsenz).

        Returns:
            (score_delta, detail_msg)
        """
        points = criterion["points"]
        check_method = criterion.get("check_method")

        if check_method == "keyword_presence":
            keywords = criterion.get("keywords", [])
            found_keywords = [kw for kw in keywords if kw.lower() in response.lower()]
            min_required = criterion.get("min_keywords", DEFAULT_MIN_KEYWORDS)

            if len(found_keywords) >= min_required:
                return (
                    points,
                    f"✓ {criterion['name']}: {len(found_keywords)}/{min_required} ({', '.join(found_keywords[:3])}) ({points}p)",
                )
            else:
                return (
                    0,
                    f"✗ {criterion['name']}: {len(found_keywords)}/{min_required} ({', '.join(found_keywords) if found_keywords else 'keine'})",
                )

        elif check_method == "keyword_absence":
            forbidden = criterion.get("forbidden_keywords", [])
            found_forbidden = [kw for kw in forbidden if kw.lower() in response.lower()]
            max_violations = criterion.get("max_violations", 0)

            if len(found_forbidden) <= max_violations:
                return (
                    points,
                    f"✓ {criterion['name']}: Keine verbotenen Begriffe ({points}p)",
                )
            else:
                return (
                    0,
                    f"✗ {criterion['name']}: Verbotene Begriffe gefunden: {', '.join(found_forbidden)}",
                )

        elif (
            check_method == "readability_score" or check_method == "readability_mention"
        ):
            # Check if readability is mentioned
            readability_keywords = criterion.get(
                "keywords", ["flesch", "lesbarkeit", "verständlich", "einfach"]
            )
            found = any(kw in response.lower() for kw in readability_keywords)

            if found:
                return points, f"✓ {criterion['name']}: Lesbarkeit erwähnt ({points}p)"
            else:
                return 0, f"✗ {criterion['name']}: Keine Lesbarkeits-Analyse"

        return 0, f"⚠ {criterion['name']}: Check-Methode nicht implementiert"

    def score_length_validation(
        self, response: str, criterion: Dict
    ) -> Tuple[float, str]:
        """Prüft Zeichenlimits für Button-Labels."""
        points = criterion["points"]
        max_length = criterion.get("max_length", MAX_BUTTON_LENGTH)

        # Find button labels in quotes or code blocks
        button_pattern = r'["\']([^"\']{1,100})["\']'
        buttons = re.findall(button_pattern, response)

        if not buttons:
            return 0, f"⚠ {criterion['name']}: Keine Button-Labels gefunden"

        too_long = [b for b in buttons if len(b) > max_length]

        if len(too_long) == 0:
            return (
                points,
                f"✓ {criterion['name']}: Alle Buttons <{max_length} Zeichen ({points}p)",
            )
        else:
            return (
                points * 0.5,
                f"⚠ {criterion['name']}: {len(too_long)} Buttons zu lang (z.B. '{too_long[0][:30]}...')",
            )

    def score_word_count_validation(
        self, response: str, criterion: Dict
    ) -> Tuple[float, str]:
        """Prüft Wortlimits für Onboarding-Steps."""
        points = criterion["points"]
        max_words = criterion.get("max_words_per_step", MAX_STEP_WORDS)

        # Find steps (Step 1, Step 2, etc.)
        step_pattern = r"(?:Step|Schritt)\s*\d[:\s]*(.*?)(?=(?:Step|Schritt)\s*\d|$)"
        steps = re.findall(step_pattern, response, re.DOTALL | re.IGNORECASE)

        if not steps:
            return 0, f"⚠ {criterion['name']}: Keine Steps gefunden"

        too_long = []
        for i, step in enumerate(steps, 1):
            word_count = len(step.split())
            if word_count > max_words:
                too_long.append(f"Step {i}: {word_count} Wörter")

        if len(too_long) == 0:
            return (
                points,
                f"✓ {criterion['name']}: Alle Steps <{max_words} Wörter ({points}p)",
            )
        else:
            return (
                points * 0.5,
                f"⚠ {criterion['name']}: {len(too_long)} Steps zu lang ({', '.join(too_long)})",
            )

    def score_code_validation(
        self, response: str, criterion: Dict
    ) -> Tuple[float, str]:
        """Prüft Code-Blöcke auf erforderliche Elemente (z.B. ARIA-Attribute)."""
        points = criterion["points"]
        required = criterion.get("required_elements", [])
        min_blocks = criterion.get("min_code_blocks", 1)

        # Count occurrences
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
                f"✓ {criterion['name']}: {total_found} Code-Beispiele ({', '.join(found_elements[:3])}) ({points}p)",
            )
        else:
            return (
                0,
                f"✗ {criterion['name']}: {total_found}/{min_blocks} Code-Beispiele",
            )

    def score_solution_quality(
        self, response: str, response_lower: str, config: Dict
    ) -> Tuple[float, List[str]]:
        """
        Bewertet Lösungs-Qualität (30-40 Punkte)
        Prüft Verständlichkeit, Tonalität, Handlungsanweisungen

        Returns:
            (score, details_list)
        """
        score = 0
        details = []

        for criterion in config["criteria"]:
            check_method = criterion.get("check_method")

            if check_method == "keyword_presence" or check_method == "keyword_absence":
                delta, detail = self.score_pattern_match(response, criterion)
            elif check_method == "length_validation":
                delta, detail = self.score_length_validation(response, criterion)
            elif check_method == "word_count_validation":
                delta, detail = self.score_word_count_validation(response, criterion)
            elif check_method == "code_validation":
                delta, detail = self.score_code_validation(response, criterion)
            elif check_method in ["readability_score", "readability_mention"]:
                delta, detail = self.score_pattern_match(response, criterion)
            else:
                delta, detail = (
                    0,
                    f"⚠ {criterion.get('name', 'Unknown')}: Check-Methode '{check_method}' nicht implementiert",
                )

            score += delta
            details.append(detail)

        return round(score, 2), details

    # ============================================================
    # HELPER METHODS: Formatting
    # ============================================================

    def score_table_criterion(
        self, response: str, criterion: Dict
    ) -> Tuple[float, str]:
        """Bewertet Tabellen-Formatierung."""
        points = criterion["points"]

        has_table = "|" in response and "-" in response
        table_rows = len(
            [
                line
                for line in response.split("\n")
                if line.count("|") >= MIN_TABLE_COLUMNS
            ]
        )
        min_rows = criterion.get("min_rows", DEFAULT_MIN_TABLE_ROWS)

        if has_table and table_rows >= min_rows:
            return points, f"✓ {criterion['name']}: {table_rows} Zeilen ({points}p)"
        elif has_table:
            partial = (table_rows / min_rows) * points
            return (
                partial,
                f"⚠ {criterion['name']}: {table_rows}/{min_rows} Zeilen ({partial:.1f}p)",
            )
        else:
            return 0, f"✗ {criterion['name']}: Keine Tabelle gefunden"

    def score_structure_validation(
        self, response: str, criterion: Dict
    ) -> Tuple[float, str]:
        """Prüft ob erforderliche Strukturelemente vorhanden sind."""
        points = criterion["points"]
        required_structure = criterion.get("required_structure", [])

        found = [
            elem for elem in required_structure if elem.lower() in response.lower()
        ]

        if len(found) == len(required_structure):
            return (
                points,
                f"✓ {criterion['name']}: Alle Strukturelemente vorhanden ({points}p)",
            )
        else:
            missing = set(required_structure) - set(found)
            return 0, f"✗ {criterion['name']}: Fehlende Elemente: {', '.join(missing)}"

    def score_regex_criterion(
        self, response: str, criterion: Dict
    ) -> Tuple[float, str]:
        """Bewertet Regex-Matches (z.B. WCAG-Referenzen)."""
        points = criterion["points"]
        pattern = criterion.get("check_pattern", r"\d\.\d\.\d")

        matches = re.findall(pattern, response)
        count_unique = criterion.get("count_unique", True)
        count = len(set(matches)) if count_unique else len(matches)
        min_required = criterion.get("min_occurrences", 4)

        if count >= min_required:
            return points, f"✓ {criterion['name']}: {count} Treffer ({points}p)"
        else:
            partial = (count / min_required) * points
            return (
                partial,
                f"⚠ {criterion['name']}: {count}/{min_required} Treffer ({partial:.1f}p)",
            )

    def score_formatting(
        self, response: str, response_lower: str, config: Dict
    ) -> Tuple[float, List[str]]:
        """
        Bewertet Formatierung (10-20 Punkte)
        Prüft Tabellen, Strukturierung, Code-Beispiele

        Returns:
            (score, details_list)
        """
        score = 0
        details = []

        for criterion in config["criteria"]:
            check_method = criterion.get("check_method")

            if check_method == "markdown_table_validation":
                delta, detail = self.score_table_criterion(response, criterion)
            elif check_method == "structure_validation":
                delta, detail = self.score_structure_validation(response, criterion)
            elif check_method == "keyword_presence":
                delta, detail = self.score_pattern_match(response, criterion)
            elif check_method == "regex":
                delta, detail = self.score_regex_criterion(response, criterion)
            elif check_method == "code_validation":
                delta, detail = self.score_code_validation(response, criterion)
            else:
                delta, detail = (
                    0,
                    f"⚠ {criterion.get('name', 'Unknown')}: Check-Methode '{check_method}' nicht implementiert",
                )

            score += delta
            details.append(detail)

        return round(score, 2), details

    # ============================================================
    # HELPER METHODS: Expertise
    # ============================================================

    def score_expertise(
        self, response: str, response_lower: str, config: Dict
    ) -> Tuple[float, List[str]]:
        """
        Bewertet Fachkompetenz (15-20 Punkte)
        Prüft UX-Writing-Prinzipien, Best Practices, Kontext-Bewusstsein

        Returns:
            (score, details_list)
        """
        score = 0
        details = []

        for criterion in config["criteria"]:
            check_method = criterion.get("check_method")

            if check_method == "keyword_presence":
                delta, detail = self.score_pattern_match(response, criterion)
            elif check_method == "context_awareness":
                # Check for context indicators
                indicators = criterion.get("indicators", [])
                found = sum(1 for ind in indicators if ind in response_lower)
                min_required = criterion.get("min_indicators", 2)
                points = criterion["points"]

                if found >= min_required:
                    delta = points
                    detail = f"✓ {criterion['name']}: {found}/{len(indicators)} Context-Indikatoren ({points}p)"
                else:
                    delta = 0
                    detail = f"✗ {criterion['name']}: {found}/{min_required} Context-Indikatoren"
            else:
                delta, detail = (
                    0,
                    f"⚠ {criterion.get('name', 'Unknown')}: Check-Methode '{check_method}' nicht implementiert",
                )

            score += delta
            details.append(detail)

        return round(score, 2), details

    # ============================================================
    # HELPER METHODS: Issue Checking
    # ============================================================

    def check_issue_mentioned(self, response_lower: str, keywords: List[str]) -> bool:
        """
        Prüft ob ein Issue in der Response erwähnt wurde.
        Nutzt Hybrid-Ansatz: String-Matching + Semantic Similarity

        Logik:
        1. Exakter Match von WCAG-Nummern (sehr spezifisch)
        2. String-Matching (mind. 40% der Keywords)
        3. Semantic Similarity Fallback (wenn String-Match fehlschlägt)

        Args:
            response_lower: Response in Kleinbuchstaben
            keywords: Liste von Suchbegriffen

        Returns:
            True wenn Issue wahrscheinlich erkannt wurde
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
            s.strip() for s in response_lower.split(".") if len(s.strip()) > 20
        ]

        # Wenn keine Sätze gefunden, nutze Chunks
        if not sentences:
            sentences = [
                response_lower[i : i + 200] for i in range(0, len(response_lower), 200)
            ]

        # Suche besten Match
        best_score = SemanticSimilarity.find_best_match(query, sentences)

        # Threshold 0.65 (experimentell ermittelt für MiniLM)
        return best_score > 0.65
