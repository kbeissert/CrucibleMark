"""
Multi-layer metacognition evaluation framework.
Provides robust, hybrid detection of cognitive skills.
"""

from typing import Any, TypedDict


class CorrectionDetectionResult(TypedDict):
    """Result of self-correction detection."""
    score: float
    evidence: list[str]
    has_self_correction: bool
    layers_matched: list[str]


class LinguisticAnalysisResult(TypedDict):
    """Result of linguistic analysis."""
    score: float
    evidence: list[str]
    phrase_mentioned: bool
    semantic_explanation: bool
    answer_contrast: bool


class ThoughtQualityResult(TypedDict):
    """Result of thought quality assessment."""
    score: float
    evidence: list[str]
    dimensions: dict[str, bool]


def detect_self_correction_robust(
    thought: str, answer: str, expected_answer: str = "9"
) -> CorrectionDetectionResult:
    """
    Multi-layer self-correction detection (Hybrid Approach).
    
    Layer 1 (20pts): Explicit correction keywords
    Layer 2 (20pts): Structural revision pattern ("Initially... but actually...")
    Layer 3 (10pts): Answer trajectory (wrong → correct)
    
    Args:
        thought: Model's thinking process
        answer: Model's final answer
        expected_answer: Ground truth answer (for trajectory analysis)
    
    Returns:
        CorrectionDetectionResult with score and evidence
    """
    score = 0.0
    evidence = []
    layers_matched = []
    
    thought_lower = thought.lower()
    
    # Layer 1: Explicit correction keywords (20pts)
    # ============================================
    explicit_keywords = [
        "but i was wrong",
        "let me reconsider",
        "actually, that's incorrect",
        "wait, i made a mistake",
        "i was wrong",
        "i made an error",
        "my mistake",
        "correction:",
        "actually, no",
        "on second thought",
    ]
    
    if any(kw in thought_lower for kw in explicit_keywords):
        score += 20.0
        evidence.append("✅ Layer 1: Explicit correction keyword detected")
        layers_matched.append("explicit_keywords")
    
    # Layer 2: Structural revision pattern (20pts)
    # ============================================
    # Pattern 1: "Initially/First... but/however/actually..."
    initial_indicators = [
        "initially", "at first", "first thought", "first, i thought",
        "my first instinct", "i initially thought"
    ]
    
    revision_indicators = [
        "but actually", "however", "reconsidering", "wait,", "but then",
        "on second thought", "let me reconsider", "actually, no"
    ]
    
    has_initial = any(ind in thought_lower for ind in initial_indicators)
    has_revision = any(ind in thought_lower for ind in revision_indicators)
    
    if has_initial and has_revision:
        score += 20.0
        evidence.append("✅ Layer 2: Revision structure detected (Initial → Revision)")
        layers_matched.append("revision_structure")
    
    # Layer 3: Answer trajectory analysis (10pts)
    # ============================================
    # Pattern: Wrong answer mentioned, then corrected to right answer
    # E.g., "17-9=8" is mentioned, then corrected to "9"
    
    wrong_answer_patterns = [
        "17-9=8",
        "8 sheep",
        "eight sheep",
        "=8",
    ]
    
    has_wrong_mention = any(pattern in thought for pattern in wrong_answer_patterns)
    has_correct_answer = expected_answer in answer.lower()
    
    if has_wrong_mention and has_correct_answer:
        score += 10.0
        evidence.append("✅ Layer 3: Answer trajectory (wrong → correct) detected")
        layers_matched.append("answer_trajectory")
    
    return CorrectionDetectionResult(
        score=min(score, 40.0),  # Max 40pts for self-correction
        evidence=evidence,
        has_self_correction=score > 0,
        layers_matched=layers_matched
    )


def score_linguistic_analysis_objective(
    thought: str, answer: str, phrase: str = "all but 9"
) -> LinguisticAnalysisResult:
    """
    Objective linguistic analysis scoring with clear criteria.
    
    Criterion 1 (10pts): Phrase mentioned
    Criterion 2 (20pts): Semantic explanation provided
    Criterion 3 (10pts): Contrasts with wrong interpretation
    
    Args:
        thought: Model's thinking
        answer: Model's answer
        phrase: Phrase to analyze (default: "all but 9")
    
    Returns:
        LinguisticAnalysisResult with score and evidence
    """
    score = 0.0
    evidence = []
    
    combined = (thought + " " + answer).lower()
    phrase_lower = phrase.lower()
    
    # Criterion 1: Phrase mentioned (10pts)
    # =====================================
    phrase_mentioned = phrase_lower in combined
    
    if phrase_mentioned:
        score += 10.0
        evidence.append(f"✅ Criterion 1: Phrase '{phrase}' mentioned")
    
    # Criterion 2: Semantic explanation (20pts)
    # =========================================
    # CRITICAL: Only count EXPLICIT EXPLANATIONS, not just usage
    # ✅ "all but 9 means X"         → explanation (give credit)
    # ❌ "all but 9 survive"         → usage only (no credit)
    # ❌ "all but 9 remain"          → usage only (no credit)
    
    semantic_patterns = [
        f"{phrase_lower} means",           # "all but 9 means X"
        f'"{phrase_lower}"',               # Phrase in quotes: "all but 9" means...
        f"'{phrase_lower}'",               # Phrase in single quotes: 'all but 9' means...
        "all but x means x",               # Generic explanation pattern
        f"phrase {phrase_lower}",          # "the phrase 'all but 9'..."
        "means that",                      # "all but 9 means that..."
        "that means",                      # "that means only the 9 survive"
        "means only",                      # "means only the 9 survive"
        "means 9",                         # "means 9 survive" (catches "all but 9" means 9)
        f"{phrase_lower} indicates",       # "all but 9 indicates..."
        "semantically",                    # "semantically, all but 9..."
        "expression means",                # "the expression means..."
        "refers to",                       # "all but 9 refers to..."
        "denotes",                         # "all but 9 denotes..."
    ]
    
    semantic_explanation = any(pattern in combined for pattern in semantic_patterns)
    
    if semantic_explanation:
        score += 20.0
        evidence.append("✅ Criterion 2: Semantic explanation of phrase provided")
    elif phrase_mentioned:
        evidence.append("⚠️ Criterion 2: Phrase mentioned but not explained")
    
    # Criterion 3: Contrasts wrong interpretation (10pts)
    # ==================================================
    wrong_patterns = ["17-9", "=8", "8 sheep", "eight sheep"]
    contrast_patterns = ["but not", "not", "incorrect", "wrong"]
    
    has_wrong_mention = any(pattern in thought for pattern in wrong_patterns)
    has_contrast = any(pattern in thought.lower() for pattern in contrast_patterns)
    
    if has_wrong_mention and has_contrast:
        score += 10.0
        evidence.append("✅ Criterion 3: Contrasts wrong interpretation")
    
    return LinguisticAnalysisResult(
        score=min(score, 30.0),  # Max 30pts for linguistic analysis
        evidence=evidence,
        phrase_mentioned=phrase_mentioned,
        semantic_explanation=semantic_explanation,
        answer_contrast=has_wrong_mention and has_contrast
    )


def measure_thought_quality_robust(
    thought: str, has_thought_tags: bool = True
) -> ThoughtQualityResult:
    """
    Structure-based thought quality assessment.
    
    Dimension 1 (5pts): Sufficient depth (>30 words)
    Dimension 2 (5pts): Structured reasoning
    Dimension 3 (5pts): Reasoning indicators
    
    Args:
        thought: The thought text to evaluate
        has_thought_tags: Whether thought tags were present
    
    Returns:
        ThoughtQualityResult with dimensional breakdown
    """
    import re
    
    score = 0.0
    evidence = []
    dimensions = {}
    
    if not has_thought_tags:
        return ThoughtQualityResult(
            score=0.0,
            evidence=["❌ No thought tags provided"],
            dimensions={"depth": False, "structure": False, "reasoning": False}
        )
    
    thought_lower = thought.lower()
    word_count = len(thought.split())
    
    # Dimension 1: Sufficient depth (5pts)
    # ====================================
    has_depth = word_count > 30
    dimensions["depth"] = has_depth
    
    if has_depth:
        score += 5.0
        evidence.append(f"✅ Dimension 1: Sufficient depth ({word_count} words)")
    else:
        evidence.append(f"❌ Dimension 1: Insufficient depth ({word_count} words < 30)")
    
    # Dimension 2: Structured reasoning (5pts)
    # ========================================
    structure_indicators = [
        bool(re.search(r'\d+\.', thought)),  # Numbered list
        "step" in thought_lower,
        ("first" in thought_lower and "second" in thought_lower),
        ("then" in thought_lower and "finally" in thought_lower),
    ]
    
    has_structure = any(structure_indicators)
    dimensions["structure"] = has_structure
    
    if has_structure:
        score += 5.0
        evidence.append("✅ Dimension 2: Structured reasoning detected")
    else:
        evidence.append("⚠️ Dimension 2: No explicit structure")
    
    # Dimension 3: Reasoning indicators (5pts)
    # ========================================
    reasoning_keywords = ["because", "therefore", "thus", "since", "implies", "so", "hence"]
    has_reasoning = any(kw in thought_lower for kw in reasoning_keywords)
    dimensions["reasoning"] = has_reasoning
    
    if has_reasoning:
        score += 5.0
        evidence.append("✅ Dimension 3: Causal reasoning detected")
    else:
        evidence.append("⚠️ Dimension 3: No explicit causal reasoning")
    
    return ThoughtQualityResult(
        score=min(score, 15.0),  # Max 15pts for structured quality
        evidence=evidence,
        dimensions=dimensions
    )
