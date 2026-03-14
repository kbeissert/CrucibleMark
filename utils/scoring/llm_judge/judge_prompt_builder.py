"""
Prompt builder for the LLM Judge.
Constructs system and user prompts following Chain-of-Thought best practices.

Design principles:
- Role framing: judge is a domain-expert for the specific module.
- Explicit per-level rubric: every score level has a definition + example.
- CoT mandatory: judge reasons before scoring (REASONING: ... SCORE: N).
- No hardcoded rubric text: generic rubrics are generated from scale; per-module
  overrides can be injected via rubric_override.
"""

from __future__ import annotations

import logging
from string import Template
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-specific domain descriptions for role framing
# ---------------------------------------------------------------------------
_MODULE_DOMAIN: Dict[str, str] = {
    "ux_writing": (
        "UX Writing and microcopy. You are deeply familiar with plain language principles, "
        "call-to-action clarity, error message best practices, onboarding copy, and "
        "WCAG-compliant content guidelines."
    ),
    "documentation_quality": (
        "Technical documentation. You understand structural standards (README, API docs, "
        "tutorials vs reference material), completeness critera, code example quality, "
        "and documentation-as-code workflows."
    ),
    "content_transformation": (
        "Content transformation and adaptation. You are skilled at evaluating tone shifts, "
        "audience-appropriate language, information fidelity during rewriting, and "
        "style-guide adherence."
    ),
    "reasoning_logic": (
        "Logical reasoning and problem-solving. You evaluate argument structure, "
        "step-by-step coherence, handling of edge cases, and the depth of causal analysis."
    ),
}

_DEFAULT_DOMAIN = (
    "AI output quality. You assess clarity, completeness, accuracy, and "
    "relevance against the provided golden standard."
)

# ---------------------------------------------------------------------------
# Rubric templates per scale
# ---------------------------------------------------------------------------
_RUBRIC_5: str = """Score 5 – Excellent: Fully meets the task requirements with no significant gaps.
    The response matches or surpasses the golden standard in quality, depth, and accuracy.
    Example: A complete, well-structured answer that covers all expected points.

Score 4 – Good: Mostly meets requirements with minor omissions or imprecisions.
    The core intent is addressed; small details are missing or slightly off.
    Example: A solid response that misses one secondary criterion from the rubric.

Score 3 – Adequate: Partially meets requirements. Key aspects are addressed but
    important elements are missing, vague, or inconsistent with the golden standard.
    Example: A response that covers roughly half the expected content.

Score 2 – Poor: Attempts to address the task but misses most key requirements.
    Significant inaccuracies, irrelevant content, or severe incompleteness.
    Example: A response that touches the topic but provides little useful value.

Score 1 – Unacceptable: Does not address the task, is factually wrong throughout,
    or is entirely off-topic relative to the golden standard.
    Example: A refusal, non-answer, or completely irrelevant response."""

_RUBRIC_3: str = """Score 3 – Good: Meets the task requirements with only minor gaps.
    Most key aspects from the golden standard are covered adequately.
    Example: A solid response that addresses the core problem with minimal gaps.

Score 2 – Adequate: Partially meets requirements. Some key aspects are missing
    or significantly deviate from the golden standard.
    Example: A response that addresses the main topic but skips important sub-points.

Score 1 – Poor: Fails to meet requirements. Mostly off-topic, incorrect,
    incomplete, or does not align with the golden standard.
    Example: A refusal, non-answer, or response that misses the task almost entirely."""

_RUBRIC_10: str = """Score 10 – Perfect: Flawlessly addresses every requirement; indistinguishable from the golden standard.
Score 9  – Near-perfect: Excellent response with only trivial cosmetic differences.
Score 8  – Very good: Covers all key points; minor quality differences from golden standard.
Score 7  – Good: Meets most requirements; one non-trivial gap or inaccuracy.
Score 6  – Above average: Core requirement met; two or more minor gaps.
Score 5  – Average: About half the expected quality; important points missing or shallow.
Score 4  – Below average: Multiple significant gaps; answer is useful but incomplete.
Score 3  – Poor: Touches the topic but misses most key requirements.
Score 2  – Very poor: Largely wrong, off-topic, or extremely incomplete.
Score 1  – Unacceptable: Complete failure; refusal, non-answer, or entirely irrelevant."""

_RUBRIC_BY_SCALE: Dict[int, str] = {3: _RUBRIC_3, 5: _RUBRIC_5, 10: _RUBRIC_10}

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------
_SYSTEM_TEMPLATE = Template(
    "You are a senior evaluator specialising in $domain\n\n"
    "Your task is to score an AI-generated response on a $scale-point scale. "
    "Be objective and precise. Do not reward verbosity over accuracy."
)

_USER_TEMPLATE = Template(
    "### TASK PROMPT (what the tested model was asked to do)\n"
    "$task_prompt\n\n"
    "### MODEL RESPONSE (what the tested model produced)\n"
    "$model_response\n\n"
    "### GOLDEN STANDARD (the ideal reference output)\n"
    "$golden_standard\n\n"
    "### EVALUATION RUBRIC\n"
    "$rubric\n\n"
    "---\n"
    "Reason step by step. First write your full analysis under REASONING:\n"
    "Then, output a JSON block with exactly this structure:\n"
    "```json\n"
    "{\n"
    '  "score": <1-$scale>,\n'
    '  "sub_scores": {\n'
    '    "task_compliance": <1-5>,\n'
    '    "output_quality": <1-5>,\n'
    '    "standard_adherence": <1-5>\n'
    "  }\n"
    "}\n"
    "```\n\n"
    "The JSON must be the last thing in your response.\n"
    "For the sub_scores, rate each dimension independently on a scale of 1-5:\n"
    "- 1: Poor / completely missing\n"
    "- 2: Below expectations\n"
    "- 3: Adequate / meets basic requirements\n"
    "- 4: Good / exceeds basic requirements\n"
    "- 5: Excellent / exceptional quality"
)


def build_prompts(
    task_prompt: str,
    model_response: str,
    golden_standard: str,
    module_id: str,
    scale: int,
    rubric_override: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Build the (system_prompt, user_prompt) pair for the LLM Judge.

    Args:
        task_prompt: The original prompt given to the model under test.
        model_response: The raw response produced by the model under test.
        golden_standard: The ideal reference output or rubric definition.
        module_id: Benchmark module identifier (used for role framing).
        scale: Numeric scoring scale (3, 5, or 10).
        rubric_override: Optional explicit rubric text. When provided, the
            generated generic rubric is replaced entirely.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    domain = _MODULE_DOMAIN.get(module_id, _DEFAULT_DOMAIN)
    rubric = rubric_override or _RUBRIC_BY_SCALE.get(scale, _RUBRIC_5)

    if scale not in _RUBRIC_BY_SCALE and rubric_override is None:
        logger.warning(
            "No built-in rubric for scale=%d; falling back to scale-5 rubric.", scale
        )

    system_prompt = _SYSTEM_TEMPLATE.substitute(domain=domain, scale=scale)

    clean_response = model_response.strip()
    if not clean_response:
        clean_response = "[ERROR: THE MODEL GENERATED AN EMPTY OR INVALID RESPONSE. SCORE MUST BE 1.]"

    user_prompt = _USER_TEMPLATE.substitute(
        task_prompt=task_prompt.strip(),
        model_response=clean_response,
        golden_standard=golden_standard.strip(),
        rubric=rubric,
        scale=scale,
    )
    return system_prompt, user_prompt
