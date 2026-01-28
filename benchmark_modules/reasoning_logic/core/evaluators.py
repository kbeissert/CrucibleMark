from typing import Any, cast
import re
from difflib import SequenceMatcher
from .constants import (
    MAX_SCORE,
    WEIGHT_ERROR_DETECTION,
    WEIGHT_SOLUTION_QUALITY,
    WEIGHT_CONSISTENCY,
    SCORE_THRESHOLD_HIGH,
    SCORE_THRESHOLD_MED,
    BONUS_CONSISTENCY,
    FEASIBILITY_IMPOSSIBLE,
    FEASIBILITY_LOW_MAX,
    FEASIBILITY_HIGH_MIN,
    FEASIBILITY_HIGH_MAX,
    MIN_WORD_LENGTH,
    ASSET_5B_CORE_KEYWORDS,
    ASSET_5B_QUALIFIER_KEYWORDS,
    ASSET_5B_DOMAIN_KEYWORDS,
    ASSET_5B_CONCEPT_KEYWORDS,
    ASSET_5B_SOLUTION_KEYWORDS,
    ASSET_5B_PRIO_KEYWORDS,
    ASSET_5C_ILLEGAL_MOVES,
    ASSET_5C_AWARENESS_KEYWORDS,
    ASSET_5C_REFUSAL_KEYWORDS,
    ASSET_5D_DEADLOCK_KEYWORDS,
    ASSET_5D_CIRCULAR_KEYWORDS,
    ASSET_5D_WARNING_KEYWORDS,
    STRUCTURE_KEYWORDS,
    REASONING_INDICATORS,
    CORRECTION_INDICATORS,
    MATCH_THRESHOLD_WEAK,
    TIER_MAPPING,
    SOLUTION_WEIGHT_STRUCTURE,
    SOLUTION_WEIGHT_OPTIONS,
    SOLUTION_WEIGHT_STEPS,
    SOLUTION_KEYWORDS_OPTIONS,
    SOLUTION_KEYWORDS_STEPS,
)

class ReasoningEvaluator:
    """
    Evaluator class for Reasoning benchmarks.
    Encapsulates all scoring logic (Chain of Thought, Paradoxes, Deadlocks, etc.).
    """

    def __init__(self, asset: dict[str, Any]):
        self.asset = asset
        # Dispatcher Mapping
        self._scorers = {
            "reasoning_5c_001": self._score_5c_paradox,
            "reasoning_5d_001": self._score_5d_deadlock,
            "reasoning_5b_001": self._score_5b_complex,
        }

    def score_response(self, response: str) -> dict[str, Any]:
        """
        Custom scoring for reasoning.
        Refactored to reduce complexity (Facade Pattern).
        """
        # PHASE 1: Strip <think> tags before scoring
        clean_response = self._strip_thinking_tags(response)

        asset_id = self.asset["metadata"]["id"]
        expected_output = self.asset.get("expected_output", {})

        # Strategy Pattern for Scoring
        if handler := self._scorers.get(asset_id):
            total_score, score_breakdown, details = handler(clean_response)
        elif (
            isinstance(expected_output, dict)
            and "required_findings" in expected_output
        ):
            findings = cast(list[str], expected_output["required_findings"])
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
        tier_type = self._determine_tier(asset_id)

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

    def _determine_tier(self, asset_id: str) -> str:
        """Determines the reasoning tier based on asset ID from configuration."""
        for tier_name, assets in TIER_MAPPING.items():
            if asset_id in assets:
                return tier_name
        return "Tier 1 (Operational Logic)"

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
    ) -> tuple[float, dict[str, Any], list[str]]:
        """
        Tier 2: Asset 5B - Complex Reasoning Chains (System Thinking).
        Uses 3-Tier Scoring: Concepts (40) -> Solution (70) -> Prioritization (100).
        """
        resp_lower = response.lower()
        details = []
        score_breakdown: dict[str, Any] = {}

        # 1. Concept Detection (Tier 1 Check)
        c1_core = self._contains_any(resp_lower, ASSET_5B_CORE_KEYWORDS)
        c1_qualifier = self._contains_any(resp_lower, ASSET_5B_QUALIFIER_KEYWORDS)
        has_root_cause = c1_core and c1_qualifier

        c2_domain = self._contains_any(resp_lower, ASSET_5B_DOMAIN_KEYWORDS)
        c2_concept = self._contains_any(resp_lower, ASSET_5B_CONCEPT_KEYWORDS)
        has_cross_domain = c2_domain and c2_concept

        has_integrated_solution = self._contains_any(
            resp_lower, ASSET_5B_SOLUTION_KEYWORDS
        )

        # 2. Prioritization Check (Tier 3 Check)
        # Look for numbered lists or explicit prioritization language
        # Regex looks for patterns like "1. ", "2. ", "Step 1:", "First:", etc.
        has_numbering = bool(
            re.search(
                r"(?:^|\n)\s*(?:\d+\.|step \d|phase \d)", response, re.IGNORECASE
            )
        )
        has_prio_kw = self._contains_any(resp_lower, ASSET_5B_PRIO_KEYWORDS)
        has_prioritization = has_numbering and has_prio_kw

        # --- SCORING LOGIC ---

        # Base Points: Error Detection (Max 40)
        error_pts = 0.0
        if has_root_cause:
            error_pts += 20.0
            details.append(
                "✅ Root Cause: Identified Versioning/Deprecation inconsistency."
            )
        else:
            details.append(
                "❌ Root Cause: "
                "Missed the core versioning/deprecation strategy issue."
            )

        if has_cross_domain:
            error_pts += 20.0
            details.append(
                "✅ Cross-Domain: "
                "Identified need for alignment between Code/Docs/UX."
            )
        else:
            details.append(
                "❌ Cross-Domain: Missed the systemic link between domains."
            )

        # Solution Quality (Max 50)
        # Tier 2: Integrated Solution (Base 30)
        # Tier 3: Prioritization (+20)
        solution_pts = 0.0

        if has_integrated_solution:
            solution_pts += SCORE_THRESHOLD_MED
            details.append(
                "✅ Solution: Proposed a unified policy/governance approach."
            )

            # Check for Tier 3 (Prioritization) ONLY if solution is valid
            if has_prioritization:
                solution_pts += 20.0
                details.append(
                    "✅ Prioritization: "
                    "Structured plan with clear steps/priorities."
                )
            else:
                details.append(
                    "⚠️ Prioritization: Solution is good, "
                    "but lacks clear prioritization steps (Tier 3 missed)."
                )
        # Partial credit for "fixing" things without policy
        elif "fix" in resp_lower or "korrigieren" in resp_lower:
            solution_pts = 10.0
            details.append(
                "⚠️ Solution: "
                "Proposed fixes but missed the 'Unified Policy' aspect."
            )
        else:
            details.append("❌ Solution: No clear integrated solution found.")

        # Consistency (Max 10)
        # Bonus for full Tier 2 achievement
        consistency_pts = (
            BONUS_CONSISTENCY
            if (
                error_pts >= SCORE_THRESHOLD_HIGH
                and solution_pts >= SCORE_THRESHOLD_MED
            )
            else 0.0
        )

        total_score = error_pts + solution_pts + consistency_pts

        score_breakdown = {
            "error_detection": error_pts,
            "solution_quality": solution_pts,
            "consistency": consistency_pts
        }

        return total_score, score_breakdown, details

    def _score_5c_paradox(
        self, response: str
    ) -> tuple[float, dict[str, Any], list[str]]:
        """Tier 1: Asset 5C - The Scheduling Paradox (Physics Trap)."""
        resp_lower = response.lower()
        details = []
        score_breakdown: dict[str, Any] = {}
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
                "⚠️ Partial Logic: "
                "Constraints recognized, but no clear refusal (~49 pts)."
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
    ) -> tuple[float, dict[str, Any], list[str]]:
        """Tier 2: Asset 5D - Circular Dependency (Deadlock)."""
        resp_lower = response.lower()
        breakdown: dict[str, float] = {
            "error_detection": 0.0,
            "solution_quality": 0.0,
            "consistency": 0.0,
        }

        # 1. Check for explicit Feasibility Score
        feasibility_match = re.search(r"feasibility:\s*(\d+)", resp_lower)
        feasibility_score = (
            int(feasibility_match.group(1)) if feasibility_match else None
        )

        # 2. Check for Keywords
        has_deadlock = self._contains_any(resp_lower, ASSET_5D_DEADLOCK_KEYWORDS)
        has_circular = self._contains_any(resp_lower, ASSET_5D_CIRCULAR_KEYWORDS)
        has_warning = self._contains_any(resp_lower, ASSET_5D_WARNING_KEYWORDS)

        # LEVEL 1: PERFECT (100)
        # Criteria: Feasibility 0 OR Strong Deadlock confirmation
        is_impossible_score = (
            feasibility_score is not None
            and feasibility_score == FEASIBILITY_IMPOSSIBLE
        )
        if is_impossible_score or has_deadlock:
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
        is_low_feasibility = (
            feasibility_score is not None
            and 1 <= feasibility_score <= FEASIBILITY_LOW_MAX
        )
        if is_low_feasibility or has_circular:
            breakdown = {
                "error_detection": float(WEIGHT_ERROR_DETECTION),
                "solution_quality": float(WEIGHT_SOLUTION_QUALITY * 0.5),
                "consistency": float(WEIGHT_CONSISTENCY * 0.5),
            }
            return (
                SCORE_THRESHOLD_HIGH,
                breakdown,
                [
                    "⚠️ Logic Partial (High): "
                    "Identified circular dependency but was slightly optimistic."
                ],
            )

        # LEVEL 3: WEAK WARNING (40)
        # Criteria: Feasibility 4-5 OR General warnings
        is_med_feasibility = (
            feasibility_score is not None
            and FEASIBILITY_HIGH_MIN <= feasibility_score <= FEASIBILITY_HIGH_MAX
        )
        if is_med_feasibility or has_warning:
            breakdown = {
                "error_detection": float(WEIGHT_ERROR_DETECTION * 0.5),
                "solution_quality": 0.0,
                "consistency": 0.0,
            }
            return (
                40.0,
                breakdown,
                [
                    "⚠️ Logic Partial (Low): "
                    "Recognized complexity/risk but missed the deadlock."
                ],
            )

        # LEVEL 4: FAIL (0)
        return (
            0.0,
            breakdown,
            ["❌ Logic Fail: Optimism Bias. Failed to identify deadlock or risks."],
        )

    def _score_standard_asset(
        self, response: str, required_findings: list[str]
    ) -> tuple[float, dict[str, Any], list[str]]:
        """Standard scoring for 5A, 5B using finding keywords."""
        resp_lower = response.lower()
        details = []
        score_breakdown: dict[str, Any] = {}
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
        self, resp_lower: str, required_findings: list[str], asset: dict[str, Any]
    ) -> float:
        """Calculates error detection score based on keyword matches."""
        matches = 0
        for finding in required_findings:
            keywords = [w.lower() for w in finding.split() if len(w) >= MIN_WORD_LENGTH]
            if not keywords:
                continue

            found_words = sum(1 for w in keywords if w in resp_lower)
            if found_words / len(keywords) >= MATCH_THRESHOLD_WEAK:
                matches += 1

        error_cfg = cast(
            dict[str, Any], asset.get("scoring", {}).get("error_detection", {})
        )
        error_max = float(error_cfg.get("points", WEIGHT_ERROR_DETECTION))

        if matches >= len(required_findings):
            return error_max
        return (matches / len(required_findings)) * error_max

    def _measure_solution_quality(
        self, resp_lower: str, asset: dict[str, Any]
    ) -> float:
        """Calculates solution quality score based on structure patterns."""
        qual_cfg = cast(
            dict[str, Any], asset.get("scoring", {}).get("solution_quality", {})
        )
        quality_max = float(qual_cfg.get("points", WEIGHT_SOLUTION_QUALITY))
        quality_score = 0.0

        if self._contains_any(resp_lower, STRUCTURE_KEYWORDS):
            quality_score += quality_max * SOLUTION_WEIGHT_STRUCTURE
        if self._contains_any(resp_lower, SOLUTION_KEYWORDS_OPTIONS):
            quality_score += quality_max * SOLUTION_WEIGHT_OPTIONS
        if self._contains_any(resp_lower, SOLUTION_KEYWORDS_STEPS):
            quality_score += quality_max * SOLUTION_WEIGHT_STEPS

        return min(quality_score, quality_max)

    def _measure_consistency_and_return_full(
        self,
        total_score: float,
        score_breakdown: dict[str, Any],
        details: list[str],
        response: str,
    ) -> tuple[float, dict[str, Any], list[str]]:
        """
        Measures consistency, adds it to totals, and returns final standard result.
        """
        const_cfg = cast(
            dict[str, Any], self.asset.get("scoring", {}).get("consistency", {})
        )
        const_max = float(const_cfg.get("points", WEIGHT_CONSISTENCY))
        sc, _ = self._score_consistency(response, {"points": const_max})

        score_breakdown["consistency"] = sc
        total_score += sc
        details.append(f"Consistency: {sc:.1f}/{const_max}")

        return total_score, score_breakdown, details

    def _score_similarity_fallback(
        self, response: str
    ) -> tuple[float, dict[str, Any], list[str]]:
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
        self, response: str, config: dict[str, Any]
    ) -> tuple[float, list[str]]:
        """
        Bewertet Consistency für Reasoning-Tests.
        """
        score = 0.0
        details: list[str] = []
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

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        """Helper to check if any keyword exists in text."""
        return any(k in text for k in keywords)
