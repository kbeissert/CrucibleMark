"""
Integration tests for the LLM Judge pipeline.

Tests the full flow: config → runner → (mocked provider) → parser → result.
No real API calls are made.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from utils.scoring.llm_judge.judge_config import (
    LLMJudgeConfig,
    ProviderConfig,
    ScoringConfig,
)
from utils.scoring.llm_judge.judge_parser import JudgeResult
from utils.scoring.llm_judge.judge_runner import JudgeRunner
from utils.scoring.llm_judge.providers.base_provider import JudgeProviderResponse


def _make_config(
    provider_name: str = "anthropic",
    mode: str = "complement",
    scale: int = 5,
    fail_on_parse_error: bool = False,
) -> LLMJudgeConfig:
    """Build a minimal LLMJudgeConfig for testing."""
    return LLMJudgeConfig(
        enabled=True,
        mode=mode,  # type: ignore[arg-type]
        provider=ProviderConfig(name=provider_name, model="test-model"),  # type: ignore[arg-type]
        scoring=ScoringConfig(scale=scale, fail_on_parse_error=fail_on_parse_error),
    )


def _make_provider_response(
    raw_text: str,
    model_id: str = "test-model",
    provider_name: str = "anthropic",
    latency_ms: float = 50.0,
) -> JudgeProviderResponse:
    return JudgeProviderResponse(
        raw_text=raw_text,
        model_id=model_id,
        provider_name=provider_name,
        latency_ms=latency_ms,
    )


class TestJudgeRunnerFullPipeline:
    """Full pipeline with mocked provider."""

    def _run_with_mock_response(
        self,
        raw_response: str,
        config: LLMJudgeConfig | None = None,
    ) -> JudgeResult:
        """Helper: run the judgment pipeline with the given mocked raw response."""
        if config is None:
            config = _make_config()

        mock_provider = MagicMock()
        mock_provider.complete.return_value = _make_provider_response(raw_response)

        runner = JudgeRunner(config)
        # Inject mock provider directly
        runner._provider = mock_provider

        return runner.score(
            task_prompt="Write a checkout button label.",
            model_response="Buy Now",
            golden_standard="Short, action-oriented CTA.",
            module_id="ux_writing",
        )

    def test_happy_path_score_4(self):
        raw = "REASONING: Covers most criteria well.\nSCORE: 4"
        result = self._run_with_mock_response(raw)
        assert result.score == 4
        assert result.parse_success is True
        assert "Covers most" in result.reasoning

    def test_happy_path_score_5(self):
        raw = "REASONING: Perfect match to golden standard.\nSCORE: 5"
        result = self._run_with_mock_response(raw)
        assert result.score == 5

    def test_parse_failure_returns_none_score(self):
        raw = "I think the response is decent but I cannot decide."
        result = self._run_with_mock_response(raw)
        assert result.score is None
        assert result.parse_success is False

    def test_score_brackets_parsed(self):
        raw = "REASONING: Good output.\nSCORE: [3]"
        result = self._run_with_mock_response(raw)
        assert result.score == 3

    def test_score_word_parsed(self):
        raw = "REASONING: Acceptable.\nSCORE: four"
        result = self._run_with_mock_response(raw)
        assert result.score == 4


class TestJudgeRunnerDisabled:
    """Disabled judge short-circuits without calling the provider."""

    def test_disabled_judge_returns_none_score(self):
        config = _make_config()
        config.enabled = False

        mock_provider = MagicMock()
        runner = JudgeRunner(config)
        runner._provider = mock_provider

        result = runner.score("task", "response", "golden", "ux_writing")
        assert result.score is None
        assert result.parse_success is False
        mock_provider.complete.assert_not_called()


class TestJudgeRunnerFailOnParseError:
    """fail_on_parse_error=True should raise RuntimeError on parse failure."""

    def test_raises_on_parse_failure_when_configured(self):
        config = _make_config(fail_on_parse_error=True)

        mock_provider = MagicMock()
        mock_provider.complete.return_value = _make_provider_response("No score here.")

        runner = JudgeRunner(config)
        runner._provider = mock_provider

        with pytest.raises(RuntimeError, match="failed to parse"):
            runner.score("task", "response", "golden", "ux_writing")


class TestScoreTo100Normalisation:
    """score_to_100() normalises raw judge score to a 0–100 range."""

    def _run_score_to_100(self, raw_response: str, scale: int) -> Any:
        config = _make_config(scale=scale)  # type: ignore[arg-type]
        mock_provider = MagicMock()
        mock_provider.complete.return_value = _make_provider_response(raw_response)

        runner = JudgeRunner(config)
        runner._provider = mock_provider
        return runner.score_to_100("task", "response", "golden", "ux_writing")

    def test_scale_5_score_4_normalises_to_80(self):
        raw = "REASONING: mostly good.\nSCORE: 4"
        normalised = self._run_score_to_100(raw, scale=5)
        assert normalised == pytest.approx(80.0)

    def test_scale_10_score_7_normalises_to_70(self):
        raw = "REASONING: decent.\nSCORE: 7"
        normalised = self._run_score_to_100(raw, scale=10)
        assert normalised == pytest.approx(70.0)

    def test_parse_failure_returns_none(self):
        raw = "No parseable score."
        normalised = self._run_score_to_100(raw, scale=5)
        assert normalised is None


class TestBuildResultDict:
    """build_result_dict() returns the correct dict structure."""

    def test_result_dict_keys(self):
        config = _make_config(scale=5)
        mock_provider = MagicMock()
        mock_provider.complete.return_value = _make_provider_response(
            "REASONING: good.\nSCORE: 4"
        )
        runner = JudgeRunner(config)
        runner._provider = mock_provider

        d = runner.build_result_dict("task", "response", "golden", "ux_writing")

        assert d["score"] == 4
        assert d["score_normalised"] == pytest.approx(80.0)
        assert "reasoning" in d
        assert d["parse_success"] is True
        assert d["scale"] == 5
        assert d["provider"] == "anthropic"
        assert d["model"] == "test-model"


class TestLLMJudgeConfigFromDict:
    """LLMJudgeConfig.from_dict() with and without the top-level key."""

    def test_from_dict_with_top_level_key(self):
        data = {
            "llm_judge": {
                "enabled": True,
                "mode": "replace",
                "provider": {"name": "mistral", "model": "mistral-small-latest"},
            }
        }
        config = LLMJudgeConfig.from_dict(data)
        assert config.mode == "replace"
        assert config.provider.name == "mistral"

    def test_from_dict_without_top_level_key(self):
        data = {
            "enabled": False,
            "provider": {"name": "ollama", "model": "llama3.2"},
        }
        config = LLMJudgeConfig.from_dict(data)
        assert config.enabled is False
        assert config.provider.name == "ollama"

    def test_default_applicable_modules(self):
        config = LLMJudgeConfig()
        assert "ux_writing" in config.applicable_modules
        assert "reasoning_logic" in config.applicable_modules
