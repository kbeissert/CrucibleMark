"""Tests für scripts/analysis/review/metrics.py.

Schwerpunkt: Toleranz gegenüber verschachtelten Listen-Schreibweisen in
Model-Card-Feldern (`strengths`, `known_limitations`). Hintergrund:
Card-Editor hat in mindestens 68 Karten eine Wrapper-Schicht
``[[...]]`` statt ``[...]`` eingeführt, was ``get_model_card_context``
mit TypeError crashen ließ. Der Helper ``_flatten_strings`` akzeptiert
beide Formen und filtert Nicht-Strings aus.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from scripts.analysis.review.metrics import _flatten_strings, get_model_card_context  # noqa: E402


class TestFlattenStrings:
    """Unit-Tests für _flatten_strings."""

    def test_flat_list(self):
        assert _flatten_strings(["a", "b", "c"]) == ["a", "b", "c"]

    def test_nested_wrapper_layer(self):
        """Card-Editor-Bug: ``[["a", "b"]]`` statt ``["a", "b"]``."""
        assert _flatten_strings([["a", "b"]]) == ["a", "b"]

    def test_double_nested_returns_empty(self):
        """Nur EINE Wrapper-Schicht wird aufgelöst — doppelt verschachtelt
        ist kein bekannter Fall und bleibt defensiv leer."""
        assert _flatten_strings([[["a", "b"]]]) == []

    def test_filters_non_strings(self):
        """Nicht-String-Einträge (Zahlen, None) werden stillschweigend entfernt."""
        assert _flatten_strings(["ok", 42, None, "auch ok"]) == ["ok", "auch ok"]

    def test_empty_list(self):
        assert _flatten_strings([]) == []

    def test_none(self):
        assert _flatten_strings(None) == []

    def test_non_list(self):
        """Alles, was keine Liste ist, wird als leer behandelt."""
        assert _flatten_strings("string") == []
        assert _flatten_strings(42) == []
        assert _flatten_strings({"key": "value"}) == []

    def test_preserves_order(self):
        assert _flatten_strings([["z", "a", "m"]]) == ["z", "a", "m"]

    def test_mixed_with_nested_filter(self):
        """Wenn die äußere Liste Strings UND Listen enthält, wird die
        Wrapper-Heuristik (1 Element, Element ist Liste) NICHT angewandt
        — stattdessen werden nur die Strings durchgelassen."""
        result = _flatten_strings(["solo", ["nested1", "nested2"]])
        assert result == ["solo"]


class TestGetModelCardContext:
    """End-to-End-Tests: get_model_card_context darf nicht crashen,
    egal welche Schreibweise die Card verwendet."""

    def test_real_gpt5_card_after_fix(self, tmp_path, monkeypatch):
        """Reale Card (bereits geflattet) muss lesbar sein.

        Hinweis: ``_find_card`` nutzt das relative ``CARD_DIR`` (siehe
        ``utils/model_utils.py:107``). Wir monkeypatchen den Helper, damit
        der Test unabhängig vom aktuellen Arbeitsverzeichnis läuft.
        """

        real_card = ROOT / "benchmark_scores" / "model_cards" / "gpt-5-2025-08-07.json"
        assert real_card.exists(), f"Card nicht gefunden: {real_card}"

        monkeypatch.setattr(
            "scripts.analysis.review.metrics._find_card",
            lambda model_id, card_dir=None: real_card,
        )
        ctx = get_model_card_context("gpt-5-2025-08-07")
        assert "**Stärken:**" in ctx
        assert "**Einschränkungen:**" in ctx

    def test_nested_card_does_not_crash(self, tmp_path, monkeypatch):
        """Card mit verschachtelter strengths/known_limitations darf nicht
        TypeError werfen. Verwendet eine synthetische Card in einem
        tmp-Verzeichnis, damit keine echte Card gemockt werden muss."""

        # Synthetische Card schreiben + _find_card monkeypatchen
        fake_card = tmp_path / "test-card.json"
        fake_card.write_text(
            """{
  "model_id": "test/nested-card",
  "display_name": "Test Nested",
  "developer": "Test Co",
  "origin_country": "US",
  "deployment_type": "cloud-only",
  "model_family": "TestFamily",
  "vendor": "TestVendor",
  "use_case_primary": "generalist",
  "parameter_architecture": "dense",
  "strengths": [["Stärke 1", "Stärke 2"]],
  "known_limitations": [["Limit 1"]],
  "summary": "Test summary"
}""",
            encoding="utf-8",
        )

        def _fake_find_card(_model_id: str):
            return fake_card

        monkeypatch.setattr("scripts.analysis.review.metrics._find_card", _fake_find_card)
        ctx = get_model_card_context("test/nested-card")
        assert "Stärke 1" in ctx
        assert "Stärke 2" in ctx
        assert "Limit 1" in ctx
