"""Tests fuer den vollstaendigen SSoT-Audit (scripts/dev/audit_model_cards_full.py)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Importiere das Audit-Script als Modul
import importlib.util

_AUDIT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "dev" / "audit_model_cards_full.py"
_spec = importlib.util.spec_from_file_location("audit_model_cards_full", _AUDIT_PATH)
audit_mod = importlib.util.module_from_spec(_spec)
sys.modules["audit_model_cards_full"] = audit_mod
_spec.loader.exec_module(audit_mod)


# ---------------------------------------------------------------------------
# Reines In-Memory-Test-Setup: ruft check_card() direkt auf Mini-Karten
# ---------------------------------------------------------------------------

def _make_card(**overrides) -> dict:
    """Baut eine minimale gueltige Karte (status=complete, alle Pflichtfelder)."""
    base = {
        "model_id": "test-model",
        "display_name": "Test Model",
        "developer": "Test Inc.",
        "deployment_type": "cloud-only",
        "weights_provenance_risk": "low",
        "card_status": "complete",
        "size_class": "Workstation",
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "supports_tool_use": False,
        "unknown": False,
        "architecture_tags": ["General"],
        "parameter_architecture": "dense",
    }
    base.update(overrides)
    return base


def _run(card: dict, tmp_path: Path) -> list[dict]:
    """Persistiert Karte in tmp_path und ruft check_card() darauf."""
    p = tmp_path / "test.json"
    p.write_text(json.dumps(card), encoding="utf-8")
    return audit_mod.check_card(p, card)


# ---------------------------------------------------------------------------
# Tests: TODO-Platzhalter-Schutz in draft-Karten
# ---------------------------------------------------------------------------

def test_todo_in_draft_deployment_type_is_not_critical(tmp_path):
    """In draft-Karten ist "TODO" fuer deployment_type erlaubt (Template-Default)."""
    card = _make_card(card_status="draft", deployment_type="TODO")
    findings = _run(card, tmp_path)
    criticals = [f for f in findings if f["severity"] == "CRITICAL"]
    # TODO wird vom Whitelist-Check uebersprungen, daher keine CRITICAL
    assert not any(f["code"] == "INVALID_DEPLOYMENT_TYPE" for f in criticals), (
        f"TODO in draft-Card sollte kein CRITICAL sein, bekam: {criticals}"
    )


def test_todo_in_draft_risk_level_is_not_critical(tmp_path):
    """In draft-Karten ist "TODO" fuer weights_provenance_risk erlaubt."""
    card = _make_card(card_status="draft", weights_provenance_risk="TODO")
    findings = _run(card, tmp_path)
    criticals = [f for f in findings if f["severity"] == "CRITICAL"]
    assert not any(f["code"] == "INVALID_RISK_LEVEL" for f in criticals)


def test_todo_in_draft_size_class_is_not_critical(tmp_path):
    """In draft-Karten ist "TODO" fuer size_class erlaubt."""
    card = _make_card(card_status="draft", size_class="TODO")
    findings = _run(card, tmp_path)
    criticals = [f for f in findings if f["severity"] == "CRITICAL"]
    assert not any(f["code"] == "INVALID_SIZE_CLASS" for f in criticals)


def test_invalid_value_in_complete_card_is_critical(tmp_path):
    """In complete-Karten ist jeder ungueltige Whitelist-Wert CRITICAL."""
    card = _make_card(card_status="complete", deployment_type="api-only")
    findings = _run(card, tmp_path)
    assert any(
        f["code"] == "INVALID_DEPLOYMENT_TYPE" and f["severity"] == "CRITICAL"
        for f in findings
    ), f"expected CRITICAL, got: {findings}"


# ---------------------------------------------------------------------------
# Tests: DEPRECATED_TAG-Erkennung
# ---------------------------------------------------------------------------

def test_deprecated_tag_emits_warning(tmp_path):
    """DEPRECATED-Tags aus card_vocabulary.yaml erzeugen WARNING."""
    card = _make_card(architecture_tags=["Long Context"])  # deprecated in registry
    findings = _run(card, tmp_path)
    warnings = [f for f in findings if f["code"] == "DEPRECATED_TAG"]
    assert warnings, f"expected DEPRECATED_TAG warning, got: {findings}"


def test_unknown_tag_emits_warning(tmp_path):
    """Vollkommen unbekannte Tags erzeugen UNKNOWN_TAG WARNING."""
    card = _make_card(architecture_tags=["Vollkommen-Unbekannter-Tag-12345"])
    findings = _run(card, tmp_path)
    assert any(f["code"] == "UNKNOWN_TAG" for f in findings)


def test_known_tag_emits_no_warning(tmp_path):
    """Bekannte Tags aus Reserved+Informational erzeugen keine Warnung."""
    card = _make_card(architecture_tags=["General", "Long-Context", "Coder"])
    findings = _run(card, tmp_path)
    tag_findings = [
        f for f in findings
        if f["code"] in ("DEPRECATED_TAG", "UNKNOWN_TAG")
    ]
    assert not tag_findings, f"unexpected tag findings: {tag_findings}"


# ---------------------------------------------------------------------------
# Tests: Widerspruchs-Checks
# ---------------------------------------------------------------------------

def test_unknown_complete_contradiction_is_critical(tmp_path):
    """unknown=true + card_status=complete ist ein Widerspruch (CRITICAL)."""
    card = _make_card(unknown=True, card_status="complete")
    findings = _run(card, tmp_path)
    assert any(
        f["code"] == "UNKNOWN_COMPLETE_CONTRADICTION" and f["severity"] == "CRITICAL"
        for f in findings
    )


def test_tool_use_string_is_critical(tmp_path):
    """supports_tool_use='untested' (str) ist CRITICAL, muss bool oder null sein."""
    card = _make_card(supports_tool_use="untested")
    findings = _run(card, tmp_path)
    assert any(
        f["code"] == "TOOLUSE_WRONG_TYPE" and f["severity"] == "CRITICAL"
        for f in findings
    )


def test_tool_use_null_is_ok(tmp_path):
    """supports_tool_use=null ist erlaubt (kein Finding)."""
    card = _make_card(supports_tool_use=None)
    findings = _run(card, tmp_path)
    assert not any(f["code"] == "TOOLUSE_WRONG_TYPE" for f in findings)


# ---------------------------------------------------------------------------
# Tests: Pflichtfeld- und Typpruefung
# ---------------------------------------------------------------------------

def test_missing_required_field_is_critical(tmp_path):
    """Fehlendes Pflichtfeld erzeugt MISSING_REQUIRED."""
    card = _make_card()
    del card["deployment_type"]  # Pflichtfeld entfernen
    findings = _run(card, tmp_path)
    assert any(f["code"] == "MISSING_REQUIRED" for f in findings)


def test_complete_card_missing_modalities_is_critical(tmp_path):
    """In complete-Cards fehlen input/output_modalities → CRITICAL."""
    card = _make_card(card_status="complete")
    del card["input_modalities"]
    del card["output_modalities"]
    findings = _run(card, tmp_path)
    codes = [f["code"] for f in findings]
    assert "MISSING_INPUT_MODALITIES" in codes
    assert "MISSING_OUTPUT_MODALITIES" in codes


def test_draft_card_missing_modalities_is_not_critical(tmp_path):
    """In draft-Cards ist fehlende Modalitaet nur WARNING, nicht CRITICAL."""
    card = _make_card(card_status="draft")
    del card["input_modalities"]
    del card["output_modalities"]
    findings = _run(card, tmp_path)
    criticals = [f for f in findings if f["severity"] == "CRITICAL"]
    assert not any(
        f["code"] in ("MISSING_INPUT_MODALITIES", "MISSING_OUTPUT_MODALITIES")
        for f in criticals
    )
