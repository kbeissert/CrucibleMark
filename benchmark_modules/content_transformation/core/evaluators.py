from typing import Any, Dict, List, Tuple
import re
from pathlib import Path
from utils.similarity import SemanticSimilarity
from .constants import TIER_THRESHOLDS

class ContentTransformationEvaluator:
    """
    Evaluator class for Content Transformation benchmarks.
    Encapsulates scoring logic for Error Detection (Tiered) and Solution Quality.
    """

    def __init__(self, asset: Dict[str, Any]):
        self.asset = asset

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
        # Clean reasoning tags (e.g. DeepSeek <think>) before scoring
        clean_response = self._clean_reasoning_tags(response)

        if not clean_response or clean_response.startswith("ERROR:"):
            return self._create_error_score("Invalid or error response")

        scoring_config = self.asset["scoring"]
        total_possible = scoring_config["total_points"]

        category_scores = {}
        details: list[str] = []
        violations: list[str] = []
        total_achieved: float = 0.0

        response_lower = clean_response.lower()

        # ===== KATEGORIE 1: Error Detection =====
        ed_weight = scoring_config["error_detection"]["weight"]
        ed_raw_score, ed_details, ed_violations, ed_max_possible = self._score_error_detection(
            response_lower, scoring_config["error_detection"]
        )
        
        # Normalize Score to Weight (Scaling)
        if ed_max_possible > 0:
            ed_final_score = (ed_raw_score / ed_max_possible) * ed_weight
        else:
            ed_final_score = 0.0

        category_scores["error_detection"] = {
            "achieved": round(ed_final_score, 2),
            "raw_score": ed_raw_score,
            "max": ed_weight,
            "raw_max": ed_max_possible
        }
        details.extend(ed_details)
        violations.extend(ed_violations)
        total_achieved += ed_final_score

        # ===== KATEGORIE 2: Solution Quality =====
        sq_weight = scoring_config["solution_quality"]["weight"]
        sq_raw_score, sq_details, sq_max_possible = self._score_solution_quality(
            response_lower, scoring_config["solution_quality"]
        )
        
        # Normalize Score to Weight (Scaling)
        if sq_max_possible > 0:
            sq_final_score = (sq_raw_score / sq_max_possible) * sq_weight
        else:
            sq_final_score = 0.0

        category_scores["solution_quality"] = {
            "achieved": round(sq_final_score, 2),
            "raw_score": sq_raw_score,
            "max": sq_weight,
            "raw_max": sq_max_possible
        }
        details.extend(sq_details)
        total_achieved += sq_final_score

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

    def _clean_reasoning_tags(self, response: str) -> str:
        """
        Removes reasoning tags (DeepSeek/R1) to avoid scoring internal thoughts.
        Now selectively only removes <think> to avoid false positives.
        """
        # Only remove <think> tags as they are standard for R1/DeepSeek.
        # Other tags like <reflection> caused content loss in Glossary tasks.
        tags = [
            (r'<think>.*?</think>', ''),
            (r'<reflection>.*?</reflection>', ''),
            (r'\[Reasoning\].*?\[/Reasoning\]', ''),
        ]
        
        cleaned = response
        for pattern, replacement in tags:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.DOTALL|re.IGNORECASE)
        
        return cleaned.strip()

    def _score_error_detection(
        self, response_lower: str, config: dict
    ) -> tuple[float, list[str], list[str]]:
        """
        Bewertet Issue Detection mit Tiered Difficulty (70 Punkte)
        """
        score: float = 0.0
        max_possible: float = 0.0
        details: list[str] = []
        violations: list[str] = []

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

            tier_score, tier_details, tier_violations, tier_max = self._score_tier_issues(
                response_lower, tier_issues, default_threshold, tier_name.title()
            )

            score += tier_score
            max_possible += tier_max
            details.extend(tier_details)
            violations.extend(tier_violations)

        return round(score, 2), details, violations, max_possible

    def _score_tier_issues(
        self,
        response_lower: str,
        issues: list[dict],
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
            return 0.0, details, violations, 0.0

        # Berechne max_points für diese Tier (Summe aller Issue-Points)
        tier_max_points = sum(issue.get("points", 0) for issue in issues)

        for issue in issues:
            points = issue.get("points", 0)
            keywords = issue.get("keywords", [])
            issue_name = issue.get("issue", "Unknown Issue")
            severity = issue.get("severity", "medium")

            # Check ob Issue erwähnt wird (Keyword-Matching)
            found = self._check_issue_mentioned(response_lower, keywords, min_threshold, tier_name=tier_name)

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

    def _check_issue_mentioned(
        self, response_lower: str, keywords: list[str], min_threshold: float = 0.40, tier_name: str = ""
    ) -> bool:
        """
        Prüft ob ein Issue im Response erwähnt wird (Keyword-Matching + Semantic Fallback)
        """
        if not keywords:
            return False

        # --- OPTION C: TIER-SPECIFIC SEMANTIC THRESHOLDS ---
        # Define strictness: Tier > Asset Config > Default
        semantic_thresholds = {
            'labeled': 0.45,   # Großzügig (für Dolphin/DeepSeek)
            'standard': 0.45,  # Großzügig
            'advanced': 0.50,  # Mittel
            'expert': 0.55     # STRENG (verhindert Qwen @ 100%)
        }
        
        base_threshold = 0.55
        asset_config_threshold = self.asset.get("scoring", {}).get("semantic_threshold", base_threshold)
        tier_threshold = semantic_thresholds.get(tier_name.lower(), asset_config_threshold)
        
        # Determine final Threshold: Expert enforces 0.55
        if tier_name.lower() == 'expert' and asset_config_threshold < 0.55:
            final_threshold = 0.55
        else:
            final_threshold = tier_threshold
            
        # 1. Exact Keyword Matching
        matches = sum(1 for kw in keywords if kw.lower() in response_lower)
        match_rate = matches / len(keywords)

        # 2. Threshold Check (with Expert Override for 100% Coverage)
        
        if tier_name.lower() == 'expert':
            # Expert Tier: Only PASS immediately if 100% exact match
            if match_rate == 1.0:
                 return True
            # If < 100%, we force Semantic Check for missing keywords below
        else:
            # Standard/Labeled: Use loose min_threshold (e.g. 40%)
            if match_rate >= min_threshold:
                return True

        # 3. Hybrid Semantic Check (Fallback or Enforcement)
        try:
            # Create chunks for comparison
            chunks = [
                s.strip() 
                for s in re.split(r'[.!?\n]+', response_lower) 
                if len(s.strip()) > 15
            ]
            if not chunks:
                chunks = [response_lower]
                
            # Expert Mode: Validate MISSING keywords individually
            if tier_name.lower() == 'expert':
                missing_keywords = [kw for kw in keywords if kw.lower() not in response_lower]
                
                # Check each missing keyword against the text chunks
                for kw in missing_keywords:
                    kw_score = SemanticSimilarity.find_best_match(kw, chunks)
                    # If ANY missing keyword fails the strict threshold, the whole issue fails
                    if kw_score < final_threshold:
                        return False 
                
                # If we get here, all missing keywors were semantically present
                return True

            else:
                 # Standard Mode: Check if the general "Concept" (joined keywords) is present
                 query = " ".join(keywords)
                 best_score = SemanticSimilarity.find_best_match(query, chunks)
                 return best_score > final_threshold

        except Exception:
            # Fallback if semantic check fails
            return False

    def _score_solution_quality(
        self, response_lower: str, config: dict
    ) -> tuple[float, list[str], float]:
        """
        Bewertet Lösungsqualität (30 Punkte)
        """
        score = 0.0
        details = []

        criteria = config.get("criteria", [])
        max_possible = sum(c.get("points", 0) for c in criteria)

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
            elif check_method == "negative_keyword_presence":
                # Check for ABSENCE of keywords (Sarcasm detection)
                bad_keywords = criterion.get("forbidden_keywords", [])
                
                # Checking for forbidden words in response
                found_bad = [kw for kw in bad_keywords if kw.lower() in response_lower]

                if not found_bad:
                    score += points
                    details.append(f"✓ {name}: No forbidden keywords found +{points}p")
                else:
                    details.append(
                        f"✗ {name}: Forbidden keywords found: {', '.join(found_bad)}"
                    )

            else:
                # Fallback für andere check_methods
                details.append(f"○ {name}: unsupported check_method '{check_method}'")

        return round(score, 2), details, max_possible

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
