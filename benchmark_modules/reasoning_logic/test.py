"""
Reasoning Logic Test Module
Refactored for Modularity and DRY.
"""

import time
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple, cast

from benchmark_modules.base_test import BaseTest
from benchmark_modules.reasoning_logic.constants import (
    MAX_SCORE,
    WEIGHT_ERROR_DETECTION,
    WEIGHT_SOLUTION_QUALITY,
    WEIGHT_CONSISTENCY,
    TOKEN_ESTIMATION_FACTOR,
    ASSET_5C_ILLEGAL_MOVES,
    ASSET_5C_AWARENESS_KEYWORDS,
    ASSET_5C_REFUSAL_KEYWORDS,
    ASSET_5D_POSITIVE_TOKENS,
    ASSET_5D_NEGATIVE_TOKENS,
    STRUCTURE_KEYWORDS,
    REASONING_INDICATORS,
    CORRECTION_INDICATORS,
    MATCH_THRESHOLD_WEAK
)


class ReasoningLogicTest(BaseTest):
    """
    Testklasse für Logical Reasoning & Problem Solving.
    """

    def execute(self, model: str, llm_client: Any, provider: str = 'ollama') -> Dict[str, Any]:
        """
        Executes the reasoning test.
        """
        prompt = self.asset['prompt']
        system_prompt = self.get_system_prompt()

        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        start = time.time()
        # Note: We rely on llm_client.query to handle the actual API call
        response = llm_client.query(
            model, full_prompt, provider=provider, temperature=0.6
        )
        elapsed = time.time() - start

        approx_tokens = len(response.split()) * TOKEN_ESTIMATION_FACTOR

        return {
            'raw_response': response,
            'execution_time': elapsed,
            'tokens_used': approx_tokens,
            'metadata': {
                'model': model,
                'asset_id': self.asset['metadata']['id']
            }
        }

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Custom scoring for reasoning.
        Refactored to reduce complexity (Facade Pattern).
        """
        asset_id = self.asset['metadata']['id']
        expected_output = self.asset.get('expected_output', {})

        # Strategy Pattern for Scoring
        if asset_id == 'reasoning_5c_001':
            total_score, score_breakdown, details = self._score_5c_paradox(response)
        elif asset_id == 'reasoning_5d_001':
            total_score, score_breakdown, details = self._score_5d_deadlock(response)
        elif isinstance(expected_output, dict) and 'required_findings' in expected_output:
            findings = cast(List[str], expected_output['required_findings'])
            total_score, score_breakdown, details = self._score_standard_asset(
                response, findings
            )
        else:
            total_score, score_breakdown, details = self._score_similarity_fallback(response)

        # Normierung auf MAX_SCORE
        total_score = min(total_score, MAX_SCORE)

        # --- Tier Classification & Metadata Tagging ---
        tier_type = "Tier 1 (Operational Logic)"
        tier_2_assets = ['reasoning_5d_001']  # Deep Reasoning
        if asset_id in tier_2_assets:
            tier_type = "Tier 2 (Deep Reasoning)"

        # Assemble Result
        def get_score_val(value: Any) -> float:
            if isinstance(value, dict):
                return float(value.get('score', 0))
            return float(value)

        return {
            'status': 'success',
            'total_score': float(total_score),
            'max_score': MAX_SCORE,
            'tier': tier_type,
            'category_scores': {
                k: {
                    'achieved': get_score_val(v),
                    'max': MAX_SCORE,
                    'name': k
                }
                for k, v in score_breakdown.items()
            },
            'details': details,
            'violations': []
        }

    def _score_5c_paradox(self, response: str) -> Tuple[float, Dict[str, Any], List[str]]:
        """Tier 1: Asset 5C - The Scheduling Paradox (Physics Trap)."""
        resp_lower = response.lower()
        details = []
        score_breakdown: Dict[str, Any] = {}
        total_score = 0.0

        # Check conditions using helper
        has_illegal_move = self._contains_any(resp_lower, ASSET_5C_ILLEGAL_MOVES)
        has_awareness = self._contains_any(resp_lower, ASSET_5C_AWARENESS_KEYWORDS)
        has_refusal = self._contains_any(resp_lower, ASSET_5C_REFUSAL_KEYWORDS)

        if has_illegal_move:
            if has_awareness:
                total_score = 15.0
                details.append("❌ Logic Fail: Physics violation (Walls too early) (+15 Awareness)")
            else:
                total_score = 0.0
                details.append("❌ Logic Fail: Comparison Hallucination.")
            score_breakdown = {
                'error_detection': total_score,
                'solution_quality': 0,
                'consistency': 0
            }

        elif has_refusal:
            # SUCCESS
            score_breakdown['error_detection'] = WEIGHT_ERROR_DETECTION
            score_breakdown['solution_quality'] = WEIGHT_SOLUTION_QUALITY
            score_breakdown['consistency'] = WEIGHT_CONSISTENCY
            total_score = MAX_SCORE
            details.append(f"✅ Logic Pass: Model refused invalid constraints ({MAX_SCORE} pts).")

        elif has_awareness:
            # PARTIAL
            score_breakdown['error_detection'] = WEIGHT_ERROR_DETECTION * 0.6
            score_breakdown['solution_quality'] = WEIGHT_SOLUTION_QUALITY * 0.5
            total_score = 49.0
            details.append("⚠️ Partial Logic: Constraints recognized, but no clear refusal (~49 pts).")
            score_breakdown['consistency'] = 0

        else:
            total_score = 0.0
            details.append("❌ Logic Fail: Vague response.")
            score_breakdown = {
                'error_detection': 0,
                'solution_quality': 0,
                'consistency': 0
            }

        return total_score, score_breakdown, details

    def _score_5d_deadlock(self, response: str) -> Tuple[float, Dict[str, Any], List[str]]:
        """
        Tier 2: Asset 5D - Circular Dependency.
        New Logic (Feasibility Scale 0-10):
        - Score 0: Perfect (100 pts)
        - Score 1-2: Good detection (partial)
        - Score > 2: Fail (Optimism Bias)
        """
        resp_lower = response.lower()
        breakdown = {'error_detection': 0, 'solution_quality': 0, 'consistency': 0}
        
        # Regex to find "Feasibility: <number>"
        # Matches "feasibility: 0", "feasibility: 5", "feasibility: 0/10"
        match = re.search(r'feasibility:\s*(\d+)', resp_lower)
        
        if not match:
             # Fallback: Look for standalone '0' or 'zero' if explicit format is missing but intent is clear?
             # But we requested exact format.
            return 0.0, breakdown, ["❌ Logic Fail: Format 'Feasibility: X' not found."]

        feasibility_score = int(match.group(1))
        
        # Scoring Logic
        # Target is 0.
        if feasibility_score == 0:
            breakdown = {
                'error_detection': WEIGHT_ERROR_DETECTION,
                'solution_quality': WEIGHT_SOLUTION_QUALITY,
                'consistency': WEIGHT_CONSISTENCY
            }
            return MAX_SCORE, breakdown, ["✅ Logic Pass: Feasibility rated 0 (Impossible)."]
            
        elif feasibility_score <= 2:
            # Low feasibility (1-2) means they see trouble but aren't definitive
            breakdown['error_detection'] = WEIGHT_ERROR_DETECTION * 0.8
            breakdown['solution_quality'] = WEIGHT_SOLUTION_QUALITY * 0.5
            total = (MAX_SCORE * 0.6)
            return total, breakdown, [f"⚠️ Logic Partial: Feasibility {feasibility_score}/10 (Suspicious but not impossible)."]
            
        else:
            # > 2 means they think it's solvable
            return 0.0, breakdown, [f"❌ Logic Fail: Optimism Bias. Feasibility {feasibility_score}/10 implies solvable."]

    def _score_standard_asset(
        self, response: str, required_findings: List[str]
    ) -> Tuple[float, Dict[str, Any], List[str]]:
        """Standard scoring for 5A, 5B using finding keywords."""
        resp_lower = response.lower()
        details = []
        score_breakdown: Dict[str, Any] = {}
        total_score = 0.0

        # 1. Error Detection (Match Keywords)
        matches = 0
        for finding in required_findings:
            keywords = [w.lower() for w in finding.split() if len(w) >= 3]
            if not keywords:
                continue

            found_words = sum(1 for w in keywords if w in resp_lower)
            if found_words / len(keywords) >= MATCH_THRESHOLD_WEAK:
                matches += 1

        error_cfg = cast(
            Dict[str, Any], self.asset.get('scoring', {}).get('error_detection', {})
        )
        error_max = float(error_cfg.get('points', WEIGHT_ERROR_DETECTION))

        if matches >= len(required_findings):
            error_score = error_max
        else:
            error_score = (matches / len(required_findings)) * error_max

        score_breakdown['error_detection'] = error_score
        total_score += error_score
        details.append(
            f"Error Detection: {error_score:.1f}/{error_max} "
            f"({matches}/{len(required_findings)} findings)"
        )

        # 2. Solution Quality (Structure)
        qual_cfg = cast(
            Dict[str, Any], self.asset.get('scoring', {}).get('solution_quality', {})
        )
        quality_max = float(qual_cfg.get('points', WEIGHT_SOLUTION_QUALITY))
        quality_score = 0.0

        if self._contains_any(resp_lower, STRUCTURE_KEYWORDS):
            quality_score += (quality_max * 0.4)
        if "option a" in resp_lower and "option b" in resp_lower:
            quality_score += (quality_max * 0.2)
        if "step" in resp_lower or "schritt" in resp_lower:
            quality_score += (quality_max * 0.2)

        # Cap at max
        quality_score = min(quality_score, quality_max)

        score_breakdown['solution_quality'] = quality_score
        total_score += quality_score
        details.append(f"Solution Quality: {quality_score:.1f}/{quality_max}")

        # 3. Consistency
        const_cfg = cast(
            Dict[str, Any], self.asset.get('scoring', {}).get('consistency', {})
        )
        const_max = float(const_cfg.get('points', WEIGHT_CONSISTENCY))
        sc, _ = self._score_consistency(response, {'points': const_max})
        score_breakdown['consistency'] = sc
        total_score += sc
        details.append(f"Consistency: {sc}/{const_max}")

        return total_score, score_breakdown, details

    def _score_similarity_fallback(
        self, response: str
    ) -> Tuple[float, Dict[str, Any], List[str]]:
        """Fallback for puzzles like River Crossing using sequence matcher."""
        expected = self.asset.get('expected_output', '')
        if isinstance(expected, dict):
            expected = str(expected)

        sim = SequenceMatcher(None, response.strip(), expected.strip()).ratio()

        total_score = sim * MAX_SCORE
        score_breakdown = {'logic': {'score': total_score, 'weight': MAX_SCORE}}
        details = [f"Logic Match: {total_score:.1f}%"]

        return total_score, score_breakdown, details

    def _score_consistency(
        self,
        response: str,
        config: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """
        Bewertet Consistency für Reasoning-Tests.
        """
        score = 0.0
        details: List[str] = []
        max_points = float(config.get('points', WEIGHT_CONSISTENCY))

        resp_lower = response.lower()

        has_reasoning = self._contains_any(resp_lower, REASONING_INDICATORS)
        has_correction = self._contains_any(resp_lower, CORRECTION_INDICATORS)

        if has_reasoning and has_correction:
            score = max_points
            details.append(f"✓ Konsistenz: Reasoning und Korrektur vorhanden (+{score}p)")
        elif has_reasoning or has_correction:
            score = max_points / 2
            details.append(f"~ Teilweise konsistent: Reasoning/Korrektur gefunden ({score}p)")
        else:
            details.append("✗ Inkonsistent: Kein Reasoning-Prozess erkennbar")

        return score, details

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        """Helper to check if any keyword exists in text."""
        return any(k in text for k in keywords)

    def validate_result(self, result: str, expected: str) -> float:
        """
        Validiert das Ergebnis basierend auf logischer Korrektheit.
        """
        # Simple similarity for now
        similarity = SequenceMatcher(None, result.strip(), expected.strip()).ratio()

        return float(similarity)

    def get_system_prompt(self) -> str:
        """
        Spezifischer System-Prompt, der Reasoning explizit anfordert.
        """
        return (
            "You are a logic expert. Solve the given problem step-by-step. "
            "Show your reasoning process clearly ('Chain of Thought'). "
            "Finally, provide the clear Answer."
        )
