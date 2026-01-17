#!/usr/bin/env python3
"""
Code Quality Test Module
Refactored using Facade Pattern and specialized private scoring methods.
Uses benchmark_modules.code_quality.constants for configuration.
"""

import sys
import time
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure root directory is in sys.path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmark_modules.base_test import BaseTest
from benchmark_modules.code_quality.constants import (
    DEFAULT_TEMPERATURE,
    TOKEN_MULTIPLIER,
    MIN_TABLE_COLUMNS,
    DEFAULT_MIN_TABLE_ROWS,
    DEFAULT_MIN_KEYWORDS,
    MIN_SENTENCE_LENGTH,
    SIMILARITY_THRESHOLD,
    PATTERN_CODE_BLOCK,
    ERROR_INVALID_RESPONSE,
    ERROR_TEST_FAILED
)
from utils.similarity import SemanticSimilarity


class CodeQualityTest(BaseTest):
    """
    Test-Modul für Code-Qualität und Accessibility
    
    Architecture:
    - Facade Pattern via score_response() delegating to specific private scorers.
    - Configuration driven via assets/yaml and constants.py.
    """

    def execute(self, model: str, llm_client: Any, provider: str = 'ollama') -> Dict[str, Any]:
        """
        Führt den Code Quality Test aus.
        """
        prompt = self.asset['prompt']
        full_prompt = f"{self.asset.get('context', '')}\n\n{prompt}".strip()

        start = time.time()

        try:
            # Deterministic output via low temperature
            response = llm_client.query(
                model, 
                full_prompt, 
                provider=provider, 
                temperature=DEFAULT_TEMPERATURE
            )
            elapsed = time.time() - start

            approx_tokens = int(len(response.split()) * TOKEN_MULTIPLIER)

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

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Facade Method: Main Scoring Logic
        
        Delegates to:
        - _score_error_detection (45-60 pts)
        - _score_solution_quality (30 pts)
        - _score_formatting (10-15 pts)
        - _score_expertise (Optional 10 pts)
        """
        # Clean reasoning tags (e.g. DeepSeek <think>) before scoring
        clean_response = self._clean_reasoning_tags(response)
        
        if not clean_response or clean_response.startswith("ERROR:"):
            return {
                'status': 'error',
                'total_score': 0,
                'max_score': 100,
                'category_scores': {},
                'details': [ERROR_INVALID_RESPONSE],
                'violations': [ERROR_TEST_FAILED]
            }

        scoring_config = self.asset['scoring']
        total_possible = scoring_config.get('total_points', 100)
        
        category_scores = {}
        details = []
        violations = []
        total_achieved: float = 0.0

        response_lower = clean_response.lower()

        # 1. Error Detection
        ed_conf = scoring_config.get('error_detection', {})
        ed_score, ed_details, ed_violations = self._score_error_detection(
            clean_response, response_lower, ed_conf
        )
        category_scores['error_detection'] = {
            'achieved': ed_score,
            'max': ed_conf.get('weight', 0)
        }
        details.extend(ed_details)
        violations.extend(ed_violations)
        total_achieved += ed_score

        # 2. Solution Quality
        sq_conf = scoring_config.get('solution_quality', {})
        sq_score, sq_details = self._score_solution_quality(
            clean_response, response_lower, sq_conf
        )
        category_scores['solution_quality'] = {
            'achieved': sq_score,
            'max': sq_conf.get('weight', 0)
        }
        details.extend(sq_details)
        total_achieved += sq_score

        # 3. Formatting
        fmt_conf = scoring_config.get('formatting', {})
        fmt_score, fmt_details = self._score_formatting(
            clean_response, response_lower, fmt_conf
        )
        category_scores['formatting'] = {
            'achieved': fmt_score,
            'max': fmt_conf.get('weight', 0)
        }
        details.extend(fmt_details)
        total_achieved += fmt_score

        # 4. Expertise (Optional)
        if 'expertise' in scoring_config:
            exp_conf = scoring_config['expertise']
            exp_score, exp_details = self._score_expertise(clean_response, response_lower, exp_conf)
            category_scores['expertise'] = {
                'achieved': exp_score,
                'max': exp_conf.get('weight', 0)
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

    # =========================================================================
    # Private Scoring Methods (Specialized Strategies)
    # =========================================================================

    def _score_error_detection(
        self, 
        response: str, 
        response_lower: str, 
        config: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Scoring strategy for Error Detection."""
        score = 0.0
        details = []
        violations = []
        max_score = config.get('weight', 0)

        # Dynamic Issue Iteration (supports tiered issues: labeled, standard, etc.)
        for key, issues_list in config.items():
            if key.endswith('_issues') and key != 'bonus_issues' and isinstance(issues_list, list):
                category_name = key.replace('_issues', '').replace('_', ' ').title()
                
                for issue in issues_list:
                    severity = category_name # e.g. "Critical", "Labeled"
                    found = self._check_issue_mentioned(response_lower, issue.get('keywords', []))
                    
                    points = issue.get('points', 0)
                    extra_info = f" (WCAG {issue['wcag']})" if 'wcag' in issue else ""
                    issue_name = issue.get('issue', 'Unknown Issue')

                    if found:
                        score += points
                        details.append(f"✓ {severity} erkannt: {issue_name}{extra_info}, +{points}p")
                    elif severity in ["Critical", "Labeled", "Standard"]: 
                        prefix = "✗" if severity in ["Critical", "Labeled"] else "~"
                        err_msg = f"{prefix} {severity} fehlt: {issue_name}{extra_info}, -{points}p"
                        if severity == "Critical":
                             violations.append(err_msg)
                        else:
                             # For non-critical missing issues we used to show generic warning
                             if severity == "Medium":
                                 details.append(f"○ Medium fehlt: {issue_name}{extra_info}")
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

    def _score_solution_quality(
        self, 
        response: str, 
        response_lower: str, 
        config: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """Scoring strategy for Solution Quality."""
        score = 0.0
        details = []
        
        criteria = config.get('criteria', [])
        for criterion in criteria:
            check_method = criterion.get('check_method')
            points = criterion.get('points', 0)
            
            if check_method == "regex":
                delta, detail = self._score_pattern_match(response, criterion)
                score += delta
                details.append(detail)
            
            elif check_method == "code_validation":
                delta, detail = self._score_code_validation(response, criterion)
                score += delta
                details.append(detail)
                
            elif check_method == "keyword_presence":
                delta, detail = self._score_keyword_presence(response_lower, criterion)
                score += delta
                details.append(detail)

        return round(score, 2), details

    def _score_formatting(
        self, 
        response: str, 
        response_lower: str, 
        config: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """Scoring strategy for Formatting."""
        score = 0.0
        details = []
        
        criteria = config.get('criteria', [])
        for criterion in criteria:
            check_method = criterion.get('check_method')
            
            if check_method == "markdown_table_validation":
                delta, detail = self._score_table_criterion(response, criterion)
            elif check_method == "keyword_presence": 
                delta, detail = self._score_severity_criterion(response_lower, criterion)
            elif check_method == "regex": 
                delta, detail = self._score_wcag_references(response, criterion)
            elif check_method == "list_detection":
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
        config: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """Scoring strategy for Expertise."""
        score = 0.0
        details = []
        
        criteria = config.get('criteria', [])
        for criterion in criteria:
            check_method = criterion.get('check_method')
            points = criterion.get('points', 0)
            
            if check_method == "keyword_presence":
                delta, detail = self._score_keyword_presence(response_lower, criterion)
                score += delta
                details.append(detail)
            elif check_method == "context_awareness":
                indicators = criterion.get('indicators', [])
                found = sum(1 for ind in indicators if ind in response_lower)
                min_req = criterion.get('min_indicators', 2)
                
                if found >= min_req:
                    score += points
                    details.append(f"✓ {criterion['name']}: {found}/{len(indicators)} Context-Indikatoren (+{points}p)")
                else:
                    details.append(f"~ {criterion['name']}: {found}/{min_req} Context-Indikatoren")
                    
        return round(score, 2), details

    # =========================================================================
    # Helper Methods (Low-Level Logic)
    # =========================================================================

    def _check_issue_mentioned(self, response_lower: str, keywords: List[str]) -> bool:
        """Prüft ob ein Issue erkannt wurde (Regex -> Keyword -> Semantic)."""
        if not keywords: 
            return False

        # 1. Regex Match (e.g. WCAG Numbers)
        has_wcag = any(re.match(r'\d\.\d\.\d', kw) for kw in keywords)
        if has_wcag:
            for kw in keywords:
                if re.match(r'\d\.\d\.\d', kw) and kw in response_lower:
                    return True

        # 2. Strict Keyword Matching
        matches = sum(1 for kw in keywords if kw.lower() in response_lower)
        req_ratio = 0.4
        req_matches = max(1, int(len(keywords) * req_ratio))
        
        if matches >= req_matches:
            return True

        # 3. Semantic Similarity Fallback
        query = " ".join(keywords)
        sentences = [s.strip() for s in response_lower.split('.') if len(s.strip()) > MIN_SENTENCE_LENGTH]
        if not sentences:
            sentences = [response_lower[i:i+200] for i in range(0, len(response_lower), 200)]
            
        best_score = SemanticSimilarity.find_best_match(query, sentences)
        return best_score >= SIMILARITY_THRESHOLD

    def _calculate_bonus_score(self, response_lower: str, config: Dict[str, Any], details: List[str]) -> int:
        """Scores optional bonus issues."""
        bonus_count = 0
        bonus_max = config.get('max_bonus', 5)
        bonus_points_each = config.get('bonus_points_each', 1)
        
        for issue_txt in config.get('bonus_issues', []):
            kws = issue_txt.lower().split()[:3]
            if any(kw in response_lower for kw in kws):
                bonus_count += 1
                if bonus_count <= bonus_max:
                    details.append(f"✓ Bonus: {issue_txt} (+{bonus_points_each}p)")
        
        if bonus_count > 0:
            details.append(f"  → Bonus Total: {min(bonus_count, bonus_max)} Issues gefunden")
            
        return min(bonus_count, bonus_max) * bonus_points_each

    def _score_pattern_match(self, response: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        """Generic Regex Pattern Matcher."""
        pattern = criterion.get('check_pattern', r'')
        matches = len(re.findall(pattern, response))
        min_req = criterion.get('min_occurrences', 6)
        points = criterion.get('points', 0)
        name = criterion.get('name', 'Unknown')

        if matches >= min_req:
            return points, f"✓ {name}: {matches}/{min_req} (+{points}p)"
        else:
            partial = (matches / min_req) * points
            return partial, f"~ {name}: {matches}/{min_req} ({partial:.1f}/{points}p)"

    def _score_code_validation(self, response: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        """Validates code blocks presence."""
        required = criterion.get('required_elements', [])
        total = 0
        parts = []
        name = criterion.get('name', 'Code Validation')
        points = criterion.get('points', 0)

        if required:
            for elem in required:
                # Assuming elem is simple string, no complex regex here for now
                count = response.count(elem)
                total += count
                parts.append(f"{count} {elem.replace('```', '').strip()}")
        else:
            pattern = criterion.get('check_pattern')
            if pattern:
                total = response.count(pattern)
                parts.append(f"{total} {pattern.replace('```', '').strip()}")
        
        min_req = criterion.get('min_code_blocks', 10)
        
        if total >= min_req:
            return points, f"✓ {name}: {total} Code-Blöcke ({', '.join(parts)}) (+{points}p)"
        else:
            partial = (total / min_req) * points
            return partial, f"~ {name}: {total}/{min_req} ({partial:.1f}/{points}p)"

    def _score_keyword_presence(self, response_lower: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        """Generic Keyword Counter."""
        keywords = criterion.get('keywords', [])
        found = [kw for kw in keywords if kw.lower() in response_lower]
        min_req = criterion.get('min_keywords', 4)
        points = criterion.get('points', 0)
        name = criterion.get('name', 'Keyword Check')

        if len(found) >= min_req:
            return points, f"✓ {name}: {len(found)}/{min_req} ({', '.join(found[:3])}) (+{points}p)"
        else:
            return 0, f"~ {name}: {len(found)}/{min_req} ({', '.join(found) if found else 'keine'})"

    def _score_table_criterion(self, response: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        """Validates Markdown Table structure."""
        points = criterion.get('points', 0)
        name = criterion.get('name', 'Tabelle')
        has_table = '|' in response and '-|' in response
        
        rows = [line for line in response.split('\n') if line.count('|') >= MIN_TABLE_COLUMNS]
        row_count = len(rows)
        min_rows = criterion.get('min_rows', DEFAULT_MIN_TABLE_ROWS)

        if has_table and row_count >= min_rows:
            return points, f"✓ {name}: {row_count} Zeilen (+{points}p)"
        elif has_table:
            partial = (row_count / min_rows) * points
            return partial, f"~ {name}: {row_count}/{min_rows} Zeilen ({partial:.1f}/{points}p)"
        else:
            return 0, f"✗ {name}: Keine Tabelle gefunden"

    def _score_severity_criterion(self, response_lower: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        """Specialized Keyword Scoring for Severity Levels."""
        points = criterion.get('points', 0)
        keywords = criterion.get('keywords', [])
        name = criterion.get('name', 'Severity')
        
        found = sum(1 for kw in keywords if kw in response_lower)
        min_req = criterion.get('min_keywords', DEFAULT_MIN_KEYWORDS)

        if found >= min_req:
            return points, f"✓ {name}: {found}/{len(keywords)} Severity-Level (+{points}p)"
        else:
            return 0, f"~ {name}: {found}/{min_req} Severity-Level"

    def _score_wcag_references(self, response: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        """Regex matcher for specific patterns/occurrences."""
        points = criterion.get('points', 0)
        name = criterion.get('name', 'WCAG Refs')
        pattern = criterion.get('check_pattern', r'\b[1-4]\.\d{1,2}\.\d{1,2}\b')
        
        matches = re.findall(pattern, response)
        count_unique = criterion.get('count_unique', True)
        count = len(set(matches)) if count_unique else len(matches)
        
        min_req = criterion.get('min_items', criterion.get('min_occurrences', 8))

        if count >= min_req:
            return points, f"✓ {name}: {count} Treffer (+{points}p)"
        else:
            partial = (count / min_req) * points
            return partial, f"~ {name}: {count}/{min_req} Treffer ({partial:.1f}/{points}p)"

    def _score_testing_checklist(self, response: str, response_lower: str, criterion: Dict[str, Any]) -> Tuple[float, str]:
        """Validates Testing Checklist Section."""
        points = criterion.get('points', 0)
        name = criterion.get('name', 'Checklist')
        section_kws = criterion.get('section_keywords', [])
        
        has_section = any(kw in response_lower for kw in section_kws)
        list_items = len(re.findall(r'^[-*]\s+|^\d+\.\s+', response, re.MULTILINE))
        min_items = criterion.get('min_items', 5)

        if has_section and list_items >= min_items:
            return points, f"✓ {name}: {list_items} Punkte (+{points}p)"
        elif list_items > 0:
            return 0, f"~ {name}: {list_items} Listenelemente (Test-Section: {has_section})"
        else:
            return 0, f"✗ {name}: Nicht gefunden"
