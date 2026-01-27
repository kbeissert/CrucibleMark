#!/usr/bin/env python3
"""
Documentation Quality Test Module
Bewertet Qualität von Code-Dokumentation und README-Dateien mit Tiered Difficulty System
"""

import sys
import time
import re
from pathlib import Path
from typing import Any, Dict, List

# Ensure root directory is in sys.path for imports
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmark_modules.base_test import BaseTest  # noqa: E402
from utils.similarity import SemanticSimilarity

# Constants
TOKEN_MULTIPLIER = 1.3
DEFAULT_TEMPERATURE = 0.3
TIER_THRESHOLDS = {"labeled": 0.40, "standard": 0.40, "advanced": 0.35, "expert": 0.30}
SIMILARITY_THRESHOLD = 0.70  # Lowered from 0.78 for better recall on small models
MIN_SENTENCE_LENGTH = 15

# Asset-specific configuration for fine-tuning thresholds
# Keys match the asset file stems (e.g. asset_001_readme_quality)
ASSET_SPECIFIC_CONFIG = {
    "asset_001_readme_quality": {"semantic_threshold": 0.35},
    "asset_002_rest_api_documentation": {"semantic_threshold": 0.35},
    "asset_003_component_props_documentation": {"semantic_threshold": 0.35},
    "asset_004_setup_guide_troubleshooting": {"semantic_threshold": 0.35},
    "asset_005_changelog_release_notes": {"semantic_threshold": 0.30},
}


class DocumentationTest(BaseTest):
    """
    Test-Modul für Documentation Quality mit Tiered Difficulty

    Scoring-System:
    - 70 Punkte: Error Detection (Labeled → Expert Issues)
    - 30 Punkte: Solution Quality (Code-Beispiele, Best Practices)
    """

    def execute(self, model: str, llm_client: Any, provider: str = "ollama") -> dict:
        """
        Führt Documentation Quality Test aus

        Args:
            model: LLM-Modell (z.B. "qwen2.5:14b")
            llm_client: LLMClient-Instanz
            provider: Provider (ollama, mistral, anthropic, openai)

        Returns:
            Dict mit raw_response, execution_time, tokens_used, metadata
        """
        prompt = self.asset["prompt"]

        # Context hinzufügen falls vorhanden
        if "context" in self.asset:
            full_prompt = f"{self.asset['context']}\n\n{prompt}"
        else:
            full_prompt = prompt

        # LLM Query
        start = time.time()

        try:
            # Use temperature 0.3 for Documentation Quality - balance between consistency and creativity
            response = llm_client.query(
                model, full_prompt, provider=provider, temperature=DEFAULT_TEMPERATURE
            )
            elapsed = time.time() - start

            # Token-Approximation
            approx_tokens = int(len(response.split()) * TOKEN_MULTIPLIER)

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

    def score_response(self, response: str) -> dict:
        """
        Bewertet Documentation Quality Antwort nach Tiered Difficulty System

        Scoring-Kategorien:
        1. Error Detection (70 Punkte) - Tiered (Labeled → Expert)
        2. Solution Quality (30 Punkte) - Code-Beispiele, Best Practices

        Args:
            response: LLM-Response als String

        Returns:
            Dict mit Score-Details
        """
        if not response or response.startswith("ERROR:"):
            return self._create_error_score("Invalid or error response")

        scoring_config = self.asset["scoring"]
        total_possible = scoring_config["total_points"]

        category_scores: Dict[str, Any] = {}
        details: List[str] = []
        violations: List[str] = []
        total_achieved: float = 0.0

        response_lower = response.lower()

        # ===== KATEGORIE 1: Error Detection (70 Punkte) =====
        ed_score, ed_details, ed_violations = self._score_error_detection(
            response_lower, scoring_config["error_detection"]
        )
        category_scores["error_detection"] = {
            "achieved": float(ed_score),
            "max": float(scoring_config["error_detection"]["weight"]),
        }
        details.extend(ed_details)
        violations.extend(ed_violations)
        total_achieved += ed_score

        # ===== KATEGORIE 2: Solution Quality (30 Punkte) =====
        sq_score, sq_details = self._score_solution_quality(
            response_lower, scoring_config["solution_quality"]
        )
        category_scores["solution_quality"] = {
            "achieved": float(sq_score),
            "max": float(scoring_config["solution_quality"]["weight"]),
        }
        details.extend(sq_details)
        total_achieved += sq_score

        return {
            "status": "success",
            "total_score": round(total_achieved, 2),
            "max_score": total_possible,
            "percentage": round((total_achieved / total_possible) * 100, 2),
            "category_scores": category_scores,
            "details": details,
            "violations": violations,
            "metadata": {
                "response_length": len(response),
                "word_count": len(response.split()),
            },
        }

    def _score_error_detection(
        self, response_lower: str, config: dict
    ) -> tuple[float, list[str], list[str]]:
        """
        Bewertet Issue Detection mit Tiered Difficulty (70 Punkte)

        Levels:
        - Labeled Issues (17.5P): Offensichtlich
        - Standard Issues (21.0P): Erkennbar
        - Advanced Issues (17.5P): Subtil
        - Expert Issues (14.0P): Sehr schwer

        Returns:
            (score, details_list, violations_list)
        """
        score: float = 0.0
        details = []
        violations = []

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
            max_points = sum(issue.get("points", 0) for issue in tier_issues)

            tier_score, tier_details, tier_violations = self._score_tier_issues(
                response_lower,
                tier_issues,
                max_points,
                default_threshold,
                tier_name.title(),
            )

            score += tier_score
            details.extend(tier_details)
            violations.extend(tier_violations)

        return round(score, 2), details, violations

    def _score_tier_issues(
        self,
        response_lower: str,
        issues: list[dict],
        max_points: float,
        min_threshold: float,
        tier_name: str,
    ) -> tuple[float, list[str], list[str]]:
        """
        Bewertet eine Tier-Kategorie (z.B. Labeled, Standard, Advanced, Expert)
        """
        tier_score: float = 0.0
        details: list[str] = []
        violations: list[str] = []

        if not issues:
            return 0.0, details, violations

        # Berechne max_points für diese Tier (Summe aller Issue-Points)
        current_max_points = sum(issue.get("points", 0) for issue in issues)

        for issue in issues:
            points = issue.get("points", 0)
            keywords = issue.get("keywords", [])
            issue_name = issue.get("issue", "Unknown Issue")
            severity = issue.get("severity", "medium")
            inverse_match = issue.get("inverse_match", False)

            # Determine required match parameters
            # Priority: min_keywords (int) > required_ratio (float) > min_threshold (default)
            explicit_min_keywords = issue.get("min_keywords")
            explicit_ratio = issue.get("required_ratio")
            
            target_matches = None
            if explicit_min_keywords is not None:
                target_matches = int(explicit_min_keywords)
            else:
                ratio = explicit_ratio if explicit_ratio is not None else min_threshold
                target_matches = max(1, int(len(keywords) * ratio))

            # Check ob Issue erwähnt wird (Hybrid Matching)
            found = self._check_issue_mentioned(response_lower, keywords, target_matches)

            if inverse_match:
                if not found:
                    tier_score += points
                    details.append(f"✓ [{tier_name}] {issue_name} (Nicht gefunden): +{points}p")
                else:
                    violations.append(f"✗ [{tier_name}] {issue_name} (Unerwünscht gefunden): -{points}p")
            else:
                if found:
                    tier_score += points
                    details.append(f"✓ [{tier_name}] {issue_name}: +{points}p")
                # Für Critical/High = Violation, sonst nur Details
                elif severity in ["critical", "high"]:
                    violations.append(f"✗ [{tier_name}] {issue_name}: -{points}p")
                else:
                    details.append(f"○ [{tier_name}] {issue_name}: 0p")

        # Direkter Score ohne Normalisierung (Issue-Points sind bereits korrekt)
        details.append(f"  → {tier_name} Total: {tier_score:.1f}/{max_points}p")

        return round(tier_score, 2), details, violations

    def _check_issue_mentioned(
        self, response_lower: str, keywords: list[str], target_matches: int
    ) -> bool:
        """
        Prüft ob ein Issue im Response erwähnt wird (Hybrid: Keyword + Semantic).
        
        Args:
            response_lower: Response text (lowercase)
            keywords: List of keywords to match
            target_matches: Absolute number of keywords required
            
        Returns:
            True if matched via keywords OR semantic similarity
        """
        # 1. Clean Response (DeepSeek Reasoning Tags)
        response_cleaned = re.sub(r'<think>.*?</think>', '', response_lower, flags=re.DOTALL)
        
        if not keywords:
            return False

        # 2. String Matching (Keyword Count)
        matches = sum(1 for kw in keywords if kw.lower() in response_cleaned)
        
        asset_id = self.asset_path.stem
        # DEBUG: print(f"DEBUG [{asset_id}]: Keywords={keywords[:3]}... Matches={matches}/{target_matches}")

        if matches >= target_matches:
            return True

        # 3. Semantic Similarity (Fallback)
        # Only if string match failed. Handles synonyms.
        # Note: Semantic check essentially acts as "Match Found" (aka >= 1 concept matches)
        # It's hard to quantify "how many matches" via Semantics, so we treat high similarity as a Pass.
        # This acts as a Safety Net for the "Synonym Trap".
        query = " ".join(keywords)

        # Split response into sentences/chunks
        sentences = [
            s.strip() 
            for s in response_cleaned.split('.') 
            if len(s.strip()) > MIN_SENTENCE_LENGTH
        ]
        
        # Fallback chunks if no sentences
        if not sentences:
            sentences = [response_cleaned[i:i+200] for i in range(0, len(response_cleaned), 200)]
            
        try:
            # Determine threshold (Global default + Asset specific override)
            threshold = SIMILARITY_THRESHOLD
            
            if asset_id in ASSET_SPECIFIC_CONFIG:
                threshold = ASSET_SPECIFIC_CONFIG[asset_id].get("semantic_threshold", threshold)

            best_score = SemanticSimilarity.find_best_match(query, sentences)
            # DEBUG: print(f"DEBUG [{asset_id}]: Semantic Best={best_score:.3f} Threshold={threshold}")
            return best_score > threshold
        except Exception as e:
            # Fallback if similarity fails
            # DEBUG: print(f"DEBUG [{asset_id}]: Semantic Error={e}")
            return False

    def _score_solution_quality(
        self, response_lower: str, config: dict
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
        score = 0
        details = []

        criteria = config.get("criteria", [])

        for criterion in criteria:
            name = criterion.get("name", "Unknown")
            points = criterion.get("points", 0)
            keywords = criterion.get("keywords", [])
            check_method = criterion.get("check_method", "keyword_presence")
            min_keywords = criterion.get("min_keywords", 1)

            if check_method == "keyword_presence":
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
            "status": "error",
            "total_score": 0,
            "max_score": 100,
            "percentage": 0,
            "category_scores": {
                "error_detection": {"achieved": 0, "max": 70},
                "solution_quality": {"achieved": 0, "max": 30},
            },
            "details": [error_msg],
            "violations": ["Test konnte nicht ausgeführt werden"],
            "metadata": {"response_length": 0, "word_count": 0},
            "error": error_msg,
        }


# Example Usage
if __name__ == "__main__":
    print("Documentation Quality Test Module")
    print("Verwende run_benchmark.py zum Ausführen der Tests")
