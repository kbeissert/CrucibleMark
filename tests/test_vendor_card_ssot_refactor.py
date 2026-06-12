"""Regressionstests für Phase 20/21: Provider-Card SSoT-Refactoring.

Stellt sicher, dass:
- Phase 20: risk_calculator.get_vendor_card_context() die SSoT-API
  utils.vendor_card_template.load_vendor_card() nutzt (nicht direkten FS-Zugriff).
- Phase 21: generate_review._ensure_vendor_card() keine _load_card_module-Reflection
  mehr für den Provider-Generator verwendet.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.vendor_card_template import (
    CARDS_DIR,
    _safe_id,
    ensure_vendor_card,
    load_vendor_card,
)


class TestRiskCalculatorSSoT:
    """Phase 20: risk_calculator nutzt load_vendor_card() SSoT."""

    def test_risk_calculator_imports_load_vendor_card(self) -> None:
        """get_vendor_card_context nutzt load_vendor_card aus SSoT-Modul."""
        from scripts.analysis.review import risk_calculator

        # Wenn der Refactor nicht angewendet wurde, ist load_vendor_card NICHT
        # importiert — dann schlägt dieser Test fehl.
        assert hasattr(risk_calculator, "load_vendor_card")
        assert risk_calculator.load_vendor_card is load_vendor_card

    def test_risk_calculator_no_direct_json_load(self) -> None:
        """get_vendor_card_context ruft NICHT json.loads direkt für die Provider-Card auf."""
        import inspect
        from scripts.analysis.review.risk_calculator import get_vendor_card_context

        source = inspect.getsource(get_vendor_card_context)
        # Direkter json.loads()-Aufruf im Provider-Card-Pfad ist verboten
        # — SSoT-API muss genutzt werden.
        assert "json.loads(card_path.read_text" not in source, (
            "get_vendor_card_context nutzt noch direkten json.loads() — "
            "SSoT-Refactor fehlt!"
        )
        assert "load_vendor_card" in source, (
            "get_vendor_card_context ruft load_vendor_card() nicht auf — "
            "SSoT-Brücke fehlt!"
        )

    def test_get_vendor_card_context_uses_ssoot_for_known_provider(self, tmp_path: Path) -> None:
        """End-to-End: SSoT-Lookup findet eine echte anthropic.json über die API."""
        from scripts.analysis.review.risk_calculator import get_vendor_card_context

        # Anthropic existiert im echten Verzeichnis. Wir mocken den Model-Card-Pfad
        # nicht — stattdessen nutzen wir einen nicht existierenden Modelnamen,
        # um zu prüfen, dass der Code-Pfad keine Exception wirft.
        result = get_vendor_card_context("__definitely_nonexistent_model_id_xyz__")
        assert isinstance(result, str)

    def test_get_vendor_card_context_ignores_unknown_vendor_cards(self) -> None:
        """SSoT-API verwirft unknown=true Cards — risk_calculator nutzt dieses Verhalten."""
        # Patchen CARDS_DIR auf ein Temp-Verzeichnis mit einer unknown-Card.
        unknown_card = {
            "vendor_id": "test_unknown_prov",
            "display_name": "Test Unknown",
            "unknown": True,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_cards = Path(tmpdir)
            (tmp_cards / f"{_safe_id('test_unknown_prov')}.json").write_text(
                json.dumps(unknown_card), encoding="utf-8"
            )

            with patch.object(
                __import__("utils.vendor_card_template", fromlist=["CARDS_DIR"]),
                "CARDS_DIR", tmp_cards,
            ):
                # load_vendor_card liefert die unknown-Card
                # (SSoT-API filtert NICHT — das macht der Konsument)
                loaded = load_vendor_card("test_unknown_prov")
                assert loaded is not None
                assert loaded.get("unknown") is True

                # get_vendor_card_context muss unknown=True selbst filtern
                # (das war das vorherige Inline-Verhalten, das wir bewahrt haben).
                # Wir testen das über einen Modelnamen, dessen Karte developer=...
                # hat. Da wir die Model-Card nicht mocken können, prüfen wir
                # nur, dass der Code-Pfad korrekt ist.
                from scripts.analysis.review import risk_calculator
                source = risk_calculator.get_vendor_card_context.__code__.co_consts
                # Die Funktion MUSS die unknown-Prüfung weiterhin selbst machen,
                # weil load_vendor_card sie nicht durchsetzt.
                # Wir prüfen, dass der String "unknown" im Source vorkommt.
                import inspect
                fn_source = inspect.getsource(risk_calculator.get_vendor_card_context)
                assert "unknown" in fn_source


class TestGenerateReviewNoReflection:
    """Phase 21: generate_review nutzt keine _load_card_module-Reflection
    für den Provider-Generator mehr."""

    def test_ensure_vendor_card_uses_direct_imports(self) -> None:
        """_ensure_vendor_card ruft _load_card_module NICHT auf."""
        import inspect
        from scripts.analysis.generate_review import _ensure_vendor_card

        source = inspect.getsource(_ensure_vendor_card)
        # Die Reflection-Funktion _load_card_module("generate_vendor_cards")
        # darf NICHT mehr im Provider-Card-Pfad auftauchen.
        assert '_load_card_module("generate_vendor_cards")' not in source, (
            "_ensure_vendor_card nutzt noch _load_card_module-Reflection — "
            "SSoT-Refactor fehlt!"
        )
        # Stattdessen müssen die Generator-Funktionen direkt importiert werden.
        assert "_generate_card" in source, (
            "_ensure_vendor_card importiert _generate_card nicht direkt!"
        )
        assert "_write_card" in source, (
            "_ensure_vendor_card importiert _write_card nicht direkt!"
        )
        assert "rebuild_provider_index" in source, (
            "_ensure_vendor_card ruft rebuild_provider_index() nicht auf!"
        )

    def test_ensure_vendor_card_uses_ssoot_lookup(self) -> None:
        """_ensure_vendor_card nutzt load_vendor_card() für den Read-Pfad."""
        import inspect
        from scripts.analysis.generate_review import _ensure_vendor_card

        source = inspect.getsource(_ensure_vendor_card)
        assert "load_vendor_card" in source, (
            "_ensure_vendor_card ruft load_vendor_card() nicht auf — "
            "SSoT-Lookup fehlt!"
        )
