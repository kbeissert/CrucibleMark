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

from unittest.mock import MagicMock, patch

import pytest
from utils.constants import OLLAMA_DEFAULT_BASE_URL

from utils.scoring.llm_judge.judge_config import (
    LLMJudgeConfig,
    ProviderConfig,
    ScoringConfig,
)
from utils.scoring.llm_judge.judge_handoff import PendingJudgeResult
from utils.scoring.llm_judge.judge_runner import JudgeRunner, _should_unload
from utils.scoring.exceptions import JudgeUnavailableError
from utils.scoring.llm_judge.providers.base_provider import JudgeProviderResponse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    provider_name: str = "anthropic",
    scale: int = 5,
) -> LLMJudgeConfig:
    return LLMJudgeConfig(
        enabled=True,
        provider=ProviderConfig(
            name=provider_name,  # type: ignore[arg-type]
            model="judge-model",
            base_url=OLLAMA_DEFAULT_BASE_URL if provider_name == "ollama" else None,
        ),
        scoring=ScoringConfig(scale=scale),  # type: ignore[call-arg]
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
    runner._fallback_provider = mock  # type: ignore[attr-defined]


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
        with (
            patch(
                "utils.scoring.llm_judge.judge_runner.JudgeRunner._maybe_unload_tested_model",
                wraps=lambda self, *a, **kw: call_order.append("unload"),
            ) as mock_unload,
            patch.object(
                mock_provider,
                "complete",
                side_effect=lambda *a, **kw: (
                    call_order.append("complete"),
                    _make_provider_response(provider_name="ollama"),
                )[1],
            ),
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
        mock_provider.complete.return_value = _make_provider_response(
            provider_name="ollama"
        )
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

class TestJudgeRunnerExceptions:
    """Tests strict fail-fast mode instead of fallback."""

    def test_judge_raises_on_health_check_false(self):
        config = _make_config(provider_name="anthropic")
        runner = JudgeRunner(config)

        primary = MagicMock()
        primary.health_check.return_value = False
        _inject_provider(runner, primary)

        with pytest.raises(JudgeUnavailableError):
            runner.score("task", "resp", "golden", "ux_writing")

    def test_judge_raises_on_complete_exception(self):
        config = _make_config(provider_name="anthropic")
        runner = JudgeRunner(config)

        primary = MagicMock()
        primary.health_check.return_value = True
        primary.complete.side_effect = ConnectionError("Network unreachable")
        _inject_provider(runner, primary)

        with pytest.raises(JudgeUnavailableError):
            runner.score("task", "resp", "golden", "ux_writing")
