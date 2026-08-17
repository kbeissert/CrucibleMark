"""Tests für die echte-Token-Pipeline (v5.1.5).

SSoT-Vertrag:
- ``tokens_per_second`` = echte Output-Tokens (inkl. Thinking) / Wall-Time.
- Fallback auf die Modul-Schätzung nur wenn der Provider kein Usage meldet.
- ``input_tokens``/``output_tokens`` = echte Provider-Usage-Werte.
- Judge-Context und Audit-Log zeigen die echte Breakdown;
  Visible Output = ``output_tokens - reasoning_tokens`` (NICHT
  ``tokens_used - reasoning_tokens`` — das hätte Input-Tokens fälschlich
  als sichtbaren Output gezählt).
"""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from schemas.result import BenchmarkResult  # noqa: E402
from utils.base_runner import BaseBenchmarkRunner  # noqa: E402
from utils.benchmark_utils import save_audit_log  # noqa: E402
from utils.scoring.judge_evaluator import _inject_token_usage_context  # noqa: E402
from utils.scoring.llm_judge.judge_prompt_builder import _format_token_usage_lines  # noqa: E402


def _make_runner() -> BaseBenchmarkRunner:
    """Runner ohne __init__ (keine ConfigValidator/LLMClient-Instanzierung)."""
    runner = BaseBenchmarkRunner.__new__(BaseBenchmarkRunner)
    validator = MagicMock()
    validator.config = {}
    runner.validator = validator
    return runner


def _make_exec_result(
    tokens_used: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    execution_time: float = 0.0,
) -> BenchmarkResult:
    return BenchmarkResult(
        status="success",
        execution_time=execution_time,
        tokens_used=tokens_used,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        raw_response="answer",
    )


_ASSET_DATA = {"metadata": {"id": "test_001", "name": "Test"}}


class TestTpsRealTokens:
    """build_base_result: TPS aus echten Output-Tokens (inkl. Thinking)."""

    def test_tps_from_real_output_tokens(self):
        """Echte Output-Tokens schlagen die Modul-Schätzung."""
        runner = _make_runner()
        # Schätzung (words*1.3) = 1200, echte Output-Tokens = 2500 (inkl. Thinking)
        exec_result = _make_exec_result(
            tokens_used=1200, input_tokens=800, output_tokens=2500, execution_time=100.0,
        )
        result = runner.build_base_result("test-model", _ASSET_DATA, exec_result, "vllm_spark")
        assert result["tokens_per_second"] == pytest.approx(25.0)
        assert result["input_tokens"] == 800
        assert result["output_tokens"] == 2500

    def test_tps_fallback_to_module_estimate(self):
        """Kein Provider-Usage (output_tokens=0) → Fallback auf Modul-Schätzung."""
        runner = _make_runner()
        exec_result = _make_exec_result(tokens_used=1200, execution_time=100.0)
        result = runner.build_base_result("test-model", _ASSET_DATA, exec_result, "ollama")
        assert result["tokens_per_second"] == pytest.approx(12.0)
        assert result["input_tokens"] == 0
        assert result["output_tokens"] == 0

    def test_tps_zero_without_execution_time(self):
        runner = _make_runner()
        exec_result = _make_exec_result(tokens_used=1200, output_tokens=2500)
        result = runner.build_base_result("test-model", _ASSET_DATA, exec_result, "ollama")
        assert result["tokens_per_second"] == 0.0


class TestInjectClientMetadata:
    """_inject_client_metadata: echte Breakdown aus dem LLMClient propagieren."""

    def test_propagates_input_output_tokens(self):
        runner = _make_runner()
        runner.client = SimpleNamespace(
            last_response_metadata={"finish_reason": "stop"},
            last_input_tokens=800,
            last_output_tokens=2500,
        )
        exec_result = _make_exec_result()
        runner._inject_client_metadata(exec_result)
        assert exec_result.input_tokens == 800
        assert exec_result.output_tokens == 2500

    def test_module_aggregate_wins_over_client_last_call(self):
        """Multi-Call-Modul (ToolUse): Modul-Summe > Client-Last-Call → Summe bleibt."""
        runner = _make_runner()
        runner.client = SimpleNamespace(
            last_response_metadata={},
            last_input_tokens=300,
            last_output_tokens=400,
        )
        exec_result = _make_exec_result(input_tokens=1100, output_tokens=1500)
        runner._inject_client_metadata(exec_result)
        assert exec_result.input_tokens == 1100
        assert exec_result.output_tokens == 1500

    def test_no_client_metadata_is_noop(self):
        runner = _make_runner()
        runner.client = SimpleNamespace()
        exec_result = _make_exec_result()
        runner._inject_client_metadata(exec_result)
        assert exec_result.input_tokens == 0
        assert exec_result.output_tokens == 0


class TestJudgeTokenUsageContext:
    """Judge bekommt die echte Token-Breakdown."""

    def test_context_includes_real_breakdown(self):
        result = {
            "tokens_used": 3300,
            "input_tokens": 800,
            "output_tokens": 2500,
            "reasoning_tokens": 1500,
            "token_limit_used": 8000,
        }
        kwargs: dict = {}
        _inject_token_usage_context(kwargs, result, "code_quality")
        ctx = kwargs["token_usage_context"]
        assert ctx["tokens_used"] == 3300
        assert ctx["input_tokens"] == 800
        assert ctx["output_tokens"] == 2500
        assert ctx["reasoning_tokens"] == 1500

    def test_context_without_breakdown_keys(self):
        result = {"tokens_used": 1196, "reasoning_tokens": 976}
        kwargs: dict = {}
        _inject_token_usage_context(kwargs, result, "code_quality")
        ctx = kwargs["token_usage_context"]
        assert "input_tokens" not in ctx
        assert "output_tokens" not in ctx


class TestJudgeVisibleOutputFormula:
    """Visible Output = output_tokens - reasoning_tokens (echte Formel)."""

    def test_visible_output_from_real_output_tokens(self):
        ctx = {
            "tokens_used": 3002,
            "input_tokens": 802,
            "output_tokens": 2200,
            "reasoning_tokens": 1500,
            "token_budget": 8000,
        }
        joined = "\n".join(_format_token_usage_lines(ctx))
        # Korrigierte Formel: 2200 - 1500 = 700 (NICHT 3002 - 1500 = 1502)
        assert "Visible output tokens**: 700" in joined
        assert "1502" not in joined
        # Thinking-Anteil relativ zu Output (NICHT zu Input+Output)
        assert "68% of generated output" in joined
        # Breakdown-Zeile
        assert "802 input + 2,200 output tokens" in joined

    def test_visible_output_skipped_without_output_tokens(self):
        """Keine Output-Usage → keine (falsche) Visible-Zeile, Anteil am Total."""
        ctx = {"tokens_used": 1196, "reasoning_tokens": 976, "token_budget": 8000}
        joined = "\n".join(_format_token_usage_lines(ctx))
        assert "Visible output tokens" not in joined
        assert "82% of total consumption" in joined
        assert "976" in joined

    def test_zero_visible_output_clamped(self):
        """Budget-Erschöpfung: alles Thinking → visible = 0, nicht negativ."""
        ctx = {
            "tokens_used": 2000,
            "input_tokens": 500,
            "output_tokens": 1500,
            "reasoning_tokens": 1500,
            "token_budget": 2000,
        }
        joined = "\n".join(_format_token_usage_lines(ctx))
        assert "Visible output tokens**: 0" in joined


class TestAuditLogBreakdown:
    """Audit-Log-Header zeigt die echte Breakdown auf der Tokens-Used-Zeile."""

    def test_header_contains_breakdown(self, tmp_path):
        save_audit_log(
            model="test-model",
            asset_id="test_001",
            prompt="prompt",
            response="response",
            judge_response="judge",
            base_dir=tmp_path,
            tokens_used=3300,
            reasoning_tokens=1500,
            input_tokens=800,
            output_tokens=2500,
            tokens_per_second=25.0,
        )
        content = (tmp_path / "test-model" / "test_001.md").read_text(encoding="utf-8")
        assert "**Tokens Used:** 3300 — 800 Input + 2500 Output" in content
        assert "davon 1500 Reasoning-Tokens" in content

    def test_header_legacy_without_breakdown(self, tmp_path):
        save_audit_log(
            model="test-model",
            asset_id="test_001",
            prompt="prompt",
            response="response",
            judge_response="judge",
            base_dir=tmp_path,
            tokens_used=1196,
            reasoning_tokens=976,
        )
        content = (tmp_path / "test-model" / "test_001.md").read_text(encoding="utf-8")
        assert "**Tokens Used:** 1196 _(davon 976 Reasoning-Tokens" in content
