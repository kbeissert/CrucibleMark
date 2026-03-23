from __future__ import annotations
from utils.constants import MS_PER_SECOND
"""
LLM Judge Runner — orchestration layer.

Wires provider selection → (optional unload) → prompt building → LLM call
→ response parsing into a single cohesive score() entry point consumed by
benchmark modules.

New in Phase 2:
  - Provider fallback chain: primary → fallback on health/connection failure.
  - Ollama model unload before judge load (both-Ollama path only).
  - judge_latency_ms measured independently around provider.complete().
  - judge_provider_used recorded in every JudgeResult.
  - score_pending() accepts a PendingJudgeResult directly.

Provider selection is driven entirely by config; no branching on provider
name happens here beyond the lazy-import factory.
"""


import logging
import time
from typing import Any, Dict, Optional

from utils.constants import OLLAMA_DEFAULT_BASE_URL
from .judge_config import FallbackProviderConfig, LLMJudgeConfig
from .judge_parser import JudgeResult, parse
from .judge_prompt_builder import build_prompts
from .providers.base_provider import JudgeProviderResponse, LLMJudgeProvider

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider factory helpers
# ---------------------------------------------------------------------------


def _build_provider(config: LLMJudgeConfig) -> LLMJudgeProvider:
    """
    Instantiate the primary provider from config.

    Args:
        config: Validated LLMJudgeConfig.

    Returns:
        A concrete LLMJudgeProvider instance.

    Raises:
        ValueError: If the provider name is unrecognised.
    """
    prov_cfg = config.provider
    final_model = (
        config.module_judge_model if config.module_judge_model else prov_cfg.model
    )
    kwargs: Dict[str, Any] = {
        "model": final_model,
        "temperature": prov_cfg.temperature,
        "max_tokens": prov_cfg.max_tokens,
        "timeout_seconds": prov_cfg.timeout_seconds,
    }

    if prov_cfg.name == "anthropic":
        from .providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(**kwargs)

    if prov_cfg.name == "google":
        from .providers.google_provider import GoogleProvider

        return GoogleProvider(**kwargs)

    if prov_cfg.name == "mistral":
        from .providers.mistral_provider import MistralProvider

        return MistralProvider(**kwargs)

    if prov_cfg.name == "openai":
        from .providers.openai_provider import OpenAIProvider

        return OpenAIProvider(**kwargs)

    if prov_cfg.name == "ollama":
        from .providers.ollama_provider import OllamaProvider

        base_url = prov_cfg.base_url or OLLAMA_DEFAULT_BASE_URL
        return OllamaProvider(**kwargs, base_url=base_url)

    raise ValueError(
        f"Unknown LLM Judge provider: '{prov_cfg.name}'. "
        "Valid values: anthropic, mistral, openai, ollama, google."
    )


def _build_fallback_provider(
    fb_cfg: FallbackProviderConfig, module_judge_model: Optional[str] = None
) -> LLMJudgeProvider:
    """
    Instantiate the fallback provider from a FallbackProviderConfig.

    Args:
        fb_cfg: Validated FallbackProviderConfig.

    Returns:
        A concrete LLMJudgeProvider instance.

    Raises:
        ValueError: If the provider name is unrecognised.
    """
    final_model = module_judge_model if module_judge_model else fb_cfg.model
    kwargs: Dict[str, Any] = {
        "model": final_model,
        "temperature": fb_cfg.temperature,
        "max_tokens": fb_cfg.max_tokens,
        "timeout_seconds": fb_cfg.timeout_seconds,
    }

    if fb_cfg.name == "anthropic":
        from .providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(**kwargs)

    if fb_cfg.name == "google":
        from .providers.google_provider import GoogleProvider

        return GoogleProvider(**kwargs)

    if fb_cfg.name == "mistral":
        from .providers.mistral_provider import MistralProvider

        return MistralProvider(**kwargs)

    if fb_cfg.name == "openai":
        from .providers.openai_provider import OpenAIProvider

        return OpenAIProvider(**kwargs)

    if fb_cfg.name == "ollama":
        from .providers.ollama_provider import OllamaProvider

        base_url = fb_cfg.base_url or OLLAMA_DEFAULT_BASE_URL
        return OllamaProvider(**kwargs, base_url=base_url)

    raise ValueError(
        f"Unknown fallback provider: '{fb_cfg.name}'. "
        "Valid values: anthropic, mistral, openai, ollama, google."
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _try_complete(
    provider: LLMJudgeProvider,
    system_prompt: str,
    user_prompt: str,
    provider_label: str,
) -> Optional[JudgeProviderResponse]:
    """
    Attempt provider.complete() and return None on any exception.

    Latency is NOT measured here; callers wrap this call with time.monotonic()
    independently so they control the measurement boundary.

    Args:
        provider: The provider to call.
        system_prompt: System instruction for the judge.
        user_prompt: User payload with task, response, golden standard.
        provider_label: Human-readable label used in log messages.

    Returns:
        JudgeProviderResponse on success, None on any exception.
    """
    try:
        return provider.complete(system_prompt, user_prompt)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning(
            "LLM Judge: provider '%s' complete() failed: %s", provider_label, exc
        )
        return None


def _should_unload(
    tested_model_provider: Optional[str],
    judge_provider_name: str,
) -> bool:
    """
    Return True only when both the tested model and judge model are Ollama-based.

    Cloud providers do not share VRAM with the local Ollama instance, so
    unloading is irrelevant (and would unnecessarily evict the tested model,
    slowing the next benchmark test).
    """
    return (
        tested_model_provider is not None
        and tested_model_provider.lower() == "ollama"
        and judge_provider_name.lower() == "ollama"
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class JudgeRunner:
    """
    Orchestrates a single judge evaluation run.

    Phase-2 capabilities:
    - Fallback provider: primary → fallback on health-check failure or exception.
    - Ollama unload: evicts the tested model before loading the judge (Ollama-only).
    - Independent latency tracking: judge_latency_ms measured around complete() only.
    - Transparent response_time_ms: never modified, passed through from caller.

    Typical usage::

        runner = JudgeRunner(config)
        result = runner.score(
            task_prompt="Write a button label for a checkout action.",
            model_response="Buy Now",
            golden_standard="Short, action-oriented CTA that conveys urgency.",
            module_id="ux_writing",
        )
        print(result.score, result.judge_latency_ms, result.judge_provider_used)
    """

    def __init__(self, config: LLMJudgeConfig) -> None:
        """
        Args:
            config: Validated LLMJudgeConfig. Build one from YAML via
                    LLMJudgeConfig.from_dict(yaml_data).
        """
        self._config = config
        self._provider: Optional[LLMJudgeProvider] = None
        self._fallback_provider: Optional[LLMJudgeProvider] = None

    @property
    def provider(self) -> LLMJudgeProvider:
        """Lazily initialise the primary provider (once per runner instance)."""
        if self._provider is None:
            self._provider = _build_provider(self._config)
        return self._provider

    @property
    def fallback_provider(self) -> Optional[LLMJudgeProvider]:
        """Lazily initialise the fallback provider when configured."""
        if self._fallback_provider is None and self._config.provider.fallback:
            self._fallback_provider = _build_fallback_provider(
                self._config.provider.fallback, self._config.module_judge_model
            )
        return self._fallback_provider

    # ------------------------------------------------------------------
    # Internal: provider lifecycle helpers
    # ------------------------------------------------------------------

    def _maybe_unload_tested_model(
        self,
        tested_model_id: Optional[str],
        tested_model_provider: Optional[str],
    ) -> None:
        """
        Unload the tested Ollama model before the judge loads, if applicable.

        Sequence when unload is triggered:
          [Benchmark task complete]
          → [unload_model called — confirmed OK by Ollama]
          → [unload_delay_ms sleep (inside unload_model)]
          → [Judge model loads via complete()]

        The existing benchmark cooldown (AdaptivePauseCalculator in
        run_local_benchmark.py) runs between consecutive benchmark tasks and
        is NOT modified by this call. The unload is an additional step that
        happens immediately after the task completes, before the cooldown of
        the next iteration begins.

        Only called when both tested model and judge are Ollama-based.

        Args:
            tested_model_id: Ollama model tag of the tested model.
            tested_model_provider: Provider name for the tested model.
        """
        if not _should_unload(tested_model_provider, self._config.provider.name):
            return

        if tested_model_id is None:
            logger.debug("Ollama unload skipped: tested_model_id not provided.")
            return

        from .providers.ollama_provider import OllamaProvider

        base_url = self._config.provider.base_url or OLLAMA_DEFAULT_BASE_URL
        unload_delay_ms = self._config.provider.unload_delay_ms

        try:
            unload_provider = OllamaProvider(
                model=tested_model_id,
                temperature=0.0,
                max_tokens=1,
                timeout_seconds=self._config.provider.timeout_seconds,
                base_url=base_url,
            )
            success = unload_provider.unload_model(
                model_id=tested_model_id,
                unload_delay_ms=unload_delay_ms,
            )
            if success:
                logger.debug(
                    "Tested model '%s' unloaded from Ollama (delay=%d ms).",
                    tested_model_id,
                    unload_delay_ms,
                )
            else:
                logger.warning(
                    "Ollama unload of '%s' reported failure; continuing anyway.",
                    tested_model_id,
                )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning(
                "Exception during Ollama unload of '%s': %s", tested_model_id, exc
            )

    def _call_with_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[Optional[JudgeProviderResponse], str, str]:
        """
        Try primary provider; fall back on health-check failure or exception.

        Fallback triggers when:
          - primary.health_check() returns False, OR
          - primary.complete() raises any exception.

        Fallback does NOT trigger on parse errors (parse happens after
        complete() returns successfully).

        Args:
            system_prompt: System instruction for the judge.
            user_prompt: User payload with evaluation context.

        Returns:
            Tuple of (JudgeProviderResponse or None, provider_label_used, model_label_used).
        """
        primary_name = self._config.provider.name
        primary_model = self._config.provider.model
        fb_cfg = self._config.provider.fallback

        # -- 1. Primary API Key / environment check --
        use_primary = True
        import os

        if primary_name == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
            logger.info(
                "LLM Judge: ANTHROPIC_API_KEY not found. Skipping primary provider '%s'.",
                primary_name,
            )
            use_primary = False
        elif primary_name == "google" and not os.getenv("GOOGLE_API_KEY"):
            logger.info(
                "LLM Judge: GOOGLE_API_KEY not found. Skipping primary provider '%s'.",
                primary_name,
            )
            use_primary = False

        # -- 2. Primary health check --
        if use_primary:
            try:
                if not self.provider.health_check():
                    logger.warning(
                        "LLM Judge: primary provider '%s' health_check() returned False.",
                        primary_name,
                    )
                    use_primary = False
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.warning(
                    "LLM Judge: primary provider '%s' health_check() raised: %s",
                    primary_name,
                    exc,
                )
                use_primary = False

        # -- 3. Primary complete() --
        if use_primary:
            response = _try_complete(
                self.provider, system_prompt, user_prompt, primary_name
            )
            if response is not None:
                return response, primary_name, primary_model
            logger.warning(
                "LLM Judge: primary provider '%s' failed; checking fallback.",
                primary_name,
            )

        # -- 4. Fallback --
        if fb_cfg is None or self.fallback_provider is None:
            logger.warning(
                "LLM Judge: no fallback configured for provider '%s'; "
                "returning score=None.",
                primary_name,
            )
            return None, primary_name, primary_model

        fallback_name = fb_cfg.name
        fallback_model = fb_cfg.model
        logger.info(
            "LLM Judge: switching to fallback provider '%s' (model=%s).",
            fallback_name,
            fallback_model,
        )
        response = _try_complete(
            self.fallback_provider, system_prompt, user_prompt, fallback_name
        )
        return response, fallback_name, fallback_model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(
        self,
        task_prompt: str,
        model_response: str,
        golden_standard: str,
        module_id: str,
        rubric_override: Optional[str] = None,
        tested_model_id: Optional[str] = None,
        tested_model_provider: Optional[str] = None,
        response_time_ms: Optional[float] = None,
    ) -> JudgeResult:
        """
        Evaluate a model response and return a structured JudgeResult.

        Args:
            task_prompt: The original prompt sent to the model under test.
            model_response: The response produced by the model under test.
            golden_standard: The ideal reference output or textual rubric.
            module_id: Benchmark module identifier for role-framing.
            rubric_override: Optional explicit rubric text.
            tested_model_id: Ollama model tag of the tested model. When provided
                and both tested model and judge are Ollama-based, the tested
                model is unloaded before the judge is called.
            tested_model_provider: Provider name for the tested model
                (e.g. ``"ollama"``). Used to decide if unload is needed.
            response_time_ms: The tested model's response time in milliseconds.
                Passed through UNCHANGED — never modified by the runner.

        Returns:
            JudgeResult with score, reasoning, judge_latency_ms,
            judge_provider_used, and parse_success flag.

        Raises:
            RuntimeError: Only when scoring.fail_on_parse_error is True and
                          the score could not be parsed.
        """
        if not self._config.enabled:
            logger.debug("LLM Judge is disabled; returning empty JudgeResult.")
            return JudgeResult(
                score=None,
                reasoning="LLM Judge disabled.",
                raw_response="",
                parse_success=False,
                judge_latency_ms=None,
                judge_provider_used=None,
                judge_model_used=None,
            )

        # Unload tested model (Ollama-only; confirmed before judge loads)
        self._maybe_unload_tested_model(tested_model_id, tested_model_provider)

        scale = self._config.scoring.scale
        system_prompt, user_prompt = build_prompts(
            task_prompt=task_prompt,
            model_response=model_response,
            golden_standard=golden_standard,
            module_id=module_id,
            scale=scale,
            rubric_override=rubric_override,
        )

        logger.debug(
            "LLM Judge: evaluating module '%s' (primary='%s', model='%s').",
            module_id,
            self._config.provider.name,
            self._config.provider.model,
        )

        # Measure latency independently around the provider call only
        t_start = time.monotonic()
        provider_response, provider_used, model_used = self._call_with_fallback(
            system_prompt, user_prompt
        )
        judge_latency_ms = (time.monotonic() - t_start) * MS_PER_SECOND

        if provider_response is None:
            return JudgeResult(
                score=None,
                reasoning="",
                raw_response="",
                parse_success=False,
                judge_latency_ms=judge_latency_ms,
                judge_provider_used=None,
                judge_model_used=None,
            )

        result = parse(provider_response.raw_text)
        # Attach runner-level metadata not set by the parser
        result.judge_latency_ms = judge_latency_ms
        result.judge_provider_used = provider_used
        result.judge_model_used = model_used

        if not result.parse_success and self._config.scoring.fail_on_parse_error:
            raise RuntimeError(
                f"LLM Judge failed to parse a score from provider response. "
                f"Provider: {provider_used}, "
                f"Raw (first 300 chars): {provider_response.raw_text[:300]}"
            )

        logger.debug(
            "LLM Judge result: score=%s, parse_success=%s, "
            "provider=%s, latency=%.0f ms",
            result.score,
            result.parse_success,
            provider_used,
            judge_latency_ms,
        )
        return result

    def score_pending(self, pending: Any) -> JudgeResult:
        """
        Convenience wrapper that accepts a PendingJudgeResult from judge_handoff.

        The PendingJudgeResult's response_time_ms is passed through to score()
        unchanged. The JudgeRunner never modifies it.

        Args:
            pending: A PendingJudgeResult instance.

        Returns:
            JudgeResult with all Phase-3 fields populated.

        Raises:
            TypeError: If pending is not a PendingJudgeResult.
        """
        # Import here to avoid circular dependency at module load time
        from .judge_handoff import PendingJudgeResult  # noqa: PLC0415

        if not isinstance(pending, PendingJudgeResult):
            raise TypeError(
                f"score_pending() requires a PendingJudgeResult, got {type(pending)}"
            )

        return self.score(
            task_prompt=pending.task_prompt,
            model_response=pending.model_response,
            golden_standard=pending.golden_standard,
            module_id=pending.module_id,
            response_time_ms=pending.response_time_ms,
        )

    def score_to_100(
        self,
        task_prompt: str,
        model_response: str,
        golden_standard: str,
        module_id: str,
        rubric_override: Optional[str] = None,
        tested_model_id: Optional[str] = None,
        tested_model_provider: Optional[str] = None,
        response_time_ms: Optional[float] = None,
    ) -> Optional[float]:
        """
        Convenience wrapper that normalises the judge score to 0–100.

        Returns None if parsing failed and fail_on_parse_error is False.
        """
        result = self.score(
            task_prompt=task_prompt,
            model_response=model_response,
            golden_standard=golden_standard,
            module_id=module_id,
            rubric_override=rubric_override,
            tested_model_id=tested_model_id,
            tested_model_provider=tested_model_provider,
            response_time_ms=response_time_ms,
        )
        if result.score is None:
            return None
        scale = self._config.scoring.scale
        if scale <= 0:
            return None
        return round((result.score / scale) * 100.0, 2)

    def build_result_dict(
        self,
        task_prompt: str,
        model_response: str,
        golden_standard: str,
        module_id: str,
        rubric_override: Optional[str] = None,
        tested_model_id: Optional[str] = None,
        tested_model_provider: Optional[str] = None,
        response_time_ms: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Run the judge and return a dict ready for merging into BenchmarkResult.data.

        response_time_ms is passed through unchanged from the caller and
        included in the dict so downstream consumers have both the tested-model
        latency and the judge latency in a single structure.

        In complement mode callers can do::

            result.data["llm_judge"] = runner.build_result_dict(...)

        Returns:
            Dict with keys: score, score_normalised, reasoning, provider, model,
                            parse_success, scale, judge_latency_ms,
                            judge_provider_used, response_time_ms.
        """
        judge_result = self.score(
            task_prompt=task_prompt,
            model_response=model_response,
            golden_standard=golden_standard,
            module_id=module_id,
            rubric_override=rubric_override,
            tested_model_id=tested_model_id,
            tested_model_provider=tested_model_provider,
            response_time_ms=response_time_ms,
        )
        scale = self._config.scoring.scale
        normalised: Optional[float] = None
        if judge_result.score is not None:
            if scale > 0:
                normalised = round((judge_result.score / scale) * 100.0, 2)

        return {
            "score": judge_result.score,
            "score_normalised": normalised,
            "reasoning": judge_result.reasoning,
            "provider": self._config.provider.name,
            "model": self._config.provider.model,
            "parse_success": judge_result.parse_success,
            "scale": scale,
            "judge_latency_ms": judge_result.judge_latency_ms,
            "judge_provider_used": judge_result.judge_provider_used,
            "judge_model_used": judge_result.judge_model_used,
            "response_time_ms": response_time_ms,
        }
