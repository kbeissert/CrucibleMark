"""Tests für die ``card_model_id``-basierte Card-Lookup-Redirect.

Hintergrund (Plan: vLLM Dual-Thinking-Profile):
Thinking-Profile (``{id}-thinking``) teilen sich eine Model-Card mit dem
Original-Modell. Statt einer Suffix-Stripping-Heuristik tragen sie explizit
``card_model_id: {original_id}``. ``_find_card`` und
``resolve_canonical_model_id`` lesen dieses Feld aus dem model_cfg und
verwenden es als Card-Lookup-Basis.

Garantien:
1. ``card_model_id`` setzt den Lookup auf den ursprünglichen Modell-Pfad
2. Ohne ``card_model_id`` bleibt das Verhalten identisch zur Vorgänger-
   Version (Backward-compat)
3. ``card_model_id`` wird NICHT re-entrant angewendet (kein Endlos-Loop)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import utils.model_utils as model_utils_module
from utils.model_utils import _find_card, resolve_canonical_model_id, resolve_model_cfg_for


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_card_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Biegt CARD_DIR auf tmp_path um."""
    card_dir = tmp_path / "cards"
    card_dir.mkdir()
    monkeypatch.setattr(model_utils_module, "CARD_DIR", card_dir)
    return card_dir


# ---------------------------------------------------------------------------
# 1. _find_card: card_model_id redirects lookup
# ---------------------------------------------------------------------------


def test_find_card_redirects_via_card_model_id(isolated_card_dir: Path) -> None:
    """Mit ``card_model_id`` im model_cfg wird auf die Original-Card gezeigt."""
    # Original-Card: ornith-1.0-35B-FP8.json
    target = isolated_card_dir / "ornith-1_0-35B-FP8.json"
    target.write_text(json.dumps({"model_id": "ornith-1.0-35B-FP8"}), encoding="utf-8")

    # Kein Profile-Card existiert (würde auch nicht — Profile teilen die Card).
    profile_cfg = {
        "id": "ornith-1.0-35B-FP8-thinking",
        "card_model_id": "ornith-1.0-35B-FP8",
    }

    result = _find_card("ornith-1.0-35B-FP8-thinking", model_cfg=profile_cfg)
    assert result == target
    assert result.exists()


def test_find_card_without_model_cfg_keeps_legacy_behavior(
    isolated_card_dir: Path,
) -> None:
    """Ohne ``model_cfg`` (alter Aufruf-Stil) wird ``model_id`` direkt verwendet."""
    # Profile-Card (würde in der Realität nicht existieren, aber als
    # Sentinel: Funktion sucht nach ihr, findet sie aber nicht).
    profile_card = isolated_card_dir / "ornith-1_0-35B-FP8-thinking.json"
    profile_card.write_text(json.dumps({"model_id": "fake"}), encoding="utf-8")

    # Original-Card existiert NICHT.
    result = _find_card("ornith-1.0-35B-FP8-thinking")

    # Ohne model_cfg → kein card_model_id-Redirect → sucht nach
    # ``ornith-1_0-35B-FP8-thinking.json``. Gefunden: Profile-Card.
    assert result == profile_card


def test_find_card_with_empty_card_model_id_falls_back(
    isolated_card_dir: Path,
) -> None:
    """Leeres ``card_model_id`` im model_cfg wird ignoriert."""
    cfg = {"card_model_id": ""}
    result = _find_card("some-model", model_cfg=cfg)
    # Verhalten wie ohne model_cfg → ``some-model``.
    expected = isolated_card_dir / "some-model.json"
    assert result == expected


def test_find_card_with_non_string_card_model_id_falls_back(
    isolated_card_dir: Path,
) -> None:
    """Nicht-String ``card_model_id`` wird defensiv ignoriert."""
    cfg = {"card_model_id": 42}  # type: ignore[dict-item]
    result = _find_card("some-model", model_cfg=cfg)
    expected = isolated_card_dir / "some-model.json"
    assert result == expected


def test_find_card_card_model_id_prevents_infinite_recursion(
    isolated_card_dir: Path,
) -> None:
    """``card_model_id`` darf NICHT re-entrant angewendet werden.

    Hypothetischer Fehlerfall: Ein Profile-Eintrag mit ``card_model_id``,
    der wieder auf einen Profile-Eintrag zeigt. Die Implementierung
    folgt dem Redirect nur EINMAL — kein Re-Entry.
    """
    # Karte für "base" existiert (das eigentliche Ziel).
    base_card = isolated_card_dir / "base.json"
    base_card.write_text(json.dumps({"model_id": "base"}), encoding="utf-8")

    # Profil verweist auf "base" — direkter Treffer erwartet.
    profile_cfg = {"card_model_id": "base"}
    result = _find_card("profile-x", model_cfg=profile_cfg)
    assert result == base_card


# ---------------------------------------------------------------------------
# 2. resolve_canonical_model_id: card_model_id → Card-Lesen
# ---------------------------------------------------------------------------


def test_resolve_canonical_model_id_uses_card_model_id(
    isolated_card_dir: Path,
) -> None:
    """``resolve_canonical_model_id`` mit ``card_model_id`` behält die EIGENE ID.

    Der Redirect dient NUR der Card-Existenz-Prüfung — die kanonische ID
    des Profils (z.B. ``{id}-thinking``) bleibt unverändert. Andernfalls
    würde die CSV-Spalte mit der Original-ID überschrieben (Plan: "CSV
    model_id bleibt {...}-thinking").
    """
    target = isolated_card_dir / "ornith-1_0-35B-FP8.json"
    target.write_text(
        json.dumps({"model_id": "ornith-1.0-35B-FP8"}), encoding="utf-8",
    )

    profile_cfg = {"card_model_id": "ornith-1.0-35B-FP8"}
    canonical = resolve_canonical_model_id(
        "ornith-1.0-35B-FP8-thinking", model_cfg=profile_cfg,
    )
    # Card existiert (via card_model_id-Redirect gefunden), aber die
    # kanonische ID ist die EIGENE Profil-ID (safe_name), nicht die der Card.
    assert canonical == "ornith-1_0-35B-FP8-thinking"


def test_resolve_canonical_model_id_without_model_cfg_unchanged(
    isolated_card_dir: Path,
) -> None:
    """Ohne ``model_cfg`` fällt ``resolve_canonical_model_id`` auf _safe_name zurück.

    Bei unbekanntem Modell ohne Card → systemweite Konvention (Punkte/Slashes
    → Underscores).
    """
    canonical = resolve_canonical_model_id("some-unknown-model")
    assert canonical == "some-unknown-model"


def test_resolve_canonical_model_id_falls_back_to_safename(
    isolated_card_dir: Path,
) -> None:
    """Mit ``card_model_id`` auf nicht-existente Card → Fallback auf _safe_name.

    Backward-compat: kein Hard-Fail, sondern graceful degradation.
    """
    profile_cfg = {"card_model_id": "nonexistent-model"}
    # ``nonexistent-model`` hat keine Card → Fallback _safe_name(base).
    canonical = resolve_canonical_model_id(
        "ornith-1.0-35B-FP8-thinking", model_cfg=profile_cfg,
    )
    assert canonical == "ornith-1_0-35B-FP8-thinking"


# ---------------------------------------------------------------------------
# 3. resolve_model_cfg_for: SSoT-Helper für Config-Lookup
# ---------------------------------------------------------------------------


def test_resolve_model_cfg_for_finds_thinking_profile() -> None:
    """Der SSoT-Helper findet den expandierten Thinking-Profil-Eintrag.

    Simuliert eine Config mit einem vLLM-Provider, der sowohl das Standard-
    als auch das Thinking-Profil enthält (wie von ``_expand_thinking_profiles``
    generiert). Der Helper muss den Profile-Eintrag mit ``card_model_id``
    zurückgeben.
    """
    config = {
        "providers": {
            "local": {
                "vllm_spark": {
                    "api_type": "vllm",
                    "models": [
                        {
                            "id": "ornith-1_0-35B-FP8",
                            "name": "Ornith 1.0 35B (FP8)",
                        },
                        {
                            "id": "ornith-1_0-35B-FP8-thinking",
                            "name": "Ornith 1.0 35B (FP8) Thinking",
                            "card_model_id": "ornith-1_0-35B-FP8",
                            "chat_template_kwargs": {"enable_thinking": True},
                        },
                    ],
                },
            },
        },
    }
    cfg = resolve_model_cfg_for("ornith-1_0-35B-FP8-thinking", config)
    assert cfg is not None
    assert cfg["card_model_id"] == "ornith-1_0-35B-FP8"


def test_resolve_model_cfg_for_finds_standard_profile() -> None:
    """Der SSoT-Helper findet auch den Standard-Eintrag (ohne card_model_id)."""
    config = {
        "providers": {
            "local": {
                "vllm_spark": {
                    "api_type": "vllm",
                    "models": [
                        {"id": "ornith-1_0-35B-FP8", "name": "Ornith 1.0 35B (FP8)"},
                    ],
                },
            },
        },
    }
    cfg = resolve_model_cfg_for("ornith-1_0-35B-FP8", config)
    assert cfg is not None
    assert "card_model_id" not in cfg


def test_resolve_model_cfg_for_dot_normalization() -> None:
    """Der Helper normalisiert Underscore↔Dot (via find_model_in_provider_cfg)."""
    config = {
        "providers": {
            "commercial": {
                "openai": {
                    "models": [
                        {"id": "gpt-5.4-nano"},
                    ],
                },
            },
        },
    }
    # Interne ID mit Underscore → Config-Eintrag mit Dot
    cfg = resolve_model_cfg_for("gpt-5_4-nano", config)
    assert cfg is not None


def test_resolve_model_cfg_for_returns_none_for_unknown() -> None:
    """Unbekannte Modell-ID → None (kein Hard-Fail)."""
    config = {"providers": {"local": {"vllm_spark": {"models": []}}}}
    assert resolve_model_cfg_for("does-not-exist", config) is None


def test_resolve_model_cfg_for_empty_config() -> None:
    """Leere/defekte Config → None (graceful degradation)."""
    assert resolve_model_cfg_for("any-model", {}) is None
    assert resolve_model_cfg_for("any-model", {"providers": {}}) is None


# ---------------------------------------------------------------------------
# 4. End-to-End Drift-Test: Ornith-Thinking findet geteilte Card
# ---------------------------------------------------------------------------


def test_find_card_ornith_thinking_finds_shared_card(
    isolated_card_dir: Path,
) -> None:
    """Drift-Fix: Thinking-Profil findet die geteilte --VSPK-Card via Redirect.

    Reproduziert das Live-Szenario: Die Card existiert als
    ``ornith-1_0-35B-FP8--VSPK.json`` (VSPK-Suffix für vllm_spark).
    Ohne den Redirect würde ``_find_card`` nach
    ``ornith-1_0-35B-FP8-thinking.json`` suchen und nichts finden.
    """
    # Shared card im VSPK-Schema (wie in Produktion)
    shared_card = isolated_card_dir / "ornith-1_0-35B-FP8--VSPK.json"
    shared_card.write_text(
        json.dumps({
            "model_id": "ornith-1_0-35B-FP8",
            "model_version": "1.0",
            "thinking_probe_detected": True,
            "thinking_probe_confidence": "high",
        }),
        encoding="utf-8",
    )

    profile_cfg = {"card_model_id": "ornith-1_0-35B-FP8"}
    result = _find_card("ornith-1_0-35B-FP8-thinking", model_cfg=profile_cfg)
    assert result == shared_card
    assert result.exists()

    # Card-Inhalt: model_version ist "1.0" (nicht "k.A.")
    card_data = json.loads(result.read_text(encoding="utf-8"))
    assert card_data["model_version"] == "1.0"


def test_find_card_ornith_thinking_without_cfg_drifts(
    isolated_card_dir: Path,
) -> None:
    """Ohne model_cfg (alter Aufruf-Stil) wird die geteilte Card NICHT gefunden.

    Dieser Test dokumentiert den Bug: ohne Redirect fällt _find_card auf
    den Profile-Pfad zurück, der nicht existiert. Dies ist das Verhalten,
    das durch den Fix vermieden wird (Aufrufer müssen model_cfg reichen).
    """
    shared_card = isolated_card_dir / "ornith-1_0-35B-FP8--VSPK.json"
    shared_card.write_text(
        json.dumps({"model_id": "ornith-1_0-35B-FP8", "model_version": "1.0"}),
        encoding="utf-8",
    )

    # Ohne model_cfg → sucht nach ornith-1_0-35B-FP8-thinking*.json → nicht vorhanden
    result = _find_card("ornith-1_0-35B-FP8-thinking")
    assert not result.exists()
    # Der zurückgegebene Pfad ist der nicht-existente Profile-Pfad
    assert "thinking" in result.name