"""
Tests für den Denkzeit-Wächter (Loop-Guard) der Eskalationsleiter.

SSoT: ``utils/providers/base.py::BaseProviderClient._run_reask_ladder``.

Hintergrund (Session 2026-09-21, Ornith-1.0-9b / Logical Reasoning 5B): Das
Modell verbrannte Erstversuch (25000 T) + Eskalationsstufe 2 (32000 T) ohne
sichtbaren Output und lief dabei in nicht terminierende Thinking-Ketten — der
Client-Timeout-Retry-Zirkus hielt den Test > 80 min fest. Der Wächter deckelt
die GESAMTE Eskalationsphase (``reasoning_reask.escalation_time_limit_s``,
Default 1800 s); der Erstversuch bleibt uhrfrei (Laufzeit = Messwert).

Abgrenzung (Kern der Klassifizierung):
  - Budget erreicht, leer    → reasoning_reask_exhausted (Budgethunger)
  - Zeit erschöpft, abgebrochen → reasoning_loop_suspected (Loop-Verdacht)

Coverage:
   1. Watchdog reißt blockierenden Eskalations-Request ab → loop_suspected,
      exhausted NICHT gesetzt, close() wurde gerufen
   2. Erschöpftes Zeitbudget → kein weiterer Stufen-Request
   3. Last-Resort wird nach Zeit-Abbruch unterbunden
   4. Guard deaktiviert (0) → Alt-Verhalten (exhausted), kein close()
   5. Normaler Erfolg innerhalb des Limits → kein Loop-Flag (Regression)
   6. Pydantic/CSV-Injektion auf echtem BenchmarkResult
   7. Card-Kalibrierung bei Loop-Abbruch unterbunden
   8. Judge-Kontext + Prompt-Builder-Zeile (Loop statt Re-Ask-Zeile)
   9. Audit-Log-CAUTION-Block (Reviewer-Traceability)
  10. Bridge-Skip: residuale CoT nach Loop-Abbruch ist keine Antwort

Disk-IO-frei; Zeitlimits im Sub-Sekunden-Bereich halten die Suite schnell.
"""

import io
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.providers.base import BaseProviderClient  # noqa: E402
from utils.scoring.judge_evaluator import _inject_token_usage_context  # noqa: E402
from utils.scoring.llm_judge.judge_prompt_builder import (  # noqa: E402
    _format_token_usage_lines,
)


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


class _LoopGuardClient(BaseProviderClient):
    """Stub: zählt Watchdog-Close-Aufrufe, sonst wie der Re-Ask-Test-Client."""

    def __init__(self, metadata: dict | None = None, config: dict | None = None):
        merged = {"reasoning_reask": {"min_visible_chars": 15}}
        if config:
            for key, value in config.items():
                if key == "reasoning_reask":
                    merged["reasoning_reask"].update(value)
                else:
                    merged[key] = value
        super().__init__(config=merged)
        self.last_response_metadata = metadata or {}
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


def _truncation_metadata(used: int = 12000) -> dict:
    """Metadata eines reasoning-only truncateten Erstversuchs."""
    return {
        "finish_reason": "length",
        "token_limit_used": used,
        "think_content": "Let me work through this task carefully...",
        "reasoning_tokens": used,
    }


def _reask_kwargs() -> dict:
    return {"_module_key": "logical_reasoning"}


def _guard_config(limit: float, last_resort: int = 48000) -> dict:
    return {
        "reasoning_reask": {
            "escalation_time_limit_s": limit,
            "last_resort_budget": last_resort,
        }
    }


def _slow_query(delay: float, response: str = ""):
    """Query-Stub: blockt ``delay`` Sekunden, zählt Aufrufe, liefert response.

    Ignoriert bewusst den Watchdog-Abbruch (kein raise) — so lässt sich
    deterministisch testen, dass ein NACH dem Call abgelaufenes Zeitbudget
    die nächste Stufe verweigert (der Watchdog hat trotzdem gefeuert).
    """
    calls: list[dict] = []

    def _query(**kwargs) -> str:
        calls.append(kwargs)
        time.sleep(delay)
        return response

    _query.calls = calls  # type: ignore[attr-defined]
    return _query


def _aborting_query(client: _LoopGuardClient, response: str = ""):
    """Query-Stub: blockt bis der Watchdog close() gerufen hat, wirft dann.

    Simuliert die reale Verkabelung: TCP FIN → Connection-Exception im
    blockierenden Streaming-Call.
    """
    calls: list[dict] = []

    def _query(**kwargs) -> str:
        calls.append(kwargs)
        deadline = time.monotonic() + 5.0
        while client.close_calls == 0 and time.monotonic() < deadline:
            time.sleep(0.005)
        if client.close_calls > 0:
            raise RuntimeError("connection aborted by watchdog")
        return response

    _query.calls = calls  # type: ignore[attr-defined]
    return _query


def _run_ladder(client: _LoopGuardClient, query) -> str:
    return client._maybe_reask_reasoning_truncation(
        content="",
        model="ornith-1_0-9b",
        prompt="PROMPT",
        temperature=0.6,
        stream_handler=None,
        kwargs=_reask_kwargs(),
        query=query,
    )


# ---------------------------------------------------------------------------
# 1 + 2: Watchdog-Abbruch und erschöpftes Zeitbudget
# ---------------------------------------------------------------------------


def test_watchdog_aborts_blocking_escalation_request():
    """Timeout mitten im Request: Watchdog reißt die Connection ab, der
    Abbruch wird als Loop-Verdacht klassifiziert — nicht als Fehler."""
    client = _LoopGuardClient(_truncation_metadata(), _guard_config(0.2))
    query = _aborting_query(client)

    content = _run_ladder(client, query)

    assert content == ""
    assert len(query.calls) == 1
    assert client.close_calls >= 1
    meta = client.last_response_metadata
    assert meta["reasoning_loop_suspected"] is True
    assert meta["reasoning_loop_stage"] == 2
    assert meta["reasoning_loop_elapsed_s"] >= 0.2
    # Abgrenzung: Budgetkette wurde NICHT durchlaufen → kein exhausted.
    assert "reasoning_reask_exhausted" not in meta
    assert meta["reasoning_reask_stage"] == 2


def test_exhausted_time_budget_blocks_next_stage():
    """Stufe 2 verbraucht das Zeitbudget legal (Antwort leer): Die nächste
    Stufe wird verweigert, ohne einen weiteren Request zu starten."""
    client = _LoopGuardClient(_truncation_metadata(), _guard_config(0.2))
    query = _slow_query(0.35)  # länger als das Limit, aber ohne raise

    content = _run_ladder(client, query)

    assert content == ""
    assert len(query.calls) == 1
    assert client.close_calls >= 1  # Watchdog feuerte während des Requests
    meta = client.last_response_metadata
    assert meta["reasoning_loop_suspected"] is True
    assert meta["reasoning_loop_stage"] == 3  # Abbruch VOR Stufe 3
    assert "reasoning_reask_exhausted" not in meta


def test_last_resort_suppressed_after_loop_abort():
    """Nach Zeit-Abbruch startet kein Last-Resort mehr — die Eskalationsphase
    hat ihr Budget verbraucht (Loop-Verdacht statt geöffneter Ausnahme)."""
    client = _LoopGuardClient(
        _truncation_metadata(), _guard_config(0.2, last_resort=48000)
    )
    query = _slow_query(0.35)

    content = _run_ladder(client, query)

    assert content == ""
    assert len(query.calls) == 1  # nur Stufe 2, kein Last-Resort-Request
    assert client.last_response_metadata["reasoning_loop_suspected"] is True
    assert "reasoning_last_resort" not in client.last_response_metadata


# ---------------------------------------------------------------------------
# 3 + 4: Guard deaktiviert / normaler Erfolg
# ---------------------------------------------------------------------------


def test_guard_disabled_keeps_exhausted_semantics():
    """``escalation_time_limit_s: 0`` = Alt-Verhalten: Leiter läuft bis zur
    Budget-Erschöpfung, exhausted bleibt das einzige Signal."""
    client = _LoopGuardClient(_truncation_metadata(), _guard_config(0.0))
    query = _slow_query(0.0)  # instant-leer, keine Zeitproblematik

    # Zwei Stufen leer → erschöpft (last_resort=0 hält den Test schlank)
    client.config["reasoning_reask"]["last_resort_budget"] = 0
    content = _run_ladder(client, query)

    assert content == ""
    assert len(query.calls) == 2
    assert client.close_calls == 0
    meta = client.last_response_metadata
    assert meta["reasoning_reask_exhausted"] is True
    assert "reasoning_loop_suspected" not in meta


def test_successful_escalation_within_limit_has_no_loop_flag():
    """Regression: Erfolg innerhalb des Limits → kein Loop-Flag, keine
    Abgrenzungs-Spuren, Antwort wird durchgereicht."""
    client = _LoopGuardClient(_truncation_metadata(), _guard_config(30.0))
    query = _slow_query(0.0, response="ESKALIERTE ANTWORT")

    content = _run_ladder(client, query)

    assert content == "ESKALIERTE ANTWORT"
    assert len(query.calls) == 1
    assert client.close_calls == 0
    meta = client.last_response_metadata
    assert "reasoning_loop_suspected" not in meta
    assert meta["reasoning_reask_stage"] == 2


# ---------------------------------------------------------------------------
# 5: Pydantic/CSV-Injektion auf echtem BenchmarkResult
# ---------------------------------------------------------------------------


def test_inject_loop_metadata_into_benchmark_result():
    """Regression (AGENTS.md 2026-09-19): BenchmarkResult ist Pydantic — die
    Loop-Felder müssen deklariert sein, sonst ValueError → stille ❌-Rows."""
    from schemas.result import BenchmarkResult
    from utils.base_runner import BaseBenchmarkRunner

    runner = object.__new__(BaseBenchmarkRunner)
    runner.client = SimpleNamespace(
        last_response_metadata={
            "finish_reason": "length",
            "token_limit_used": 32000,
            "reasoning_tokens": 32000,
            "think_content": "Loop...",
            "reasoning_reask": True,
            "reasoning_reask_initial_budget": 25000,
            "reasoning_reask_stage": 2,
            "reasoning_reask_final_budget": 32000,
            "reasoning_loop_suspected": True,
            "reasoning_loop_stage": 2,
            "reasoning_loop_elapsed_s": 1801.4,
        },
        last_token_usage=57000,
        last_request_cost=0.0,
    )
    exec_result = BenchmarkResult()

    runner._inject_client_metadata(exec_result)  # darf nicht raisen

    assert exec_result.reasoning_loop_suspected is True
    assert exec_result.reasoning_loop_stage == 2
    assert exec_result.reasoning_loop_elapsed_s == pytest.approx(1801.4)
    assert exec_result.reasoning_reask_exhausted is False


def test_build_base_result_includes_loop_columns():
    """CSV-Spalten (dynamisch): Loop-Felder landen im Result-Dict."""
    from schemas.result import BenchmarkResult
    from utils.base_runner import BaseBenchmarkRunner

    runner = object.__new__(BaseBenchmarkRunner)
    runner.validator = SimpleNamespace(config={})
    exec_result = BenchmarkResult()
    exec_result.reasoning_reask = True
    exec_result.reasoning_reask_stage = 2
    exec_result.reasoning_reask_final_budget = 32000
    exec_result.reasoning_loop_suspected = True
    exec_result.reasoning_loop_stage = 2
    exec_result.reasoning_loop_elapsed_s = 1802.0

    row = runner.build_base_result(
        "ornith-1_0-9b",
        {"metadata": {"id": "logical_reasoning_5b", "name": "Complex Chains"}},
        exec_result,
        "llamacpp_spark",
    )

    assert row["reasoning_loop_suspected"] is True
    assert row["reasoning_loop_stage"] == 2
    assert row["reasoning_loop_elapsed_s"] == pytest.approx(1802.0)


# ---------------------------------------------------------------------------
# 6: Card-Kalibrierung bei Loop-Abbruch unterbunden
# ---------------------------------------------------------------------------


def test_persist_cot_calibration_skips_loop_abort(monkeypatch):
    """Loop-Abbruch ist kein Eskalations-Erfolg: Kein Card-Write."""
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
    exec_result.reasoning_reask_stage = 2
    exec_result.reasoning_reask_final_budget = 32000
    exec_result.reasoning_loop_suspected = True
    exec_result.raw_response = ""

    runner._persist_cot_calibration_if_earned(exec_result, "m")
    assert calls == []


# ---------------------------------------------------------------------------
# 7: Judge-Kontext + Prompt-Builder-Zeile
# ---------------------------------------------------------------------------


def test_judge_context_and_prompt_line_on_loop_abort():
    """Loop-Verdacht: eigener Kontext, Loop-Zeile ERSETZT die Re-Ask-Zeile
    (die würde eine eskalierte Antwort suggerieren, die nie existierte)."""
    result = {
        "tokens_used": 57000,
        "reasoning_reask": True,
        "reasoning_reask_initial_budget": 25000,
        "reasoning_reask_stage": 2,
        "reasoning_reask_final_budget": 32000,
        "reasoning_loop_suspected": True,
        "reasoning_loop_stage": 2,
        "reasoning_loop_elapsed_s": 1803.0,
    }
    kwargs: dict = {}
    _inject_token_usage_context(kwargs, result, "logical_reasoning")

    ctx = kwargs["token_usage_context"]
    assert ctx["reasoning_loop_suspected"] is True
    assert ctx["reasoning_loop_stage"] == 2
    assert ctx["reasoning_loop_elapsed_s"] == pytest.approx(1803.0)

    lines = "\n".join(_format_token_usage_lines(ctx))
    assert "time-limit guard TRIGGERED" in lines
    assert "ladder stage 2" in lines
    assert "1,803s" in lines
    assert "re-ask" not in lines.lower()  # Re-Ask-Zeile unterdrückt


# ---------------------------------------------------------------------------
# 8: Audit-Log-CAUTION-Block
# ---------------------------------------------------------------------------


def test_audit_log_loop_caution_block():
    """Reviewer-Traceability: eigener CAUTION-Block mit Loop-Verdacht und
    Abgrenzung zur Budget-Erschöpfung."""
    from utils.benchmark_utils import _write_escalation_ladder_block

    buf = io.StringIO()
    _write_escalation_ladder_block(
        buf,
        reasoning_reask_stage=2,
        reasoning_reask_exhausted=False,
        reasoning_reask_final_budget=32000,
        cot_calibrated_start=False,
        reasoning_loop_suspected=True,
        reasoning_loop_stage=2,
        reasoning_loop_elapsed_s=1804.0,
    )
    block = buf.getvalue()
    assert "Denkzeit-Wächter ausgelöst" in block
    assert "Loop-Verdacht" in block
    assert "NICHT ausgeschöpft" in block
    assert "Leiter erschöpft" not in block
    assert "Last-Resort" not in block


# ---------------------------------------------------------------------------
# 9: Bridge-Skip (unified_runner)
# ---------------------------------------------------------------------------


def test_judge_bridge_skipped_on_loop_abort():
    """Loop-Abbruch zählt wie Erschöpfung: residuale CoT wird NICHT als
    Antwort gefüttert — refusal-Pfad (Judge-Skip → 0 %) statt Schein-Urteil."""
    from scripts.core.unified_runner import UnifiedBenchmarkRunner

    result = {
        "think_content": "Residual CoT " * 100,
        "reasoning_loop_suspected": True,
    }
    out = UnifiedBenchmarkRunner._apply_judge_pipeline(
        object(),  # Guard-Pfad berührt self nicht (Early-Return vor Pause)
        result=result,
        response="",
        asset_data={},
        benchmark_info={},
        model="ornith-1_0-9b",
        provider="llamacpp_spark",
        is_local=True,
        pause_calculator=None,
    )
    assert out["refusal_flag"] is True
    assert "reasoning_only_response" not in out
