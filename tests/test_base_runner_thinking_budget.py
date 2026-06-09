"""
Tests for Option B: provider parameter in resolve_token_budget().

Option B verbindet die Thinking-Probe-SSoT (Model Card) mit dem optionalen
Provider-Card-Override (``thinking_override``) an die Token-Budget-Berechnung
in ``utils/model_utils.resolve_token_budget``. Die Aufrufer-Stelle ist
``utils.base_runner.BaseBenchmarkRunner.execute_test_module``.

Coverage:
  1. Backward-compat: provider=None → alter Pfad (Card-Probe + Trigger)
  2. Trigger-Fallback ohne Card: magistral/o1 etc. → 5x
  3. Provider-Override value=false aktiv → KEIN 5x (Cost-Benchmark-Szenario)
  4. Provider-Override value=true aktiv → 5x
  5. Override active_until in Vergangenheit → inaktiv, Trigger/Probe gewinnt
  6. Probe-Resultat true in Model-Card → 5x (SSoT)
  7. Probe-Resultat false in Model-Card → KEIN 5x (SSoT)
  8. effective is None → Trigger-Liste bleibt erhalten
  9. max_output_tokens-Cap aus Model Card bleibt erhalten
 10. Explicit-Budget + reasoning → 5x
 11. Kein Explicit-Budget + reasoning < 10000 → floor 25000
 12. Audit-Log bei Override-Anwendung

Disk-IO wird über ``monkeypatch`` vermieden, indem ``_find_card`` und
``load_provider_card`` mit In-Memory-Stubs ersetzt werden.
"""

import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils import model_utils  # noqa: E402
from utils.model_utils import resolve_token_budget  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


# Models mit Reasoning-Triggern in is_reasoning_model()
REASONING_TRIGGERS_MODEL = "magistral-medium-latest"   # löst Trigger aus
NON_REASONING_MODEL = "llama-3.3-70b-instruct"         # kein Trigger, keine Card


def _card_dict(detected=None) -> dict:
    """Baut eine minimal-Model-Card für Tests."""
    return {
        "model_id": "test-model",
        "thinking_probe_detected": detected,
    }


def _provider_card_dict(thinking_override: dict | None) -> dict:
    """Baut eine minimal-Provider-Card für Tests."""
    card: dict = {
        "provider_id": "test-provider",
        "display_name": "Test Provider",
    }
    if thinking_override is not None:
        card["thinking_override"] = thinking_override
    return card


def _config() -> dict:
    """Minimale benchmark_config für Token-Budget-Tests."""
    return {
        "token_budgets": {
            "code_quality": 2000,
            "reasoning_logic": 4000,
        },
        "token_budgets_reasoning_models": {
            "code_quality": 8000,
            "reasoning_logic": 16000,
        },
        "defaults": {"generation": {"num_predict": 8192}},
    }


@pytest.fixture
def stub_card_loader(monkeypatch, tmp_path):
    """Patcht _find_card und load_provider_card, sodass Tests keine Disk-IO
    auslösen.

    Implementierung: Echte JSON-Dateien in ``tmp_path`` schreiben, die
    Stubs geben die entsprechenden Pfade zurück. So funktioniert
    ``card_path.exists()`` korrekt und ``json.loads`` kann lesen.
    """
    state = {
        "model_card": None,         # dict | None  (None = nicht gefunden)
        "provider_card": None,      # dict | None  (None = nicht gefunden)
        "find_card_calls": 0,
        "tmp_path": tmp_path,
    }

    def fake_find_card(model_id, card_dir=None):
        state["find_card_calls"] += 1
        if state["model_card"] is not None:
            # Echte Datei in tmp_path, damit .exists() True ist und
            # json.loads(path.read_text()) funktioniert.
            path = tmp_path / f"{model_id}.json"
            path.write_text(json.dumps(state["model_card"]), encoding="utf-8")
            return path
        return tmp_path / f"nonexistent-{model_id}.json"  # .exists() == False

    def fake_load_provider_card(provider_id):
        if state["provider_card"] is None:
            return None
        # Echte Datei in tmp_path, damit load_provider_card (intern json.loads +
        # path.read_text) konsistent funktioniert.
        path = tmp_path / f"provider-{provider_id}.json"
        path.write_text(json.dumps(state["provider_card"]), encoding="utf-8")
        return json.loads(path.read_text(encoding="utf-8"))

    # _find_card ist im resolve_token_budget()-Scope per Modul-Name auflösbar.
    monkeypatch.setattr(model_utils, "_find_card", fake_find_card)

    # load_provider_card wird IN resolve_token_budget importiert, daher müssen
    # wir den Import-Pfad in utils.provider_card_template patchen, das ist
    # die Quelle, aus der der lokale Import schöpft.
    from utils import provider_card_template
    monkeypatch.setattr(provider_card_template, "load_provider_card", fake_load_provider_card)

    return state


# ---------------------------------------------------------------------------
# Backward-Compat (provider=None)
# ---------------------------------------------------------------------------


def test_provider_none_no_5x_for_normal_model(stub_card_loader):
    """Backward-compat: provider=None, normales Model ohne Trigger, ohne Card
    → kein 5x, bleibt beim expliziten Modul-Budget (2000)."""
    tokens, reasoning = resolve_token_budget(
        NON_REASONING_MODEL, 2000, _config(), "code_quality", provider=None,
    )
    assert reasoning is False
    assert tokens == 2000


def test_provider_none_trigger_fallback_5x(stub_card_loader):
    """Backward-compat: provider=None, Model mit "magistral"-Trigger → 5x
    via token_budgets_reasoning_models (8000)."""
    tokens, reasoning = resolve_token_budget(
        REASONING_TRIGGERS_MODEL, 2000, _config(), "code_quality", provider=None,
    )
    assert reasoning is True
    assert tokens == 8000  # aus token_budgets_reasoning_models.code_quality


def test_provider_kwarg_missing_is_backward_compat(stub_card_loader):
    """Wenn provider-Kwarg komplett fehlt (alter Call-Site in mistral.py
    etc.), bleibt das Verhalten identisch: Trigger-Fallback."""
    tokens, reasoning = resolve_token_budget(
        REASONING_TRIGGERS_MODEL, 2000, _config(), "code_quality",
    )
    assert reasoning is True
    assert tokens == 8000


# ---------------------------------------------------------------------------
# Provider-Override aktiv
# ---------------------------------------------------------------------------


def test_override_value_false_no_5x(stub_card_loader):
    """Provider-Override value=false aktiv → KEIN 5x trotz Reasoning-Trigger.

    Use-Case: Cost-Benchmark soll CoT-Suppression für faire Speed-Vergleiche
    erzwingen. Das Modell hat 'magistral' im Namen (Trigger), aber der Override
    sagt explizit 'kein Reasoning'.
    """
    stub_card_loader["provider_card"] = _provider_card_dict({
        "value": False,
        "reason": "Cost-Benchmark: CoT-Suppression für Speed-Vergleich",
    })
    tokens, reasoning = resolve_token_budget(
        REASONING_TRIGGERS_MODEL, 2000, _config(), "code_quality", provider="test-provider",
    )
    assert reasoning is False
    assert tokens == 2000  # kein 5x


def test_override_value_true_5x(stub_card_loader):
    """Provider-Override value=true aktiv auf einem NON-Reasoning-Modell →
    5x wird angewendet."""
    stub_card_loader["provider_card"] = _provider_card_dict({
        "value": True,
        "reason": "A/B-Test: explizit Reasoning erzwingen",
    })
    tokens, reasoning = resolve_token_budget(
        NON_REASONING_MODEL, 2000, _config(), "code_quality", provider="test-provider",
    )
    assert reasoning is True
    assert tokens == 8000  # 5x via token_budgets_reasoning_models


def test_override_expired_falls_back_to_trigger(stub_card_loader):
    """Override active_until in der Vergangenheit → inaktiv, Trigger-Liste greift."""
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    stub_card_loader["provider_card"] = _provider_card_dict({
        "value": False,
        "reason": "Saisonale CoT-Suppression",
        "active_until": past,
    })
    tokens, reasoning = resolve_token_budget(
        REASONING_TRIGGERS_MODEL, 2000, _config(), "code_quality", provider="test-provider",
    )
    assert reasoning is True  # Trigger-Liste gewinnt
    assert tokens == 8000


def test_override_no_reason_is_inactive(stub_card_loader):
    """Override ohne reason → inaktiv (Pflichtfeld), Trigger gewinnt."""
    stub_card_loader["provider_card"] = _provider_card_dict({
        "value": False,
        # reason fehlt → Pflichtfeld nicht erfüllt
    })
    tokens, reasoning = resolve_token_budget(
        REASONING_TRIGGERS_MODEL, 2000, _config(), "code_quality", provider="test-provider",
    )
    assert reasoning is True  # Trigger gewinnt


def test_override_logs_audit_trail(stub_card_loader, caplog):
    """Override-Anwendung erzeugt einen [ThinkingOverride] Audit-Log-Eintrag."""
    stub_card_loader["provider_card"] = _provider_card_dict({
        "value": False,
        "reason": "Cost-Benchmark Q3 2026",
    })
    with caplog.at_level(logging.INFO, logger="utils.model_utils"):
        resolve_token_budget(
            NON_REASONING_MODEL, 2000, _config(), "code_quality",
            provider="test-provider",
        )
    assert any("[ThinkingOverride]" in rec.message for rec in caplog.records), (
        f"Expected [ThinkingOverride] audit log, got: {[r.message for r in caplog.records]}"
    )


# ---------------------------------------------------------------------------
# Card-Probe SSoT
# ---------------------------------------------------------------------------


def test_probe_true_in_card_5x(stub_card_loader):
    """Model-Card hat thinking_probe_detected=true, kein Provider-Override →
    5x via Probe-SSoT (gewinnt über Trigger-Liste)."""
    stub_card_loader["model_card"] = _card_dict(detected=True)
    stub_card_loader["provider_card"] = None  # kein Override
    tokens, reasoning = resolve_token_budget(
        NON_REASONING_MODEL, 2000, _config(), "code_quality", provider="test-provider",
    )
    assert reasoning is True
    assert tokens == 8000


def test_probe_false_in_card_no_5x(stub_card_loader):
    """Model-Card hat thinking_probe_detected=false, kein Provider-Override →
    KEIN 5x (Card-Probe SSoT gewinnt über Trigger-Liste)."""
    stub_card_loader["model_card"] = _card_dict(detected=False)
    stub_card_loader["provider_card"] = None
    tokens, reasoning = resolve_token_budget(
        REASONING_TRIGGERS_MODEL, 2000, _config(), "code_quality", provider="test-provider",
    )
    assert reasoning is False  # Probe SSoT gewinnt über 'magistral'-Trigger
    assert tokens == 2000


def test_no_card_no_override_keeps_trigger_fallback(stub_card_loader):
    """Provider gesetzt, aber weder Model-Card noch Provider-Card-Override →
    effective_thinking = None → Trigger-Liste bleibt erhalten."""
    stub_card_loader["model_card"] = None
    stub_card_loader["provider_card"] = _provider_card_dict(None)  # kein Override-Key
    tokens, reasoning = resolve_token_budget(
        REASONING_TRIGGERS_MODEL, 2000, _config(), "code_quality", provider="test-provider",
    )
    assert reasoning is True  # Trigger greift
    assert tokens == 8000


def test_provider_none_no_card_uses_trigger(stub_card_loader):
    """provider=None (legacy), keine Model-Card, magistr-Trigger → 5x."""
    stub_card_loader["model_card"] = None
    stub_card_loader["provider_card"] = None
    tokens, reasoning = resolve_token_budget(
        REASONING_TRIGGERS_MODEL, 2000, _config(), "code_quality", provider=None,
    )
    assert reasoning is True
    assert tokens == 8000


# ---------------------------------------------------------------------------
# Edge-Cases
# ---------------------------------------------------------------------------


def test_max_output_tokens_card_cap_still_applies(stub_card_loader):
    """Model-Card-Cap (max_output_tokens) wird auch mit Override angewendet."""
    stub_card_loader["model_card"] = {
        "model_id": "test-model",
        "thinking_probe_detected": True,
        "max_output_tokens": 4096,
    }
    stub_card_loader["provider_card"] = None
    tokens, reasoning = resolve_token_budget(
        NON_REASONING_MODEL, 2000, _config(), "code_quality", provider="test-provider",
    )
    # 5x-Budget wäre 8000, aber Card-Cap 4096 begrenzt.
    assert reasoning is True
    assert tokens == 4096


def test_explicit_budget_with_reasoning_uses_5x_module_budget(stub_card_loader):
    """Explizites Modul-Budget + reasoning + module_key NICHT in
    token_budgets_reasoning_models → Multiplikator auf das explizite
    Budget (3000 * 5 = 15000)."""
    stub_card_loader["model_card"] = _card_dict(detected=True)
    stub_card_loader["provider_card"] = None
    # "code_quality" ist in token_budgets_reasoning_models (8000). Wir nutzen
    # einen Modul-Key, der NICHT dort steht, um den 5x-Fallback zu erzwingen.
    tokens, reasoning = resolve_token_budget(
        NON_REASONING_MODEL, 3000, _config(), "ux_writing", provider="test-provider",
    )
    # 3000 * 5 = 15000 (kein token_budgets_reasoning_models["ux_writing"])
    assert reasoning is True
    assert tokens == 15000


def test_no_explicit_budget_with_reasoning_floor_25000(stub_card_loader):
    """Kein explizites Modul-Budget + reasoning → tokens < 10000 → floor 25000."""
    stub_card_loader["model_card"] = _card_dict(detected=True)
    stub_card_loader["provider_card"] = None
    tokens, reasoning = resolve_token_budget(
        NON_REASONING_MODEL, None, _config(), "code_quality", provider="test-provider",
    )
    assert reasoning is True
    # Default 8192 < 10000 → floor 25000
    assert tokens == 25000


def test_provider_none_unchanged_when_no_module_key(stub_card_loader):
    """module_key=None + reasoning-Trigger + kein Override → 5x auf Default."""
    stub_card_loader["model_card"] = None
    stub_card_loader["provider_card"] = None
    tokens, reasoning = resolve_token_budget(
        REASONING_TRIGGERS_MODEL, 5000, _config(), None, provider=None,
    )
    assert reasoning is True
    # 5000 * 5 = 25000 (kein module_key in token_budgets_reasoning_models)
    assert tokens == 25000


def test_malformed_model_card_json_falls_through_to_trigger(stub_card_loader):
    """Model-Card mit ungültigem JSON → wird ignoriert, Trigger greift.

    Simuliert eine korrupte Card-Datei, indem tmp_path eine
    nicht-JSON-Datei enthält. is_reasoning_model_from_card()
    fängt JSONDecodeError und returnt None → Trigger-Liste gewinnt.
    """
    # Echte Datei mit kaputtem JSON in tmp_path schreiben
    tmp = stub_card_loader["tmp_path"]
    broken_path = tmp / f"{REASONING_TRIGGERS_MODEL}.json"
    broken_path.write_text("{ this is : not, valid JSON ", encoding="utf-8")

    # _find_card so anpassen, dass es die kaputte Datei zurückgibt
    from utils import model_utils as _mu
    original_find = _mu._find_card
    def broken_find(model_id, card_dir=None):
        if model_id == REASONING_TRIGGERS_MODEL:
            return broken_path
        return tmp / f"nonexistent-{model_id}.json"

    _mu._find_card = broken_find
    try:
        tokens, reasoning = resolve_token_budget(
            REASONING_TRIGGERS_MODEL, 2000, _config(), "code_quality",
            provider="test-provider",
        )
        # is_reasoning_model_from_card() returns None (JSONDecodeError gefangen)
        # → effective_thinking = None → Trigger "magistral" greift
        assert reasoning is True
        assert tokens == 8000
    finally:
        _mu._find_card = original_find
