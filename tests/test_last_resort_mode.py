"""Tests für den Last-Resort-Modus (letzte Stufe der Eskalationsleiter).

Anforderung (Session 110): Nach erschöpfter Leiter / Cap-Block / fehlendem
Ceiling EIN finaler Versuch mit deutlich geöffnetem Budget — nur für die
betroffenen Einzelfragen, vollständig dokumentiert im Report, bewusst OHNE
Card-Kalibrierung (sonst würde Stufe 1 künftiger Läufe auf das geöffnete
Budget springen und das Budget für ALLE Fragen öffnen).

SSoT: ``utils/providers/base.py`` (``_run_last_resort_attempt``,
``_load_reask_last_resort_budget``, ``_finalize_reask_metadata``).
"""

import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.providers.base import BaseProviderClient  # noqa: E402
from utils.scoring.judge_evaluator import _inject_token_usage_context  # noqa: E402
from utils.scoring.llm_judge.judge_prompt_builder import (  # noqa: E402
    _format_token_usage_lines,
)


class _ReaskClient(BaseProviderClient):
    def __init__(self, metadata: dict | None = None, config: dict | None = None):
        super().__init__(config=config or {})
        self.last_response_metadata = metadata or {}


def _truncation_metadata(used: int = 12000) -> dict:
    return {
        "finish_reason": "length",
        "token_limit_used": used,
        "think_content": "Deep reasoning...",
        "reasoning_tokens": used,
    }


def _reask_kwargs() -> dict:
    return {"_module_key": "ux_writing"}


@pytest.fixture()
def stub_query():
    calls: list[dict] = []
    container: dict = {"responses": []}

    def _query(**kwargs) -> str:
        calls.append(kwargs)
        return container["responses"].pop(0) if container["responses"] else ""

    _query.calls = calls  # type: ignore[attr-defined]
    _query.container = container  # type: ignore[attr-defined]
    return _query


# ---------------------------------------------------------------------------
# Leiter → Last-Resort
# ---------------------------------------------------------------------------


def test_ladder_exhaustion_triggers_last_resort_success(stub_query):
    """12k leer → 24k leer → 32k leer → Last-Resort 48k Erfolg: stage=4,
    last_resort=True, exhausted=False, Metadata annotiert."""
    client = _ReaskClient(_truncation_metadata())
    stub_query.container["responses"] = ["", "", "LAST RESORT SUCCESS"]
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == "LAST RESORT SUCCESS"
    assert [c["max_tokens"] for c in stub_query.calls] == [24000, 32000, 48000]
    meta = client.last_response_metadata
    assert meta["reasoning_reask"] is True
    assert meta["reasoning_reask_stage"] == 4
    assert meta["reasoning_reask_final_budget"] == 48000
    assert meta["reasoning_last_resort"] is True
    assert meta["reasoning_last_resort_budget"] == 48000
    assert "reasoning_reask_exhausted" not in meta


def test_last_resort_when_no_ceiling_above_calibrated_start(stub_query):
    """Kalibrierter Start 32k (kein Ceiling darüber) → Last-Resort direkt als
    Stufe 2 — der GLM-5.3-Fall (ux_writing_002 brannte 32000, 1.1 %)."""
    client = _ReaskClient(_truncation_metadata(used=32000))
    stub_query.container["responses"] = ["SUCCESS AT 48K"]
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == "SUCCESS AT 48K"
    assert [c["max_tokens"] for c in stub_query.calls] == [48000]
    meta = client.last_response_metadata
    assert meta["reasoning_reask"] is True
    assert meta["reasoning_reask_stage"] == 2
    assert meta["reasoning_last_resort"] is True
    assert meta["reasoning_last_resort_budget"] == 48000
    assert meta["reasoning_reask_initial_budget"] == 32000


def test_last_resort_bypasses_budget_cap(stub_query):
    """Cap-Block-Guard blockiert nur die regulären Stufen — der Last-Resort
    läuft mit _cap_bypass=True über den wirksamen Cap hinaus (48000 > 32768)."""
    client = _ReaskClient(_truncation_metadata())
    stub_query.container["responses"] = ["", "", "SUCCESS AT 48K"]
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
        budget_cap=32768,
    )
    assert result == "SUCCESS AT 48K"
    assert [c["max_tokens"] for c in stub_query.calls] == [24000, 32000, 48000]
    assert stub_query.calls[-1]["_cap_bypass"] is True
    # Die regulären Stufen wurden vom Cap NICHT blockiert (24000/32000 ≤ 32768)


def test_last_resort_failure_marks_exhausted(stub_query):
    """Auch der Last-Resort bleibt leer → exhausted=True, leere Rückgabe."""
    client = _ReaskClient(_truncation_metadata())
    stub_query.container["responses"] = ["", "", "", ""]
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == ""
    assert len(stub_query.calls) == 3
    meta = client.last_response_metadata
    assert meta["reasoning_last_resort"] is True
    assert meta["reasoning_reask_exhausted"] is True


def test_last_resort_disabled_via_config(stub_query):
    """last_resort_budget: 0 → Alt-Verhalten (Erschöpfung ohne Last-Resort)."""
    client = _ReaskClient(
        _truncation_metadata(),
        config={"reasoning_reask": {"last_resort_budget": 0}},
    )
    stub_query.container["responses"] = ["", ""]
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == ""
    assert len(stub_query.calls) == 2  # nur die regulären Stufen
    assert "reasoning_last_resort" not in client.last_response_metadata


def test_cap_block_also_triggers_last_resort(stub_query):
    """Cap-Block bei der ersten Stufe (Ziel > Cap) → Last-Resort greift trotzdem
    (Bypass) — der Fall 'Cap blockiert alles' bekommt ebenfalls eine bewertbare
    Antwort-Chance."""
    client = _ReaskClient(_truncation_metadata(used=12000))
    stub_query.container["responses"] = ["SUCCESS AT 48K"]
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
        budget_cap=20000,  # blockiert Stufe 2 (24000 > 20000)
    )
    assert result == "SUCCESS AT 48K"
    assert [c["max_tokens"] for c in stub_query.calls] == [48000]
    assert stub_query.calls[0]["_cap_bypass"] is True


# ---------------------------------------------------------------------------
# Cap-Bypass in _resolve_request_tokens
# ---------------------------------------------------------------------------


class _CapBypassClient(BaseProviderClient):
    PROVIDER_NAMES = ["testbypass"]

    def __init__(self):
        super().__init__(config={})
        self._provider_cfg = {"max_tokens": 32768, "model_max_tokens": {}}

    def _get_provider_cfg(self) -> dict:
        return self._provider_cfg


def test_resolve_request_tokens_bypass_skips_cap(monkeypatch):
    """_cap_bypass=True → die Cap-Kaskade wird übersprungen (48000 bleibt 48000)."""
    monkeypatch.setattr(
        "utils.model_thinking._read_max_output_tokens_from_card", lambda m: None,
    )
    client = _CapBypassClient()
    name, tokens = client._resolve_request_tokens(
        "test-model", {"max_tokens": 48000, "_cap_bypass": True, "_module_key": "ux_writing"},
    )
    assert tokens == 48000


def test_resolve_request_tokens_without_bypass_clamps(monkeypatch):
    """Ohne Bypass clippt die Kaskade auf den wirksamen Cap (Regression)."""
    monkeypatch.setattr(
        "utils.model_thinking._read_max_output_tokens_from_card", lambda m: None,
    )
    client = _CapBypassClient()
    name, tokens = client._resolve_request_tokens(
        "test-model", {"max_tokens": 48000, "_module_key": "ux_writing"},
    )
    assert tokens == 32768


# ---------------------------------------------------------------------------
# Kein Card-Write bei Last-Resort-Erfolg
# ---------------------------------------------------------------------------


def test_persist_cot_calibration_skips_last_resort(monkeypatch):
    """Last-Resort-Erfolg schreibt bewusst KEINE Card-Kalibrierung — sonst würde
    Stufe 1 künftiger Läufe auf das geöffnete Budget springen."""
    from schemas.result import BenchmarkResult
    from utils.base_runner import BaseBenchmarkRunner

    calls: list = []

    def _record(model_id, calibrated_budget, stage, notes=None):
        calls.append((model_id, calibrated_budget, stage))
        return True

    monkeypatch.setattr(
        "utils.model_card_io.update_model_card_cot_calibration", _record,
    )
    runner = object.__new__(BaseBenchmarkRunner)
    exec_result = BenchmarkResult()
    exec_result.reasoning_reask = True
    exec_result.reasoning_reask_stage = 4
    exec_result.reasoning_reask_final_budget = 48000
    exec_result.reasoning_last_resort = True
    exec_result.raw_response = "VISIBLE OUTPUT"

    runner._persist_cot_calibration_if_earned(exec_result, "some-model")

    assert calls == []


# ---------------------------------------------------------------------------
# Pydantic-Injektion + CSV-Spalten
# ---------------------------------------------------------------------------


def test_inject_client_metadata_last_resort():
    from schemas.result import BenchmarkResult
    from utils.base_runner import BaseBenchmarkRunner

    runner = object.__new__(BaseBenchmarkRunner)
    runner.client = SimpleNamespace(
        last_response_metadata={
            "finish_reason": "length",
            "token_limit_used": 48000,
            "reasoning_reask": True,
            "reasoning_reask_initial_budget": 32000,
            "reasoning_reask_stage": 2,
            "reasoning_reask_final_budget": 48000,
            "reasoning_last_resort": True,
            "reasoning_last_resort_budget": 48000,
        },
        last_token_usage=80000,
        last_request_cost=0.0,
    )
    exec_result = BenchmarkResult()

    runner._inject_client_metadata(exec_result)

    assert exec_result.reasoning_last_resort is True
    assert exec_result.reasoning_last_resort_budget == 48000
    assert exec_result.reasoning_reask_stage == 2


def test_build_base_result_includes_last_resort_columns():
    from schemas.result import BenchmarkResult
    from utils.base_runner import BaseBenchmarkRunner

    runner = object.__new__(BaseBenchmarkRunner)
    runner.validator = SimpleNamespace(config={})
    exec_result = BenchmarkResult()
    exec_result.reasoning_last_resort = True
    exec_result.reasoning_last_resort_budget = 48000

    row = runner.build_base_result(
        "m",
        {"metadata": {"id": "ux_writing_002", "name": "UX Writing"}},
        exec_result,
        "openrouter",
    )

    assert row["reasoning_last_resort"] is True
    assert row["reasoning_last_resort_budget"] == 48000


# ---------------------------------------------------------------------------
# Judge-Kontext + Prompt-Zeile
# ---------------------------------------------------------------------------


def test_judge_context_includes_last_resort():
    kwargs: dict = {}
    result = {
        "tokens_used": 80000,
        "reasoning_reask": True,
        "reasoning_reask_stage": 2,
        "reasoning_last_resort": True,
        "reasoning_last_resort_budget": 48000,
    }
    _inject_token_usage_context(kwargs, result, "ux_writing")
    ctx = kwargs["token_usage_context"]
    assert ctx["reasoning_last_resort"] is True
    assert ctx["reasoning_last_resort_budget"] == 48000


def test_prompt_builder_renders_last_resort_line():
    lines = _format_token_usage_lines(
        {
            "token_budget": 48000,
            "reasoning_reask": True,
            "reasoning_reask_stage": 2,
            "reasoning_last_resort": True,
            "reasoning_last_resort_budget": 48000,
        }
    )
    lr_lines = [line for line in lines if "Last-resort mode" in line]
    assert len(lr_lines) == 1
    assert "48,000-token budget" in lr_lines[0]
    assert "escalation ladder was exhausted" in lr_lines[0]
    assert "exceptional resource investment" in lr_lines[0]


# ---------------------------------------------------------------------------
# Audit-Log-Block
# ---------------------------------------------------------------------------


def test_audit_block_last_resort_success():
    from utils.benchmark_utils import _write_escalation_ladder_block

    buf = io.StringIO()
    _write_escalation_ladder_block(
        buf,
        reasoning_reask_stage=2,
        reasoning_reask_exhausted=False,
        reasoning_reask_final_budget=48000,
        cot_calibrated_start=True,
        reasoning_last_resort=True,
        reasoning_last_resort_budget=48000,
    )
    out = buf.getvalue()
    assert "🚨 Last-Resort-Modus: Stufe 2 (48,000 Tokens)" in out
    assert "Erschöpfungsgrenze" in out
    assert "Einsatzkosten" in out
    assert "KEINE Card-Kalibrierung" in out
    assert "Card-Kalibrierung" in out  # 📌-Note (kalibrierter Start)


def test_audit_block_last_resort_exhausted():
    from utils.benchmark_utils import _write_escalation_ladder_block

    buf = io.StringIO()
    _write_escalation_ladder_block(
        buf,
        reasoning_reask_stage=4,
        reasoning_reask_exhausted=True,
        reasoning_reask_final_budget=48000,
        cot_calibrated_start=False,
        reasoning_last_resort=True,
        reasoning_last_resort_budget=48000,
    )
    out = buf.getvalue()
    assert "⛔ Last-Resort erschöpft: Stufe 4 (48,000 Tokens)" in out
    assert "endgültige" in out


from types import SimpleNamespace  # noqa: E402  (für die Injektions-Tests)
