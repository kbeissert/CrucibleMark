import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Need to import LocalBenchmarkRunner
from scripts.core.run_local_benchmark import LocalBenchmarkRunner
from schemas.result import BenchmarkResult


@pytest.fixture
def mock_local_runner():
    # We create a LocalBenchmarkRunner with a mocked validator
    with (
        patch("utils.base_runner.ConfigValidator") as MockValidator,
        patch("utils.base_runner.LLMClient"),
        patch("utils.base_runner.ResultManager"),
    ):
        runner = LocalBenchmarkRunner("test")
        # We inject a mock config
        runner.validator = MagicMock()
        yield runner


@pytest.fixture
def mock_dependencies():
    with (
        patch("scripts.core.run_local_benchmark.load_asset_yaml") as mock_load,
        patch(
            "scripts.core.run_local_benchmark.LocalBenchmarkRunner._execute_test"
        ) as mock_exec,
        patch(
            "scripts.core.run_local_benchmark.LocalBenchmarkRunner.build_base_result"
        ) as mock_base,
        patch(
            "scripts.core.run_local_benchmark.calculate_score_contributions"
        ) as mock_calc,
        patch("requests.post") as mock_req,
        patch("time.sleep") as mock_sleep,
    ):
        mock_load.return_value = {
            "metadata": {"id": "asset_1"},
            "prompt": "test prompt",
            "golden_standard": {"text": "golden"},
        }

        # execution return
        mock_test_instance = MagicMock()

        # Provide a BenchmarkResult object initialized legally
        mock_exec_res = BenchmarkResult(
            status="success",
            execution_time=1.5,
            tokens_used=100,
            cost_usd=0.0,
            raw_response="hello world, this is a very long response that passes the 15 char limit",
        )
        mock_exec_res.data = {"total_score": 100, "max_score": 100}
        mock_test_instance.score_response.return_value = mock_exec_res

        mock_exec.return_value = (mock_test_instance, mock_exec_res)
        mock_base.return_value = {
            "asset_id": "asset_1",
            "execution_time": 1.5,
            "tokens_used": 100,
            "percentage": 100,
            "model": "test",
            "total_score": 100,
            "max_score": 100,
        }
        mock_calc.side_effect = lambda res, cfg: res

        yield {
            "load": mock_load,
            "exec": mock_exec,
            "base": mock_base,
            "calc": mock_calc,
            "req": mock_req,
            "sleep": mock_sleep,
        }


def test_pipeline_integration_disabled(mock_local_runner, mock_dependencies):
    mock_local_runner.validator.config = {
        "llm_judge": {"enabled": False, "applicable_modules": ["test_mod"]}
    }

    result = mock_local_runner._process_single_test(
        model="test_model",
        asset_path=Path("dummy_asset.yaml"),
        benchmark_info={"id": "test_mod"},
    )

    # Assert judge keys exist but are None
    assert "llm_judge_score" in result
    assert result["llm_judge_score"] is None
    # Ensure unload was NOT called
    mock_dependencies["req"].assert_not_called()


def test_pipeline_integration_not_applicable(mock_local_runner, mock_dependencies):
    mock_local_runner.validator.config = {
        "llm_judge": {"enabled": True, "applicable_modules": ["other_mod"]}
    }

    result = mock_local_runner._process_single_test(
        model="test_model",
        asset_path=Path("dummy_asset.yaml"),
        benchmark_info={"id": "test_mod"},
    )

    # Assert judge keys exist but are None
    assert result["llm_judge_score"] is None
    mock_dependencies["req"].assert_not_called()


def test_pipeline_integration_enabled_applicable(mock_local_runner, mock_dependencies):
    mock_local_runner.validator.config = {
        "llm_judge": {
            "enabled": True,
            "applicable_modules": ["test_mod"],
            "providers": {"ollama": "http://localhost:11434"},
        }
    }

    mock_pause = MagicMock()

    with (
        patch("utils.scoring.llm_judge.judge_runner.JudgeRunner") as MockJudgeRunner,
        patch("utils.scoring.llm_judge.judge_config.LLMJudgeConfig") as MockConfig,
        patch("requests.post") as mock_req_post,
    ):
        mock_judge_instance = MagicMock()
        mock_judge_instance.score.return_value = MagicMock(
            score=95.0,
            reasoning="good",
            latency_ms=500.0,
            provider_used="judge_prov",
            parse_success=True,
        )
        MockJudgeRunner.return_value = mock_judge_instance

        result = mock_local_runner._process_single_test(
            model="test_model",
            asset_path=Path("dummy_asset.yaml"),
            benchmark_info={"id": "test_mod"},
            pause_calculator=mock_pause,
        )

        mock_pause.wait.assert_called_once()
        mock_req_post.assert_called_once()  # unload model called
        mock_judge_instance.score.assert_called_once()

        assert result["llm_judge_score"] == 95.0
        assert result["llm_judge_reasoning"] == "good"
