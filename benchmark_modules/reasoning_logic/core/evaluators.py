from typing import Any, Dict, List, Tuple, cast
import re
from difflib import SequenceMatcher
from .constants import (
    MAX_SCORE,
    WEIGHT_ERROR_DETECTION,
    WEIGHT_SOLUTION_QUALITY,
    WEIGHT_CONSISTENCY,
    ASSET_5C_ILLEGAL_MOVES,
    ASSET_5C_AWARENESS_KEYWORDS,
    ASSET_5C_REFUSAL_KEYWORDS,
    STRUCTURE_KEYWORDS,
    REASONING_INDICATORS,
    CORRECTION_INDICATORS,
    MATCH_THRESHOLD_WEAK,
)

class ReasoningEvaluator:
    """
    Evaluator class for Reasoning benchmarks.
    Encapsulates all scoring logic (Chain of Thought, Paradoxes, Deadlocks, etc.).
    """

    def __init__(self, asset: Dict[str, Any]):
        self.asset = asset

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Custom scoring for reasoning.
        Refactored to reduce complexity (Facade Pattern).
        """
        # PHASE 1: Strip <think> tags before scoring
        clean_response = self._strip_thinking_tags(response)

        asset_id = self.asset["metadata"]["id"]
        expected_output = self.asset.get("expected_output", {})

        # Strategy Pattern for Scoring
        if asset_id == "reasoning_5c_001":
            total_score, score_breakdown, details = self._score_5c_paradox(clean_response)
        elif asset_id == "reasoning_5d_001":
            total_score, score_breakdown, details = self._score_5d_deadlock(clean_response)
        elif asset_id == "reasoning_5b_001":
            # PHASE 4: Specialized handling for Complex Chains to support narrative variance
            total_score, score_breakdown, details = self._score_5b_complex(clean_response)
        elif (
            isinstance(expected_output, dict) and "required_findings" in expected_output
        ):
            findings = cast(List[str], expected_output["required_findings"])
            total_score, score_breakdown, details = self._score_standard_asset(
                clean_response, findings
            )
        else:
            total_score, score_breakdown, details = self._score_similarity_fallback(
                clean_response
            )

        # Normierung auf MAX_SCORE
        total_score = min(total_score, MAX_SCORE)

        # --- Tier Classification & Metadata Tagging ---
        tier_type = "Tier 1 (Operational Logic)"

        # PHASE 2: Asset 001 is Tier 0 (Sanity Check)
        if asset_id == "reasoning_001_river":
            tier_type = "Tier 0 (Sanity Check)"

        tier_2_assets = [
            "reasoning_5a_001",
            "reasoning_5b_001",
            "reasoning_5c_001",
            "reasoning_5d_001",
        ]  # Deep Reasoning
        if asset_id in tier_2_assets:
            tier_type = "Tier 2 (Deep Reasoning)"

        # Assemble Result
        def get_score_val(value: Any) -> float:
            if isinstance(value, dict):
                return float(value.get("score", 0))
            return float(value)

        return {
            "status": "success",
            "total_score": float(total_score),
            "max_score": MAX_SCORE,
            "tier": tier_type,
            "category_scores": {
                k: {"achieved": get_score_val(v), "max": MAX_SCORE, "name": k}
                for k, v in score_breakdown.items()
            },
            "details": details,
            "violations": [],
        }

    def _strip_thinking_tags(self, text: str) -> str:
        """
        Removes <think>...</think> blocks from DeepSeek R1 responses.
        These blocks contain internal reasoning that should not be scored.
        """
        if not text:
            return ""
        # Remove multiline <think> blocks
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def _score_5b_complex(
        self, response: str
    ) -> Tuple[float, Dict[str, Any], List[str]]:
        """
        Tier 2: Asset 5B - Complex Reasoning Chains (System Thinking).
        Uses 3-Tier Scoring: Concepts (40) -> Solution (70) -> Prioritization (100).
        """
        resp_lower = response.lower()
        details = []
        score_breakdown: Dict[str, Any] = {}

        # 1. Concept Detection (Tier 1 Check)
        c1_core = any(x in resp_lower for x in ["versioning", "deprecation", "lifecycle", "veraltet", "versionierung", "api version"])
        c1_qualifier = any(x in resp_lower for x in ["inconsistent", "strategy", "mismatch", "conflict", "inkonsistent", "widersprüchlich", "confusion", "ambiguity"])
        has_root_cause = c1_core and c1_qualifier

        c2_domain = any(x in resp_lower for x in ["code", "docs", "documentation", "ux", "frontend", "backend"])
        c2_concept = any(x in resp_lower for x in ["alignment", "consistency", "reflect", "mirror", "dependency", "abhängigkeit", "spiegeln", "synchronize", "match"])
        has_cross_domain = c2_domain and c2_concept

        c3_sol = any(x in resp_lower for x in ["unified", "policy", "standard", "communication", "central", "einheitlich", "kommunikation", "governance", "single source"])
        has_integrated_solution = c3_sol

        # 2. Prioritization Check (Tier 3 Check)
        # Look for numbered lists or explicit prioritization language
        # Regex looks for patterns like "1. ", "2. ", "Step 1:", "First:", etc.
        # AND keywords like "priority", "prioritize", "start with", "immediate".
        has_numbering = bool(re.search(r"(?:^|\n)\s*(?:\d+\.|step \d|phase \d)", response, re.IGNORECASE))
        has_prio_kw = any(x in resp_lower for x in ["priorit", "immediate", "short-term", "first step", "sofort", "schritt 1"])
        has_prioritization = has_numbering and has_prio_kw

        # --- SCORING LOGIC ---

        # Base Points: Error Detection (Max 40)
        error_pts = 0.0
        if has_root_cause:
            error_pts += 20.0
            details.append("✅ Root Cause: Identified Versioning/Deprecation inconsistency.")
        else:
            details.append("❌ Root Cause: Missed the core versioning/deprecation strategy issue.")

        if has_cross_domain:
            error_pts += 20.0
            details.append("✅ Cross-Domain: Identified need for alignment between Code/Docs/UX.")
        else:
            details.append("❌ Cross-Domain: Missed the systemic link between domains.")

        # Solution Quality (Max 50)
        # Tier 2: Integrated Solution (Base 30)
        # Tier 3: Prioritization (+20)
        solution_pts = 0.0

        if has_integrated_solution:
            solution_pts += 30.0
            details.append("✅ Solution: Proposed a unified policy/governance approach.")

            # Check for Tier 3 (Prioritization) ONLY if solution is valid
            if has_prioritization:
                solution_pts += 20.0
                details.append("✅ Prioritization: Structured plan with clear steps/priorities.")
            else:
                details.append("⚠️ Prioritization: Solution is good, but lacks clear prioritization steps (Tier 3 missed).")
        # Partial credit for "fixing" things without policy
        elif "fix" in resp_lower or "korrigieren" in resp_lower:
            solution_pts = 10.0
            details.append("⚠️ Solution: Proposed fixes but missed the 'Unified Policy' aspect.")
        else:
            details.append("❌ Solution: No clear integrated solution found.")

        # Consistency (Max 10)
        # Bonus for full Tier 2 achievement
        consistency_pts = 10.0 if (error_pts >= 40.0 and solution_pts >= 30.0) else 0.0

        total_score = error_pts + solution_pts + consistency_pts

        score_breakdown = {
            "error_detection": error_pts,
            "solution_quality": solution_pts,
            "consistency": consistency_pts
        }

        return total_score, score_breakdown, details

    def _score_5c_paradox(
        self, response: str
    ) -> Tuple[float, Dict[str, Any], List[str]]:
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
                details.append(
                    "❌ Logic Fail: Physics violation (Walls too early) (+15 Awareness)"
                )
            else:
                total_score = 0.0
                details.append("❌ Logic Fail: Comparison Hallucination.")
            score_breakdown = {
                "error_detection": total_score,
                "solution_quality": 0,
                "consistency": 0,
            }

        elif has_refusal:
            # SUCCESS
            score_breakdown["error_detection"] = WEIGHT_ERROR_DETECTION
            score_breakdown["solution_quality"] = WEIGHT_SOLUTION_QUALITY
            score_breakdown["consistency"] = WEIGHT_CONSISTENCY
            total_score = MAX_SCORE
            details.append(
                f"✅ Logic Pass: Model refused invalid constraints ({MAX_SCORE} pts)."
            )

        elif has_awareness:
            # PARTIAL
            score_breakdown["error_detection"] = WEIGHT_ERROR_DETECTION * 0.6
            score_breakdown["solution_quality"] = WEIGHT_SOLUTION_QUALITY * 0.5
            total_score = 49.0
            details.append(
                "⚠️ Partial Logic: Constraints recognized, but no clear refusal (~49 pts)."
            )
            score_breakdown["consistency"] = 0

        else:
            total_score = 0.0
            details.append("❌ Logic Fail: Vague response.")
            score_breakdown = {
                "error_detection": 0,
                "solution_quality": 0,
                "consistency": 0,
            }

        return total_score, score_breakdown, details

    def _score_5d_deadlock(
        self, response: str
    ) -> Tuple[float, Dict[str, Any], List[str]]:
        """Tier 2: Asset 5D - Circular Dependency (Deadlock)."""
        resp_lower = response.lower()
        breakdown: Dict[str, float] = {
            "error_detection": 0.0,
            "solution_quality": 0.0,
            "consistency": 0.0,
        }

        # 1. Check for explicit Feasibility Score
        feasibility_match = re.search(r"feasibility:\s*(\d+)", resp_lower)
        feasibility_score = int(feasibility_match.group(1)) if feasibility_match else None

        # 2. Check for Keywords
        has_deadlock_kws = any(x in resp_lower for x in ["impossible", "deadlock", "unsolvable", "cannot be implemented"])
        has_circular_kws = any(x in resp_lower for x in ["circular dependency", "circular reference", "mutual exclusion", "cycle detected"])
        has_warning_kws = any(x in resp_lower for x in ["high risk", "complex", "race condition", "challenging", "careful synchronization"])

        # LEVEL 1: PERFECT (100)
        # Criteria: Feasibility 0 OR Strong Deadlock confirmation
        if (feasibility_score is not None and feasibility_score == 0) or has_deadlock_kws:
            breakdown = {
                "error_detection": float(WEIGHT_ERROR_DETECTION),
                "solution_quality": float(WEIGHT_SOLUTION_QUALITY),
                "consistency": float(WEIGHT_CONSISTENCY),
            }
            return (
                float(MAX_SCORE),
                breakdown,
                ["✅ Logic Pass: Correctly identified as Impossible/Deadlock."],
            )

        # LEVEL 2: GOOD CATCH (70)
        # Criteria: Feasibility 1-3 OR Specific Circular Dependency identification
        if (feasibility_score is not None and 1 <= feasibility_score <= 3) or has_circular_kws:
            breakdown = {
                "error_detection": float(WEIGHT_ERROR_DETECTION),
                "solution_quality": float(WEIGHT_SOLUTION_QUALITY * 0.5),
                "consistency": float(WEIGHT_CONSISTENCY * 0.5),
            }
            return (
                70.0,
                breakdown,
                ["⚠️ Logic Partial (High): Identified circular dependency but was slightly optimistic."],
            )

        # LEVEL 3: WEAK WARNING (40)
        # Criteria: Feasibility 4-5 OR General warnings
        if (feasibility_score is not None and 4 <= feasibility_score <= 5) or has_warning_kws:
            breakdown = {
                "error_detection": float(WEIGHT_ERROR_DETECTION * 0.5),
                "solution_quality": 0.0,
                "consistency": 0.0,
            }
            return (
                40.0,
                breakdown,
                ["⚠️ Logic Partial (Low): Recognized complexity/risk but missed the deadlock."],
            )

        # LEVEL 4: FAIL (0)
        return (
            0.0,
            breakdown,
            ["❌ Logic Fail: Optimism Bias. Failed to identify deadlock or risks."],
        )

    def _score_standard_asset(
        self, response: str, required_findings: List[str]
    ) -> Tuple[float, Dict[str, Any], List[str]]:
        """Standard scoring for 5A, 5B using finding keywords."""
        resp_lower = response.lower()
        details = []
        score_breakdown: Dict[str, Any] = {}
        total_score = 0.0

        # 1. Error Detection (Match Keywords)
        error_score = self._measure_error_detection(
            resp_lower, required_findings, self.asset
        )

        error_max = float(WEIGHT_ERROR_DETECTION)
        if error_cfg := self.asset.get("scoring", {}).get("error_detection"):
            error_max = float(error_cfg.get("points", error_max))

        score_breakdown["error_detection"] = error_score
        total_score += error_score
        details.append(f"Error Detection: {error_score:.1f}/{error_max}")

        # 2. Solution Quality (Structure)
        quality_score = self._measure_solution_quality(resp_lower, self.asset)
        score_breakdown["solution_quality"] = quality_score
        total_score += quality_score
        details.append(f"Solution Quality: {quality_score:.1f}")

        # 3. Consistency and Finalize
        return self._measure_consistency_and_return_full(
            total_score, score_breakdown, details, response
        )

    def _measure_error_detection(
        self, resp_lower: str, required_findings: List[str], asset: Dict[str, Any]
    ) -> float:
        """Calculates error detection score based on keyword matches."""
        matches = 0
        for finding in required_findings:
            keywords = [w.lower() for w in finding.split() if len(w) >= 3]
            if not keywords:
                continue

            found_words = sum(1 for w in keywords if w in resp_lower)
            if found_words / len(keywords) >= MATCH_THRESHOLD_WEAK:
                matches += 1

        error_cfg = cast(
            Dict[str, Any], asset.get("scoring", {}).get("error_detection", {})
        )
        error_max = float(error_cfg.get("points", WEIGHT_ERROR_DETECTION))

        if matches >= len(required_findings):
            return error_max
        return (matches / len(required_findings)) * error_max

    def _measure_solution_quality(
        self, resp_lower: str, asset: Dict[str, Any]
    ) -> float:
        """Calculates solution quality score based on structure patterns."""
        qual_cfg = cast(
            Dict[str, Any], asset.get("scoring", {}).get("solution_quality", {})
        )
        quality_max = float(qual_cfg.get("points", WEIGHT_SOLUTION_QUALITY))
        quality_score = 0.0

        if self._contains_any(resp_lower, STRUCTURE_KEYWORDS):
            quality_score += quality_max * 0.4
        if "option a" in resp_lower and "option b" in resp_lower:
            quality_score += quality_max * 0.2
        if "step" in resp_lower or "schritt" in resp_lower:
            quality_score += quality_max * 0.2

        return min(quality_score, quality_max)

    def _measure_consistency_and_return_full(
        self,
        total_score: float,
        score_breakdown: Dict[str, Any],
        details: List[str],
        response: str,
    ) -> Tuple[float, Dict[str, Any], List[str]]:
        """Measures consistency, adds it to totals, and returns final standard result."""
        const_cfg = cast(
            Dict[str, Any], self.asset.get("scoring", {}).get("consistency", {})
        )
        const_max = float(const_cfg.get("points", WEIGHT_CONSISTENCY))
        sc, _ = self._score_consistency(response, {"points": const_max})

        score_breakdown["consistency"] = sc
        total_score += sc
        details.append(f"Consistency: {sc:.1f}/{const_max}")

        return total_score, score_breakdown, details

    def _score_similarity_fallback(
        self, response: str
    ) -> Tuple[float, Dict[str, Any], List[str]]:
        """Fallback for puzzles like River Crossing using sequence matcher."""
        expected = self.asset.get("expected_output", "")
        if isinstance(expected, dict):
            expected = str(expected)

        sim = SequenceMatcher(None, response.strip(), expected.strip()).ratio()

        total_score = sim * MAX_SCORE
        score_breakdown = {"logic": {"score": total_score, "weight": MAX_SCORE}}
        details = [f"Logic Match: {total_score:.1f}%"]

        return total_score, score_breakdown, details

    def _score_consistency(
        self, response: str, config: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """
        Bewertet Consistency für Reasoning-Tests.
        """
        score = 0.0
        details: List[str] = []
        max_points = float(config.get("points", WEIGHT_CONSISTENCY))

        resp_lower = response.lower()

        has_reasoning = self._contains_any(resp_lower, REASONING_INDICATORS)
        has_correction = self._contains_any(resp_lower, CORRECTION_INDICATORS)

        if has_reasoning and has_correction:
            score = max_points
            details.append(
                f"✓ Konsistenz: Reasoning und Korrektur vorhanden (+{score}p)"
            )
        elif has_reasoning or has_correction:
            score = max_points / 2
            details.append(
                f"~ Teilweise konsistent: Reasoning/Korrektur gefunden ({score}p)"
            )
        else:
            details.append("✗ Inkonsistent: Kein Reasoning-Prozess erkennbar")

        return score, details

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        """Helper to check if any keyword exists in text."""
        return any(k in text for k in keywords)
