#!/usr/bin/env python3
"""
Code Quality Test Module
Refactored using Clean Architecture (Core/MVC).
Delegates logic to benchmark_modules.code_quality.core.evaluators.
"""

import sys
import time
from pathlib import Path
from typing import Any

import yaml

from benchmark_modules.base_test import BaseTest
from benchmark_modules.code_quality.core.constants import (
    DEFAULT_TEMPERATURE,
    TOKEN_MULTIPLIER,
)
from benchmark_modules.code_quality.core.evaluators import CodeQualityEvaluator
from schemas.result import BenchmarkResult
from utils.model_utils import get_model_version
from utils.ollama_config import GLOBAL_GEN_DEFAULTS

# Ensure root directory is in sys.path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class CodeQualityTest(BaseTest):
    """
    Test module for Code Quality and Accessibility.
    Acts as a lightweight runner, delegating scoring to CodeQualityEvaluator.
    """

    def __init__(self, asset_path: Path):
        super().__init__(asset_path)
        # 1. Start with Global Defaults
        self.generation_config = GLOBAL_GEN_DEFAULTS.copy()
        # 2. Merge Module Overrides
        self._load_module_config()

    def _load_module_config(self) -> None:
        """Loads generation parameters from config.yaml and merges with defaults."""
        try:
            config_path = Path(__file__).parent / "config.yaml"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    module_gen = data.get("generation", {})
                    # Update (Override) global defaults with module specifics
                    self.generation_config.update(module_gen)
        except (OSError, yaml.YAMLError, TypeError):
            # Fallback is silent as these are optional overrides
            pass

    def execute(
        self,
        model: str,
        llm_client: Any,
        provider: str = "ollama",
        **kwargs: Any,
    ) -> BenchmarkResult:
        """
        Executes the Code Quality test for a given model.

        Args:
            model: Model identifier
            llm_client: Client for LLM interaction
            provider: Provider name (default: "ollama")
            **kwargs: Additional arguments

        Returns:
            Dict containing raw_response, execution_time, tokens_used, metadata
        """
        prompt = self.asset["prompt"]
        full_prompt = f"{self.asset.get('context', '')}\n\n{prompt}".strip()

        # Merge module config into kwargs
        # (kwargs from caller take precedence if collision, but usually config is the source)
        query_kwargs = {**self.generation_config, **kwargs}

        start = time.time()

        try:
            # Deterministic output via low temperature
            # Temperature from config overrides DEFAULT_TEMPERATURE if present in query_kwargs
            # We pop it to avoid "multiple values for keyword argument" error
            temp = query_kwargs.pop("temperature", DEFAULT_TEMPERATURE)

            response = llm_client.query(
                model,
                full_prompt,
                provider=provider,
                temperature=temp,
                **query_kwargs,
            )
            # Use clean execution time (excluding timeouts/retries) if available
            if (
                hasattr(llm_client, "last_query_duration")
                and llm_client.last_query_duration > 0
            ):
                elapsed = llm_client.last_query_duration
            else:
                elapsed = time.time() - start

            approx_tokens = int(len(response.split()) * TOKEN_MULTIPLIER)

            load_time = getattr(llm_client, "last_response_metadata", {}).get(
                "load_duration", 0.0
            )

            return BenchmarkResult(
                status="success",
                primary_score=None,
            max_score=100.0,
                rendered_value="Pending",
                raw_response=response,
                evaluated_prompt=full_prompt,
                execution_time=elapsed,
                load_time=load_time,
                tokens_used=approx_tokens,
                tokens_per_second=getattr(llm_client, "last_response_metadata", {}).get("tokens_per_second", 0.0),
                finish_reason=getattr(llm_client, "last_response_metadata", {}).get("finish_reason"),
                token_limit_cutoff=getattr(llm_client, "last_response_metadata", {}).get("token_limit_cutoff", False),
                token_limit_fallback=getattr(llm_client, "last_response_metadata", {}).get("token_limit_fallback", False),
                token_limit_used=getattr(llm_client, "last_response_metadata", {}).get("token_limit_used"),
                cost_usd=getattr(llm_client, "last_request_cost", 0.0),
                model_version=get_model_version(model_name=model, provider=provider),
                meta={
                    "model": model,
                    "asset_id": self.asset["metadata"]["id"],
                    "prompt_length": len(full_prompt),
                    **getattr(llm_client, "last_response_metadata", {}),
                },
            )
        except (OSError, RuntimeError, ValueError) as e:
            return BenchmarkResult(
                status="error",
                primary_score=0.0,
                rendered_value="ERROR",
                raw_response=str(e),
                evaluated_prompt="",
                execution_time=0.0,
                load_time=0.0,
                tokens_used=0,
                tokens_per_second=0.0,
                finish_reason="error",
                token_limit_cutoff=False,
                token_limit_fallback=False,
                token_limit_used=None,
                cost_usd=0.0,
                model_version=get_model_version(model_name=model, provider=provider),
                meta={
                    "model": model,
                    "asset_id": self.asset.get("metadata", {}).get("id", "unknown"),
                    "error": str(e),
                },
            )

    def score_response(self, result: BenchmarkResult) -> BenchmarkResult:
        """
        Delegates scoring to the core evaluator and updates the BenchmarkResult.
        """
        evaluator = CodeQualityEvaluator(self.asset)
        score_dict = evaluator.score_response(result.raw_response)

        result.primary_score = score_dict.get("score", score_dict.get("total_score"))
        result.tier = score_dict.get("tier", "Tier 1 (Undefined)")
        result.data = score_dict
        result.rendered_value = f"{result.primary_score} %" if result.primary_score is not None else "N/A"

        return result
