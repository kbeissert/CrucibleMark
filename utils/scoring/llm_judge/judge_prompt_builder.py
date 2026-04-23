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

from utils.model_utils import get_model_identity

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
    "cli_benchmark": (
        "CLI and Shell scripting. You evaluate correctness, command line efficiency, "
        "and adherence to requested tools while accepting semantically equivalent solutions."
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

Score 1 – Very Poor: Touches the topic but is mostly incorrect or missing critical context.
    Example: A highly flawed response that barely relates to the core task.

Score 0 – Unacceptable: Does not address the task, is factually wrong throughout,
    or is entirely off-topic relative to the golden standard.
    Example: A refusal, non-answer, or completely irrelevant response."""

_RUBRIC_3: str = """Score 3 – Good: Meets the task requirements with only minor gaps.
    Most key aspects from the golden standard are covered adequately.
    Example: A solid response that addresses the core problem with minimal gaps.

Score 2 – Adequate: Partially meets requirements. Some key aspects are missing
    or significantly deviate from the golden standard.
    Example: A response that addresses the main topic but skips important sub-points.

Score 1 – Poor: Fails to meet requirements. Mostly off-topic, incorrect,
    or incomplete.
    Example: A heavily flawed response.

Score 0 – Unacceptable: Completely fails to meet requirements.
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
Score 1  – Almost Unacceptable: Barely answers the prompt, mostly irrelevant.
Score 0  – Unacceptable: Complete failure; refusal, non-answer, or entirely irrelevant."""

_RUBRIC_BY_SCALE: Dict[int, str] = {3: _RUBRIC_3, 5: _RUBRIC_5, 10: _RUBRIC_10}

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------
_SYSTEM_TEMPLATE = Template(
    "You are a senior evaluator specialising in $domain\n\n"
    "Your task is to score an AI-generated response on a $scale-point scale. "
    "Be objective and precise. Do not reward verbosity over accuracy.\n\n"
    "### LENGTH & FOCUS CONSTRAINTS (CRITICAL) ###\n"
    "- Keep your entire reasoning highly concise and strictly between 500 and 1000 words.\n"
    "- You MUST NOT write exhaustive, line-by-line analyses. Focus only on the 3-5 most critical deviations or strengths that justify your score.\n"
    "- You should use direct quotes from the model's output or the Golden Standard, but keep them extremely brief (max 1-2 lines per quote).\n"
    "- Stop writing once the most critical points are made. Do not exceed the required word limits."
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
    '  "score": <0-$scale>,\n'
    '  "sub_scores": {\n'
    '    "task_compliance": <0-5>,\n'
    '    "output_quality": <0-5>,\n'
    '    "standard_adherence": <0-5>\n'
    "  }\n"
    "}\n"
    "```\n\n"
    "The JSON must be the last thing in your response.\n"
    "For the sub_scores, rate each dimension independently on a scale of 0-5:\n"
    "- 0: Completely missing / unacceptable\n"
    "- 1: Poor / highly flawed\n"
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
    tested_model_id: Optional[str] = None,
    required_language: Optional[str] = None,
    language_weight: float = 0.20,
    token_budget_context: Optional[Dict[str, int]] = None,
    truncation_context: bool = False,
) -> Tuple[str, str]:
    """
    Build the (system_prompt, user_prompt) pair for the LLM Judge.

    Args:
        task_prompt: The original prompt given to the model under test.
        model_response: The raw response produced by the model under test.
        golden_standard: The ideal reference output or rubric definition.
        module_id: Benchmark module identifier (used for role framing).
        scale: Numeric scoring scale (3, 5, or 10).
        rubric_override: Optional explicit rubric text.
        tested_model_id: Model tag or identifier for the tested model. Used
            to provide specialized evaluation context.
        required_language: ISO-639-1 language code (e.g. ``"de"``) when the
            task prompt explicitly mandates a response language. When set, the
            judge is instructed to penalise language violations under
            task_compliance.
        language_weight: Fraction of the total score attributed to language
            compliance (default 0.20 = 20%). Displayed in the judge rubric header.
        token_budget_context: Optional dict with ``{"standard": int, "elevated": int}``
            for reasoning models. When provided, the judge is instructed to deduct
            from output_quality if the visible response is unnecessarily verbose
            beyond the standard budget.

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

    if tested_model_id:
        identity = get_model_identity(tested_model_id)
        if identity.get("tags"):
            tags_str = ", ".join(identity["tags"])
            system_prompt += (
                f"\n\n### EVALUATION CONTEXT ###\n"
                f"The model being evaluated is tagged with: {tags_str}.\n"
                "Take this into account when evaluating responses:\n"
                "- **Coder**: May be excused for ignoring socio-political nuance or failing pure writing tasks, but must excel at logic.\n"
                "- **Thinking / Reasoning**: Extremely long, thorough chain-of-thought answers are expected and should NOT be penalized for verbosity. (e.g. o1, o3, DeepSeek R1, QwQ, Magistral, GLM-5.x — models with fixed internal Chain-of-Thought)\n"
                "- **Instruct**: Focused on direct instruction following. Answers might be shorter and more direct; they lack deep reasoning steps.\n"
                "- **Preview / Test**: Experimental phase. Minor formatting or minor coherence drops might be expected.\n"
                "- **Uncensored-Abliterated**: Vector surgery might cause abrupt context termination, loop errors, or reasoning collapse.\n"
                "- **Uncensored-Finetuned**: Safe architectural baseline but may show sampling instability under complex reasoning pressure.\n"
                "- **Agentic-Orchestrator**: This model is designed as an orchestrator in multi-agent pipelines (spawning sub-agents for concrete subtasks). It may underperform on strict single-turn format tasks (e.g. exact CLI one-liners) that would normally be delegated to a specialized sub-agent. Do not penalize orchestration-style verbosity or meta-level framing.\n"
                "- **Thinking-Optional**: This model supports toggleable extended thinking (e.g. Qwen3, Gemini 2.5) but runs in standard mode here (no explicit thinking budget passed). Evaluate output quality only — do not penalize if the answer is thorough without visible chain-of-thought tags. Latency may be higher than comparable models due to internal planning steps even in standard mode."
            )

    if required_language:
        _LANG_LABELS: Dict[str, str] = {"de": "German (Deutsch)", "en": "English"}
        lang_label = _LANG_LABELS.get(required_language, required_language.upper())
        system_prompt += (
            f"\n\n## LANGUAGE COMPLIANCE (Mandatory \u2013 {int(language_weight * 100)}% of total score) ##\n"
            f"The task prompt explicitly requires the response to be in **{lang_label}**. "
            f"Check the response language **before** evaluating content quality "
            f"and apply the following deductions to `task_compliance`:\n"
            f"- Response is primarily in a **different language**: deduct **1.5 points**.\n"
            f"- Response **mixes languages** (e.g. English explanations with {lang_label} output): deduct **0.5 points**.\n"
            f"- Response is correctly and consistently in {lang_label}: no deduction."
        )

    if token_budget_context:
        _tb_standard = token_budget_context.get("standard")
        _tb_elevated = token_budget_context.get("elevated")
        if _tb_standard and _tb_elevated:
            system_prompt += (
                f"\n\n### TOKEN BUDGET NOTE (VERBOSITY PENALTY) ###\n"
                f"This is a reasoning model. An elevated token budget of **{_tb_elevated} tokens** "
                f"was granted (standard for this module: {_tb_standard} tokens) to accommodate "
                f"internal chain-of-thought / thinking tokens.\n"
                f"The elevated budget exists for internal reasoning only — it must **not** produce "
                f"a longer visible response than the task requires.\n"
                f"Apply the following deduction to `output_quality`:\n"
                f"- Visible response exceeds **{_tb_standard * 2} tokens** AND the excess is padding, "
                f"repetition, or reformatting rather than substantive quality: "
                f"**deduct 1 point from output_quality**.\n"
                f"- Concise, focused response within approximately {_tb_standard} tokens that fully "
                f"addresses the task: no deduction."
            )

    clean_response = model_response.strip()
    if not clean_response:
        clean_response = "[ERROR: THE MODEL GENERATED AN EMPTY OR INVALID RESPONSE. SCORE MUST BE 1.]"

    if truncation_context:
        system_prompt += (
            "\n\n### TRUNCATION NOTE ###\n"
            "The model response below was cut off due to token budget limits. "
            "Evaluate the **quality of the provided content independently of its completeness** — "
            "do not penalize because the response is shorter than expected or ends abruptly. "
            "Score what is present on its own merits."
        )

    user_prompt = _USER_TEMPLATE.substitute(
        task_prompt=task_prompt.strip(),
        model_response=clean_response,
        golden_standard=golden_standard.strip(),
        rubric=rubric,
        scale=scale,
    )
    return system_prompt, user_prompt
