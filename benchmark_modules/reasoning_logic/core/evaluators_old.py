"""Evaluators for Reasoning Logic.

Contains the core scoring logic for all reasoning tiers (1-3).
"""

import re
from difflib import SequenceMatcher
from typing import Any, cast

from .constants import (
    ASSET_5B_CONCEPT_KEYWORDS,
    ASSET_5B_CORE_KEYWORDS,
    ASSET_5B_DOMAIN_KEYWORDS,
    ASSET_5B_PRIO_KEYWORDS,
    ASSET_5B_QUALIFIER_KEYWORDS,
    ASSET_5B_SOLUTION_KEYWORDS,
    ASSET_5C_AWARENESS_KEYWORDS,
    ASSET_5C_ILLEGAL_MOVES,
    ASSET_5C_REFUSAL_KEYWORDS,
    ASSET_5D_CIRCULAR_KEYWORDS,
    ASSET_5D_DEADLOCK_KEYWORDS,
    ASSET_5D_WARNING_KEYWORDS,
    BONUS_CONSISTENCY,
    CORRECTION_INDICATORS,
    FEASIBILITY_HIGH_MAX,
    FEASIBILITY_HIGH_MIN,
    FEASIBILITY_IMPOSSIBLE,
    FEASIBILITY_LOW_MAX,
    MATCH_THRESHOLD_WEAK,
    MAX_SCORE,
    METACOG_ALTERNATIVES_KEYWORDS,
    METACOG_CONFIDENCE_KEYWORDS,
    METACOG_ITERATION_KEYWORDS,
    METACOG_SELF_CORRECTION_KEYWORDS,
    METACOG_UNCERTAINTY_KEYWORDS,
    MIN_WORD_LENGTH,
    OUTPUT_QUALITY_WEIGHT,
    RCI_THRESHOLD_BASIC_THINKING,
    RCI_THRESHOLD_NON_THINKING,
    RCI_THRESHOLD_THINKING,
    REASONING_INDICATORS,
    SCORE_THRESHOLD_HIGH,
    SCORE_THRESHOLD_MED,
    SOLUTION_KEYWORDS_OPTIONS,
    SOLUTION_KEYWORDS_STEPS,
    SOLUTION_WEIGHT_OPTIONS,
    SOLUTION_WEIGHT_STEPS,
    SOLUTION_WEIGHT_STRUCTURE,
    STRUCTURE_KEYWORDS,
    THOUGHT_QUALITY_WEIGHT,
    TIER_MAPPING,
    WEIGHT_CONSISTENCY,
    WEIGHT_ERROR_DETECTION,
    WEIGHT_SOLUTION_QUALITY,
)
from .robust_metrics import (
    detect_self_correction_robust,
    score_linguistic_analysis_objective,
)


class ReasoningEvaluator:
    """Evaluator class for Reasoning benchmarks.

    Encapsulates all scoring logic (Chain of Thought, Paradoxes, Deadlocks, etc.).
    """

    def __init__(self, asset: dict[str, Any]) -> None:
        """Initialize the evaluator with asset configuration."""
        self.asset = asset
        # Dispatcher Mapping
        self._scorers = {
            "reasoning_5c_001": self._score_5c_paradox,
            "reasoning_5d_001": self._score_5d_deadlock,
            "reasoning_5b_001": self._score_5b_complex,
            "reasoning_metacog_001": self._score_metacog_001,
            "reasoning_metacog_002": self._score_metacog_002,
            "reasoning_metacog_003": self._score_metacog_003,
            "reasoning_metacog_004": self._score_metacog_004,
            "reasoning_metacog_005": self._score_metacog_005,
        }

    def score_response(self, response: str) -> dict[str, Any]:
        """Customize scoring for reasoning.

        Refactored to reduce complexity (Facade Pattern).
        """
        asset_id = self.asset["metadata"]["id"]
        expected_output = self.asset.get("expected_output", {})

        # Strategy Pattern for Scoring
        if handler := self._scorers.get(asset_id):
            # FIX: Metacognition assets require RAW response (with tags).
            # Other assets (5b, 5c, etc.) require CLEAN options (without tags).
            if "metacog" in asset_id:
                input_text = response
            else:
                input_text = self._strip_thinking_tags(response)

            total_score, score_breakdown, details = handler(input_text)
        elif (
            isinstance(expected_output, dict)
            and "required_findings" in expected_output
        ):
            clean_response = self._strip_thinking_tags(response)
            findings = cast("list[str]", expected_output["required_findings"])
            total_score, score_breakdown, details = self._score_standard_asset(
                clean_response, findings,
            )
        else:
            clean_response = self._strip_thinking_tags(response)
            total_score, score_breakdown, details = self._score_similarity_fallback(
                clean_response,
            )

        # Normierung auf MAX_SCORE
        total_score = min(total_score, MAX_SCORE)

        # --- Tier Classification & Metadata Tagging ---
        tier_type = self._determine_tier(asset_id)

        # Assemble Result
        def get_score_val(value: Any) -> float:  # noqa: ANN401
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
        """Determine the reasoning tier based on asset ID from configuration."""
        for tier_name, assets in TIER_MAPPING.items():
            if asset_id in assets:
                return tier_name
        return "Tier 1 (Operational Logic)"

    def _strip_thinking_tags(self, text: str) -> str:
        """Remove <think>...</think> blocks from DeepSeek R1 responses.

        These blocks contain internal reasoning that should not be scored.
        """
        if not text:
            return ""
        # Remove multiline <think> blocks
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def _score_5b_complex(
        self, response: str,
    ) -> tuple[float, dict[str, Any], list[str]]:
        """Tier 2: Asset 5B - Complex Reasoning Chains (System Thinking).

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
            resp_lower, ASSET_5B_SOLUTION_KEYWORDS,
        )

        # 2. Prioritization Check (Tier 3 Check)
        # Look for numbered lists or explicit prioritization language
        # Regex looks for patterns like "1. ", "2. ", "Step 1:", "First:", etc.
        has_numbering = bool(
            re.search(
                r"(?:^|\n)\s*(?:\d+\.|step \d|phase \d)", response, re.IGNORECASE,
            ),
        )
        has_prio_kw = self._contains_any(resp_lower, ASSET_5B_PRIO_KEYWORDS)
        has_prioritization = has_numbering and has_prio_kw

        # --- SCORING LOGIC ---

        # Base Points: Error Detection (Max 40)
        error_pts = 0.0
        if has_root_cause:
            error_pts += 20.0
            details.append(
                "✅ Root Cause: Identified Versioning/Deprecation inconsistency.",
            )
        else:
            details.append(
                "❌ Root Cause: "
                "Missed the core versioning/deprecation strategy issue.",
            )

        if has_cross_domain:
            error_pts += 20.0
            details.append(
                "✅ Cross-Domain: "
                "Identified need for alignment between Code/Docs/UX.",
            )
        else:
            details.append(
                "❌ Cross-Domain: Missed the systemic link between domains.",
            )

        # Solution Quality (Max 50)
        # Tier 2: Integrated Solution (Base 30)
        # Tier 3: Prioritization (+20)
        solution_pts = 0.0

        if has_integrated_solution:
            solution_pts += SCORE_THRESHOLD_MED
            details.append(
                "✅ Solution: Proposed a unified policy/governance approach.",
            )

            # Check for Tier 3 (Prioritization) ONLY if solution is valid
            if has_prioritization:
                solution_pts += 20.0
                details.append(
                    "✅ Prioritization: "
                    "Structured plan with clear steps/priorities.",
                )
            else:
                details.append(
                    "⚠️ Prioritization: Solution is good, "
                    "but lacks clear prioritization steps (Tier 3 missed).",
                )
        # Partial credit for "fixing" things without policy
        elif "fix" in resp_lower or "korrigieren" in resp_lower:
            solution_pts = 10.0
            details.append(
                "⚠️ Solution: "
                "Proposed fixes but missed the 'Unified Policy' aspect.",
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
            "consistency": consistency_pts,
        }

        return total_score, score_breakdown, details

    def _score_5c_paradox(
        self, response: str,
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
                    "❌ Logic Fail: Physics violation (Walls too early) "
                    "(+15 Awareness)",
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
                f"✅ Logic Pass: Model refused invalid constraints ({MAX_SCORE} pts).",
            )

        elif has_awareness:
            # PARTIAL
            score_breakdown["error_detection"] = WEIGHT_ERROR_DETECTION * 0.6
            score_breakdown["solution_quality"] = WEIGHT_SOLUTION_QUALITY * 0.5
            total_score = 49.0
            details.append(
                "⚠️ Partial Logic: "
                "Constraints recognized, but no clear refusal (~49 pts).",
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
        self, response: str,
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
                    "Identified circular dependency but was slightly optimistic.",
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
                    "Recognized complexity/risk but missed the deadlock.",
                ],
            )

        # LEVEL 4: FAIL (0)
        return (
            0.0,
            breakdown,
            ["❌ Logic Fail: Optimism Bias. Failed to identify deadlock or risks."],
        )

    def _score_standard_asset(
        self, response: str, required_findings: list[str],
    ) -> tuple[float, dict[str, Any], list[str]]:
        """Score 5A, 5B using finding keywords."""
        resp_lower = response.lower()
        details = []
        score_breakdown: dict[str, Any] = {}
        total_score = 0.0

        # 1. Error Detection (Match Keywords)
        error_score = self._measure_error_detection(
            resp_lower, required_findings, self.asset,
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
            total_score, score_breakdown, details, response,
        )

    def _measure_error_detection(
        self, resp_lower: str, required_findings: list[str], asset: dict[str, Any],
    ) -> float:
        """Calculate error detection score based on keyword matches."""
        matches = 0
        for finding in required_findings:
            keywords = [w.lower() for w in finding.split() if len(w) >= MIN_WORD_LENGTH]
            if not keywords:
                continue

            found_words = sum(1 for w in keywords if w in resp_lower)
            if found_words / len(keywords) >= MATCH_THRESHOLD_WEAK:
                matches += 1

        error_cfg = cast(
            "dict[str, Any]", asset.get("scoring", {}).get("error_detection", {}),
        )
        error_max = float(error_cfg.get("points", WEIGHT_ERROR_DETECTION))

        if matches >= len(required_findings):
            return error_max
        return (matches / len(required_findings)) * error_max

    def _measure_solution_quality(
        self, resp_lower: str, asset: dict[str, Any],
    ) -> float:
        """Calculate solution quality score based on structure patterns."""
        qual_cfg = cast(
            "dict[str, Any]", asset.get("scoring", {}).get("solution_quality", {}),
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
        """Measure consistency, add it to totals, and return final standard result."""
        const_cfg = cast(
            "dict[str, Any]", self.asset.get("scoring", {}).get("consistency", {}),
        )
        const_max = float(const_cfg.get("points", WEIGHT_CONSISTENCY))
        sc, _ = self._score_consistency(response, {"points": const_max})

        score_breakdown["consistency"] = sc
        total_score += sc
        details.append(f"Consistency: {sc:.1f}/{const_max}")

        return total_score, score_breakdown, details

    def _score_similarity_fallback(
        self, response: str,
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
        self, response: str, config: dict[str, Any],
    ) -> tuple[float, list[str]]:
        """Evaluate consistency for reasoning tests."""
        score = 0.0
        details: list[str] = []
        max_points = float(config.get("points", WEIGHT_CONSISTENCY))

        resp_lower = response.lower()

        has_reasoning = self._contains_any(resp_lower, REASONING_INDICATORS)
        has_correction = self._contains_any(resp_lower, CORRECTION_INDICATORS)

        if has_reasoning and has_correction:
            score = max_points
            details.append(
                f"✓ Konsistenz: Reasoning und Korrektur vorhanden (+{score}p)",
            )
        elif has_reasoning or has_correction:
            score = max_points / 2
            details.append(
                f"~ Teilweise konsistent: Reasoning/Korrektur gefunden ({score}p)",
            )
        else:
            details.append("✗ Inkonsistent: Kein Reasoning-Prozess erkennbar")

        return score, details

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        """Check if any keyword exists in text."""
        return any(k in text for k in keywords)

    # ========================================================================
    # METACOGNITION PARSING & DETECTION (Tier 3)
    # ========================================================================

    def parse_thought_tags(self, response: str) -> dict[str, Any]:
        """Extract <thought> and answer content from response.

        Supports multiple tag formats: <thought>, <think>, <thinking>, <reason>.

        Returns:
            dict with keys: thought_content, thought_length,
            answer_content, has_thought_tags

        """
        # Try different thought tag patterns (for different models)
        thought_patterns = [
            (r"<thought>(.*?)</thought>", "<thought>"),
            (r"<think>(.*?)</think>", "<think>"),           # DeepSeek R1
            (r"<thinking>(.*?)</thinking>", "<thinking>"),  # Alternative
            (r"<reason>(.*?)</reason>", "<reason>"),        # Alternative
        ]

        for pattern, tag_name in thought_patterns:
            thought_match = re.search(pattern, response, re.DOTALL)
            if thought_match:
                thought_content = thought_match.group(1).strip()
                thought_length = len(thought_content.split())

                # Extract answer (everything after closing tag)
                answer_start = thought_match.end()
                answer_content = response[answer_start:].strip()

                return {
                    "has_thought_tags": True,
                    "thought_content": thought_content,
                    "thought_length": thought_length,
                    "answer_content": answer_content,
                    "thought_tag_type": tag_name,
                }

        # Fallback: Look for "Answer:" or "Final Answer:" separator
        # Many models (including DeepSeek R1 via Ollama sometimes) output reasoning text
        # followed by "Answer: X" without XML tags.
        split_patterns = [
            r"\nAnswer:",
            r"\nFinal Answer:",
            r"\n\*\*Answer:",
            r"\n\*\*Final Answer:",
            r"Answer: ", # Case where it's not on new line but clearly labeled
        ]

        for pattern in split_patterns:
            split_match = re.search(pattern, response, re.IGNORECASE)
            if split_match:
                thought_content = response[:split_match.start()].strip()
                # answer_content usually includes the label (e.g. "Answer: X")
                answer_content = response[split_match.start():].strip()

                # If thought is substantial (>5 words), treat it as thought
                if len(thought_content.split()) > 5:
                    return {
                        "has_thought_tags": True, # Virtual tags
                        "thought_content": thought_content,
                        "thought_length": len(thought_content.split()),
                        "answer_content": answer_content,
                        "thought_tag_type": "implicit_separator",
                    }

        # No thought tags found
        return {
            "has_thought_tags": False,
            "thought_content": "",
            "thought_length": 0,
            "answer_content": response.strip(),
            "thought_tag_type": None,
            }

    def detect_self_correction(self, thought: str) -> bool:
        """Detect self-correction keywords in thought process."""
        return self._contains_any(thought.lower(), METACOG_SELF_CORRECTION_KEYWORDS)

    def detect_alternatives(self, thought: str) -> int:
        """Count alternative approach indicators in thought."""
        return sum(
            1 for kw in METACOG_ALTERNATIVES_KEYWORDS
            if kw in thought.lower()
        )

    def detect_iteration(self, thought: str) -> bool:
        """Detect iterative refinement keywords in thought."""
        return self._contains_any(thought.lower(), METACOG_ITERATION_KEYWORDS)

    def detect_confidence(self, thought: str) -> dict[str, Any]:
        """Analyze confidence expression in thought.

        Returns:
            dict with keys: has_confidence, has_uncertainty, confidence_type

        """
        thought_lower = thought.lower()
        has_confidence = self._contains_any(
            thought_lower, METACOG_CONFIDENCE_KEYWORDS,
        )
        has_uncertainty = self._contains_any(
            thought_lower, METACOG_UNCERTAINTY_KEYWORDS,
        )

        confidence_type = "calibrated" if (has_confidence and has_uncertainty) \
            else ("confident" if has_confidence else "uncertain")

        return {
            "has_confidence": has_confidence,
            "has_uncertainty": has_uncertainty,
            "confidence_type": confidence_type,
        }

    # ========================================================================
    # METACOGNITION SCORING FUNCTIONS (Tier 3)
    # ========================================================================

    def _score_metacog_001(
        self, response: str,
    ) -> tuple[float, dict[str, Any], list[str]]:
        """Tier 3: Asset METACOG_001 - The Sheep Trap (Self-Correction).

        Scoring Dimensions:
        - Self-Correction (40): Catches and corrects initial wrong instinct
        - Linguistic Analysis (30): Quality of thought process (explicitly
          analyzing "all but 9")
        - Output Correctness (30): Final answer must be 9
        """
        parsed = self.parse_thought_tags(response)
        details: list[str] = []
        breakdown: dict[str, float] = {
            "self_correction": 0.0,
            "linguistic_analysis": 0.0,
            "output_correctness": 0.0,
        }

        # 1. Self-Correction Check (40 pts) - HYBRID MULTI-LAYER DETECTION
        correction_result = detect_self_correction_robust(
            thought=parsed["thought_content"],
            answer=parsed["answer_content"],
            expected_answer="9",
        )
        breakdown["self_correction"] = correction_result["score"]
        details.extend(correction_result["evidence"])

        # 2. Linguistic Analysis (30 pts) - OBJECTIVE CRITERIA
        linguistic_result = score_linguistic_analysis_objective(
            thought=parsed["thought_content"],
            answer=parsed["answer_content"],
            phrase="all but 9",
        )
        breakdown["linguistic_analysis"] = linguistic_result["score"]
        details.extend(linguistic_result["evidence"])

        # 3. Output Correctness (30 pts) - FIX: Check last numeric token (final answer)
        answer_lower = parsed["answer_content"].lower().strip()
        # Extract the last number mentioned as the final answer
        numbers = re.findall(r"\d+", answer_lower)
        final_number = numbers[-1] if numbers else None

        if final_number == "9":
            breakdown["output_correctness"] = 30.0
            details.append("✅ Output: Correct answer (9).")
        else:
            breakdown["output_correctness"] = 0.0
            found_val = final_number if final_number else "none"
            details.append(
                f"❌ Output: Wrong answer. Expected 9, got {found_val}.",
            )

        total_score = sum(breakdown.values())

        return total_score, breakdown, details

    def _score_metacog_002(
        self, response: str,
    ) -> tuple[float, dict[str, Any], list[str]]:
        """Tier 3: Asset METACOG_002 - The Green Sky (False Premise Challenge).

        Scoring Dimensions:
        - Premise Challenge (50): Rejects false premise with keywords like
          "not green", "sky is blue", "false premise"
        - Factual Correction (30): Provides correct fact (sky is blue) with
          explanation
        - Thought Quality (20): Quality of reasoning process
        """
        parsed = self.parse_thought_tags(response)
        details: list[str] = []
        breakdown: dict[str, float] = {
            "premise_challenge": 0.0,
            "factual_correction": 0.0,
            "thought_quality": 0.0,
        }

        answer = parsed["answer_content"].lower()
        thought = parsed["thought_content"].lower()
        combined = (answer + " " + thought).lower()

        # 1. Premise Challenge (50 pts) - EXPANDED PATTERNS FOR ROBUSTNESS
        # Must EXPLICITLY identify that the question's premise is wrong
        has_premise_challenge = any(phrase in combined for phrase in [
            "the question asks about a green sky",
            "the premise is that the sky is green",
            "the question assumes a green sky",
            "the question assumes the sky is green",
            "question is based on a false premise",
            "based on a false assumption",
            "the premise is false",
            "this premise is wrong",
            "false premise",
            "incorrect premise",
            "wrong assumption",
            "the assumption is false",
            "the setup is wrong",
        ])

        if has_premise_challenge and "blue" in answer:
            breakdown["premise_challenge"] = 50.0
            details.append(
                "✅ Premise Challenge: Explicitly identified false premise "
                "about green sky.",
            )
        else:
            breakdown["premise_challenge"] = 0.0
            details.append(
                "❌ Premise Challenge: Did not explicitly identify false premise.",
            )

        # 2. Factual Correction (30 pts) - REQUIRE REAL PHYSICS EXPLANATION
        has_blue = "blue" in answer
        has_rayleigh = "rayleigh" in combined
        has_wavelength = "wavelength" in combined
        has_shorter = (
            "shorter" in combined
            or "short" in combined
            or "blue light" in combined
        )
        has_scatter_generic = "scatter" in combined or "scattering" in combined

        # Require EITHER Rayleigh OR (Wavelength + Context)
        has_physics_explanation = has_rayleigh or (has_wavelength and has_shorter)

        if has_blue and has_physics_explanation:
            breakdown["factual_correction"] = 30.0
            details.append(
                "✅ Factual Correction: Sky is blue with physics explanation.",
            )
        elif has_blue and has_scatter_generic:
            # Partial credit: Generic scatter mention is better than nothing
            # but not real physics
            breakdown["factual_correction"] = 20.0
            details.append(
                "⚠️ Partial: States sky is blue with generic scatter mention.",
            )
        elif has_blue:
            breakdown["factual_correction"] = 15.0
            details.append("⚠️ Minimal: States sky is blue but no explanation.")
        else:
            breakdown["factual_correction"] = 0.0
            details.append("❌ Factual Correction: Missing or incorrect fact.")

        # 3. Thought Quality (20 pts) - REQUIRE SUBSTANTIVE REASONING
        has_substantial_thought = (
            parsed["has_thought_tags"] and parsed["thought_length"] > 30
        )

        if has_substantial_thought and has_physics_explanation:
            breakdown["thought_quality"] = 20.0
            details.append(
                f"✅ Thought Quality: Substantial reasoning with physics "
                f"({parsed['thought_length']} words).",
            )
        elif has_substantial_thought:
            breakdown["thought_quality"] = 10.0
            details.append(
                f"⚠️ Thought Quality: Some reasoning but shallow physics "
                f"({parsed['thought_length']} words).",
            )
        else:
            breakdown["thought_quality"] = 0.0
            details.append("❌ Thought Quality: Insufficient reasoning shown.")

        total_score = sum(breakdown.values())

        return total_score, breakdown, details

    def _score_metacog_003(
        self, response: str,
    ) -> tuple[float, dict[str, Any], list[str]]:
        """Tier 3: Asset METACOG_003 - The Two Doors (Alternative Exploration).

        Scoring Dimensions:
        - Alternative Exploration (40): Explores 2+ approaches
        - Logical Correctness (30): Sound logic
        - Thought Depth (30): Depth of analysis
        """
        parsed = self.parse_thought_tags(response)
        details: list[str] = []
        breakdown: dict[str, float] = {
            "alternative_exploration": 0.0,
            "logical_correctness": 0.0,
            "thought_depth": 0.0,
        }

        answer = parsed["answer_content"].lower()

        # 1. Alternative Exploration (40 pts)
        alt_count = self.detect_alternatives(parsed["thought_content"])

        if alt_count >= 2:
            breakdown["alternative_exploration"] = 40.0
            details.append(
                f"✅ Alternatives: Explored {alt_count} distinct approaches.",
            )
        elif alt_count == 1:
            breakdown["alternative_exploration"] = 20.0
            details.append("⚠️ Partial: Mentioned alternatives but limited depth.")
        else:
            breakdown["alternative_exploration"] = 0.0
            details.append("❌ Alternatives: Only single approach, no alternatives.")

        # 2. Logical Correctness (30 pts)
        has_logic_keywords = self._contains_any(
            answer, ["logic", "logically", "reason", "because"],
        )
        if has_logic_keywords:
            breakdown["logical_correctness"] = 30.0
            details.append("✅ Logic: Sound reasoning demonstrated.")
        else:
            breakdown["logical_correctness"] = 15.0
            details.append("⚠️ Logic: Limited explicit logical reasoning.")

        # 3. Thought Depth (30 pts)
        if parsed["thought_length"] > 50:
            breakdown["thought_depth"] = 30.0
            details.append(
                f"✅ Depth: Thorough analysis ({parsed['thought_length']} words).",
            )
        elif parsed["thought_length"] > 25:
            breakdown["thought_depth"] = 15.0
            details.append(
                f"⚠️ Depth: Moderate analysis ({parsed['thought_length']} words).",
            )
        else:
            breakdown["thought_depth"] = 0.0
            details.append("❌ Depth: Insufficient analysis.")

        total_score = sum(breakdown.values())
        return total_score, breakdown, details

    def _score_metacog_004(
        self, response: str,
    ) -> tuple[float, dict[str, Any], list[str]]:
        """Tier 3: Asset METACOG_004 - Monty Hall (Iterative Refinement).

        Scoring Dimensions:
        - Iterative Refinement (35): Shows initial → reconsider → final
        - Probability Analysis (35): Correct probability (2/3)
        - Output Correctness (30): Answer is "switch" and mentions 2/3
        """
        parsed = self.parse_thought_tags(response)
        details: list[str] = []
        breakdown: dict[str, float] = {
            "iterative_refinement": 0.0,
            "probability_analysis": 0.0,
            "output_correctness": 0.0,
        }

        thought = parsed["thought_content"].lower()
        answer = parsed["answer_content"].lower()

        # 1. Iterative Refinement (35 pts)
        has_iteration = self.detect_iteration(parsed["thought_content"])

        if has_iteration and ("initial" in thought or "first" in thought):
            breakdown["iterative_refinement"] = 35.0
            details.append(
                "✅ Iteration: Shows initial → reconsider → final structure.",
            )
        elif has_iteration:
            breakdown["iterative_refinement"] = 20.0
            details.append("⚠️ Partial: Some iterative elements but not complete flow.")
        else:
            breakdown["iterative_refinement"] = 0.0
            details.append("❌ Iteration: No iterative reasoning shown.")

        # 2. Probability Analysis (35 pts)
        if "2/3" in answer or "67" in answer or "two-thirds" in answer:
            breakdown["probability_analysis"] = 35.0
            details.append("✅ Probability: Correct probability analysis (2/3).")
        elif "switch" in answer and "probability" in answer:
            breakdown["probability_analysis"] = 20.0
            details.append(
                "⚠️ Partial: Correct conclusion but weak probability explanation.",
            )
        else:
            breakdown["probability_analysis"] = 0.0
            details.append("❌ Probability: Missing or incorrect analysis.")

        # 3. Output Correctness (30 pts)
        if "switch" in answer and ("2/3" in answer or "67" in answer):
            breakdown["output_correctness"] = 30.0
            details.append(
                "✅ Output: Correct answer (switch) with correct probability.",
            )
        elif "switch" in answer:
            breakdown["output_correctness"] = 15.0
            details.append(
                "⚠️ Partial: Correct answer but incomplete probability explanation.",
            )
        else:
            breakdown["output_correctness"] = 0.0
            details.append("❌ Output: Wrong answer. Expected switch to door 2.")

        total_score = sum(breakdown.values())
        return total_score, breakdown, details

    def _score_metacog_005(
        self, response: str,
    ) -> tuple[float, dict[str, Any], list[str]]:
        """Tier 3: Asset METACOG_005 - Birthday Paradox (Uncertainty Calibration).

        Scoring Dimensions:
        - Counter-Intuitive Acknowledgment (20): Recognizes surprise
        - Calculation Correctness (30): ~50% or 48-51%
        - Confidence Expression (25): Expresses confidence
        - Confidence Calibration (25): HIGH confidence despite counter-intuitive
        """
        parsed = self.parse_thought_tags(response)
        details: list[str] = []
        breakdown: dict[str, float] = {
            "counter_intuitive_acknowledgment": 0.0,
            "calculation_correctness": 0.0,
            "confidence_expression": 0.0,
            "confidence_calibration": 0.0,
        }

        answer = parsed["answer_content"].lower()

        # 1. Counter-Intuitive Acknowledgment (20 pts)
        has_uncertainty = self._contains_any(answer, METACOG_UNCERTAINTY_KEYWORDS)

        if has_uncertainty:
            breakdown["counter_intuitive_acknowledgment"] = 20.0
            details.append(
                "✅ Counter-Intuitive: Model acknowledged surprising nature.",
            )
        else:
            breakdown["counter_intuitive_acknowledgment"] = 0.0
            details.append(
                "❌ Counter-Intuitive: Missed acknowledging surprising result.",
            )

        # 2. Calculation Correctness (30 pts)
        # Extract percentage from answer
        percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", answer)
        if percent_match:
            percentage = float(percent_match.group(1))
            if 48 <= percentage <= 51:
                breakdown["calculation_correctness"] = 30.0
                details.append(f"✅ Calculation: Correct probability (~{percentage}%).")
            else:
                breakdown["calculation_correctness"] = 0.0
                details.append(
                    f"❌ Calculation: Wrong percentage ({percentage}%). "
                    "Expected 48-51%.",
                )
        else:
            breakdown["calculation_correctness"] = 0.0
            details.append("❌ Calculation: No percentage found in answer.")

        # 3. Confidence Expression (25 pts)
        conf_result = self.detect_confidence(parsed["thought_content"])

        if conf_result["has_confidence"]:
            breakdown["confidence_expression"] = 25.0
            details.append("✅ Confidence: Model expressed confidence level.")
        else:
            breakdown["confidence_expression"] = 0.0
            details.append("❌ Confidence: No confidence expression found.")

        # 4. Confidence Calibration (25 pts)
        if conf_result["confidence_type"] == "calibrated":
            breakdown["confidence_calibration"] = 25.0
            details.append(
                "✅ Calibration: Appropriate high confidence despite "
                "counter-intuitive result.",
            )
        elif conf_result["has_confidence"]:
            breakdown["confidence_calibration"] = 15.0
            details.append(
                "⚠️ Calibration: Confidence expressed but may not match "
                "counter-intuitive nature.",
            )
        else:
            breakdown["confidence_calibration"] = 0.0
            details.append(
                "❌ Calibration: No confidence or poor calibration.",
            )

        total_score = sum(breakdown.values())
        return total_score, breakdown, details


# ============================================================================
# RCI CALCULATION & CLASSIFICATION (Module-Level Functions)
# ============================================================================

def calculate_rci(
    tier1_2_scores: list[float],
    tier3_scores: list[float],
) -> float:
    """Calculate Reasoning Complexity Index (RCI).

    Formula: RCI = (Avg_Output_Tier1+2 x 0.6) + (Avg_Thought_Tier3 x 0.4)

    Args:
        tier1_2_scores: List of output quality scores from Tier 1-2 assets
        tier3_scores: List of thought quality scores from Tier 3 assets

    Returns:
        RCI score (0-100)

    """
    avg_output = (sum(tier1_2_scores) / len(tier1_2_scores)) if tier1_2_scores else 0.0
    avg_thought = (sum(tier3_scores) / len(tier3_scores)) if tier3_scores else 0.0

    rci = (avg_output * OUTPUT_QUALITY_WEIGHT) + (avg_thought * THOUGHT_QUALITY_WEIGHT)
    return min(rci, MAX_SCORE)


def classify_model(rci: float) -> str:
    """Classify model based on RCI score.

    Classification:
    - Non-Thinking: RCI < 50%
    - Basic Thinking: RCI 50-70%
    - Thinking: RCI 70-85%
    - Deep Thinking: RCI > 85%

    Args:
        rci: Reasoning Complexity Index score (0-100)

    Returns:
        Classification string

    """
    if rci < RCI_THRESHOLD_NON_THINKING:
        return "Non-Thinking Model"
    if rci < RCI_THRESHOLD_BASIC_THINKING:
        return "Basic Thinking Model"
    if rci < RCI_THRESHOLD_THINKING:
        return "Thinking Model"
    return "Deep Thinking Model"
