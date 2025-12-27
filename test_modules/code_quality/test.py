#!/usr/bin/env python3
"""
Code Quality Test Module - WCAG 2.2 Accessibility Audit
Erweiterte Version mit vollständigem Scoring für 11 Issues
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import re
import time

# Ensure root directory is in sys.path for imports
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from test_modules.base_test import BaseTest
from utils.similarity import SemanticSimilarity

# Constants for scoring thresholds
MIN_TABLE_COLUMNS = 2  # Minimum pipes for table detection
DEFAULT_MIN_TABLE_ROWS = 8  # Default minimum rows for complete table
DEFAULT_MIN_KEYWORDS = 3  # Default minimum keywords to match


class CodeQualityTest(BaseTest):
    """
    Test-Modul für Code-Qualität und Accessibility

    Features:
    - Erkennung von 11 WCAG-Issues (5 Critical, 3 High, 4 Medium)
    - Bonus-Punkte für Edge-Cases
    - Lösungsqualitäts-Bewertung (Quick Fix + Best Practice)
    - Formatierungs-Checks (Tabellen, Code-Blöcke)
    - Fachkompetenz-Bewertung (WCAG 2.2, AT, Tools)
    """

    def execute(self, model: str, llm_client, provider: str = 'ollama') -> Dict:
        """
        Führt WCAG-Audit-Test aus

        Args:
            model: LLM-Modell (z.B. "qwen2.5:14b")
            llm_client: LLMClient-Instanz
            provider: Provider (ollama, mistral, anthropic, openai)

        Returns:
            Dict mit raw_response, execution_time, tokens_used, metadata
        """
        prompt = self.asset['prompt']

        # Context hinzufügen falls vorhanden
        if 'context' in self.asset:
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
                'raw_response': response,
                'execution_time': elapsed,
                'tokens_used': approx_tokens,
                'metadata': {
                    'model': model,
                    'asset_id': self.asset['metadata']['id'],
                    'prompt_length': len(full_prompt)
                }
            }
        except Exception as e:
            return {
                'raw_response': f"ERROR: {str(e)}",
                'execution_time': 0.0,
                'tokens_used': 0,
                'metadata': {
                    'model': model,
                    'error': str(e)
                }
            }

    def score_response(self, response: str) -> Dict:
        """
        Bewertet WCAG-Audit-Antwort nach Asset-Scoring-Kriterien

        Scoring-Kategorien:
        1. Fehlererkennung (45 Punkte)
        2. Lösungsqualität (30 Punkte)
        3. Formatierung (15 Punkte)
        4. Fachkompetenz (10 Punkte)

        Returns:
            Dict mit total_score, category_scores, details, violations
        """
        if not response or response.startswith("ERROR:"):
            return {
                'status': 'error',
                'total_score': 0,
                'max_score': 100,
                'category_scores': {},
                'details': ["Keine gültige Response erhalten"],
                'violations': ["Test konnte nicht ausgeführt werden"]
            }

        scoring_config = self.asset['scoring']
        total_possible = scoring_config['total_points']

        category_scores = {}
        details = []
        violations = []
        total_achieved = 0

        response_lower = response.lower()

        # ===== KATEGORIE 1: Fehlererkennung (45 Punkte) =====
        ed_score, ed_details, ed_violations = self._score_error_detection(
            response, response_lower, scoring_config['error_detection']
        )
        category_scores['error_detection'] = {
            'achieved': ed_score,
            'max': scoring_config['error_detection']['weight']
        }
        details.extend(ed_details)
        violations.extend(ed_violations)
        total_achieved += ed_score

        # ===== KATEGORIE 2: Lösungsqualität (30 Punkte) =====
        sq_score, sq_details = self._score_solution_quality(
            response, response_lower, scoring_config['solution_quality']
        )
        category_scores['solution_quality'] = {
            'achieved': sq_score,
            'max': scoring_config['solution_quality']['weight']
        }
        details.extend(sq_details)
        total_achieved += sq_score

        # ===== KATEGORIE 3: Formatierung (15 Punkte) =====
        fmt_score, fmt_details = self._score_formatting(
            response, response_lower, scoring_config['formatting']
        )
        category_scores['formatting'] = {
            'achieved': fmt_score,
            'max': scoring_config['formatting']['weight']
        }
        details.extend(fmt_details)
        total_achieved += fmt_score

        # ===== KATEGORIE 4: Fachkompetenz (Optional) =====
        if 'expertise' in scoring_config:
            exp_score, exp_details = self._score_expertise(
                response, response_lower, scoring_config['expertise']
            )
            category_scores['expertise'] = {
                'achieved': exp_score,
                'max': scoring_config['expertise']['weight']
            }
            details.extend(exp_details)
            total_achieved += exp_score
        else:
            category_scores['expertise'] = {'achieved': 0, 'max': 0}

        return {
            'status': 'success',
            'total_score': round(total_achieved, 2),
            'max_score': total_possible,
            'category_scores': category_scores,
            'details': details,
            'violations': violations
        }

    def _check_and_score_issue(
        self, 
        response_lower: str, 
        issue: Dict, 
        severity: str
    ) -> Tuple[float, Optional[str], Optional[str]]:
        """
        Hilfsfunktion: Prüft ein einzelnes Issue und gibt Score/Details zurück.
        
        Returns:
            (score_delta, detail_msg, violation_msg)
        """
        found = self._check_issue_mentioned(response_lower, issue['keywords'])
        extra_info = f" (WCAG {issue['wcag']})" if 'wcag' in issue else ""
        
        if found:
            detail = f"✓ {severity} erkannt: {issue['issue']}{extra_info}, +{issue['points']}p"
            return issue['points'], detail, None
        elif severity == "Medium":
            detail = f"○ Medium fehlt: {issue['issue']}{extra_info}"
            return 0, detail, None
        else:
            violation_prefix = "✗" if severity == "Critical" else "~"
            violation = f"{violation_prefix} {severity} fehlt: {issue['issue']}{extra_info}, -{issue['points']}p"
            return 0, None, violation

    def _calculate_bonus_score(
        self,
        response_lower: str,
        config: Dict,
        details: List[str]
    ) -> int:
        """Berechnet Bonus-Punkte für zusätzlich gefundene Issues."""
        bonus_count = 0
        bonus_max = config.get('max_bonus', 5)
        bonus_issues = config.get('bonus_issues', [])
        
        for bonus_issue in bonus_issues:
            keywords = bonus_issue.lower().split()[:3]
            if any(kw in response_lower for kw in keywords):
                bonus_count += 1
                if bonus_count <= bonus_max:
                    details.append(
                        f"✓ Bonus: {bonus_issue} "
                        f"(+{config['bonus_points_each']}p)"
                    )
        
        if bonus_count > 0:
            details.append(
                f"  → Bonus Total: {min(bonus_count, bonus_max)} Issues gefunden"
            )
        
        return min(bonus_count, bonus_max) * config.get('bonus_points_each', 1)

    def _score_error_detection(
        self, 
        response: str, 
        response_lower: str, 
        config: Dict
    ) -> Tuple[int, List[str], List[str]]:
        """
        Bewertet Fehlererkennung (45 Punkte)

        Returns:
            (score, details_list, violations_list)
        """
        score = 0
        details = []
        violations = []
        max_score = config['weight']

        # Dynamic Issue Scoring: Iterate over all keys ending in '_issues'
        # This supports both old (critical_issues) and new (labeled_issues) formats
        for key, issues_list in config.items():
            if key.endswith('_issues') and key != 'bonus_issues' and isinstance(issues_list, list):
                # Derive category name (e.g. "critical_issues" -> "Critical")
                category_name = key.replace('_issues', '').replace('_', ' ').title()
                
                for issue in issues_list:
                    delta, detail, violation = self._check_and_score_issue(
                        response_lower, issue, category_name
                    )
                    score += delta
                    if detail:
                        details.append(detail)
                    if violation:
                        violations.append(violation)

        # === BONUS Issues (1 Punkt pro Issue, max 5 Punkte) ===
        bonus_score = self._calculate_bonus_score(response_lower, config, details)
        score += bonus_score

        # Cap bei max_score
        score = min(score, max_score)

        return score, details, violations

    def _score_pattern_match(
        self, 
        response: str, 
        criterion: Dict
    ) -> Tuple[float, str]:
        """
        Hilfsfunktion: Bewertet Pattern-basierte Kriterien (SQ-001, SQ-002).
        
        Returns:
            (score_delta, detail_msg)
        """
        pattern = criterion.get('check_pattern', r'')
        matches = len(re.findall(pattern, response))
        min_required = criterion.get('min_occurrences', 6)
        points = criterion['points']
        
        if matches >= min_required:
            return points, f"✓ {criterion['name']}: {matches}/{min_required} (+{points}p)"
        else:
            partial = (matches / min_required) * points
            return partial, f"~ {criterion['name']}: {matches}/{min_required} ({partial:.1f}/{points}p)"

    def _score_solution_quality(
        self, 
        response: str, 
        response_lower: str, 
        config: Dict
    ) -> Tuple[float, List[str]]:
        """
        Bewertet Lösungsqualität (30 Punkte)

        Prüft:
        - Quick Fixes vorhanden
        - Best Practices vorhanden
        - Code-Beispiele syntaktisch korrekt
        - Moderne Web-Standards genutzt

        Returns:
            (score, details_list)
        """
        score = 0
        details = []

        for criterion in config['criteria']:
            check_method = criterion.get('check_method')
            points = criterion['points']

            if check_method == "regex":  # Quick Fixes / Best Practices
                delta, detail = self._score_pattern_match(response, criterion)
                score += delta
                details.append(detail)

            elif check_method == "code_validation":  # Code-Beispiele
                required_elements = criterion.get('required_elements', [])
                total_blocks = 0
                details_parts = []

                if required_elements:
                    for elem in required_elements:
                        # Remove comments if present in YAML list item (though YAML parser handles that usually)
                        # But here elem is just the string like "```html"
                        count = response.count(elem)
                        total_blocks += count
                        details_parts.append(f"{count} {elem.replace('```', '').strip()}")
                else:
                    # Fallback: Check pattern if no required_elements
                    pattern = criterion.get('check_pattern')
                    if pattern:
                        total_blocks = response.count(pattern)
                        details_parts.append(f"{total_blocks} {pattern.replace('```', '').strip()}")

                min_required = criterion.get('min_code_blocks', 10)

                if total_blocks >= min_required:
                    score += points
                    details.append(
                        f"✓ {criterion['name']}: {total_blocks} Code-Blöcke "
                        f"({', '.join(details_parts)}) (+{points}p)"
                    )
                else:
                    partial = (total_blocks / min_required) * points
                    score += partial
                    details.append(
                        f"~ {criterion['name']}: {total_blocks}/{min_required} "
                        f"({partial:.1f}/{points}p)"
                    )

            elif check_method == "keyword_presence":  # Moderne Web-Standards
                keywords = criterion.get('keywords', [])
                found_keywords = [
                    kw for kw in keywords 
                    if kw.lower() in response_lower
                ]
                min_required = criterion.get('min_keywords', 4)

                if len(found_keywords) >= min_required:
                    score += points
                    details.append(
                        f"✓ {criterion['name']}: {len(found_keywords)}/{min_required} "
                        f"({', '.join(found_keywords[:3])}) (+{points}p)"
                    )
                else:
                    details.append(
                        f"~ {criterion['name']}: {len(found_keywords)}/{min_required} "
                        f"({', '.join(found_keywords) if found_keywords else 'keine'})"
                    )

        return round(score, 2), details

    def _score_table_criterion(
        self, 
        response: str, 
        criterion: Dict
    ) -> Tuple[float, str]:
        """Bewertet Tabellen-Formatierung."""
        points = criterion['points']
        has_table = '|' in response and '-|' in response
        table_rows = len([
            line for line in response.split('\n') 
            if line.count('|') >= MIN_TABLE_COLUMNS
        ])
        min_rows = criterion.get('min_rows', DEFAULT_MIN_TABLE_ROWS)

        if has_table and table_rows >= min_rows:
            return points, f"✓ {criterion['name']}: {table_rows} Zeilen (+{points}p)"
        elif has_table:
            partial = (table_rows / min_rows) * points
            return partial, f"~ {criterion['name']}: {table_rows}/{min_rows} Zeilen ({partial:.1f}/{points}p)"
        else:
            return 0, f"✗ {criterion['name']}: Keine Tabelle gefunden"

    def _score_severity_criterion(
        self, 
        response_lower: str, 
        criterion: Dict
    ) -> Tuple[float, str]:
        """Bewertet Severity-Level Keywords."""
        points = criterion['points']
        keywords = criterion.get('keywords', [])
        found = sum(1 for kw in keywords if kw in response_lower)
        min_required = criterion.get('min_keywords', DEFAULT_MIN_KEYWORDS)

        if found >= min_required:
            return points, f"✓ {criterion['name']}: {found}/{len(keywords)} Severity-Level (+{points}p)"
        else:
            return 0, f"~ {criterion['name']}: {found}/{min_required} Severity-Level"

    def _score_wcag_references(
        self, 
        response: str, 
        criterion: Dict
    ) -> Tuple[float, str]:
        """Bewertet Regex-Matches (z.B. WCAG-Referenzen)."""
        points = criterion['points']
        pattern = criterion.get('check_pattern', r'\b[1-4]\.\d{1,2}\.\d{1,2}\b')
        matches = re.findall(pattern, response)
        
        count_unique = criterion.get('count_unique', True)
        count = len(set(matches)) if count_unique else len(matches)
        
        min_required = criterion.get('min_occurrences', 8)
        if 'min_items' in criterion:
            min_required = criterion['min_items']

        if count >= min_required:
            return points, f"✓ {criterion['name']}: {count} Treffer (+{points}p)"
        else:
            partial = (count / min_required) * points
            return partial, f"~ {criterion['name']}: {count}/{min_required} Treffer ({partial:.1f}/{points}p)"

    def _score_testing_checklist(
        self, 
        response: str,
        response_lower: str, 
        criterion: Dict
    ) -> Tuple[float, str]:
        """Bewertet Testing-Checkliste."""
        points = criterion['points']
        section_keywords = criterion.get('section_keywords', [])
        has_test_section = any(kw in response_lower for kw in section_keywords)
        
        list_items = len(re.findall(r'^[-*]\s+|^\d+\.\s+', response, re.MULTILINE))
        min_items = criterion.get('min_items', 5)

        if has_test_section and list_items >= min_items:
            return points, f"✓ {criterion['name']}: {list_items} Punkte (+{points}p)"
        elif list_items > 0:
            return 0, f"~ {criterion['name']}: {list_items} Listenelemente (Test-Section: {has_test_section})"
        else:
            return 0, f"✗ {criterion['name']}: Nicht gefunden"

    def _score_formatting(
        self, 
        response: str, 
        response_lower: str, 
        config: Dict
    ) -> Tuple[float, List[str]]:
        """
        Bewertet Formatierung (10 Punkte)

        Prüft:
        - Strukturierte Tabelle
        - Severity-Level Markierungen
        - WCAG-Referenzen
        - Testing-Checkliste

        Returns:
            (score, details_list)
        """
        score = 0
        details = []

        for criterion in config['criteria']:
            check_method = criterion.get('check_method')

            if check_method == "markdown_table_validation":  # Tabelle
                delta, detail = self._score_table_criterion(response, criterion)
            elif check_method == "keyword_presence":  # Severity
                delta, detail = self._score_severity_criterion(response_lower, criterion)
            elif check_method == "regex":  # WCAG-Referenzen
                delta, detail = self._score_wcag_references(response, criterion)
            elif check_method == "list_detection":  # Testing-Checkliste
                delta, detail = self._score_testing_checklist(response, response_lower, criterion)
            else:
                continue
            
            score += delta
            details.append(detail)

        return round(score, 2), details

    def _score_expertise(
        self, 
        response: str, 
        response_lower: str, 
        config: Dict
    ) -> Tuple[float, List[str]]:
        """
        Bewertet Fachkompetenz (10 Punkte)

        Prüft:
        - WCAG 2.2 neue Kriterien
        - Assistive Technology Kenntnisse
        - Testing-Tools Empfehlungen
        - Business-Kontext Verständnis

        Returns:
            (score, details_list)
        """
        score = 0
        details = []

        for criterion in config['criteria']:
            check_method = criterion.get('check_method')
            points = criterion['points']

            if check_method == "keyword_presence":  # Keyword-basiert
                keywords = criterion.get('keywords', [])
                found_keywords = [
                    kw for kw in keywords 
                    if kw.lower() in response_lower
                ]
                min_required = criterion.get('min_keywords', 2)

                if len(found_keywords) >= min_required:
                    score += points
                    details.append(
                        f"✓ {criterion['name']}: "
                        f"{', '.join(found_keywords[:3])} (+{points}p)"
                    )
                else:
                    details.append(
                        f"~ {criterion['name']}: {len(found_keywords)}/{min_required} "
                        f"({', '.join(found_keywords) if found_keywords else 'keine'})"
                    )

            elif check_method == "context_awareness":  # Business-Kontext
                indicators = criterion.get('indicators', [])
                found = sum(1 for ind in indicators if ind in response_lower)
                min_required = criterion.get('min_indicators', 2)

                if found >= min_required:
                    score += points
                    details.append(
                        f"✓ {criterion['name']}: {found}/{len(indicators)} "
                        f"Context-Indikatoren (+{points}p)"
                    )
                else:
                    details.append(
                        f"~ {criterion['name']}: {found}/{min_required} "
                        f"Context-Indikatoren"
                    )

        return round(score, 2), details

    def _check_issue_mentioned(
        self, 
        response_lower: str, 
        keywords: List[str]
    ) -> bool:
        """
        Prüft ob ein Issue in der Response erwähnt wurde.
        Nutzt Hybrid-Ansatz: String-Matching + Semantic Similarity.

        Logik:
        1. Exakter Match von WCAG-Nummern (sehr spezifisch)
        2. String-Matching (mind. 40% der Keywords)
        3. Semantic Similarity (Fallback, wenn String-Match fehlschlägt)

        Args:
            response_lower: Response in Kleinbuchstaben
            keywords: Liste von Suchbegriffen

        Returns:
            True wenn Issue wahrscheinlich erkannt wurde
        """
        if not keywords:
            return False

        # 1. WCAG Nummer Check (Regex)
        has_wcag_number = any(re.match(r'\d\.\d\.\d', kw) for kw in keywords)
        if has_wcag_number:
            # Wenn WCAG Nummer im Text vorkommt -> Treffer
            for kw in keywords:
                if re.match(r'\d\.\d\.\d', kw) and kw in response_lower:
                    return True

        # 2. String Matching (Keyword Count)
        matches = sum(1 for kw in keywords if kw.lower() in response_lower)
        required_ratio = 0.4
        required_matches = max(1, int(len(keywords) * required_ratio))
        
        if matches >= required_matches:
            return True

        # 3. Semantic Similarity (Fallback)
        # Wir prüfen, ob der Kern des Issues (aus den Keywords gebildet) im Text vorkommt.
        # Da wir nicht den ganzen Text embedden wollen (zu langsam/groß),
        # suchen wir nach Sätzen, die relevant sein könnten.
        # Vereinfachung: Wir vergleichen die Keywords als "Satz" mit dem Text.
        
        # Konstruiere eine "Query" aus den Keywords
        query = " ".join(keywords)
        
        # Splitte Response in Sätze (grob)
        sentences = [s.strip() for s in response_lower.split('.') if len(s.strip()) > 20]
        
        # Wenn keine Sätze gefunden, nutze Chunks
        if not sentences:
            sentences = [response_lower[i:i+200] for i in range(0, len(response_lower), 200)]
            
        # Suche besten Match
        best_score = SemanticSimilarity.find_best_match(query, sentences)
        
        # Threshold: 0.65 (experimentell ermittelt für MiniLM)
        return best_score >= 0.65
