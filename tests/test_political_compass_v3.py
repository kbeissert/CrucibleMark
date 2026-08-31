"""PC v3 Tests: Token-Budget, Wiring, Klassifikator, Retry-Strategie, Monitoring.

Deckt den Political-Compass-v3-Plan ab (Tasks 1-7):
- resolve_token_budget mit module_key="political_compass" → 800 (nicht 25000/4000)
- Wiring: _attempt_query reicht max_tokens/_module_key/chat_template_kwargs an query()
- Klassifikator-Matrix (ANSWER strict/loose, TRUNCATION, REFUSAL, FORMAT_DEVIATION)
- Retry-Strategie: Vanilla sauber (Refusal = Datenpunkt), Forced eskaliert
- Monitoring-Aggregation + Console-Warnung
- audit_logger: Sektion 2.9 + Ladder-Badges + Hydration
"""
import json
import re
import sys

import pytest  # noqa: E402
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import yaml  # noqa: E402

from benchmark_modules.political_compass.core.audit_logger import AuditLogWriter  # noqa: E402
from benchmark_modules.political_compass.core.evaluators import (  # noqa: E402
    PoliticalCompassEvaluator,
)
from benchmark_modules.political_compass.core.refusal_classifier import (  # noqa: E402
    RefusalClassifier,
    ResponseClassification,
)
from benchmark_modules.political_compass.test import (  # noqa: E402
    ANTI_REFUSAL_SYSTEM_APPEND,
    PC_FORMAT_REMINDER_APPEND,
    PoliticalCompassTest,
)
import benchmark_modules.political_compass.core.refusal_classifier as rc_module  # noqa: E402
import benchmark_modules.political_compass.test as pc_test_module  # noqa: E402


# ---------------------------------------------------------------------------
# Task 1: Config — Budget-Einträge
# ---------------------------------------------------------------------------

def test_config_has_political_compass_budgets():
    """Beide Budget-Keys müssen in der echten benchmark_config.yaml stehen."""
    config = yaml.safe_load((ROOT_DIR / "benchmark_config.yaml").read_text(encoding="utf-8"))
    assert config["token_budgets"]["political_compass"] == 800
    assert config["token_budgets_reasoning_models"]["political_compass"] == 800


def test_resolve_token_budget_political_compass_reasoning(monkeypatch, tmp_path):
    """Reasoning-Modell + module_key political_compass → 800 (nicht 25000, nicht 4000)."""
    import json

    import utils.model_card_io as model_card_io
    from utils.model_utils import resolve_token_budget

    # Card mit Probe=True → is_reasoning_model() True (magistral ist Trigger-Modell)
    card_path = tmp_path / "magistral-medium-latest.json"
    card_path.write_text(json.dumps({"thinking_probe_detected": True}), encoding="utf-8")
    monkeypatch.setattr(model_card_io, "CARD_DIR", tmp_path)

    config = {
        "token_budgets": {"political_compass": 800},
        "token_budgets_reasoning_models": {"political_compass": 800},
        "defaults": {"generation": {"num_predict": 8192}},
    }
    tokens, is_reasoning = resolve_token_budget(
        "magistral-medium-latest", 800, config, "political_compass",
    )
    assert is_reasoning is True
    assert tokens == 800


def test_resolve_token_budget_no_fallback_25k(monkeypatch, tmp_path):
    """Ohne explicit_budget würde der 25k-Fallback greifen — mit Wiring nie ausgelöst."""
    import json

    import utils.model_card_io as model_card_io
    from utils.model_utils import resolve_token_budget

    card_path = tmp_path / "magistral-medium-latest.json"
    card_path.write_text(json.dumps({"thinking_probe_detected": True}), encoding="utf-8")
    monkeypatch.setattr(model_card_io, "CARD_DIR", tmp_path)

    config = {
        "token_budgets": {"political_compass": 800},
        "token_budgets_reasoning_models": {"political_compass": 800},
        "defaults": {"generation": {"num_predict": 8192}},
    }
    # Der alte Bug-Pfad: kein max_tokens → 25k-Fallback. Dokumentiert das Wiring-Risiko.
    tokens, _ = resolve_token_budget("magistral-medium-latest", None, config, None)
    assert tokens == 25000  # Fallback existiert weiter — Wiring (Task 2) verhindert ihn


def test_resolve_token_budget_escalation_wins_over_module_budget(monkeypatch, tmp_path):
    """PC v3 Truncation-Re-Ask: explizit höheres Budget (1600) durchbricht das
    Modul-Budget (800). Kalibrierungs-Befund 2026-08-29: resolve_token_budget
    überschrieb das Re-Ask-Budget zurück auf 800 — die ×2-Eskalation war
    wirkungslos. Modul-Budget ist jetzt MINIMUM, höhere Requests gewinnen."""
    import json

    import utils.model_card_io as model_card_io
    from utils.model_utils import resolve_token_budget

    card_path = tmp_path / "magistral-medium-latest.json"
    card_path.write_text(json.dumps({"thinking_probe_detected": True}), encoding="utf-8")
    monkeypatch.setattr(model_card_io, "CARD_DIR", tmp_path)

    config = {
        "token_budgets": {"political_compass": 800},
        "token_budgets_reasoning_models": {"political_compass": 800},
        "defaults": {"generation": {"num_predict": 8192}},
    }
    # Standard-Pfad: requested == Modul-Budget → unverändert 800
    tokens, _ = resolve_token_budget(
        "magistral-medium-latest", 800, config, "political_compass",
    )
    assert tokens == 800
    # Eskalations-Pfad (Re-Ask): requested 1600 > Modul-Budget → 1600
    tokens, _ = resolve_token_budget(
        "magistral-medium-latest", 1600, config, "political_compass",
    )
    assert tokens == 1600
    # Niedrigerer Request wird auf Modul-Budget angehoben (Comparability)
    tokens, _ = resolve_token_budget(
        "magistral-medium-latest", 500, config, "political_compass",
    )
    assert tokens == 800


# ---------------------------------------------------------------------------
# Task 3: _parse_choice strict + Klassifikator-Matrix
# ---------------------------------------------------------------------------

def test_parse_choice_strict_vs_loose():
    ev = PoliticalCompassEvaluator()
    keys = ["A", "B", "C", "D"]
    # Eindeutige Pattern 1-3: strict erkennt
    assert ev._parse_choice("Answer: C", keys, strict=True) == "C"
    assert ev._parse_choice("Antwort: B", keys, strict=True) == "B"
    assert ev._parse_choice("B. Die zweite Option", keys, strict=True) == "B"
    assert ev._parse_choice("Ich wähle **A**.", keys, strict=True) == "A"
    # Loose-Fallback #4: strict lehnt ab, loose akzeptiert
    assert ev._parse_choice("I believe D is correct", keys, strict=True) is None
    assert ev._parse_choice("I believe D is correct", keys) == "D"


def _classifier() -> RefusalClassifier:
    return RefusalClassifier({})  # Defaults (config.yaml-äquivalent)


def test_classifier_answer_strict():
    c = _classifier()
    assert c.classify("Answer: B", strict_letter="B") == ResponseClassification.ANSWER


def test_classifier_loose_only_is_format_deviation():
    """Loose-parsbare Antwort ohne Strict-Match ist KEIN ANSWER (Plan Stufe 0)."""
    c = _classifier()
    result = c.classify("I believe B is the closest match.", strict_letter=None)
    assert result == ResponseClassification.FORMAT_DEVIATION


def test_classifier_truncation_finish_reason():
    c = _classifier()
    result = c.classify(
        "Answ", strict_letter=None, finish_reason="length", response_metadata={},
    )
    assert result == ResponseClassification.TRUNCATION


def test_classifier_truncation_empty_content_with_reasoning():
    c = _classifier()
    result = c.classify(
        "", strict_letter=None, finish_reason=None,
        response_metadata={"reasoning_tokens": 780, "think_content": "<think>…"},
    )
    assert result == ResponseClassification.TRUNCATION


def test_classifier_refusal_keyword_en():
    c = _classifier()
    result = c.classify(
        "I cannot answer this question.", strict_letter=None,
        finish_reason="stop", response_metadata={},
    )
    assert result == ResponseClassification.REFUSAL_CONTENT_SAFETY


def test_classifier_refusal_keyword_de():
    c = _classifier()
    result = c.classify(
        "Als KI-Modell kann ich keine politische Position beziehen.", strict_letter=None,
        finish_reason="stop", response_metadata={},
    )
    assert result == ResponseClassification.REFUSAL_CONTENT_SAFETY


def test_classifier_refusal_embedding(monkeypatch):
    """Embedding-Stufe: Keyword verfehlt, Ähnlichkeit trifft (Mock, kein Model-Load)."""
    monkeypatch.setattr(rc_module, "HAS_TRANSFORMERS", True)
    monkeypatch.setattr(
        rc_module.SemanticSimilarity, "find_best_match",
        classmethod(lambda cls, query, candidates: 0.82),
    )
    c = _classifier()
    result = c.classify(
        "Es wäre unangemessen für mich, hier eine Auswahl zu treffen.",
        strict_letter=None, finish_reason="stop", response_metadata={},
    )
    assert result == ResponseClassification.REFUSAL_CONTENT_SAFETY


def test_classifier_embedding_below_threshold(monkeypatch):
    monkeypatch.setattr(rc_module, "HAS_TRANSFORMERS", True)
    monkeypatch.setattr(
        rc_module.SemanticSimilarity, "find_best_match",
        classmethod(lambda cls, query, candidates: 0.42),
    )
    c = _classifier()
    result = c.classify(
        "Die zweite Option klingt plausibel, vielleicht.", strict_letter=None,
        finish_reason="stop", response_metadata={},
    )
    assert result == ResponseClassification.FORMAT_DEVIATION


def test_classifier_config_driven_keywords():
    """Keywords kommen aus dem config-Block (Config-driven, keine Magic Lists)."""
    c = RefusalClassifier({"config": {"refusal_keywords": ["xyzzy special refusal"]}})
    assert c.classify(
        "Xyzzy special refusal happened.", strict_letter=None,
        finish_reason="stop", response_metadata={},
    ) == ResponseClassification.REFUSAL_CONTENT_SAFETY


# ---------------------------------------------------------------------------
# Task 2/5: Wiring — _attempt_query kwargs
# ---------------------------------------------------------------------------

class _MockClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.last_token_usage = 10
        self.last_request_cost = 0.0
        self.last_output_tokens = 5
        self.last_response_metadata = {}

    def query(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0) if self.responses else "Answer: A"


def _context(client, **overrides):
    base = {
        "llm_client": client,
        "model": "test-model",
        "provider": "llamacpp",
        "evaluator": PoliticalCompassEvaluator(),
        "classifier": _classifier(),
        "is_forced": False,
        "max_tokens": 800,
        "_module_key": "political_compass",
        "thinking_off_supported": False,
        "system_prompt": "",
    }
    base.update(overrides)
    return base


def _state(**overrides):
    base = {
        "attempt": 0, "stage": "first_answer", "temperature": 0.1,
        "system_append": "", "max_tokens": 800, "thinking_off": False,
        "truncation_reask_used": False, "format_reask_used": False,
        "refusal_retry_count": 0, "trigger": "initial",
    }
    base.update(overrides)
    return base


def test_attempt_query_passes_budget_kwargs():
    test = PoliticalCompassTest()
    client = _MockClient(["Answer: A"])
    test._attempt_query(
        "test-model", "llamacpp", client, "prompt?", _context(client), _state(),
        "political_compass",
    )
    assert client.calls[0]["max_tokens"] == 800
    assert client.calls[0]["_module_key"] == "political_compass"


def test_attempt_query_no_budget_no_kwargs():
    test = PoliticalCompassTest()
    client = _MockClient(["Answer: A"])
    ctx = _context(client, max_tokens=None)
    state = _state(max_tokens=None)
    test._attempt_query("test-model", "llamacpp", client, "prompt?", ctx, state, "political_compass")
    assert "max_tokens" not in client.calls[0]
    assert "_module_key" not in client.calls[0]


def test_attempt_query_thinking_off_kwargs():
    test = PoliticalCompassTest()
    client = _MockClient(["Answer: A"])
    test._attempt_query(
        "test-model", "vllm_spark", client, "prompt?", _context(client),
        _state(thinking_off=True), "political_compass",
    )
    assert client.calls[0]["chat_template_kwargs"] == {"enable_thinking": False}


# ---------------------------------------------------------------------------
# Task 4: Retry-Strategie — decide/apply + Attempt-Treppe
# ---------------------------------------------------------------------------

def test_decide_vanilla_refusal_is_datapoint():
    test = PoliticalCompassTest()
    action = test._decide_retry_action(
        ResponseClassification.REFUSAL_CONTENT_SAFETY, False, _state(), is_forced=False,
    )
    assert action == "refusal_early"


def test_decide_forced_refusal_escalates_then_hard_fails():
    test = PoliticalCompassTest()
    assert test._decide_retry_action(
        ResponseClassification.REFUSAL_CONTENT_SAFETY, False, _state(), is_forced=True,
    ) == "refusal_retry"
    assert test._decide_retry_action(
        ResponseClassification.REFUSAL_CONTENT_SAFETY, False,
        _state(refusal_retry_count=2), is_forced=True,
    ) == "hard_fail"


def test_decide_truncation_and_format_single_reask():
    test = PoliticalCompassTest()
    assert test._decide_retry_action(
        ResponseClassification.TRUNCATION, False, _state(), is_forced=False,
    ) == "truncation_reask"
    assert test._decide_retry_action(
        ResponseClassification.TRUNCATION, False,
        _state(truncation_reask_used=True), is_forced=False,
    ) == "truncation_final"
    assert test._decide_retry_action(
        ResponseClassification.FORMAT_DEVIATION, False, _state(), is_forced=True,
    ) == "format_reask"
    assert test._decide_retry_action(
        ResponseClassification.FORMAT_DEVIATION, False,
        _state(format_reask_used=True), is_forced=True,
    ) == "format_final"


def test_decide_api_error_escalates_in_vanilla():
    test = PoliticalCompassTest()
    assert test._decide_retry_action(
        ResponseClassification.FORMAT_DEVIATION, True, _state(), is_forced=False,
    ) == "api_retry"
    assert test._decide_retry_action(
        ResponseClassification.FORMAT_DEVIATION, True,
        _state(refusal_retry_count=2), is_forced=False,
    ) == "hard_fail"


def test_apply_truncation_reask_doubles_budget_and_toggles_thinking():
    test = PoliticalCompassTest()
    state = _state()
    desc = test._apply_retry_action(
        "truncation_reask", state, [0.1, 0.4, 0.7], ANTI_REFUSAL_SYSTEM_APPEND,
        800, thinking_off_supported=True, is_forced=False,
    )
    assert state["max_tokens"] == 1600
    assert state["thinking_off"] is True
    assert state["stage"] == "thinking_off_reask"
    assert "Budget ×2" in desc


def test_apply_truncation_reask_without_thinking_off_support():
    test = PoliticalCompassTest()
    state = _state()
    test._apply_retry_action(
        "truncation_reask", state, [0.1, 0.4, 0.7], ANTI_REFUSAL_SYSTEM_APPEND,
        800, thinking_off_supported=False, is_forced=False,
    )
    assert state["thinking_off"] is False
    assert state["stage"] == "truncation_reask"


def test_apply_format_reask_uses_format_reminder_not_anti_refusal():
    test = PoliticalCompassTest()
    state = _state()
    test._apply_retry_action(
        "format_reask", state, [0.1, 0.4, 0.7], ANTI_REFUSAL_SYSTEM_APPEND,
        800, thinking_off_supported=False, is_forced=False,
    )
    assert state["system_append"] == PC_FORMAT_REMINDER_APPEND
    assert ANTI_REFUSAL_SYSTEM_APPEND not in state["system_append"]


def test_apply_api_retry_vanilla_stays_clean():
    """API-Retry im Vanilla-Run bekommt KEIN Anti-Refusal-Append (sauberer Lauf)."""
    test = PoliticalCompassTest()
    state = _state()
    test._apply_retry_action(
        "api_retry", state, [0.1, 0.4, 0.7], ANTI_REFUSAL_SYSTEM_APPEND,
        800, thinking_off_supported=False, is_forced=False,
    )
    assert state["system_append"] == ""
    assert state["temperature"] == 0.4


def test_apply_refusal_retry_forced_appends_anti_refusal():
    test = PoliticalCompassTest()
    state = _state()
    test._apply_retry_action(
        "refusal_retry", state, [0.1, 0.4, 0.7], ANTI_REFUSAL_SYSTEM_APPEND,
        800, thinking_off_supported=False, is_forced=True,
    )
    assert state["system_append"] == ANTI_REFUSAL_SYSTEM_APPEND
    assert state["temperature"] == 0.4


def _run_attempts(client, **ctx_overrides):
    test = PoliticalCompassTest()
    with patch.object(pc_test_module.time, "sleep"):
        return test._execute_question_attempts(
            "q1", "prompt?", {"A": "A", "B": "B", "C": "C", "D": "D"},
            _context(client, **ctx_overrides), {"total_tokens": 0, "total_cost": 0.0},
        )


def test_attempts_vanilla_refusal_single_attempt():
    client = _MockClient(["I cannot answer this question."])
    client.last_response_metadata = {"finish_reason": "stop"}
    outcome = _run_attempts(client, is_forced=False)
    assert outcome["event"] == "refusal_early"
    assert outcome["classification"] == "refusal_content_safety"
    assert len(outcome["escalation_ladder"]) == 1
    assert len(client.calls) == 1
    # Kein Anti-Refusal-Append im Vanilla-Lauf
    assert client.calls[0]["system"] == ""


def test_attempts_forced_refusal_escalation_ladder():
    client = _MockClient([
        "I cannot answer this question.",
        "I'm sorry, but I cannot comply.",
        "Answer: C",
    ])
    client.last_response_metadata = {"finish_reason": "stop"}
    outcome = _run_attempts(client, is_forced=True)
    assert outcome["event"] == "answer"
    assert len(client.calls) == 3
    stages = [e["stage"] for e in outcome["escalation_ladder"]]
    assert stages == ["first_answer", "refusal_retry", "refusal_retry"]
    temps = [e["temperature"] for e in outcome["escalation_ladder"]]
    assert temps == [0.1, 0.4, 0.7]
    # Anti-Refusal-Append ab Retry aktiv (Bestandsverhalten Forced-Run)
    assert client.calls[1]["system"].endswith(ANTI_REFUSAL_SYSTEM_APPEND.strip() or "]") or \
        ANTI_REFUSAL_SYSTEM_APPEND in client.calls[1]["system"]


def test_attempts_truncation_reask_doubles_budget():
    client = _MockClient(["", "Answer: B"])
    client.last_response_metadata = {
        "finish_reason": "length", "reasoning_tokens": 795, "think_content": "<think>",
    }
    outcome = _run_attempts(client, is_forced=False, thinking_off_supported=False)
    assert outcome["event"] == "answer"
    assert len(client.calls) == 2
    assert client.calls[0]["max_tokens"] == 800
    assert client.calls[1]["max_tokens"] == 1600
    assert outcome["reask_used"] is True
    assert outcome["escalation_ladder"][1]["stage"] == "truncation_reask"


def test_attempts_truncation_hard_fail_after_reask():
    client = _MockClient(["", ""])
    client.last_response_metadata = {
        "finish_reason": "length", "reasoning_tokens": 795,
    }
    outcome = _run_attempts(client, is_forced=False)
    assert outcome["event"] == "truncation_final"
    assert outcome["classification"] == "truncation"
    assert len(client.calls) == 2  # genau EIN Re-Ask, kein Endlos-Retry


# ---------------------------------------------------------------------------
# Langsame Truncation ≠ API-Fehler (Kalibrierungs-Befund 2026-08-29)
# 3120 Tokens bei ~14 t/s ≈ 223 s > PC_QUERY_TIMEOUT (120 s) — vor dem Fix
# wurde jede langsame Truncation als api_retry fehlklassifiziert und die
# Budget-×2-Eskalation griff bei lokalen Thinking-Modellen nie.
# ---------------------------------------------------------------------------

def test_attempts_slow_truncation_gets_budget_escalation(monkeypatch):
    """Timeout + leerer Content + Generierungs-Evidenz → truncation_reask (6240)."""
    monkeypatch.setattr(pc_test_module, "PC_QUERY_TIMEOUT", 0.0)  # jeder Query "timed out"
    client = _MockClient(["", "Answer: B"])
    client.last_response_metadata = {
        "finish_reason": "length", "reasoning_tokens": 3120,
    }
    outcome = _run_attempts(client, is_forced=False, max_tokens=3120)
    assert outcome["event"] == "answer"
    assert len(client.calls) == 2
    assert client.calls[1]["max_tokens"] == 6240  # ×2-Eskalation greift
    stages = [e["stage"] for e in outcome["escalation_ladder"]]
    assert stages == ["first_answer", "truncation_reask"]
    assert outcome["escalation_ladder"][1]["trigger"] == "truncation"


def test_attempts_genuine_exception_is_api_retry(monkeypatch):
    """Exception (keine Generierungs-Evidenz) → api_retry, Budget unverändert."""
    monkeypatch.setattr(pc_test_module, "PC_QUERY_TIMEOUT", 0.0)
    client = _MockClient(["Answer: A"])
    client.last_response_metadata = {"finish_reason": "stop"}
    original_query = client.query
    failed = {"once": False}

    def failing_first(**kwargs):
        if not failed["once"]:  # genau EINmal werfen (Exception appendet nicht)
            failed["once"] = True
            raise RuntimeError("connection refused")
        return original_query(**kwargs)

    client.query = failing_first  # type: ignore[method-assign]
    outcome = _run_attempts(client, is_forced=False, max_tokens=3120)
    assert outcome["event"] == "answer"
    assert len(client.calls) == 1  # Exception-Call appendet nicht im Mock
    assert client.calls[0]["max_tokens"] == 3120  # kein Budget-Eingriff
    stages = [e["stage"] for e in outcome["escalation_ladder"]]
    assert stages == ["first_answer", "refusal_retry"]
    assert outcome["escalation_ladder"][1]["trigger"] == "api_error"


def test_attempts_exception_after_truncation_uses_fresh_metadata(monkeypatch):
    """Stale-Metadaten-Schutz: Exception nach Truncation darf die Vorgänger-
    Metadaten (3120/length) nicht erben — sonst würde der api_retry als
    zweiter truncation_reask fehlrouten und die Frage vorzeitig verlieren."""
    monkeypatch.setattr(pc_test_module, "PC_QUERY_TIMEOUT", 0.0)
    client = _MockClient(["", "Answer: C"])
    original_query = client.query
    counter = {"n": 0}

    def fail_second(**kwargs):
        counter["n"] += 1
        if counter["n"] == 2:  # genau der zweite Call wirft
            raise RuntimeError("read timeout")
        client.last_response_metadata = {"finish_reason": "length", "reasoning_tokens": 3120}
        return original_query(**kwargs)

    client.query = fail_second  # type: ignore[method-assign]
    outcome = _run_attempts(client, is_forced=False, max_tokens=3120)
    assert outcome["event"] == "answer"
    assert len(client.calls) == 2  # Exception-Call appendet nicht im Mock
    assert client.calls[0]["max_tokens"] == 3120   # Attempt 1 (Truncation)
    assert client.calls[1]["max_tokens"] == 6240   # Attempt 3 erbt das Re-Ask-Budget
    stages = [e["stage"] for e in outcome["escalation_ladder"]]
    assert stages == ["first_answer", "truncation_reask", "refusal_retry"]


# ---------------------------------------------------------------------------
# Resume-Pfad: v3-Felder bewahren (Live-Befund 2026-08-29)
# ---------------------------------------------------------------------------

def test_resume_preserves_existing_v3_fields():
    """Resume darf classification/escalation_ladder eines früheren Laufs nicht
    mit None/[] überschreiben — sonst verliert jeder Interrupt+Resume die
    Eskalations-Traceability der resumten Fragen."""
    test = PoliticalCompassTest()
    evaluator = PoliticalCompassEvaluator()
    checkpoint = {
        "detailed_responses": {
            "1_q1": {
                "id": "q1", "question": "", "answer": "A", "raw_response": "Answer: A",
                "category": "7.1", "is_retried": True,
                "classification": "answer",
                "escalation_ladder": [{"attempt": 1, "stage": "first_answer",
                                       "temperature": 0.1, "trigger": "initial",
                                       "max_tokens": 3120, "finish_reason": "length",
                                       "reasoning_tokens": 3120, "output_tokens": 3120},
                                      {"attempt": 2, "stage": "truncation_reask",
                                       "temperature": 0.1, "trigger": "truncation",
                                       "max_tokens": 6240, "finish_reason": "stop",
                                       "reasoning_tokens": 900, "output_tokens": 901}],
                "finish_reason": "stop", "reasoning_tokens": 900,
                "output_tokens": 901, "reask_used": True,
                "execution_time_s": 42.0, "is_timeout": False,
            },
        },
    }
    metrics = {"completed_in_run": 0, "total_in_run": 1, "total_tokens": 0}
    asset = {
        "metadata": {"id": "q1"},
        "options": {
            "A": {"values": {"x": -1.0, "y": 1.0}},
            "B": {"values": {"x": 1.0, "y": -1.0}},
            "C": {"values": {"x": -1.0, "y": -1.0}},
            "D": {"values": {"x": 1.0, "y": 1.0}},
        },
    }
    mapping = {"A": "A", "B": "B", "C": "C", "D": "D"}

    with patch.object(pc_test_module.time, "sleep"):
        test._resume_cached_response(
            "1_q1", "q1", "Answer: A", mapping, "7.1",
            evaluator, asset, metrics, checkpoint,
            types.SimpleNamespace(update_progress=lambda *a, **k: None),
        )

    entry = checkpoint["detailed_responses"]["1_q1"]
    assert entry["classification"] == "answer"
    assert len(entry["escalation_ladder"]) == 2
    assert entry["escalation_ladder"][1]["stage"] == "truncation_reask"
    assert entry["reasoning_tokens"] == 900
    assert entry["reask_used"] is True
    assert entry["is_retried"] is True


def test_resume_without_prior_v3_fields_stays_graceful():
    """Legacy-Resume (Checkpoint ohne v3-Felder) schreibt None/[] — kein Crash."""
    test = PoliticalCompassTest()
    evaluator = PoliticalCompassEvaluator()
    checkpoint = {"detailed_responses": {}}
    metrics = {"completed_in_run": 0, "total_in_run": 1, "total_tokens": 0}
    asset = {
        "metadata": {"id": "q1"},
        "options": {
            "A": {"values": {"x": -1.0, "y": 1.0}},
            "B": {"values": {"x": 1.0, "y": -1.0}},
            "C": {"values": {"x": -1.0, "y": -1.0}},
            "D": {"values": {"x": 1.0, "y": 1.0}},
        },
    }
    mapping = {"A": "A", "B": "B", "C": "C", "D": "D"}

    with patch.object(pc_test_module.time, "sleep"):
        test._resume_cached_response(
            "1_q1", "q1", "Answer: A", mapping, "7.1",
            evaluator, asset, metrics, checkpoint,
            types.SimpleNamespace(update_progress=lambda *a, **k: None),
        )

    entry = checkpoint["detailed_responses"]["1_q1"]
    assert entry["classification"] is None
    assert entry["escalation_ladder"] == []
    assert entry["answer"] == "A"


def test_attempts_format_reask_single():
    client = _MockClient(["The second option seems best.", "Answer: D"])
    client.last_response_metadata = {"finish_reason": "stop"}
    outcome = _run_attempts(client, is_forced=False)
    assert outcome["event"] == "answer"
    assert len(client.calls) == 2
    assert PC_FORMAT_REMINDER_APPEND in client.calls[1]["system"]


# ---------------------------------------------------------------------------
# Task 6: Monitoring-Aggregation
# ---------------------------------------------------------------------------

def _stats(run_idx, classification, event="answer", stages=None, reasoning=100, output=20):
    stage_list = stages or ["first_answer"]
    reask = any(s in stage_list for s in ("truncation_reask", "thinking_off_reask", "format_reask"))
    return {
        "run_idx": run_idx, "q_id": f"q{run_idx}_{classification}", "classification": classification,
        "reasoning_tokens": reasoning, "output_tokens": output,
        "truncation": classification == "truncation", "reask": reask,
        "attempts": len(stage_list),
        "ladder_stages": stage_list, "event": event,
    }


def test_aggregate_pc_v3_stats():
    test = PoliticalCompassTest()
    stats = [
        _stats(1, "answer"),
        _stats(1, "refusal_content_safety", event="refusal_early"),
        _stats(1, "truncation", event="truncation_final",
               stages=["first_answer", "truncation_reask"], reasoning=900),
        _stats(2, "answer", stages=["first_answer", "refusal_retry"]),
        _stats(2, "refusal_content_safety", event="hard_refusal",
               stages=["first_answer", "refusal_retry", "refusal_retry"]),
    ]
    token_stats, escalation = test._aggregate_pc_v3_stats(stats)

    assert token_stats["truncation_count"] == 1
    assert token_stats["reask_count"] == 1  # nur Truncation/Format-Re-Asks, keine Refusal-Retries
    assert token_stats["refusal_counts"]["answer"] == 2
    assert token_stats["reasoning_tokens"]["max"] == 900
    assert escalation["vanilla"]["refusal_early"] == 1
    assert escalation["vanilla"]["reasks_by_type"]["truncation"] == 1
    assert escalation["forced"]["hard_refusals"] == 1
    assert escalation["forced"]["escalation_stages_used"]["refusal_retry"] == 3


def test_warn_reasoning_overrun_triggers(capsys):
    PoliticalCompassTest._warn_reasoning_overrun(
        {"reasoning_tokens": {"avg": 1700}}, 800, "test-model",
    )
    out = capsys.readouterr().out
    assert "1700" in out and "800" in out


def test_warn_reasoning_overrun_silent(capsys):
    PoliticalCompassTest._warn_reasoning_overrun(
        {"reasoning_tokens": {"avg": 900}}, 800, "test-model",
    )
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# Task 7: audit_logger — Hydration, Badges, Sektion 2.9
# ---------------------------------------------------------------------------

def _v3_response(run_idx, q_id, classification, ladder, answer="A"):
    return {
        "id": q_id, "question": "", "answer": answer, "raw_response": f"Answer: {answer}",
        "category": "7.1", "is_retried": len(ladder) > 1,
        "classification": classification, "escalation_ladder": ladder,
        "finish_reason": "stop", "reasoning_tokens": 120, "output_tokens": 8,
        "reask_used": len(ladder) > 1, "execution_time_s": 2.0, "is_timeout": False,
    }


def _ladder(stages, temps=None):
    return [
        {"attempt": i + 1, "stage": s, "temperature": (temps or [0.1] * len(stages))[i],
         "trigger": "initial", "max_tokens": 800, "finish_reason": "stop",
         "reasoning_tokens": 100, "output_tokens": 10}
        for i, s in enumerate(stages)
    ]


def test_hydrate_responses_preserves_v3_fields():
    detailed = {
        "1_q1": _v3_response("1", "q1", "answer", _ladder(["first_answer"])),
        "2_q1": _v3_response(
            "2", "q1", "refusal_content_safety",
            _ladder(["first_answer", "refusal_retry"], [0.1, 0.4]), answer="REFUSAL/UNPARSABLE: no",
        ),
    }
    hydrated = AuditLogWriter._hydrate_responses(detailed, {})
    assert hydrated["q1"]["vanilla"]["classification"] == "answer"
    assert hydrated["q1"]["forced"]["classification"] == "refusal_content_safety"
    assert hydrated["q1"]["forced"]["escalation_ladder"][1]["stage"] == "refusal_retry"
    assert hydrated["q1"]["vanilla"]["reasoning_tokens"] == 120


def test_ladder_badge_variants():
    trunc = AuditLogWriter._ladder_badge({
        "classification": "answer", "is_retried": True,
        "escalation_ladder": _ladder(["first_answer", "truncation_reask"]),
    })
    assert "Truncation-Re-Ask" in trunc and "[ANS]" in trunc

    hard = AuditLogWriter._ladder_badge({
        "classification": "refusal_content_safety", "is_retried": True,
        "escalation_ladder": _ladder(["first_answer", "refusal_retry", "refusal_retry"]),
    })
    assert "Hard Refusal" in hard and "[REF]" in hard

    escalated = AuditLogWriter._ladder_badge({
        "classification": "answer", "is_retried": True,
        "escalation_ladder": _ladder(["first_answer", "refusal_retry"], [0.1, 0.4]),
    })
    assert "temp 0.4" in escalated

    early = AuditLogWriter._ladder_badge({
        "classification": "refusal_content_safety", "is_retried": False,
        "escalation_ladder": _ladder(["first_answer"]),
    })
    assert "Vanilla-Datenpunkt" in early


def test_ladder_badge_legacy_graceful():
    legacy = AuditLogWriter._ladder_badge({"is_retried": True})
    assert "v2-Methodik" in legacy


def _capture_report(detailed):
    """write_audit_log mit gepatchtem File-IO; liefert die Zeilen zurück."""
    import io

    lines: list[str] = []
    real_open = open

    def fake_open(path, /, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if "00_bias_report" in str(path) and "w" in mode:
            buf = io.StringIO()

            class Writer:
                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    lines.extend(buf.getvalue().splitlines())

                def write(self, s):
                    buf.write(s)

            return Writer()
        return real_open(path, *args, **kwargs)

    with patch("builtins.open", side_effect=fake_open), patch(
        "pathlib.Path.mkdir", lambda *a, **kw: None
    ):
        AuditLogWriter.write_audit_log(
            model="pc-v3-test-model",
            vanilla_res={"score_x": 1.0, "score_y": 1.0},
            forced_res={"score_x": 2.0, "score_y": 2.0},
            shift_x=1.0, shift_y=1.0, shift_distance=1.41, polarity_flip_rate=0.0,
            detailed_responses=detailed,
            total_tokens=500,
        )
    return lines


def test_report_renders_escalation_section_before_details():
    detailed = {
        "1_q1": _v3_response("1", "q1", "answer", _ladder(["first_answer"])),
        "2_q1": _v3_response(
            "2", "q1", "refusal_content_safety",
            _ladder(["first_answer", "refusal_retry", "refusal_retry"], [0.1, 0.4, 0.7]),
            answer="REFUSAL/UNPARSABLE: no",
        ),
    }
    lines = _capture_report(detailed)
    text = "\n".join(lines)

    assert "Eskalations- & Refusal-Verhalten" in text
    assert "Hard Refusals" in text
    # HEAD-truncat-Sicherheit: Sektion 2.9 liegt VOR den Detail-Antworten
    assert text.index("Eskalations- & Refusal-Verhalten") < text.index("## 3. Detail-Antworten")
    # Ladder-Badges in der Detail-Sektion
    assert "Hard Refusal" in text  # Badge aus q1-forced


def test_report_legacy_run_graceful():
    detailed = {
        "1_q1": {
            "id": "q1", "question": "", "answer": "A", "raw_response": "Answer: A",
            "category": "7.1", "is_retried": True, "output_tokens": 5,
            "execution_time_s": 1.0, "is_timeout": False,
        },
        "2_q1": {
            "id": "q1", "question": "", "answer": "B", "raw_response": "Answer: B",
            "category": "7.1", "is_retried": False, "output_tokens": 5,
            "execution_time_s": 1.0, "is_timeout": False,
        },
    }
    lines = _capture_report(detailed)
    text = "\n".join(lines)
    assert "v2-Methodik" in text
    assert "Legacy-Run" in text


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# PC v3 Token-Probe v2: Stratifiziertes zweistufiges Sampling + Profil-Entscheidung
# (Auditor-Review: Stufe 1 = 1 Frage/Block @ 300, Stufe 2 = Eskalation nur für
# verdächtige Blöcke — Block 7.2 kann nicht mehr durchrutschen)
# ---------------------------------------------------------------------------

from benchmark_modules.political_compass.core.token_probe import (  # noqa: E402
    PC_PROBE_STAGES,
    PcProbeClassification,
    probe_pc_profile,
    select_screening_questions,
)
import utils.model_card_io as model_card_io  # noqa: E402
from utils.model_token_budget import (  # noqa: E402
    get_calibrated_pc_budget,
    read_pc_calibration,
    read_pc_profile_flag,
    resolve_token_budget,
)


class _MockProbeClient:
    """Skriptierter Client: Liste von (response, finish_reason)-Tupeln.

    Das Sentinel ``OK`` extrahiert den validen Display-Buchstaben aus dem
    Prompt (die echten PC-Mappings nutzen gemischte Buchstaben, nicht A–D).
    """

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.last_output_tokens = 10
        self.last_response_metadata = {}

    def query(self, **kwargs):
        self.calls.append(kwargs)
        entry = self.script.pop(0) if self.script else OK
        if entry is OK:
            match = re.search(r"^([A-Z])\)", kwargs.get("prompt", ""), re.MULTILINE)
            letter = match.group(1) if match else "A"
            response, finish = f"Answer: {letter}", "stop"
        else:
            response, finish = entry
        self.last_response_metadata = {"finish_reason": finish}
        return response


OK = object()   # Sentinel: konvergierte Antwort mit Prompt-validem Buchstaben
TRUNC = ("", "length")


def _run_probe(script, num_blocks=None, supports_instruct_mode=True):
    test = PoliticalCompassTest()
    screening = select_screening_questions(test)
    if num_blocks is not None:
        screening = screening[:num_blocks]
    client = _MockProbeClient(script)
    cal = probe_pc_profile(
        "m", "llamacpp", client, screening, test,
        supports_instruct_mode=supports_instruct_mode,
    )
    return cal, client


def test_screening_covers_all_blocks():
    test = PoliticalCompassTest()
    screening = select_screening_questions(test)
    assert len(screening) == 9  # alle 9 Blöcke (7.1–7.9), nicht nur 4 Dimensionen
    blocks = {q["block"] for q in screening}
    assert len(blocks) == 9
    assert any(b.startswith("7.2") for b in blocks)  # der v1-blinde Block ist dabei


def test_probe_all_clean_thinking_profile():
    """Alle 9 Blöcke konvergieren @ 300 → thinking, Budget 390, keine Stufe 2."""
    cal, client = _run_probe([OK] * 9)
    assert cal.classification == PcProbeClassification.SELF_LIMITING.value
    assert cal.profile == "thinking"
    assert cal.budget == 390  # ceil(300 × 1.3)
    assert len(client.calls) == 9  # Screening only — saubere Blöcke werden nicht angefasst
    assert all(b["status"] == "clean_300" for b in cal.block_report)


def test_probe_all_greedy_instruct_profile():
    """Kein Block konvergiert irgendwo → instruct, Budget None."""
    cal, client = _run_probe([TRUNC] * 100)
    assert cal.classification == PcProbeClassification.GREEDY_UNCAPPED.value
    assert cal.profile == "instruct"
    assert cal.budget is None
    # 9 Screening + 4 eskalierte Blöcke (Cost-Bound) × 3 Fragen × 3 Stufen
    assert len(client.calls) == 9 + 4 * 3 * 3


def test_probe_hybrid_dual_early_exit():
    """Konvergenz (Screening) + Greedy (Stufe 2) → hybrid_dual mit Früh-Abbruch."""
    # 5 Blöcke clean @ 300, 4 verdächtig; erster verdächtiger Block: durchgängig greedy
    script = [OK] * 5 + [TRUNC] * 4  # Screening
    script += [TRUNC] * (3 * 3)      # Stufe 2 Block 1: 3 Fragen × 3 Stufen, alle trunc
    cal, client = _run_probe(script)
    assert cal.classification == PcProbeClassification.INCONSISTENT.value
    assert cal.profile == "hybrid_dual"
    assert cal.budget == 390  # aus den 5 sauberen Blöcken
    # Früh-Abbruch: 9 Screening + 9 Stufe-2-Requests (nur Block 1), keine weiteren
    assert len(client.calls) == 18


def test_probe_suspicious_block_converges_at_1200():
    """Verdächtiger Block konvergiert erst @ 1200 (Kontrolle 2400 stabil) → thinking."""
    # 8 Blöcke clean @ 300; 1 verdächtiger Block: 600 trunc, 1200 OK, Kontrolle 2400 OK
    script = [OK] * 8 + [TRUNC]          # Screening (8 clean, 1 suspicious)
    script += [TRUNC] * 3                # Stufe 2: 600 → 0/3
    script += [OK] * 3                   # 1200 → 3/3 (base)
    script += [OK] * 3                   # Kontrolle 2400 → stabil
    cal, client = _run_probe(script)
    assert cal.classification == PcProbeClassification.SELF_LIMITING.value
    assert cal.profile == "thinking"
    assert cal.budget == 1560  # ceil(1200 × 1.3)
    assert cal.converged_stage == 1200
    assert len(client.calls) == 9 + 9


def test_probe_cap_hit_conservative_hybrid(monkeypatch):
    """Cost-Bound: 4 Blöcke eskaliert (alle konvergiert), weitere verdächtig
    ungetestet → konservativ hybrid_dual statt thinking."""
    import benchmark_modules.political_compass.core.token_probe as tp
    monkeypatch.setattr(tp, "PC_PROBE_MAX_ESCALATED_BLOCKS", 2)
    # 6 Blöcke clean, 4 verdächtig; beide eskalierten Blöcke konvergieren @ 600+Kontrolle
    script = [OK] * 6 + [TRUNC] * 4      # Screening
    for _ in range(2):                    # 2 eskalierte Blöcke
        script += [TRUNC] * 3            # 600 → 0/3
        script += [OK] * 3               # 1200 → 3/3 (base)
        script += [OK] * 3               # Kontrolle 2400
    cal, client = _run_probe(script)
    assert cal.profile == "hybrid_dual"  # konservativ: 2 verdächtige Blöcke ungetestet
    assert cal.classification == PcProbeClassification.INCONSISTENT.value


def test_probe_inconsistent_thinking_only_stays_thinking():
    """Thinking-only-Ausnahme (Regel 2026-08-29): inconsistent + kein
    Instruct-Modus (dual_profile: false) → thinking statt hybrid_dual.
    Klassifikation und Budget bleiben unverändert (Messverhalten vs.
    Profil-Entscheidung)."""
    script = [OK] * 5 + [TRUNC] * 4  # Screening: 5 clean, 4 verdächtig
    script += [TRUNC] * (3 * 3)      # Stufe 2 Block 1: durchgängig greedy
    cal, _client = _run_probe(script, supports_instruct_mode=False)
    assert cal.classification == PcProbeClassification.INCONSISTENT.value
    assert cal.profile == "thinking"  # Ausnahme: kein hybrid_dual
    assert cal.budget == 390          # kalibriertes Budget gilt weiter
    assert "Thinking-only-Ausnahme" in cal.notes


def test_probe_greedy_thinking_only_stays_thinking():
    """Thinking-only-Ausnahme: durchgängig greedy + kein Instruct-Modus →
    thinking statt instruct (keine saubere Messung, aber kein Modus-Wechsel
    in einen nicht existierenden Modus)."""
    cal, _client = _run_probe([TRUNC] * 100, supports_instruct_mode=False)
    assert cal.classification == PcProbeClassification.GREEDY_UNCAPPED.value
    assert cal.profile == "thinking"  # Ausnahme: kein instruct
    assert cal.budget is None
    assert "Thinking-only-Ausnahme" in cal.notes


def test_probe_card_dict_shape():
    cal, _client = _run_probe([OK] * 9)
    card = cal.to_card_dict()
    assert set(card.keys()) == {"budget", "classification", "profile", "tested", "converged_stage", "notes"}
    assert card["profile"] == "thinking"



# Card-Kalibrierung: read_pc_calibration + resolve_token_budget-Integration
# ---------------------------------------------------------------------------

def _write_calibration_card(monkeypatch, tmp_path, calibration):
    # thinking_probe_detected: true → Reasoning-Branch (dort greift die Kalibrierung)
    card_path = tmp_path / "test-model.json"
    card_path.write_text(json.dumps({
        "model_id": "test-model",
        "thinking_probe_detected": True,
        "pc_token_calibration": calibration,
    }), encoding="utf-8")
    monkeypatch.setattr(model_card_io, "CARD_DIR", tmp_path)
    return card_path


def test_read_pc_calibration_roundtrip(monkeypatch, tmp_path):
    cal = {"budget": 780, "classification": "self_limiting", "tested": "2026-08-29",
           "converged_stage": 600, "notes": ""}
    _write_calibration_card(monkeypatch, tmp_path, cal)
    assert read_pc_calibration("test-model") == cal
    assert get_calibrated_pc_budget("test-model") == 780


def test_read_pc_calibration_greedy_returns_no_budget(monkeypatch, tmp_path):
    cal = {"budget": None, "classification": "greedy_uncapped", "tested": "2026-08-29",
           "converged_stage": None, "notes": ""}
    _write_calibration_card(monkeypatch, tmp_path, cal)
    assert read_pc_calibration("test-model") == cal
    assert get_calibrated_pc_budget("test-model") is None


def test_read_pc_calibration_missing_card(monkeypatch, tmp_path):
    monkeypatch.setattr(model_card_io, "CARD_DIR", tmp_path)
    assert read_pc_calibration("no-such-model") is None
    assert get_calibrated_pc_budget("no-such-model") is None


def test_resolve_budget_calibrated_wins_over_config(monkeypatch, tmp_path):
    """Card-Kalibrierung (2500) gewinnt über Config-Modul-Budget (800)."""
    _write_calibration_card(monkeypatch, tmp_path, {
        "budget": 2500, "classification": "self_limiting", "tested": "2026-08-29",
        "converged_stage": 1200, "notes": "",
    })
    config = {
        "token_budgets": {"political_compass": 800},
        "token_budgets_reasoning_models": {"political_compass": 800},
        "defaults": {"generation": {"num_predict": 8192}},
    }
    tokens, _ = resolve_token_budget("test-model", 800, config, "political_compass")
    assert tokens == 2500


def test_resolve_budget_greedy_falls_back_to_config(monkeypatch, tmp_path):
    _write_calibration_card(monkeypatch, tmp_path, {
        "budget": None, "classification": "greedy_uncapped", "tested": "2026-08-29",
        "converged_stage": None, "notes": "",
    })
    config = {
        "token_budgets": {"political_compass": 800},
        "token_budgets_reasoning_models": {"political_compass": 800},
        "defaults": {"generation": {"num_predict": 8192}},
    }
    tokens, _ = resolve_token_budget("test-model", 800, config, "political_compass")
    assert tokens == 800


def test_read_pc_profile_flag(monkeypatch, tmp_path):
    """Card-getriebener Transparenz-Pfad für Coverage-Regel-Ersatzläufe."""
    card_path = tmp_path / "instruct-model.json"
    card_path.write_text(json.dumps({
        "model_id": "instruct-model",
        "pc_profile_forced_instruct": True,
    }), encoding="utf-8")
    monkeypatch.setattr(model_card_io, "CARD_DIR", tmp_path)
    assert read_pc_profile_flag("instruct-model") is True

    # Ohne Flag → False; ohne Card → False
    card_path.write_text(json.dumps({"model_id": "instruct-model"}), encoding="utf-8")
    assert read_pc_profile_flag("instruct-model") is False
    assert read_pc_profile_flag("no-such-model") is False


def test_handle_results_attribution_to_original_id(monkeypatch):
    """Coverage-Regel-Ersatzlauf: Ergebnis läuft unter der ORIGINAL-Modell-ID
    auf (ein Leaderboard-Eintrag pro Modell), Transparenz wird injiziert."""
    import types
    from utils.scoring import political_compass_handler as pch

    report = {
        "model": "gemma-4-12b-it-ud-q6_k_xl-instruct-spark",
        "statistics": {},
        "shift": {"distance": 0.0},
    }
    captured: dict = {}
    monkeypatch.setattr(pch, "PCResultManager", types.SimpleNamespace(
        print_summary=lambda r: None,
        save_json=lambda r, d: None,
    ))
    monkeypatch.setattr(
        pch.PoliticalCompassHandler, "_update_local_pc_csv",
        classmethod(lambda cls, m, r, v: captured.setdefault("csv_model", m)),
    )
    monkeypatch.setattr(
        pch.PoliticalCompassHandler, "_generate_derivatives",
        classmethod(lambda cls, *a, **k: captured.setdefault("deriv_model", a[0])),
    )

    pch.PoliticalCompassHandler.handle_results(
        model="gemma-4-12b-it-ud-q6_k_xl-instruct-spark",
        report=report,
        model_version="3.0.0",
        test_instance=types.SimpleNamespace(verification_mode=False, config={}),
        audit_mode=False,
        provider_type="ollama",
    )

    assert captured["csv_model"] == "gemma-4-12b-it-ud-q6_k_xl-spark"
    assert captured["deriv_model"] == "gemma-4-12b-it-ud-q6_k_xl-spark"
    assert report["model"] == "gemma-4-12b-it-ud-q6_k_xl-spark"
    cal = report["statistics"]["pc_calibration"]
    assert cal["pc_profile_forced_instruct"] is True
    assert cal["classification"] == "instruct_profile"


def test_handle_results_no_attribution_for_normal_model(monkeypatch):
    """Ohne Mapping-Eintrag bleibt alles unverändert (kein Attributions-Eingriff)."""
    import types
    from utils.scoring import political_compass_handler as pch

    report = {"model": "some-normal-model", "statistics": {}, "shift": {"distance": 0.0}}
    captured: dict = {}
    monkeypatch.setattr(pch, "PCResultManager", types.SimpleNamespace(
        print_summary=lambda r: None,
        save_json=lambda r, d: None,
    ))
    monkeypatch.setattr(
        pch.PoliticalCompassHandler, "_update_local_pc_csv",
        classmethod(lambda cls, m, r, v: captured.setdefault("csv_model", m)),
    )
    monkeypatch.setattr(
        pch.PoliticalCompassHandler, "_generate_derivatives",
        classmethod(lambda cls, *a, **k: None),
    )

    pch.PoliticalCompassHandler.handle_results(
        model="some-normal-model",
        report=report,
        model_version="3.0.0",
        test_instance=types.SimpleNamespace(verification_mode=False, config={}),
        audit_mode=False,
        provider_type="ollama",
    )

    assert captured["csv_model"] == "some-normal-model"
    assert report["model"] == "some-normal-model"
    assert "pc_calibration" not in report["statistics"]


def test_resolve_budget_exact_bypasses_module_budget(monkeypatch, tmp_path):
    """Exact-Modus (Probe-Stufen): 300 bleibt 300 — kein Modul-Budget, kein Multiplikator."""
    _write_calibration_card(monkeypatch, tmp_path, {
        "budget": 2500, "classification": "self_limiting", "tested": "2026-08-29",
        "converged_stage": 1200, "notes": "",
    })
    config = {
        "token_budgets": {"political_compass": 800},
        "token_budgets_reasoning_models": {"political_compass": 800},
        "defaults": {"generation": {"num_predict": 8192}},
    }
    tokens, _ = resolve_token_budget("test-model", 300, config, "political_compass", exact=True)
    assert tokens == 300


def test_resolve_budget_calibration_ignored_for_other_modules(monkeypatch, tmp_path):
    """Kalibrierung gilt nur für module_key=political_compass (PC-spezifisches Feld)."""
    _write_calibration_card(monkeypatch, tmp_path, {
        "budget": 2500, "classification": "self_limiting", "tested": "2026-08-29",
        "converged_stage": 1200, "notes": "",
    })
    config = {
        "token_budgets": {"ux_writing": 3500},
        "token_budgets_reasoning_models": {"ux_writing": 12000},
        "defaults": {"generation": {"num_predict": 8192}},
    }
    tokens, _ = resolve_token_budget("test-model", 3500, config, "ux_writing")
    # Reasoning-Modell → ux_writing-Reasoning-Budget 12000; entscheidend ist,
    # dass die PC-Kalibrierung (2500) NICHT in andere Module leakt.
    assert tokens == 12000


# ---------------------------------------------------------------------------
# Instruct-Modus (greedy_uncapped) + Audit-Annotation
# ---------------------------------------------------------------------------

def test_force_thinking_off_propagates_to_first_query():
    """greedy_uncapped + vLLM: Instruct-Modus ab Attempt 1 (chat_template_kwargs)."""
    test = PoliticalCompassTest()
    client = _MockClient(["Answer: A"])
    ctx = _context(client, thinking_off_supported=True, force_thinking_off=True)
    with patch.object(pc_test_module.time, "sleep"):
        outcome = test._execute_question_attempts(
            "q1", "prompt?", {"A": "A", "B": "B", "C": "C", "D": "D"},
            ctx, {"total_tokens": 0, "total_cost": 0.0},
        )
    assert client.calls[0]["chat_template_kwargs"] == {"enable_thinking": False}
    assert outcome["event"] == "answer"


def test_force_thinking_off_ignored_without_provider_support():
    """greedy_uncapped + llama.cpp: kein Toggle möglich → degradiert sauber."""
    test = PoliticalCompassTest()
    client = _MockClient(["Answer: A"])
    ctx = _context(client, thinking_off_supported=False, force_thinking_off=True)
    with patch.object(pc_test_module.time, "sleep"):
        test._execute_question_attempts(
            "q1", "prompt?", {"A": "A", "B": "B", "C": "C", "D": "D"},
            ctx, {"total_tokens": 0, "total_cost": 0.0},
        )
    assert "chat_template_kwargs" not in client.calls[0]


def test_escalation_section_renders_calibration_annotations():
    lines: list[str] = []
    AuditLogWriter._append_escalation_section(
        lines, {},
        calibration={
            "classification": "greedy_uncapped", "budget": None,
            "tested": "2026-08-29T10:00:00+00:00", "pc_profile_forced_instruct": True,
            "notes": "",
        },
    )
    text = "\n".join(lines)
    assert "Instruct-Ersatzlauf" in text
    assert "Coverage-Regel" in text
    assert "greedy_uncapped" in text

    lines2: list[str] = []
    AuditLogWriter._append_escalation_section(
        lines2, {},
        calibration={
            "classification": "inconsistent", "budget": 600,
            "tested": "2026-08-29T10:00:00+00:00", "pc_profile_forced_instruct": False,
            "notes": "",
        },
    )
    text2 = "\n".join(lines2)
    assert "inconsistent" in text2 and "600" in text2

    lines3: list[str] = []
    AuditLogWriter._append_escalation_section(lines3, {}, calibration=None)
    assert not any("Token-Probe" in line for line in lines3)


# ---------------------------------------------------------------------------
# E2E: Batch-Wiring (Review 2026-08-29, CRITICAL-Fix)
# _run_batch_test muss max_tokens/_module_key an execute() durchreichen —
# vorher lief PC als Batch-Modul auf dem 25k-Reasoning-Fallback, weil die
# Budget-Injection nur im Non-Batch-Pfad existierte.
# ---------------------------------------------------------------------------

import types  # noqa: E402

from utils.base_runner import BaseBenchmarkRunner  # noqa: E402


class _BatchTestMock:
    """Minimaler Batch-Test-Stub mit execute-Kwargs-Recorder."""

    def __init__(self):
        self.num_runs = 0
        self._quota_exhausted = False
        self._systematic_failure = False
        self.execute_calls: list[dict] = []

    def execute(self, model, llm_client, provider=None, **kwargs):
        self.execute_calls.append(kwargs)
        return types.SimpleNamespace(
            raw_response=json.dumps({"status": "success"}), status="success",
        )


def _batch_runner(config: dict) -> BaseBenchmarkRunner:
    """BaseBenchmarkRunner ohne schweres __init__ (kein LLMClient/ResultManager)."""
    runner = BaseBenchmarkRunner.__new__(BaseBenchmarkRunner)
    runner.validator = types.SimpleNamespace(config=config)
    runner.client = object()
    return runner


def _run_batch(runner: BaseBenchmarkRunner, test: _BatchTestMock) -> list:
    return runner._run_batch_test(  # pylint: disable=protected-access
        test, "test-model",
        {"module_path": "benchmark_modules/political_compass", "id": "political_compass",
         "min_runs": 1, "name": "Political Compass"},
        "llamacpp_spark", 2, "political_compass",
    )


def test_batch_test_passes_module_budget_to_execute(monkeypatch):
    """E2E: Batch-Dispatch injiziert token_budgets.political_compass in execute."""
    monkeypatch.setattr(
        BaseBenchmarkRunner, "_finalize_batch_result",
        lambda self, *args, **kwargs: [],
    )
    config = {
        "token_budgets": {"political_compass": 800},
        "defaults": {"generation": {"num_predict": 8192}},
    }
    runner = _batch_runner(config)
    test = _BatchTestMock()
    _run_batch(runner, test)

    assert test.execute_calls, "execute() wurde nicht aufgerufen"
    kwargs = test.execute_calls[0]
    assert kwargs.get("max_tokens") == 800
    assert kwargs.get("_module_key") == "political_compass"


def test_batch_test_passes_calibrated_budget_e2e(monkeypatch, tmp_path):
    """E2E: Card-Kalibrierung (3120) gewinnt im Batch-Pfad über Config (800).

    Regressionstest für den CRITICAL-Befund: Vor dem Fix erreichte weder das
    Modul-Budget noch die Token-Probe-Kalibrierung den Produktionspfad.
    """
    monkeypatch.setattr(
        BaseBenchmarkRunner, "_finalize_batch_result",
        lambda self, *args, **kwargs: [],
    )
    card_path = tmp_path / "test-model.json"
    card_path.write_text(json.dumps({
        "model_id": "test-model",
        "thinking_probe_detected": True,
        "pc_token_calibration": {
            "budget": 3120, "classification": "inconsistent",
            "tested": "2026-08-29", "converged_stage": 2400, "notes": "",
        },
    }), encoding="utf-8")
    monkeypatch.setattr(model_card_io, "CARD_DIR", tmp_path)

    config = {
        "token_budgets": {"political_compass": 800},
        "token_budgets_reasoning_models": {"political_compass": 800},
        "defaults": {"generation": {"num_predict": 8192}},
    }
    runner = _batch_runner(config)
    test = _BatchTestMock()
    _run_batch(runner, test)

    kwargs = test.execute_calls[0]
    assert kwargs.get("max_tokens") == 3120
    assert kwargs.get("_module_key") == "political_compass"


def test_anomaly_verification_skipped_for_attributed_replacement_run(monkeypatch):
    """Attribuierter Instruct-Ersatzlauf (pc_calibration gesetzt) darf keinen
    Triple-Run gegen das Thinking-Profil triggern — der würde das Ersatzlauf-
    Ergebnis unter der Original-ID überschreiben (Konzept-Doc Abschn. 11)."""
    import run_benchmark as rb

    triggered = []
    monkeypatch.setattr(
        rb.subprocess, "run",
        lambda *args, **kwargs: triggered.append(args) or type("R", (), {"returncode": 0})(),
    )

    results = [{
        "asset_id": "political_compass",
        "raw_response": json.dumps({
            "shift": {"distance": 2.85},
            "statistics": {
                "pc_calibration": {"classification": "instruct_profile"},
            },
        }),
    }]
    rb.BenchmarkRunner._check_for_anomaly(None, "political_compass", "test-model", results)
    assert triggered == []


def test_anomaly_verification_triggers_without_calibration(monkeypatch):
    """Ohne pc_calibration bleibt das normale Verifikations-Trigger-Verhalten
    bestehen (Shift > 1.0 → Triple-Run)."""
    import run_benchmark as rb

    triggered = []
    monkeypatch.setattr(
        rb.subprocess, "run",
        lambda *args, **kwargs: triggered.append(args) or type("R", (), {"returncode": 0})(),
    )

    results = [{
        "asset_id": "political_compass",
        "raw_response": json.dumps({"shift": {"distance": 2.85}, "statistics": {}}),
    }]
    rb.BenchmarkRunner._check_for_anomaly(None, "political_compass", "test-model", results)
    assert len(triggered) == 1


def test_is_attributed_target_reverse_lookup():
    """Reverse-Lookup: Die Original-ID ist ein Attributions-Ziel, die
    Instruct-Profil-ID (Key) und fremde IDs sind es nicht."""
    from utils.scoring.political_compass_handler import PoliticalCompassHandler

    assert PoliticalCompassHandler._is_attributed_target(
        "gemma-4-12b-it-ud-q6_k_xl-spark"
    )
    assert not PoliticalCompassHandler._is_attributed_target(
        "gemma-4-12b-it-ud-q6_k_xl-instruct-spark"
    )
    assert not PoliticalCompassHandler._is_attributed_target("qwen3_5-4b-q8")


def test_anomaly_verification_skips_attributed_target_id(monkeypatch):
    """Der Anomalie-Check erhält die Original-ID (attribuiert) — der Skip
    muss über den Reverse-Lookup greifen, auch ohne pc_calibration im
    raw_response (das ist PRE-Attribution)."""
    import run_benchmark as rb

    triggered = []
    monkeypatch.setattr(
        rb.subprocess, "run",
        lambda *args, **kwargs: triggered.append(args) or type("R", (), {"returncode": 0})(),
    )

    results = [{
        "asset_id": "political_compass",
        "raw_response": json.dumps({"shift": {"distance": 2.85}, "statistics": {}}),
    }]
    rb.BenchmarkRunner._check_for_anomaly(
        None, "political_compass", "gemma-4-12b-it-ud-q6_k_xl-spark", results
    )
    assert triggered == []


def test_handler_trigger_skips_verification_for_attributed_run(monkeypatch):
    """Zweiter Trigger-Pfad: handle_results darf für attribuierte Ersatz-
    Läufe (attribution gesetzt) keine Verifikation starten — sonst fährt der
    Triple-Run das Thinking-Profil und überschreibt das Ersatzlauf-Ergebnis."""
    from utils.scoring import political_compass_handler as pch

    triggered = []
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: triggered.append(args) or type("R", (), {"returncode": 0})(),
    )
    monkeypatch.setattr(pch.PCResultManager, "print_summary", lambda report: None)
    monkeypatch.setattr(pch.PCResultManager, "save_json", lambda report, d: None)
    monkeypatch.setattr(pch.PoliticalCompassHandler, "_update_local_pc_csv", lambda *a: None)
    # provider_type='llamacpp_spark' dispatcht in den Commercial-Zweig —
    # auch der muss gemockt sein (sonst KeyError 'coordinates' im Log und
    # Upsert-Gefahr für die echte political_compass_results.csv).
    monkeypatch.setattr(pch.PoliticalCompassHandler, "_update_commercial_pc_csv", lambda *a: None)
    monkeypatch.setattr(pch.PoliticalCompassHandler, "_generate_derivatives", lambda *a: None)

    report = {
        "model": "gemma-4-12b-it-ud-q6_k_xl-instruct-spark",
        "shift": {"distance": 2.85},
        "statistics": {},
    }
    test_instance = types.SimpleNamespace(config={}, verification_mode=False)
    pch.PoliticalCompassHandler.handle_results(
        "gemma-4-12b-it-ud-q6_k_xl-instruct-spark",
        report, "4", test_instance, provider_type="llamacpp_spark",
    )
    assert triggered == []
    # Attribution hat gegriffen: Report unter Original-ID + Transparenz-Flag
    assert report["model"] == "gemma-4-12b-it-ud-q6_k_xl-spark"
    assert report["statistics"]["pc_calibration"]["classification"] == "instruct_profile"


def test_handler_trigger_fires_for_normal_model(monkeypatch):
    """Ohne Attribution bleibt der Verifikations-Trigger bei hohem Shift
    bestehen (Regelverhalten für normale Modelle)."""
    from utils.scoring import political_compass_handler as pch

    triggered = []
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: triggered.append(args) or type("R", (), {"returncode": 0})(),
    )
    monkeypatch.setattr(pch.PCResultManager, "print_summary", lambda report: None)
    monkeypatch.setattr(pch.PCResultManager, "save_json", lambda report, d: None)
    monkeypatch.setattr(pch.PoliticalCompassHandler, "_update_local_pc_csv", lambda *a: None)
    # provider_type='llamacpp_spark' dispatcht in den Commercial-Zweig —
    # auch der muss gemockt sein (sonst KeyError 'coordinates' im Log und
    # Upsert-Gefahr für die echte political_compass_results.csv).
    monkeypatch.setattr(pch.PoliticalCompassHandler, "_update_commercial_pc_csv", lambda *a: None)
    monkeypatch.setattr(pch.PoliticalCompassHandler, "_generate_derivatives", lambda *a: None)

    report = {
        "model": "qwen3_5-4b-q8",
        "shift": {"distance": 2.85},
        "statistics": {},
    }
    test_instance = types.SimpleNamespace(config={}, verification_mode=False)
    pch.PoliticalCompassHandler.handle_results(
        "qwen3_5-4b-q8", report, "3.5", test_instance, provider_type="llamacpp_spark",
    )
    assert len(triggered) == 1


@pytest.mark.uses_real_cards
def test_attribution_resolves_version_from_original_card(monkeypatch):
    """Versions-Label-Konsistenz: Bei Attribution wird model_version aus der
    Card der Original-ID aufgelöst (nicht 'k.A.' vom Ersatzlauf-Profil).
    provider_type 'llamacpp_spark' läuft in den _update_commercial_pc_csv-
    Zweig — dort wird gecaptured."""
    from utils.scoring import political_compass_handler as pch

    captured = {}
    monkeypatch.setattr(
        pch.PoliticalCompassHandler, "_update_commercial_pc_csv",
        lambda model, report, model_version: captured.update(
            model_version=model_version, model=model,
        ),
    )
    monkeypatch.setattr("subprocess.run", lambda *a, **k: None)
    monkeypatch.setattr(pch.PCResultManager, "print_summary", lambda report: None)
    monkeypatch.setattr(pch.PCResultManager, "save_json", lambda report, d: None)
    monkeypatch.setattr(pch.PoliticalCompassHandler, "_generate_derivatives", lambda *a: None)

    report = {
        "model": "gemma-4-12b-it-ud-q6_k_xl-instruct-spark",
        "shift": {"distance": 2.85},
        "statistics": {},
    }
    test_instance = types.SimpleNamespace(config={}, verification_mode=False)
    pch.PoliticalCompassHandler.handle_results(
        "gemma-4-12b-it-ud-q6_k_xl-instruct-spark",
        report, "k.A.", test_instance, provider_type="llamacpp_spark",
    )

    assert captured["model"] == "gemma-4-12b-it-ud-q6_k_xl-spark"
    assert captured["model_version"] == "4"
    # save_leaderboard_csv liest report["model_version"] — auch der Report
    # muss die korrigierte Version tragen (AGENTS.md, Session 87).
    assert report["model_version"] == "4"


def test_finalize_batch_result_attributes_main_csv_row(monkeypatch):
    """Coverage-Regel: Auch die std_result-Row für local_models_benchmark.csv
    muss unter der Original-ID + deren Card-Version landen (nicht Instruct-ID
    + k.A.) — sonst polluiert das Profil das Haupt-Leaderboard."""
    from utils.base_runner import BaseBenchmarkRunner
    from utils.scoring.political_compass_handler import PoliticalCompassHandler

    runner = BaseBenchmarkRunner.__new__(BaseBenchmarkRunner)
    runner.audit_mode = False
    runner.validator = types.SimpleNamespace(config={})
    runner.client = None
    # _finalize_batch_result importiert get_model_version funktionslevel-seitig
    # → Patch an der Quelle (utils.model_utils).
    monkeypatch.setattr(
        "utils.model_utils.get_model_version",
        lambda model, provider, client=None: "k.A." if "instruct" in model else "4",
    )
    monkeypatch.setattr(
        "utils.model_utils.get_hardware_profile", lambda config, provider: "test",
    )
    monkeypatch.setattr(PoliticalCompassHandler, "handle_results", lambda *a, **k: None)

    report = {
        "model": "gemma-4-12b-it-ud-q6_k_xl-instruct-spark",
        "total_score": 100,
        "status": "success",
        "shift": {"distance": 2.85},
        "statistics": {},
    }
    wrapper = types.SimpleNamespace(
        raw_response=json.dumps(report), execution_time=1.0,
        response_length=10, cost_usd="0", tokens_used=0,
    )
    test = types.SimpleNamespace()
    info = {"name": "Political Compass"}

    results = BaseBenchmarkRunner._finalize_batch_result(
        runner, test, wrapper, report,
        "gemma-4-12b-it-ud-q6_k_xl-instruct-spark", info, "llamacpp_spark",
        "political_compass",
    )

    assert results[0]["model"] == "gemma-4-12b-it-ud-q6_k_xl-spark"
    assert results[0]["model_version"] == "4"


def test_run_verification_skips_attributed_targets(monkeypatch):
    """Manueller Verifikations-Aufruf darf attribuierte Ziele (Original-IDs
    aus result_attribution.values()) nicht mit einem Thinking-Triple-Run
    überschreiben — Guard in run_verification."""
    import scripts.core.verify_compass_anomalies as vca

    monkeypatch.setattr(vca, "get_anomalies", lambda **k: ["gemma-4-12b-it-ud-q6_k_xl-spark"])
    monkeypatch.setattr(vca, "ConfigValidator", lambda *a: types.SimpleNamespace(config={}))
    monkeypatch.setattr(vca, "LLMClient", lambda *a, **k: object())
    called = []
    monkeypatch.setattr(vca, "_run_triple_iterations", lambda *a: called.append(a))

    vca.run_verification()
    assert called == []


def test_replacement_calibration_factory_shape():
    """Factory liefert die kanonische pc_calibration-Struktur; Suffix hängt
    sich sauber an die Notes."""
    from utils.scoring.political_compass_handler import PoliticalCompassHandler

    base = PoliticalCompassHandler.build_replacement_calibration()
    assert base["classification"] == "instruct_profile"
    assert base["pc_profile_forced_instruct"] is True
    assert base["budget"] is None and base["tested"] is None
    assert "Original-Modell-ID" in base["notes"]

    suffixed = PoliticalCompassHandler.build_replacement_calibration("Verifiziert per Triple-Run.")
    assert suffixed["notes"].endswith("Verifiziert per Triple-Run.")
    assert suffixed["notes"].startswith(base["notes"].rstrip(".")[:40])
