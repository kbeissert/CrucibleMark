"""
Tests für die Reasoning-only Truncation Eskalationsleiter (absolute Stufen-Deckel).

SSoT: ``utils/providers/base.py::BaseProviderClient._maybe_reask_reasoning_truncation``.

Hintergrund (Session 2026-09-19, ux_writing_002): Always-Thinking-Modelle mit
nicht-terminierendem CoT (GLM-5.3-Flash, Ornith-1.0-9b) verbrannten das
komplette 12k-Modul-Budget im Reasoning-Kanal (``finish_reason=length``,
0 sichtbarer Output) — Judge bewertete einen leeren String → 0.0/5.

Coverage:
  1. Trigger: leerer Content + finish_reason=length + Reasoning-Signal →
     Re-Ask mit nächstem Stufen-Deckel, Metadata annotiert
  2. Leiter: 12k leer → 24k leer → 32k Erfolg (stage=3, final_budget=32000)
  3. Leiter ab Floor: 25k → nächster Deckel 32k (ein Re-Ask)
  4. Erschöpfung: höchste Stufe weiterhin leer → exhausted=True, leere Rückgabe
  5. Kein Trigger: sichtbarer Content (Comparability — kein "best of 2")
  6. Kein Trigger: finish_reason=stop / kein Reasoning-Signal / kein Budget
  7. Guards: bereits eskaliert, _budget_exact, PC-Modul (eigene v3-Leiter)
  8. Cap-Block: Stufen-Ziel > Cap → Guard verweigert, keine sinnlosen Requests
  9. Config: ceilings/max_escalations aus benchmark_config, Defaults ohne
     Sektion, Konsistenz-Clamp
 10. Terminal-Sichtbarkeit: Eskalations-/Erschöpfungs-Zeilen im Log
 11. Pydantic-Regression: Metadata-Injektion auf echtem BenchmarkResult
 12. Card-Persistierung: Write nach oben, Guard-Bedingungen, Card-First-Lese-
     Pfad (resolve_token_budget, PC-Ausnahme, Exact-Modus)
 13. Erschöpfungs-Bridge-Skip in _apply_judge_pipeline
 14. Judge-Kontext + Prompt-Builder: Stufe/Erschöpfung/Kalibrierung
 15. Audit-Log-Block: Reviewer-Traceability

Disk-IO-frei wo möglich: Query wird als Callable-Stub injiziert; Card-Tests
nutzen tmp_path mit gepatchtem _find_card.
"""

import io
import json
import sys
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


class _ReaskClient(BaseProviderClient):
    """Minimaler Client-Stub: nur last_response_metadata und config sind relevant."""

    def __init__(self, metadata: dict | None = None, config: dict | None = None):
        super().__init__(config=config or {})
        self.last_response_metadata = metadata or {}


def _truncation_metadata(used: int = 12000) -> dict:
    """Metadata eines reasoning-only truncateten Erstversuchs."""
    return {
        "finish_reason": "length",
        "token_limit_used": used,
        "think_content": "Let me work through this task carefully...",
        "reasoning_tokens": used,
    }


def _reask_kwargs() -> dict:
    """Basis-Kwargs wie sie die Connectoren an _maybe_reask... durchreichen."""
    return {"_module_key": "ux_writing"}


@pytest.fixture()
def stub_query():
    """Query-Stub, der Aufrufe aufzeichnet und konfigurierbare Antworten liefert."""
    calls: list[dict] = []
    container: dict = {"responses": ["ESKALIERTE ANTWORT"]}

    def _query(**kwargs) -> str:
        calls.append(kwargs)
        return container["responses"].pop(0) if container["responses"] else ""

    _query.calls = calls  # type: ignore[attr-defined]
    _query.container = container  # type: ignore[attr-defined]
    return _query


# ---------------------------------------------------------------------------
# Trigger-Fall
# ---------------------------------------------------------------------------


def test_reask_triggers_on_reasoning_only_truncation(stub_query):
    client = _ReaskClient(_truncation_metadata())
    result = client._maybe_reask_reasoning_truncation(
        content="",
        model="glm-5_3-flash-exl3",
        prompt="PROMPT",
        temperature=1.0,
        stream_handler=None,
        kwargs=_reask_kwargs(),
        query=stub_query,
        budget_cap=24000,
    )
    assert result == "ESKALIERTE ANTWORT"
    assert len(stub_query.calls) == 1
    reask = stub_query.calls[0]
    assert reask["max_tokens"] == 24000
    assert reask["_reasoning_reask"] is True
    assert reask["prompt"] == "PROMPT"
    assert reask["temperature"] == 1.0
    assert client.last_response_metadata["reasoning_reask"] is True
    assert client.last_response_metadata["reasoning_reask_initial_budget"] == 12000
    assert client.last_response_metadata["reasoning_reask_stage"] == 2
    assert client.last_response_metadata["reasoning_reask_final_budget"] == 24000
    assert "reasoning_reask_exhausted" not in client.last_response_metadata


def test_reask_preserves_original_kwargs(stub_query):
    """Module-Key und weitere Kwargs werden unverändert durchgereichert."""
    client = _ReaskClient(_truncation_metadata())
    kwargs = {"_module_key": "ux_writing", "system": None, "chat_template_kwargs": {"enable_thinking": True}}
    client._maybe_reask_reasoning_truncation(
        content="",
        model="test-model",
        prompt="P",
        temperature=0.6,
        stream_handler=None,
        kwargs=kwargs,
        query=stub_query,
    )
    reask = stub_query.calls[0]
    assert reask["_module_key"] == "ux_writing"
    assert reask["chat_template_kwargs"] == {"enable_thinking": True}
    # Original-Kwargs dürfen nicht mutiert werden
    assert "_reasoning_reask" not in kwargs


# ---------------------------------------------------------------------------
# Leiter-Kletterlogik (absolute Stufen-Deckel)
# ---------------------------------------------------------------------------


def test_ladder_full_climb_to_success(stub_query):
    """12k leer → 24k leer → 32k Erfolg: stage=3, final_budget=32000."""
    client = _ReaskClient(_truncation_metadata())
    stub_query.container["responses"] = ["", "SUCCESS AT 32K"]
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == "SUCCESS AT 32K"
    assert [c["max_tokens"] for c in stub_query.calls] == [24000, 32000]
    meta = client.last_response_metadata
    assert meta["reasoning_reask"] is True
    assert meta["reasoning_reask_initial_budget"] == 12000
    assert meta["reasoning_reask_stage"] == 3
    assert meta["reasoning_reask_final_budget"] == 32000
    assert "reasoning_reask_exhausted" not in meta


def test_ladder_climbs_from_floor_above_first_ceiling(stub_query):
    """Floor-Start 25k liegt über dem ersten Deckel → nächster Deckel 32k."""
    client = _ReaskClient(_truncation_metadata(used=25000))
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == "ESKALIERTE ANTWORT"
    assert [c["max_tokens"] for c in stub_query.calls] == [32000]
    assert client.last_response_metadata["reasoning_reask_stage"] == 2
    assert client.last_response_metadata["reasoning_reask_final_budget"] == 32000


def test_ladder_exhaustion_marks_metadata(stub_query):
    """Höchste Stufe weiterhin leer → exhausted=True, leere Rückgabe."""
    client = _ReaskClient(
        _truncation_metadata(),
        config={"reasoning_reask": {"last_resort_budget": 0}},  # Alt-Verhalten ohne Last-Resort
    )
    stub_query.container["responses"] = ["", ""]
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == ""
    assert len(stub_query.calls) == 2
    meta = client.last_response_metadata
    assert meta["reasoning_reask"] is True
    assert meta["reasoning_reask_stage"] == 3
    assert meta["reasoning_reask_final_budget"] == 32000
    assert meta["reasoning_reask_exhausted"] is True


def test_ladder_stops_when_trigger_vanishes(stub_query):
    """Stiller Refusal nach Eskalation (finish_reason=stop, leer) → Leiter stoppt
    UND Last-Resort greift nicht (mehr Budget löst keinen Refusal).

    Die finale Stufe lieferte weiterhin 0 sichtbaren Output → exhausted=True
    (Messgrenze), obwohl noch ein Ceiling übrig wäre."""
    client = _ReaskClient(_truncation_metadata())
    stub_query.container["responses"] = [""]

    def _flip_to_stop(**kwargs):
        stub_query.calls.append(kwargs)
        client.last_response_metadata = {
            "finish_reason": "stop",
            "token_limit_used": 24000,
            "reasoning_tokens": 0,
        }
        return ""

    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=_flip_to_stop,
    )
    assert result == ""
    assert len(stub_query.calls) == 1
    meta = client.last_response_metadata
    assert meta["reasoning_reask"] is True
    assert meta["reasoning_reask_stage"] == 2
    assert meta["reasoning_reask_exhausted"] is True


# ---------------------------------------------------------------------------
# Kein Trigger / Guards
# ---------------------------------------------------------------------------


def test_no_reask_when_content_present(stub_query):
    """Sichtbarer Output vorhanden → akzeptiert, kein best-of-2 Cherry-Picking."""
    client = _ReaskClient(_truncation_metadata())
    result = client._maybe_reask_reasoning_truncation(
        content="Teilweise Antwort",
        model="test-model",
        prompt="P",
        temperature=1.0,
        stream_handler=None,
        kwargs=_reask_kwargs(),
        query=stub_query,
    )
    assert result == "Teilweise Antwort"
    assert stub_query.calls == []


def test_no_reask_when_finish_reason_stop(stub_query):
    client = _ReaskClient({"finish_reason": "stop", "token_limit_used": 12000, "think_content": "x"})
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == ""
    assert stub_query.calls == []


def test_no_reask_without_reasoning_signal(stub_query):
    """length + leer, aber kein Thinking → gestörter Request, kein Re-Ask."""
    client = _ReaskClient({"finish_reason": "length", "token_limit_used": 12000})
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == ""
    assert stub_query.calls == []


def test_no_reask_without_token_limit_used(stub_query):
    meta = _truncation_metadata()
    meta.pop("token_limit_used")
    client = _ReaskClient(meta)
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == ""
    assert stub_query.calls == []


def test_no_second_reask_when_already_escalated(stub_query):
    """Guard: Nested-Query-Aufrufe eskalieren nicht selbst — die Leiter
    kontrolliert alle Stufen zentral."""
    client = _ReaskClient(_truncation_metadata())
    kwargs = {"_reasoning_reask": True}
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=kwargs, query=stub_query,
    )
    assert result == ""
    assert stub_query.calls == []


def test_no_reask_in_exact_budget_mode(stub_query):
    """Guard: PC-Token-Probe/pc_calibrate messen Truncation-Stufen — dort
    würde eine Eskalation die Stufen-Semantik verfälschen."""
    client = _ReaskClient(_truncation_metadata())
    kwargs = {"_budget_exact": True}
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=0.1,
        stream_handler=None, kwargs=kwargs, query=stub_query,
    )
    assert result == ""
    assert stub_query.calls == []


def test_no_reask_on_political_compass_module(stub_query):
    """Guard: PC hat seine eigene v3-Leiter mit Thinking-Off — autoritativ."""
    client = _ReaskClient(_truncation_metadata())
    kwargs = {"_module_key": "political_compass"}
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=kwargs, query=stub_query,
    )
    assert result == ""
    assert stub_query.calls == []


# ---------------------------------------------------------------------------
# Cap-Block-Guard
# ---------------------------------------------------------------------------


def test_cap_block_refuses_escalation_beyond_cap(stub_query):
    """Stufen-Ziel (24000) > Cap (20000) → Guard verweigert, KEIN Request.

    Anders als die alte ×2-Logik wird nicht auf den Cap gedeckelt — es gibt
    nur absolute Stufen-Deckel, und Ziele darüber sind unzulässig."""
    client = _ReaskClient(
        _truncation_metadata(used=12000),
        config={"reasoning_reask": {"last_resort_budget": 0}},  # Guard-Isolation
    )
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
        budget_cap=20000,
    )
    assert result == ""
    assert stub_query.calls == []


def test_no_reask_when_cap_blocks_escalation(stub_query):
    """Cap ≤ nächstem Ceiling → eskaliertes Budget wäre unzulässig."""
    client = _ReaskClient(
        _truncation_metadata(used=24000),
        config={"reasoning_reask": {"last_resort_budget": 0}},  # Guard-Isolation
    )
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
        budget_cap=24000,
    )
    assert result == ""
    assert stub_query.calls == []


# ---------------------------------------------------------------------------
# Config-Parsing (config-driven)
# ---------------------------------------------------------------------------


def test_ladder_config_defaults_without_section():
    client = _ReaskClient(config={})
    ceilings, max_escalations = client._load_reask_ladder_config()
    assert ceilings == [24000, 32000]
    assert max_escalations == 2


def test_ladder_config_custom_ceilings(stub_query):
    client = _ReaskClient(
        _truncation_metadata(),
        config={"reasoning_reask": {"ceilings": [16000], "max_escalations": 1}},
    )
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == "ESKALIERTE ANTWORT"
    assert [c["max_tokens"] for c in stub_query.calls] == [16000]


def test_ladder_config_clamps_max_escalations(stub_query):
    """max_escalations > len(ceilings) → hart auf len(ceilings) gedeckelt."""
    client = _ReaskClient(
        _truncation_metadata(),
        config={"reasoning_reask": {"ceilings": [16000, 20000], "max_escalations": 5, "last_resort_budget": 0}},
    )
    ceilings, max_escalations = client._load_reask_ladder_config()
    assert max_escalations == 2
    stub_query.container["responses"] = ["", ""]
    result = client._maybe_reask_reasoning_truncation(
        content="", model="m", prompt="P", temperature=1.0,
        stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
    )
    assert result == ""
    assert [c["max_tokens"] for c in stub_query.calls] == [16000, 20000]


# ---------------------------------------------------------------------------
# Terminal-Sichtbarkeit (Logger-Zeilen)
# ---------------------------------------------------------------------------


def test_terminal_lines_on_escalation(stub_query, caplog):
    """Eskalation muss im Terminal sichtbar sein: Warnung vor + Ergebnis nach
    dem Re-Request (Blanko-Format via Root-Logger, wie Memory-Recovery-Zeilen)."""
    import logging

    client = _ReaskClient(_truncation_metadata())
    with caplog.at_level(logging.INFO, logger="utils.providers.base"):
        client._maybe_reask_reasoning_truncation(
            content="", model="glm-5_3-flash-exl3", prompt="P", temperature=1.0,
            stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
            budget_cap=24000,
        )
    messages = [r.getMessage() for r in caplog.records]
    assert any("Tokenbudget erhöht" in m and "24000 Tokens" in m for m in messages)
    assert any("Re-Ask erfolgreich" in m for m in messages)


def test_terminal_line_on_exhausted_ladder(stub_query, caplog):
    """Erschöpfung → Messgrenzen-Zeile mit Stufe und Budget."""
    import logging

    client = _ReaskClient(
        _truncation_metadata(),
        config={"reasoning_reask": {"last_resort_budget": 0}},  # Alt-Verhalten
    )
    stub_query.container["responses"] = ["", ""]
    with caplog.at_level(logging.WARNING, logger="utils.providers.base"):
        client._maybe_reask_reasoning_truncation(
            content="", model="m", prompt="P", temperature=1.0,
            stream_handler=None, kwargs=_reask_kwargs(), query=stub_query,
        )
    messages = [r.getMessage() for r in caplog.records]
    assert any("Tokenbudget erhöht" in m for m in messages)
    assert any("Leiter erschöpft" in m and "32000" in m for m in messages)


# ---------------------------------------------------------------------------
# Pydantic-Regression: Metadata-Injektion auf echtem BenchmarkResult
# ---------------------------------------------------------------------------


def test_inject_client_metadata_reasoning_reask_no_raise():
    """Regression (Session 2026-09-19, ux_writing 2❌): BenchmarkResult ist ein
    Pydantic-Modell — das Setzen undeklarierter Felder (reasoning_reask) in
    _inject_client_metadata warf ValueError NACH erfolgreichem Re-Ask und
    verwandelte eskalierte Tests in ❌-Error-Rows ("Test execution failed").
    Alle Leiter-Felder müssen deklariert sein und die Injektion darf nicht raisen."""
    from schemas.result import BenchmarkResult
    from utils.base_runner import BaseBenchmarkRunner

    runner = object.__new__(BaseBenchmarkRunner)  # schweres __init__ umgehen
    runner.client = SimpleNamespace(
        last_response_metadata={
            "finish_reason": "length",
            "token_limit_used": 32000,
            "token_limit_cutoff": True,
            "reasoning_tokens": 32000,
            "think_content": "Let me work through...",
            "reasoning_reask": True,
            "reasoning_reask_initial_budget": 12000,
            "reasoning_reask_stage": 3,
            "reasoning_reask_exhausted": True,
            "reasoning_reask_final_budget": 32000,
        },
        last_token_usage=56274,
        last_request_cost=0.0,
    )
    exec_result = BenchmarkResult()

    runner._inject_client_metadata(exec_result)  # darf nicht raisen

    assert exec_result.reasoning_reask is True
    assert exec_result.reasoning_reask_initial_budget == 12000
    assert exec_result.reasoning_reask_stage == 3
    assert exec_result.reasoning_reask_exhausted is True
    assert exec_result.reasoning_reask_final_budget == 32000
    assert exec_result.token_limit_used == 32000
    assert exec_result.token_limit_cutoff is True


def test_inject_client_metadata_calibrated_start():
    from schemas.result import BenchmarkResult
    from utils.base_runner import BaseBenchmarkRunner

    runner = object.__new__(BaseBenchmarkRunner)
    runner.client = SimpleNamespace(
        last_response_metadata={},
        last_token_usage=0,
        last_request_cost=0.0,
    )
    exec_result = BenchmarkResult()
    exec_result.cot_calibrated_start = True

    runner._inject_client_metadata(exec_result)

    assert exec_result.cot_calibrated_start is True


def test_build_base_result_includes_ladder_columns():
    """CSV-Spalten (dynamisch): alle Leiter-Felder landen im Result-Dict."""
    from schemas.result import BenchmarkResult
    from utils.base_runner import BaseBenchmarkRunner

    runner = object.__new__(BaseBenchmarkRunner)
    runner.validator = SimpleNamespace(config={})
    exec_result = BenchmarkResult()
    exec_result.reasoning_reask = True
    exec_result.reasoning_reask_initial_budget = 12000
    exec_result.reasoning_reask_stage = 3
    exec_result.reasoning_reask_exhausted = True
    exec_result.reasoning_reask_final_budget = 32000
    exec_result.cot_calibrated_start = True

    row = runner.build_base_result(
        "glm-5_3-flash-exl3",
        {"metadata": {"id": "ux_writing_002", "name": "UX Writing"}},
        exec_result,
        "vllm_spark",
    )

    assert row["reasoning_reask"] is True
    assert row["reasoning_reask_initial_budget"] == 12000
    assert row["reasoning_reask_stage"] == 3
    assert row["reasoning_reask_exhausted"] is True
    assert row["reasoning_reask_final_budget"] == 32000
    assert row["cot_calibrated_start"] is True


# ---------------------------------------------------------------------------
# Card-Persistierung: Write-Pfad (model_card_io)
# ---------------------------------------------------------------------------


def _card_fixture(tmp_path: Path, data: dict) -> Path:
    card = tmp_path / "calibration-fixture-model.json"
    card.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return card


@pytest.fixture()
def patch_card_lookup(monkeypatch, tmp_path):
    """Patched _find_card in beiden Card-IO-Konsumenten auf eine tmp-Card."""
    holder: dict = {"path": None}

    def _fake_find(_model_id: str) -> Path:
        return holder["path"] or (tmp_path / "does-not-exist.json")

    monkeypatch.setattr("utils.model_card_io._find_card", _fake_find)
    monkeypatch.setattr("utils.model_token_budget._find_card", _fake_find)
    return holder


def test_cot_calibration_write_creates_entry(tmp_path, patch_card_lookup):
    from utils.model_card_io import update_model_card_cot_calibration

    patch_card_lookup["path"] = _card_fixture(tmp_path, {"model_id": "calibration-fixture-model"})

    assert update_model_card_cot_calibration(
        "calibration-fixture-model", calibrated_budget=24000, stage=2,
    ) is True

    data = json.loads(patch_card_lookup["path"].read_text(encoding="utf-8"))
    cal = data["cot_budget_calibration"]
    assert cal["calibrated_budget"] == 24000
    assert cal["stage"] == 2
    assert cal["tested"]  # ISO-Datum gesetzt
    assert "Eskalationsleiter" in cal["notes"]
    # SSoT-Write-Konvention: Trailing-Newline (Git-Status-Flap-Schutz)
    assert patch_card_lookup["path"].read_text(encoding="utf-8").endswith("\n")


def test_cot_calibration_upward_only(tmp_path, patch_card_lookup):
    """Re-Kalibrierung nur nach oben — gleiche/niedrigere Budgets schreiben nicht."""
    from utils.model_card_io import update_model_card_cot_calibration

    patch_card_lookup["path"] = _card_fixture(
        tmp_path,
        {"model_id": "m", "cot_budget_calibration": {"calibrated_budget": 24000, "stage": 2}},
    )

    assert update_model_card_cot_calibration(
        "m", calibrated_budget=24000, stage=2,
    ) is False
    assert update_model_card_cot_calibration(
        "m", calibrated_budget=16000, stage=2,
    ) is False
    data = json.loads(patch_card_lookup["path"].read_text(encoding="utf-8"))
    assert data["cot_budget_calibration"]["calibrated_budget"] == 24000

    assert update_model_card_cot_calibration(
        "m", calibrated_budget=32000, stage=3,
    ) is True
    data = json.loads(patch_card_lookup["path"].read_text(encoding="utf-8"))
    assert data["cot_budget_calibration"]["calibrated_budget"] == 32000
    assert data["cot_budget_calibration"]["stage"] == 3


def test_cot_calibration_missing_card(tmp_path, patch_card_lookup):
    from utils.model_card_io import update_model_card_cot_calibration

    patch_card_lookup["path"] = None  # _fake_find fällt auf nicht-existierende Datei zurück
    assert update_model_card_cot_calibration("m", calibrated_budget=24000, stage=2) is False


# ---------------------------------------------------------------------------
# Card-Persistierung: Guard im base_runner
# ---------------------------------------------------------------------------


def _exec_result_with_ladder(**overrides) -> object:
    from schemas.result import BenchmarkResult

    exec_result = BenchmarkResult()
    exec_result.reasoning_reask = True
    exec_result.reasoning_reask_stage = 2
    exec_result.reasoning_reask_final_budget = 24000
    exec_result.raw_response = "VISIBLE OUTPUT"
    for key, value in overrides.items():
        setattr(exec_result, key, value)
    return exec_result


def _recorder(monkeypatch) -> list:
    calls: list = []

    def _record(model_id, calibrated_budget, stage, notes=None):
        calls.append((model_id, calibrated_budget, stage))
        return True

    monkeypatch.setattr(
        "utils.model_card_io.update_model_card_cot_calibration", _record,
    )
    return calls


def test_persist_cot_calibration_writes_on_success(monkeypatch):
    from utils.base_runner import BaseBenchmarkRunner

    calls = _recorder(monkeypatch)
    runner = object.__new__(BaseBenchmarkRunner)
    runner._persist_cot_calibration_if_earned(
        _exec_result_with_ladder(), "calibration-fixture-model",
    )
    assert calls == [("calibration-fixture-model", 24000, 2)]


def test_persist_cot_calibration_skips_exhausted(monkeypatch):
    from utils.base_runner import BaseBenchmarkRunner

    calls = _recorder(monkeypatch)
    runner = object.__new__(BaseBenchmarkRunner)
    runner._persist_cot_calibration_if_earned(
        _exec_result_with_ladder(reasoning_reask_exhausted=True, raw_response=""),
        "m",
    )
    assert calls == []


def test_persist_cot_calibration_skips_stage_one(monkeypatch):
    from utils.base_runner import BaseBenchmarkRunner

    calls = _recorder(monkeypatch)
    runner = object.__new__(BaseBenchmarkRunner)
    runner._persist_cot_calibration_if_earned(
        _exec_result_with_ladder(reasoning_reask_stage=1, reasoning_reask_final_budget=None),
        "m",
    )
    assert calls == []


def test_persist_cot_calibration_skips_empty_response(monkeypatch):
    from utils.base_runner import BaseBenchmarkRunner

    calls = _recorder(monkeypatch)
    runner = object.__new__(BaseBenchmarkRunner)
    runner._persist_cot_calibration_if_earned(
        _exec_result_with_ladder(raw_response="   "), "m",
    )
    assert calls == []


# ---------------------------------------------------------------------------
# Card-First-Lese-Pfad: resolve_token_budget
# ---------------------------------------------------------------------------


def test_resolve_token_budget_honors_cot_calibration(tmp_path, patch_card_lookup):
    """Kalibriertes Budget hebt Stufe 1 an: max(Modul-Budget, Kalibrierung)."""
    from utils.model_token_budget import get_calibrated_cot_budget, resolve_token_budget

    patch_card_lookup["path"] = _card_fixture(
        tmp_path,
        {
            "model_id": "calibration-fixture-model",
            "cot_budget_calibration": {
                "calibrated_budget": 24000, "stage": 2, "tested": "2026-09-19",
            },
        },
    )
    assert get_calibrated_cot_budget("calibration-fixture-model") == 24000
    tokens, reasoning = resolve_token_budget(
        "calibration-fixture-model", 12000, {}, "ux_writing",
    )
    assert tokens == 24000
    assert reasoning is False


def test_resolve_token_budget_calibration_below_module_budget_wins_nothing(
    tmp_path, patch_card_lookup,
):
    from utils.model_token_budget import resolve_token_budget

    patch_card_lookup["path"] = _card_fixture(
        tmp_path,
        {
            "model_id": "calibration-fixture-model",
            "cot_budget_calibration": {"calibrated_budget": 9000, "stage": 2},
        },
    )
    tokens, _ = resolve_token_budget(
        "calibration-fixture-model", 12000, {}, "ux_writing",
    )
    assert tokens == 12000


def test_resolve_token_budget_pc_module_excluded(tmp_path, patch_card_lookup):
    """PC hat seine eigene v3-Leiter — cot_budget_calibration greift dort nicht."""
    from utils.model_token_budget import resolve_token_budget

    patch_card_lookup["path"] = _card_fixture(
        tmp_path,
        {
            "model_id": "calibration-fixture-model",
            "cot_budget_calibration": {"calibrated_budget": 24000, "stage": 2},
        },
    )
    tokens, _ = resolve_token_budget(
        "calibration-fixture-model", 800, {}, "political_compass",
    )
    assert tokens != 24000


def test_resolve_token_budget_exact_mode_ignores_calibration(tmp_path, patch_card_lookup):
    """Exact-Modus (PC-Token-Probe) bleibt von der Kalibrierung unberührt."""
    from utils.model_token_budget import resolve_token_budget

    patch_card_lookup["path"] = _card_fixture(
        tmp_path,
        {
            "model_id": "calibration-fixture-model",
            "cot_budget_calibration": {"calibrated_budget": 24000, "stage": 2},
        },
    )
    tokens, _ = resolve_token_budget(
        "calibration-fixture-model", 300, {}, "ux_writing", exact=True,
    )
    assert tokens == 300


# ---------------------------------------------------------------------------
# Erschöpfungs-Bridge-Skip (unified_runner)
# ---------------------------------------------------------------------------


def test_judge_bridge_skipped_when_ladder_exhausted():
    """Erschöpfter Lauf: residuale CoT wird NICHT als Antwort gefüttert —
    refusal-Pfad greift (Judge-Skip → 0 %) statt Schein-Bewertung."""
    from scripts.core.unified_runner import UnifiedBenchmarkRunner

    result = {"think_content": "Residual CoT " * 100, "reasoning_reask_exhausted": True}
    out = UnifiedBenchmarkRunner._apply_judge_pipeline(
        object(),  # Erschöpfungspfad berührt self nicht (Early-Return vor Pause)
        result=result,
        response="",
        asset_data={},
        benchmark_info={},
        model="m",
        provider="vllm_spark",
        is_local=True,
        pause_calculator=None,
    )
    assert out["refusal_flag"] is True
    assert "reasoning_only_response" not in out


def test_judge_bridge_still_composes_without_exhaustion(monkeypatch):
    """Ohne Erschöpfung komponiert die Bridge weiter (think_content → Judge)."""
    from scripts.core import unified_runner

    class _PipelineStub:
        def __init__(self):
            self.validator = SimpleNamespace(config={})

        def _judge_pre_pause(self, *args):  # noqa: ANN002
            pass

        def _local_memory_reset(self, *args):  # noqa: ANN002
            pass

        def _resolve_asset_config(self, *args):  # noqa: ANN002
            return None

    monkeypatch.setattr(
        unified_runner, "evaluate_with_judge", lambda **kwargs: kwargs["result"],
    )
    result = {"think_content": "Residual CoT " * 100}
    out = unified_runner.UnifiedBenchmarkRunner._apply_judge_pipeline(
        _PipelineStub(),
        result=result,
        response="",
        asset_data={},
        benchmark_info={},
        model="m",
        provider="vllm_spark",
        is_local=True,
        pause_calculator=None,
    )
    assert out.get("reasoning_only_response") is True
    assert "refusal_flag" not in out


# ---------------------------------------------------------------------------
# Judge-Kontext + Prompt-Builder
# ---------------------------------------------------------------------------


def test_judge_context_includes_ladder_info():
    kwargs: dict = {}
    result = {
        "tokens_used": 32674,
        "reasoning_tokens": 32000,
        "token_limit_used": 32000,
        "token_limit_cutoff": True,
        "reasoning_reask": True,
        "reasoning_reask_initial_budget": 12000,
        "reasoning_reask_stage": 3,
        "reasoning_reask_exhausted": True,
        "reasoning_reask_final_budget": 32000,
        "cot_calibrated_start": True,
    }
    _inject_token_usage_context(kwargs, result, "ux_writing")
    ctx = kwargs["token_usage_context"]
    assert ctx["truncated"] is True
    assert ctx["reasoning_reask"] is True
    assert ctx["reasoning_reask_initial_budget"] == 12000
    assert ctx["reasoning_reask_stage"] == 3
    assert ctx["reasoning_reask_exhausted"] is True
    assert ctx["reasoning_reask_final_budget"] == 32000
    assert ctx["cot_calibrated_start"] is True


def test_judge_context_omits_reask_when_absent():
    kwargs: dict = {}
    result = {"tokens_used": 5000, "token_limit_used": 12000}
    _inject_token_usage_context(kwargs, result, "ux_writing")
    assert "reasoning_reask" not in kwargs["token_usage_context"]
    assert "cot_calibrated_start" not in kwargs["token_usage_context"]


def test_prompt_builder_renders_ladder_success_line():
    lines = _format_token_usage_lines(
        {
            "token_budget": 24000,
            "reasoning_tokens": 12000,
            "output_tokens": 12000,
            "truncated": True,
            "reasoning_reask": True,
            "reasoning_reask_initial_budget": 12000,
            "reasoning_reask_stage": 2,
            "reasoning_reask_final_budget": 24000,
        }
    )
    reask_lines = [line for line in lines if "Reasoning-only truncation re-ask" in line]
    assert len(reask_lines) == 1
    assert "Stage 2 (24,000-token budget) produced this response" in reask_lines[0]
    assert "12,000-token budget" in reask_lines[0]
    assert "measurement limitation" in reask_lines[0]


def test_prompt_builder_renders_exhausted_line():
    lines = _format_token_usage_lines(
        {
            "token_budget": 32000,
            "reasoning_reask": True,
            "reasoning_reask_initial_budget": 12000,
            "reasoning_reask_stage": 3,
            "reasoning_reask_exhausted": True,
            "reasoning_reask_final_budget": 32000,
        }
    )
    exhausted_lines = [line for line in lines if "EXHAUSTED" in line]
    assert len(exhausted_lines) == 1
    assert "stage 3 (32,000-token budget)" in exhausted_lines[0]
    assert "measurement limitation" in exhausted_lines[0]
    assert "do not penalize content that never existed" in exhausted_lines[0]


def test_prompt_builder_renders_calibrated_start_line():
    lines = _format_token_usage_lines(
        {
            "token_budget": 24000,
            "cot_calibrated_start": True,
        }
    )
    cal_lines = [line for line in lines if "Calibrated start budget" in line]
    assert len(cal_lines) == 1
    assert "cot_budget_calibration" in cal_lines[0]


def test_prompt_builder_no_reask_line_without_flag():
    lines = _format_token_usage_lines({"token_budget": 12000, "truncated": True})
    assert not any("Reasoning-only truncation re-ask" in line for line in lines)
    assert not any("Calibrated start budget" in line for line in lines)


# ---------------------------------------------------------------------------
# Audit-Log-Block (Reviewer-Traceability)
# ---------------------------------------------------------------------------


def test_audit_block_success_escalation():
    from utils.benchmark_utils import _write_escalation_ladder_block

    buf = io.StringIO()
    _write_escalation_ladder_block(
        buf,
        reasoning_reask_stage=2,
        reasoning_reask_exhausted=False,
        reasoning_reask_final_budget=24000,
        cot_calibrated_start=False,
    )
    out = buf.getvalue()
    assert "Eskalationsleiter: Stufe 2 (24,000 Tokens) erfolgreich" in out
    assert "erschöpft" not in out
    assert "Card-Kalibrierung" not in out


def test_audit_block_exhaustion():
    from utils.benchmark_utils import _write_escalation_ladder_block

    buf = io.StringIO()
    _write_escalation_ladder_block(
        buf,
        reasoning_reask_stage=3,
        reasoning_reask_exhausted=True,
        reasoning_reask_final_budget=32000,
        cot_calibrated_start=False,
    )
    out = buf.getvalue()
    assert "Leiter erschöpft: Stufe 3 (32,000 Tokens)" in out
    assert "Messgrenze, kein Modellversagen" in out


def test_audit_block_calibrated_start():
    from utils.benchmark_utils import _write_escalation_ladder_block

    buf = io.StringIO()
    _write_escalation_ladder_block(
        buf,
        reasoning_reask_stage=2,
        reasoning_reask_exhausted=False,
        reasoning_reask_final_budget=24000,
        cot_calibrated_start=True,
    )
    out = buf.getvalue()
    assert "Start aus Card-Kalibrierung" in out
    assert "cot_budget_calibration" in out


def test_audit_block_absent_without_escalation():
    from utils.benchmark_utils import _write_escalation_ladder_block

    for stage in (None, 0, 1):
        buf = io.StringIO()
        _write_escalation_ladder_block(
            buf,
            reasoning_reask_stage=stage,
            reasoning_reask_exhausted=False,
            reasoning_reask_final_budget=None,
            cot_calibrated_start=False,
        )
        assert buf.getvalue() == ""
