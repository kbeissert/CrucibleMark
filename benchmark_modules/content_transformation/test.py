#!/usr/bin/env python3
"""
Content Transformation & Adaption Test Module
Bewertet die Fähigkeit von LLMs, Content in verschiedene Formate und Stile zu transformieren.
"""

import sys
import time
from pathlib import Path
from typing import Any

# Ensure root directory is in sys.path for imports
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmark_modules.base_test import BaseTest  # noqa: E402

# Constants
TOKEN_MULTIPLIER = 1.3
DEFAULT_TEMPERATURE = 0.7
TIER_THRESHOLDS = {
    'labeled': 0.40,
    'standard': 0.40,
    'advanced': 0.35,
    'expert': 0.30
}


class ContentTransformationTest(BaseTest):
    """
    Test-Modul für Content Transformation & Adaption

    Scoring-System:
    - 70 Punkte: Error Detection (Labeled → Expert Issues)
      (Hier: Erkennen von fehlenden Elementen oder Stil-Verstößen im generierten Output
       bzw. Einhaltung der Transformations-Regeln)
    - 30 Punkte: Solution Quality (Struktur, Engagement, Format-Treue)
    """

    def execute(self, model: str, llm_client: Any, provider: str = 'ollama') -> dict:
        """
        Führt Content Transformation Test aus

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
            # Use specific temperature for Content Transformation - needs creativity
            response = llm_client.query(
                model,
                full_prompt,
                provider=provider,
                temperature=DEFAULT_TEMPERATURE
            )
            elapsed = time.time() - start

            # Token-Approximation
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

    def score_response(self, response: str) -> dict:
        """
        Bewertet Content Transformation Antwort nach Tiered Difficulty System

        Scoring-Kategorien:
        1. Error Detection (70 Punkte) - Tiered (Labeled → Expert)
           (Prüft ob geforderte Elemente vorhanden sind / Fehler vermieden wurden)
        2. Solution Quality (30 Punkte) - Kreativität, Flow, Format

        Args:
            response: LLM-Response als String

        Returns:
            Dict mit Score-Details
        """
        if not response or response.startswith("ERROR:"):
            return self._create_error_score("Invalid or error response")

        scoring_config = self.asset['scoring']
        total_possible = scoring_config['total_points']

        category_scores = {}
        details: list[str] = []
        violations: list[str] = []
        total_achieved: float = 0.0

        response_lower = response.lower()

        # ===== KATEGORIE 1: Error Detection (70 Punkte) =====
        ed_score, ed_details, ed_violations = self._score_error_detection(
            response_lower, scoring_config['error_detection']
        )
        category_scores['error_detection'] = {
            'achieved': ed_score,
            'max': scoring_config['error_detection']['weight']
        }
        details.extend(ed_details)
        violations.extend(ed_violations)
        total_achieved += ed_score

        # ===== KATEGORIE 2: Solution Quality (30 Punkte) =====
        sq_score, sq_details = self._score_solution_quality(
            response_lower, scoring_config['solution_quality']
        )
        category_scores['solution_quality'] = {
            'achieved': sq_score,
            'max': scoring_config['solution_quality']['weight']
        }
        details.extend(sq_details)
        total_achieved += sq_score

        return {
            'status': 'success',
            'total_score': round(total_achieved, 2),
            'max_score': total_possible,
            'percentage': round((total_achieved / total_possible) * 100, 2),
            'category_scores': category_scores,
            'details': details,
            'violations': violations,
            'metadata': {
                'response_length': len(response),
                'word_count': len(response.split())
            }
        }

    def _score_error_detection(
        self,
        response_lower: str,
        config: dict
    ) -> tuple[float, list[str], list[str]]:
        """
        Bewertet Issue Detection mit Tiered Difficulty (70 Punkte)

        Levels:
        - Labeled Issues (17.5P): Offensichtlich
        - Standard Issues (21.0P): Erkennbar
        - Advanced Issues (17.5P): Subtil
        - Expert Issues (14.0P): Best Practices

        Returns:
            (score, details_list, violations_list)
        """
        score: float = 0.0
        details: list[str] = []
        violations: list[str] = []

        # Issues sind direkt in config als labeled_issues, standard_issues, etc.
        tier_configs = {
            'labeled': ('labeled_issues', TIER_THRESHOLDS['labeled']),
            'standard': ('standard_issues', TIER_THRESHOLDS['standard']),
            'advanced': ('advanced_issues', TIER_THRESHOLDS['advanced']),
            'expert': ('expert_issues', TIER_THRESHOLDS['expert'])
        }

        # Score jede Tier-Kategorie
        for tier_name, (tier_key, default_threshold) in tier_configs.items():
            tier_issues = config.get(tier_key, [])

            if not tier_issues:
                continue

            tier_score, tier_details, tier_violations = self._score_tier_issues(
                response_lower,
                tier_issues,
                default_threshold,
                tier_name.title()
            )

            score += tier_score
            details.extend(tier_details)
            violations.extend(tier_violations)

        return round(score, 2), details, violations

    def _score_tier_issues(
        self,
        response_lower: str,
        issues: list[dict],
        min_threshold: float,
        tier_name: str
    ) -> tuple[float, list[str], list[str]]:
        """
        Bewertet eine Tier-Kategorie (z.B. Labeled, Standard, Advanced, Expert)

        Args:
            response_lower: Response in lowercase
            issues: Liste der Issues in dieser Tier
            min_threshold: Mindest-Keyword-Match-Rate (z.B. 0.40 = 40%)
            tier_name: Name der Tier (für Details)

        Returns:
            (score, details, violations)
        """
        tier_score: float = 0.0
        details: list[str] = []
        violations: list[str] = []

        if not issues:
            return 0.0, details, violations

        # Berechne max_points für diese Tier (Summe aller Issue-Points)
        tier_max_points = sum(issue.get('points', 0) for issue in issues)

        for issue in issues:
            points = issue.get('points', 0)
            keywords = issue.get('keywords', [])
            issue_name = issue.get('issue', 'Unknown Issue')
            severity = issue.get('severity', 'medium')

            # Check ob Issue erwähnt wird (Keyword-Matching)
            found = self._check_issue_mentioned(response_lower, keywords, min_threshold)

            if found:
                tier_score += points
                details.append(f"✓ [{tier_name}] {issue_name}: +{points}p")
            # Für Critical/High = Violation, sonst nur Details
            elif severity in ['critical', 'high']:
                violations.append(f"✗ [{tier_name}] {issue_name}: -{points}p")
            else:
                details.append(f"○ [{tier_name}] {issue_name}: 0p")

        # Direkter Score ohne Normalisierung (Issue-Points sind bereits korrekt)
        details.append(f"  → {tier_name} Total: {tier_score:.1f}/{tier_max_points}p")

        return round(tier_score, 2), details, violations

    def _check_issue_mentioned(
        self,
        response_lower: str,
        keywords: list[str],
        min_threshold: float = 0.40
    ) -> bool:
        """
        Prüft ob ein Issue im Response erwähnt wird (Keyword-Matching)

        Args:
            response_lower: Response in lowercase
            keywords: Liste von Keywords
            min_threshold: Mindest-Match-Rate (z.B. 0.40 = 40%)

        Returns:
            True wenn genug Keywords gefunden
        """
        if not keywords:
            return False

        matches = sum(1 for kw in keywords if kw.lower() in response_lower)
        match_rate = matches / len(keywords)

        return match_rate >= min_threshold

    def _score_solution_quality(
        self,
        response_lower: str,
        config: dict
    ) -> tuple[float, list[str]]:
        """
        Bewertet Lösungsqualität (30 Punkte)

        Kriterien:
        - Konkrete Code-Beispiele
        - Best Practices erwähnt
        - Priorisierung vorhanden

        Returns:
            (score, details_list)
        """
        score = 0.0
        details = []

        criteria = config.get('criteria', [])

        for criterion in criteria:
            name = criterion.get('name', 'Unknown')
            points = criterion.get('points', 0)
            keywords = criterion.get('keywords', [])
            check_method = criterion.get('check_method', 'keyword_presence')
            min_keywords = criterion.get('min_keywords', 1)

            if check_method == 'keyword_presence':
                # Keyword-Matching mit min_keywords threshold
                found_keywords = [kw for kw in keywords if kw.lower() in response_lower]

                if len(found_keywords) >= min_keywords:
                    # Full points if threshold met
                    earned = points
                    score += earned
                    details.append(
                        f"✓ {name}: {len(found_keywords)}/{len(keywords)} keywords found "
                        f"(min {min_keywords}) +{earned:.1f}p"
                    )
                else:
                    details.append(
                        f"○ {name}: {len(found_keywords)}/{len(keywords)} keywords "
                        f"(min {min_keywords} required)"
                    )
            else:
                # Fallback für andere check_methods
                details.append(f"○ {name}: unsupported check_method '{check_method}'")

        return round(score, 2), details

    def _create_error_score(self, error_msg: str) -> dict:
        """Erstellt einen Error-Score bei ungültiger Response."""
        return {
            'status': 'error',
            'total_score': 0,
            'max_score': 100,
            'percentage': 0,
            'category_scores': {
                'error_detection': {'achieved': 0, 'max': 70},
                'solution_quality': {'achieved': 0, 'max': 30}
            },
            'details': [error_msg],
            'violations': ['Test konnte nicht ausgeführt werden'],
            'metadata': {
                'response_length': 0,
                'word_count': 0
            },
            'error': error_msg
        }


# Example Usage
if __name__ == "__main__":
    print("Content Transformation Test Module")
    print("Verwende run_benchmark.py zum Ausführen der Tests")
