"""
Tests für den Refusal-Retry (Safety-Refusal-Deeskalation).

SSoT: ``utils/base_runner.py::BaseBenchmarkRunner._maybe_refusal_retry``.

Hintergrund (2026-09-24, claude-opus-5 / claude-opus-5-5): Beide Opus-5-
Generationen verweigern Metacog-Assets serverseitig (stop_reason=refusal,
0 Output-Tokens). A/B-Test: Die <thought>-Tag-Formatanweisung ist der
Trigger. Der Retry wiederholt NUR bei echtem API-Refusal mit der tag-freien
Fassung (refusal_retry_prompt im Asset).

Coverage:
   1. Trigger: finish_reason=refusal → Retry läuft, refusal_retry_used=True
   2. Kein Trigger: finish_reason=end_turn → kein Retry (unverändert)
   3. Config-Gate: refusal_retry.enabled=false → kein Retry
   4. Asset-Gate: kein refusal_retry_prompt-Feld → kein Retry
   5. Prompt-Restaurierung: Original-Prompt nach Retry wiederhergestellt
   6. Retry-Result trägt die Retry-Antwort (nicht die leere Original-Antwort)
   7. CSV-Durchreichung: build_base_result enthält refusal_retry_used
   8. Audit-Block: _write_refusal_retry_block schreibt bei True, nicht bei False
   9. Schema: BenchmarkResult.refusal_retry_used (Pydantic-first)
  10. save_audit_log-Signatur: refusal_retry_used-Parameter wird akzeptiert

Mock-basiert — keine Live-Endpoints, keine Disk-IO außer Temp-Files.
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from schemas.result import BenchmarkResult  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def _make_asset(asset_id: str = "reasoning_metacog_001",
                with_retry: bool = True) -> dict:
    """Baut ein Asset-Dict mit/ohne refusal_retry_prompt."""
    asset = {
        "metadata": {"id": asset_id, "name": f"Test {asset_id}"},
        "prompt": "Original question with <thought> tags instruction.",
        "scoring": {"method": "rubric"},
    }
    if with_retry:
        asset["refusal_retry_prompt"] = "Retry question without tags."
    return asset


def _make_runner(config: dict | None = None) -> MagicMock:
    """Baut einen BaseBenchmarkRunner-Mock mit Config und Client."""
    runner = MagicMock()
    runner.validator.config = config or {"refusal_retry": {"enabled": True, "max_retries": 1}}
    runner.client = MagicMock()
    return runner


def _make_exec_result(response: str = "", finish_reason: str = "refusal") -> BenchmarkResult:
    """Baut ein BenchmarkResult für den Erstversuch."""
    result = BenchmarkResult()
    result.raw_response = response
    result.finish_reason = finish_reason
    return result


class _FakeTestInstance:
    """Modul-Test-Stub: execute() nutzt self.asset['prompt']."""

    def __init__(self, asset: dict, responses: list[str]):
        self.asset = asset
        self._responses = responses
        self._call_count = 0

    def execute(self, model, llm_client, **kwargs):
        result = BenchmarkResult()
        result.raw_response = self._responses[min(self._call_count, len(self._responses) - 1)]
        self._call_count += 1
        return result


# ---------------------------------------------------------------------------
# 1–4: Trigger-Matrix (Refusal-Retry läuft nur unter allen Bedingungen)
# ---------------------------------------------------------------------------

class TestRefusalRetryTrigger:
    """Trigger: nur echter API-Refusal + Config + Asset-Feld."""

    def test_refusal_triggers_retry(self):
        """finish_reason=refusal + enabled + retry_prompt → Retry läuft."""
        from utils.base_runner import BaseBenchmarkRunner
        runner = _make_runner()
        runner.client.last_response_metadata = {"finish_reason": "refusal"}
        asset = _make_asset()
        test_instance = _FakeTestInstance(asset, ["Retry-Antwort mit Inhalt"])
        exec_result = _make_exec_result("", "refusal")

        result = BaseBenchmarkRunner._maybe_refusal_retry(
            runner, test_instance, exec_result, "test-model", "anthropic", token_budget=12000, module_key="reasoning_logic"
        )

        assert result.refusal_retry_used is True
        assert result.raw_response == "Retry-Antwort mit Inhalt"
        assert test_instance._call_count == 1  # execute wurde 1x für den Retry gerufen

    def test_end_turn_no_retry(self):
        """finish_reason=end_turn → kein Retry, Erstversuch unverändert."""
        from utils.base_runner import BaseBenchmarkRunner
        runner = _make_runner()
        runner.client.last_response_metadata = {"finish_reason": "end_turn"}
        asset = _make_asset()
        test_instance = _FakeTestInstance(asset, ["Normale Antwort"])
        exec_result = _make_exec_result("Normale Antwort", "end_turn")

        result = BaseBenchmarkRunner._maybe_refusal_retry(
            runner, test_instance, exec_result, "test-model", "anthropic", token_budget=12000, module_key="reasoning_logic"
        )

        assert result is exec_result
        assert result.refusal_retry_used is False
        assert test_instance._call_count == 0  # kein Retry-Execute

    def test_config_disabled_no_retry(self):
        """refusal_retry.enabled=false → kein Retry trotz Refusal."""
        from utils.base_runner import BaseBenchmarkRunner
        runner = _make_runner({"refusal_retry": {"enabled": False}})
        runner.client.last_response_metadata = {"finish_reason": "refusal"}
        asset = _make_asset()
        test_instance = _FakeTestInstance(asset, ["", "Retry"])
        exec_result = _make_exec_result("", "refusal")

        result = BaseBenchmarkRunner._maybe_refusal_retry(
            runner, test_instance, exec_result, "test-model", "anthropic", token_budget=12000, module_key="reasoning_logic"
        )

        assert result is exec_result
        assert test_instance._call_count == 0

    def test_no_retry_prompt_no_retry(self):
        """Asset ohne refusal_retry_prompt → kein Retry."""
        from utils.base_runner import BaseBenchmarkRunner
        runner = _make_runner()
        runner.client.last_response_metadata = {"finish_reason": "refusal"}
        asset = _make_asset(with_retry=False)
        test_instance = _FakeTestInstance(asset, ["", "Retry"])
        exec_result = _make_exec_result("", "refusal")

        result = BaseBenchmarkRunner._maybe_refusal_retry(
            runner, test_instance, exec_result, "test-model", "anthropic", token_budget=12000, module_key="reasoning_logic"
        )

        assert result is exec_result
        assert test_instance._call_count == 0


# ---------------------------------------------------------------------------
# 5–6: Retry-Verhalten (Prompt-Mutation, Restaurierung, Result)
# ---------------------------------------------------------------------------

class TestRefusalRetryBehavior:
    """Retry: Prompt-Mutation temporär, Original restauriert."""

    def test_prompt_restored_after_retry(self):
        """Original-Prompt wird nach dem Retry restauriert."""
        from utils.base_runner import BaseBenchmarkRunner
        runner = _make_runner()
        runner.client.last_response_metadata = {"finish_reason": "refusal"}
        asset = _make_asset()
        original_prompt = asset["prompt"]
        test_instance = _FakeTestInstance(asset, ["", "Retry-Antwort"])
        exec_result = _make_exec_result("", "refusal")

        BaseBenchmarkRunner._maybe_refusal_retry(
            runner, test_instance, exec_result, "test-model", "anthropic", token_budget=12000, module_key="reasoning_logic"
        )

        assert asset["prompt"] == original_prompt

    def test_retry_uses_retry_prompt(self):
        """Der Retry-Execute ruft mit dem retry_prompt (nicht dem Original)."""
        from utils.base_runner import BaseBenchmarkRunner
        runner = _make_runner()
        runner.client.last_response_metadata = {"finish_reason": "refusal"}
        asset = _make_asset()
        captured_prompts = []

        class _CapturingTestInstance(_FakeTestInstance):
            def execute(self, model, llm_client, **kwargs):
                captured_prompts.append(self.asset["prompt"])
                return super().execute(model, llm_client, **kwargs)

        test_instance = _CapturingTestInstance(asset, ["", "Retry-Antwort"])
        exec_result = _make_exec_result("", "refusal")

        BaseBenchmarkRunner._maybe_refusal_retry(
            runner, test_instance, exec_result, "test-model", "anthropic", token_budget=12000, module_key="reasoning_logic"
        )

        assert captured_prompts == [asset["refusal_retry_prompt"]]


# ---------------------------------------------------------------------------
# 7: CSV-Durchreichung (build_base_result)
# ---------------------------------------------------------------------------

class TestRefusalRetryCsv:
    """build_base_result nimmt refusal_retry_used ins Dict auf."""

    def test_build_base_result_contains_flag(self):
        """CSV-Dict enthält refusal_retry_used aus dem exec_result."""
        from utils.base_runner import BaseBenchmarkRunner
        runner = _make_runner()
        runner._resolve_thinking_mode = MagicMock(return_value="n/a")

        exec_result = BenchmarkResult()
        exec_result.refusal_retry_used = True
        exec_result.raw_response = "Antwort"
        exec_result.execution_time = 1.0
        exec_result.primary_score = 80.0
        exec_result.max_score = 100
        exec_result.data = {"score": 80.0}
        exec_result.status = "success"

        asset_data = {"metadata": {"id": "test_asset", "name": "Test Asset"}}
        result = BaseBenchmarkRunner.build_base_result(
            runner, "test-model", asset_data, exec_result, "anthropic"
        )

        assert result["refusal_retry_used"] is True


# ---------------------------------------------------------------------------
# 8: Audit-Block
# ---------------------------------------------------------------------------

class TestRefusalRetryAuditBlock:
    """_write_refusal_retry_block: schreibt nur bei True."""

    def test_block_written_when_used(self):
        """Bei refusal_retry_used=True wird der Block geschrieben."""
        import io
        from utils.benchmark_utils import _write_refusal_retry_block

        buf = io.StringIO()
        _write_refusal_retry_block(buf, refusal_retry_used=True)
        content = buf.getvalue()
        assert "Safety-Refusal-Retry" in content
        assert "refusal" in content.lower()
        assert "Zweitversuch" in content

    def test_block_not_written_when_unused(self):
        """Bei refusal_retry_used=False bleibt der Block weg."""
        import io
        from utils.benchmark_utils import _write_refusal_retry_block

        buf = io.StringIO()
        _write_refusal_retry_block(buf, refusal_retry_used=False)
        assert buf.getvalue() == ""

    def test_original_prompt_written_when_passed(self):
        """Bei mitgegebenem Original-Prompt landet die verweigerte Fassung im Block."""
        import io
        from utils.benchmark_utils import _write_refusal_retry_block

        buf = io.StringIO()
        _write_refusal_retry_block(
            buf,
            refusal_retry_used=True,
            refusal_retry_original_prompt="Original mit <thought>-Tags",
        )
        content = buf.getvalue()
        assert "Verweigerte Original-Fassung" in content
        assert "Original mit <thought>-Tags" in content

    def test_original_prompt_section_omitted_without_prompt(self):
        """Ohne Original-Prompt bleibt der Block textlich identisch (keine Leer-Sektion)."""
        import io
        from utils.benchmark_utils import _write_refusal_retry_block

        buf_with = io.StringIO()
        _write_refusal_retry_block(buf_with, refusal_retry_used=True)
        buf_without = io.StringIO()
        _write_refusal_retry_block(
            buf_without, refusal_retry_used=True, refusal_retry_original_prompt=None,
        )
        assert buf_with.getvalue() == buf_without.getvalue()
        assert "Verweigerte Original-Fassung" not in buf_with.getvalue()


# ---------------------------------------------------------------------------
# 9: Schema (Pydantic-first)
# ---------------------------------------------------------------------------

class TestRefusalRetrySchema:
    """BenchmarkResult.refusal_retry_used: deklariert, default False."""

    def test_field_exists_with_default(self):
        result = BenchmarkResult()
        assert result.refusal_retry_used is False

    def test_field_settable(self):
        result = BenchmarkResult()
        result.refusal_retry_used = True
        assert result.refusal_retry_used is True


# ---------------------------------------------------------------------------
# 10: save_audit_log-Signatur
# ---------------------------------------------------------------------------

class TestRefusalRetryAuditSignature:
    """save_audit_log akzeptiert refusal_retry_used als Parameter."""

    def test_save_audit_log_accepts_parameter(self, tmp_path):
        """Der Parameter wird ohne TypeError akzeptiert (Signatur-Regression)."""
        import inspect
        from utils.benchmark_utils import save_audit_log

        sig = inspect.signature(save_audit_log)
        assert "refusal_retry_used" in sig.parameters
        assert sig.parameters["refusal_retry_used"].default is False

    def test_save_audit_log_accepts_original_prompt_parameter(self):
        """refusal_retry_original_prompt ist deklariert, default None."""
        import inspect
        from utils.benchmark_utils import save_audit_log

        sig = inspect.signature(save_audit_log)
        assert "refusal_retry_original_prompt" in sig.parameters
        assert sig.parameters["refusal_retry_original_prompt"].default is None
