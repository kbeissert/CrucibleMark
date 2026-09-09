"""Tests für die size_class-Konsistenzprüfung im Card-Validator.

SSoT: config/classification_taxonomy.json#size_class.classification_rules —
params_total_b steuert die Tier-Einordnung (MoE: Gesamtgröße, da das
vollständige Modell in den RAM/VRAM geladen werden muss). Der Validator
erzwingt die Ausrichtung des Card-Prozesses auf die Config (Hard-Fail).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.dev.validate_model_cards import _check_size_class_consistency

_VOCAB = frozenset({"Nano", "Edge", "Desktop", "Workstation", "Server", "Frontier"})


def _issues(data: dict, vocab: frozenset[str] = _VOCAB) -> list[str]:
    issues: list[str] = []
    _check_size_class_consistency(data, issues, vocab)
    return issues


def test_matching_size_class_passes() -> None:
    assert _issues({"size_class": "Workstation", "params_total_b": 29.6}) == []


def test_mismatch_is_hard_error() -> None:
    issues = _issues({"size_class": "Desktop", "params_total_b": 29.6})
    assert len(issues) == 1
    assert "SIZE_CLASS MISMATCH" in issues[0]
    assert "Workstation" in issues[0]


def test_moe_uses_total_params_not_active() -> None:
    """MoE-Regel: Gesamtgröße steuert — 116.8B/5.1B aktiv ist Frontier, nicht Edge."""
    assert _issues({"size_class": "Frontier", "params_total_b": 116.8, "params_active_b": 5.1}) == []
    issues = _issues({"size_class": "Edge", "params_total_b": 116.8, "params_active_b": 5.1})
    assert any("SIZE_CLASS MISMATCH" in i for i in issues)


def test_boundary_22b_is_desktop_23b_is_workstation() -> None:
    assert _issues({"size_class": "Desktop", "params_total_b": 22.0}) == []
    issues = _issues({"size_class": "Desktop", "params_total_b": 23.0})
    assert any("SIZE_CLASS MISMATCH" in i for i in issues)


def test_unknown_params_skips_param_check() -> None:
    """params_total_b unbekannt → kein Params-Check (Kaskade entscheidet zur Laufzeit)."""
    assert _issues({"size_class": "Nano", "params_total_b": None}) == []


def test_invalid_value_flagged() -> None:
    issues = _issues({"size_class": "Ultra", "params_total_b": 7.0})
    assert any("INVALID SIZE_CLASS" in i for i in issues)


def test_non_numeric_params_is_warning_only() -> None:
    issues = _issues({"size_class": "Edge", "params_total_b": "二十八"})
    assert len(issues) == 1 and "[WARN]" in issues[0]


def test_missing_size_class_no_error() -> None:
    assert _issues({"params_total_b": 29.6}) == []
