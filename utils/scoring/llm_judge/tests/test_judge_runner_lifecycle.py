"""
Lifecycle and integration tests for judge_runner.py Phase-2 capabilities.

Covers:
- Ollama unload is called before the judge when both providers are Ollama
- Fallback provider triggers when primary health_check() returns False
- Fallback provider triggers when primary complete() raises an exception
- Fallback does NOT trigger on parse errors
- response_time_ms is passed through unchanged end-to-end
- judge_latency_ms and judge_provider_used are present in results
"""

from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from utils.scoring.llm_judge.judge_config import (
    FallbackProviderConfig,
    LLMJudgeConfig,
    ProviderConfig,
    ScoringConfig,
)
from utils.scoring.llm_judge.judge_handoff import PendingJudgeResult
from utils.scoring.llm_judge.judge_parser import JudgeResult
from utils.scoring.llm_judge.judge_runner import JudgeRunner, _should_unload
from utils.scoring.llm_judge.providers.base_provider import JudgeProviderResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(
    provider_name: str = "anthropic",
    with_fallback: bool = False,
    fallback_name: str = "ollama",
    scale: int = 5,
) -> LLMJudgeConfig:
    fallback = None
    if with_fallback:
        fallback = FallbackProviderConfig(
            name=fallback_name,  # type: ignore[arg-type]
            model="qwen2.5:14b",
            base_url="http://localhost:11434",
        )
    return LLMJudgeConfig(
        enabled=True,
        provider=ProviderConfig(
            name=provider_name,  # type: ignore[arg-type]
            model="judge-model",
            base_url="http://localhost:11434" if provider_name == "ollama" else None,
            fallback=fallback,
        ),
        scoring=ScoringConfig(scale=scale),
    )


def _make_provider_response(
    raw_text: str = "REASONING: good.\nSCORE: 4",
    provider_name: str = "anthropic",
) -> JudgeProviderResponse:
    return JudgeProviderResponse(
        raw_text=raw_text,
        model_id="judge-model",
        provider_name=provider_name,
        latency_ms=50.0,
    )


def _inject_provider(runner: JudgeRunner, mock: MagicMock) -> None:
    """Directly inject a mock as the primary provider."""
    runner._provider = mock


def _inject_fallback(runner: JudgeRunner, mock: MagicMock) -> None:
    """Directly inject a mock as the fallback provider."""
    runner._fallback_provider = mock


# ---------------------------------------------------------------------------
# Tests: Ollama unload lifecycle
# ---------------------------------------------------------------------------

class TestOllamaUnloadLifecycle:
    """Verify unload is called before the judge when both are Ollama-based."""

    def test_unload_called_before_complete_when_both_ollama(self):
        """
        When tested_model_provider='ollama' and judge provider is 'ollama',
        unload_model() must be called and must complete before complete() runs.
        """
        config = _make_config(provider_name="ollama")
        runner = JudgeRunner(config)

        # Mock the primary provider
        mock_provider = MagicMock()
        mock_provider.health_check.return_value = True
        mock_provider.complete.return_value = _make_provider_response(
            provider_name="ollama"
        )
        _inject_provider(runner, mock_provider)

        call_order: list[str] = []

        # Patch OllamaProvider.unload_model to track calls
        with patch(
            "utils.scoring.llm_judge.judge_runner.JudgeRunner._maybe_unload_tested_model",
            wraps=lambda self, *a, **kw: call_order.append("unload"),
        ) as mock_unload, patch.object(
            mock_provider,
            "complete",
            side_effect=lambda *a, **kw: (
                call_order.append("complete"),
                _make_provider_response(provider_name="ollama"),
            )[1],
        ):
            runner.score(
                task_prompt="task",
                model_response="response",
                golden_standard="golden",
                module_id="ux_writing",
                tested_model_id="llama3.2",
                tested_model_provider="ollama",
            )

        assert "unload" in call_order, "Unload should have been called"
        assert "complete" in call_order, "Complete should have been called"
        assert call_order.index("unload") < call_order.index("complete"), (
            "unload must be called BEFORE complete"
        )

    def test_unload_not_called_when_cloud_tested_model(self):
        """When tested model is cloud (not Ollama), no unload should happen."""
        config = _make_config(provider_name="ollama")
        runner = JudgeRunner(config)

        mock_provider = MagicMock()
        mock_provider.health_check.return_value = True
        mock_provider.complete.return_value = _make_provider_response(provider_name="ollama")
        _inject_provider(runner, mock_provider)

        with patch(
            "utils.scoring.llm_judge.providers.ollama_provider.OllamaProvider.unload_model"
        ) as mock_unload:
            runner.score(
                task_prompt="t",
                model_response="r",
                golden_standard="g",
                module_id="ux_writing",
                tested_model_id="gpt-4o",
                tested_model_provider="openai",  # NOT ollama
            )
            mock_unload.assert_not_called()

    def test_unload_not_called_when_judge_is_cloud(self):
        """When judge is cloud (not Ollama), no unload should happen."""
        config = _make_config(provider_name="anthropic")
        runner = JudgeRunner(config)

        mock_provider = MagicMock()
        mock_provider.health_check.return_value = True
        mock_provider.complete.return_value = _make_provider_response()
        _inject_provider(runner, mock_provider)

        with patch(
            "utils.scoring.llm_judge.providers.ollama_provider.OllamaProvider.unload_model"
        ) as mock_unload:
            runner.score(
                task_prompt="t",
                model_response="r",
                golden_standard="g",
                module_id="ux_writing",
                tested_model_id="llama3.2",
                tested_model_provider="ollama",
            )
            mock_unload.assert_not_called()


class TestShouldUnloadHelper:
    """Unit tests for the _should_unload() helper."""

    def test_both_ollama_returns_true(self):
        assert _should_unload("ollama", "ollama") is True

    def test_cloud_tested_model_returns_false(self):
        assert _should_unload("anthropic", "ollama") is False

    def test_cloud_judge_returns_false(self):
        assert _should_unload("ollama", "anthropic") is False

    def test_none_tested_model_provider_returns_false(self):
        assert _should_unload(None, "ollama") is False

    def test_case_insensitive(self):
        assert _should_unload("Ollama", "OLLAMA") is True


# ---------------------------------------------------------------------------
# Tests: Fallback provider chain
# ---------------------------------------------------------------------------

class TestProviderFallback:
    """Fallback triggers on health_check=False or complete() exception."""

    def test_fallback_triggers_on_health_check_false(self):
        """When primary health_check() returns False, fallback is used."""
        config = _make_config(provider_name="anthropic", with_fallback=True)
        runner = JudgeRunner(config)

        # Primary: health_check fails
        primary = MagicMock()
        primary.health_check.return_value = False
        primary.complete.return_value = _make_provider_response()  # should not be called
        _inject_provider(runner, primary)

        # Fallback: works fine
        fallback = MagicMock()
        fallback.complete.return_value = _make_provider_response(
            raw_text="REASONING: fallback used.\nSCORE: 3",
            provider_name="ollama",
        )
        _inject_fallback(runner, fallback)

        result = runner.score("task", "resp", "golden", "ux_writing")

        primary.complete.assert_not_called()
        fallback.complete.assert_called_once()
        assert result.score == 3
        assert result.judge_provider_used == "ollama"

    def test_fallback_triggers_on_complete_exception(self):
        """When primary complete() raises, fallback is used."""
        config = _make_config(provider_name="anthropic", with_fallback=True)
        runner = JudgeRunner(config)

        primary = MagicMock()
        primary.health_check.return_value = True
        primary.complete.side_effect = ConnectionError("Network unreachable")
        _inject_provider(runner, primary)

        fallback = MagicMock()
        fallback.complete.return_value = _make_provider_response(
            raw_text="REASONING: fallback succeeded.\nSCORE: 4",
            provider_name="ollama",
        )
        _inject_fallback(runner, fallback)

        result = runner.score("task", "resp", "golden", "ux_writing")

        fallback.complete.assert_called_once()
        assert result.score == 4
        assert result.judge_provider_used == "ollama"

    def test_no_fallback_configured_returns_none_score(self):
        """When no fallback is configured and primary fails, score=None is returned."""
        config = _make_config(provider_name="anthropic", with_fallback=False)
        runner = JudgeRunner(config)

        primary = MagicMock()
        primary.health_check.return_value = False
        _inject_provider(runner, primary)

        result = runner.score("task", "resp", "golden", "ux_writing")

        assert result.score is None
        assert result.parse_success is False

    def test_primary_used_when_healthy(self):
        """When primary is healthy, fallback is never invoked."""
        config = _make_config(provider_name="anthropic", with_fallback=True)
        runner = JudgeRunner(config)

        primary = MagicMock()
        primary.health_check.return_value = True
        primary.complete.return_value = _make_provider_response(
            raw_text="REASONING: primary ok.\nSCORE: 5"
        )
        _inject_provider(runner, primary)

        fallback = MagicMock()
        _inject_fallback(runner, fallback)

        result = runner.score("task", "resp", "golden", "ux_writing")

        fallback.complete.assert_not_called()
        assert result.score == 5
        assert result.judge_provider_used == "anthropic"


class TestFallbackNotTriggeredOnParseError:
    """Parse errors must NOT trigger the fallback provider."""

    def test_parse_error_leaves_fallback_unused(self):
        """
        If complete() returns successfully but parsing fails,
        the fallback must NOT be called.
        """
        config = _make_config(provider_name="anthropic", with_fallback=True)
        runner = JudgeRunner(config)

        primary = MagicMock()
        primary.health_check.return_value = True
        # Intentionally unparseable response
        primary.complete.return_value = _make_provider_response(
            raw_text="I cannot decide on a score today."
        )
        _inject_provider(runner, primary)

        fallback = MagicMock()
        _inject_fallback(runner, fallback)

        result = runner.score("task", "resp", "golden", "ux_writing")

        fallback.complete.assert_not_called()
        assert result.parse_success is False
        assert result.score is None

    def test_fail_on_parse_error_raises_not_falls_back(self):
        """fail_on_parse_error=True should raise RuntimeError, not trigger fallback."""
        from utils.scoring.llm_judge.judge_config import ScoringConfig  # noqa: PLC0415
        config = LLMJudgeConfig(
            provider=ProviderConfig(name="anthropic", model="model"),
            scoring=ScoringConfig(fail_on_parse_error=True),
        )
        config.provider.fallback = FallbackProviderConfig(  # type: ignore[assignment]
            name="ollama", model="llama3.2"
        )
        runner = JudgeRunner(config)

        primary = MagicMock()
        primary.health_check.return_value = True
        primary.complete.return_value = _make_provider_response(
            raw_text="No score in this response."
        )
        _inject_provider(runner, primary)

        fallback = MagicMock()
        _inject_fallback(runner, fallback)

        with pytest.raises(RuntimeError, match="failed to parse"):
            runner.score("task", "resp", "golden", "ux_writing")

        fallback.complete.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: response_time_ms immutability through pipeline
# ---------------------------------------------------------------------------

class TestResponseTimePassthrough:
    """response_time_ms must pass through the pipeline unchanged."""

    def test_response_time_in_build_result_dict(self):
        config = _make_config()
        runner = JudgeRunner(config)

        mock_provider = MagicMock()
        mock_provider.health_check.return_value = True
        mock_provider.complete.return_value = _make_provider_response()
        _inject_provider(runner, mock_provider)

        result_dict = runner.build_result_dict(
            task_prompt="task",
            model_response="response",
            golden_standard="golden",
            module_id="ux_writing",
            response_time_ms=1500.0,
        )
        assert result_dict["response_time_ms"] == pytest.approx(1500.0)

    def test_response_time_not_altered_by_runner(self):
        """The runner must never modify the response_time_ms value."""
        config = _make_config()
        runner = JudgeRunner(config)

        mock_provider = MagicMock()
        mock_provider.health_check.return_value = True
        mock_provider.complete.return_value = _make_provider_response()
        _inject_provider(runner, mock_provider)

        original_ms = 9999.1
        result_dict = runner.build_result_dict(
            task_prompt="task",
            model_response="response",
            golden_standard="golden",
            module_id="ux_writing",
            response_time_ms=original_ms,
        )
        assert result_dict["response_time_ms"] == pytest.approx(original_ms)

    def test_response_time_immutable_through_pending_pipeline(self):
        """Using score_pending(): response_time_ms from PendingJudgeResult is untouched."""
        config = _make_config()
        runner = JudgeRunner(config)

        mock_provider = MagicMock()
        mock_provider.health_check.return_value = True
        mock_provider.complete.return_value = _make_provider_response()
        _inject_provider(runner, mock_provider)

        original_ms = 750.25
        pending = PendingJudgeResult(
            task_id="t1",
            module_id="ux_writing",
            task_prompt="task",
            model_response="response",
            golden_standard="golden standard",
            hybrid_score=80.0,
            response_time_ms=original_ms,
        )

        # score_pending() must not modify the PendingJudgeResult
        runner.score_pending(pending)
        assert pending.response_time_ms == pytest.approx(original_ms)


# ---------------------------------------------------------------------------
# Tests: judge_latency_ms and judge_provider_used surface to caller
# ---------------------------------------------------------------------------

class TestJudgeMetadataInResult:
    """judge_latency_ms and judge_provider_used are present and correct."""

    def test_judge_latency_ms_present_in_result(self):
        config = _make_config()
        runner = JudgeRunner(config)

        mock_provider = MagicMock()
        mock_provider.health_check.return_value = True
        mock_provider.complete.return_value = _make_provider_response()
        _inject_provider(runner, mock_provider)

        result = runner.score("task", "resp", "golden", "ux_writing")
        assert result.judge_latency_ms is not None
        assert result.judge_latency_ms >= 0.0

    def test_judge_provider_used_in_result(self):
        config = _make_config(provider_name="anthropic")
        runner = JudgeRunner(config)

        mock_provider = MagicMock()
        mock_provider.health_check.return_value = True
        mock_provider.complete.return_value = _make_provider_response()
        _inject_provider(runner, mock_provider)

        result = runner.score("task", "resp", "golden", "ux_writing")
        assert result.judge_provider_used == "anthropic"

    def test_judge_latency_in_build_result_dict(self):
        config = _make_config()
        runner = JudgeRunner(config)

        mock_provider = MagicMock()
        mock_provider.health_check.return_value = True
        mock_provider.complete.return_value = _make_provider_response()
        _inject_provider(runner, mock_provider)

        d = runner.build_result_dict("task", "resp", "golden", "ux_writing")
        assert "judge_latency_ms" in d
        assert d["judge_latency_ms"] is not None
        assert "judge_provider_used" in d
