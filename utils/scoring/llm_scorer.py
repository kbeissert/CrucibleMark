"""
LLM Scorer implementation.
Uses a small local LLM (e.g. qwen2.5:14b) to evaluate responses against a rubric.
"""

from typing import Any
from .base import BaseScorer


class LLMScorer(BaseScorer):
    """
    Evaluates text using an LLM as a judge.
    Requires an LLMClient instance to be passed in kwargs.
    """

    def score_response(
        self, response: str, asset: dict[str, Any], **kwargs
    ) -> dict[str, Any]:
        """
        Implementation of LLM-based scoring.

        Expected kwargs:
            - llm_client: Instance of LLMClient
            - judge_model: str (Name of model to use as judge)

        Asset Requirements:
            - scoring.evaluator_prompt: The system prompt for the judge
            - scoring.rubric: The criteria to evaluate against
        """
        llm_client = kwargs.get("llm_client")
        if not llm_client:
            return {
                "status": "error",
                "error": "LLMScorer requires 'llm_client' in kwargs",
            }

        # Fail-Fast (Review 2026-08-15): Der Scorer ist nicht implementiert
        # (siehe auskommentierte Registrierung in __init__.py). Statt eines
        # stillen 0-Scores ("skipped"), der historische Benchmarks verfälschen
        # würde, wirft er explizit — sollte je ein Asset `method: llm`
        # konfigurieren. Aktive Assets nutzen ausschließlich `llm_judge`
        # (JudgeEvaluator), nicht diesen Scorer.
        raise NotImplementedError(
            "LLMScorer is not implemented. Configure 'method: llm_judge' "
            "(JudgeEvaluator) instead — a silent 0-score placeholder would "
            "corrupt benchmark results."
        )
