"""Regression-Tests für die Taxonomie-SSoT (config/classification_taxonomy.json).

Sicherstellt, dass:
  1. load_taxonomy() / get_valid_values() korrekt aus der JSON-Datei lesen
  2. Die Taxonomie die kontrollierten Vokabulare für die drei relevanten
     Felder (weights_license_tier, use_case, parameter_architecture) enthält
  3. Das card_template_model.yaml keine widersprüchlichen Whitelist-Werte
     in der description listet (Doku-Drift-Schutz)
  4. ensure_card() eine WARN loggt, wenn ein nicht-TODO-Wert gegen die
     Whitelist verstößt
  5. Das Validate-Skript die gleiche Whitelist zieht wie die Card-Generierung
     (gleiche Quelle, gleiche Whitelist)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from utils.card_utils import (
    _TAXONOMY_PATH,  # noqa: PLC2701 — privates Symbol nötig für Cache-Reset
    clear_taxonomy_cache,
    get_valid_values,
    load_taxonomy,
)


# ===========================================================================
# Setup: Cache zurücksetzen zwischen Tests
# ===========================================================================


@pytest.fixture(autouse=True)
def reset_taxonomy_cache() -> None:
    """Stellt sicher, dass jeder Test die Taxonomie frisch lädt."""
    clear_taxonomy_cache()
    yield
    clear_taxonomy_cache()


# ===========================================================================
# Loader-Tests
# ===========================================================================


class TestLoadTaxonomy:
    def test_taxonomy_file_exists(self) -> None:
        assert _TAXONOMY_PATH.exists(), f"Taxonomie-Datei fehlt: {_TAXONOMY_PATH}"

    def test_load_returns_dict(self) -> None:
        taxonomy = load_taxonomy()
        assert isinstance(taxonomy, dict)
        assert len(taxonomy) > 0

    def test_required_sections_present(self) -> None:
        taxonomy = load_taxonomy()
        # Diese drei Sections sind Pflicht für die Card-Validierung.
        assert "weights_license_tier" in taxonomy
        assert "use_case" in taxonomy
        assert "parameter_architecture" in taxonomy

    def test_cache_works(self) -> None:
        # Erster Aufruf
        t1 = load_taxonomy()
        # Zweiter Aufruf sollte aus dem Cache kommen (gleiche ID)
        t2 = load_taxonomy()
        assert t1 is t2, "Taxonomie sollte gecacht werden"

    def test_clear_cache_works(self) -> None:
        t1 = load_taxonomy()
        clear_taxonomy_cache()
        t2 = load_taxonomy()
        assert t1 is not t2, "clear_taxonomy_cache sollte neuen Load erzwingen"


# ===========================================================================
# get_valid_values-Tests
# ===========================================================================


class TestGetValidValues:
    def test_weights_license_tier_values(self) -> None:
        valid = get_valid_values("weights_license_tier")
        assert isinstance(valid, frozenset)
        # Erwartete Werte laut Taxonomie (Stand 2026-06-10).
        assert "proprietary" in valid
        assert "open-weights" in valid
        assert "restricted-weights" in valid
        # Veraltete Werte, die im Template standen, dürfen NICHT enthalten sein.
        assert "open-source" not in valid
        assert "research-only" not in valid

    def test_use_case_values(self) -> None:
        valid = get_valid_values("use_case")
        assert "generalist" in valid
        assert "coding" in valid
        assert "reasoning" in valid
        assert "vision-language" in valid
        assert "agentic" in valid
        # "code" (Singular) ist im Code nirgendwo erlaubt.
        assert "code" not in valid

    def test_parameter_architecture_values(self) -> None:
        valid = get_valid_values("parameter_architecture")
        assert "dense" in valid
        assert "moe" in valid
        assert "hybrid" in valid
        # "hybrid-attention" ist zu spezifisch und kein gültiger Wert.
        assert "hybrid-attention" not in valid

    def test_unknown_section_returns_empty_frozenset(self) -> None:
        valid = get_valid_values("does-not-exist")
        assert valid == frozenset()

    def test_get_valid_values_does_not_raise_on_missing_file(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Wenn die Taxonomie-Datei fehlt, soll get_valid_values NICHT
        # crashen, sondern ein leeres Set liefern.
        nonexistent = Path("/tmp/this/does/not/exist.json")
        monkeypatch.setattr("utils.card_utils._TAXONOMY_PATH", nonexistent)
        clear_taxonomy_cache()
        valid = get_valid_values("weights_license_tier")
        assert valid == frozenset()


# ===========================================================================
# Konsistenz-Tests: Template-Doku vs. Taxonomie
# ===========================================================================


class TestTemplateTaxonomySync:
    """Stellt sicher, dass die description-Strings im card_template_model.yaml
    mit den Whitelist-Werten der Taxonomie übereinstimmen.

    Hintergrund: Wenn ein*e Entwickler*in einen neuen Wert zur Taxonomie
    hinzufügt, MUSS auch die description aktualisiert werden — und umgekehrt.
    Dieser Test schlägt Alarm, wenn die beiden Quellen auseinanderdriften.
    """

    TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "config" / "card_template_model.yaml"

    def _load_template_descriptions(self) -> dict[str, str]:
        """Lädt die description-Felder aus dem YAML-Template (ohne PyYAML)."""
        import yaml  # type: ignore[import-untyped]

        with self.TEMPLATE_PATH.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        result: dict[str, str] = {}
        for field in data.get("required_fields", []):
            name = field.get("name")
            desc = field.get("description", "")
            if name:
                result[name] = desc
        return result

    def test_weights_license_tier_template_matches_taxonomy(self) -> None:
        descs = self._load_template_descriptions()
        template_desc = descs.get("weights_license_tier", "")
        valid = get_valid_values("weights_license_tier")

        # Alle gültigen Werte müssen in der description genannt werden
        # (Pipe-getrennt). Wir prüfen Wort-Substring, nicht exakte
        # Übereinstimmung, da die Reihenfolge variieren kann.
        for value in valid:
            assert value in template_desc, (
                f"weights_license_tier='{value}' fehlt in card_template_model.yaml description: "
                f"'{template_desc}'"
            )

    def test_use_case_template_matches_taxonomy(self) -> None:
        descs = self._load_template_descriptions()
        template_desc = descs.get("use_case_primary", "")
        valid = get_valid_values("use_case")

        for value in valid:
            assert value in template_desc, (
                f"use_case_primary='{value}' fehlt in card_template_model.yaml description: "
                f"'{template_desc}'"
            )

    def test_parameter_architecture_template_matches_taxonomy(self) -> None:
        descs = self._load_template_descriptions()
        template_desc = descs.get("parameter_architecture", "")
        valid = get_valid_values("parameter_architecture")

        for value in valid:
            assert value in template_desc, (
                f"parameter_architecture='{value}' fehlt in card_template_model.yaml description: "
                f"'{template_desc}'"
            )


# ===========================================================================
# ensure_card-Tests: Whitelist-Warnung
# ===========================================================================


class TestEnsureCardWhitelistWarning:
    """ensure_card() soll WARN loggen, wenn ein kontrolliertes Feld einen
    Wert hat, der nicht in der Taxonomie steht (und nicht "TODO" / null ist).
    """

    def test_invalid_use_case_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        from utils.card_utils import ensure_card

        card_path = tmp_path / "test-model.json"
        # Pre-populate mit ungültigem use_case-Wert
        card_path.write_text(
            json.dumps(
                {
                    "model_id": "test-model",
                    "use_case_primary": "code",  # ungültig — sollte "coding" sein
                }
            ),
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING, logger="utils.card_utils"):
            ensure_card("test-model", card_path=card_path)

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("use_case_primary" in r.getMessage() for r in warnings), (
            f"Erwartete WARN für ungültigen use_case, bekam: {[r.getMessage() for r in warnings]}"
        )

    def test_invalid_tier_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        from utils.card_utils import ensure_card

        card_path = tmp_path / "test-model.json"
        card_path.write_text(
            json.dumps(
                {
                    "model_id": "test-model",
                    "weights_license_tier": "open-source",  # ungültig — veraltet
                }
            ),
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING, logger="utils.card_utils"):
            ensure_card("test-model", card_path=card_path)

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("weights_license_tier" in r.getMessage() for r in warnings), (
            f"Erwartete WARN für ungültigen tier, bekam: {[r.getMessage() for r in warnings]}"
        )

    def test_todo_value_does_not_warn(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """TODO ist explizit als 'noch zu befüllen'-Platzhalter erlaubt — keine WARN."""
        from utils.card_utils import ensure_card

        card_path = tmp_path / "test-model.json"
        # Frische Karte, weights_license_tier='TODO' (Default)
        with caplog.at_level(logging.WARNING, logger="utils.card_utils"):
            ensure_card("test-model", card_path=card_path)

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        # TODO darf KEINE Warnung auslösen
        assert not any("weights_license_tier" in r.getMessage() for r in warnings), (
            f"TODO sollte keine WARN auslösen, bekam: {[r.getMessage() for r in warnings]}"
        )

    def test_valid_values_do_not_warn(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Gültige Werte aus der Taxonomie sollen keine WARN auslösen."""
        from utils.card_utils import ensure_card

        card_path = tmp_path / "test-model.json"
        card_path.write_text(
            json.dumps(
                {
                    "model_id": "test-model",
                    "weights_license_tier": "proprietary",
                    "use_case_primary": "coding",
                    "parameter_architecture": "dense",
                }
            ),
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING, logger="utils.card_utils"):
            ensure_card("test-model", card_path=card_path)

        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert not any("nicht in der Taxonomie" in r.getMessage() for r in warnings), (
            f"Gültige Werte sollten keine WARN auslösen, bekam: "
            f"{[r.getMessage() for r in warnings]}"
        )


# ===========================================================================
# validate_model_cards.py — Whitelist-Sync
# ===========================================================================


class TestValidateScriptSync:
    """Das Validate-Skript MUSS die gleiche Whitelist ziehen wie die
    Card-Generierung. Test prüft das indirekt: Wenn die Taxonomie einen
    ungültigen Wert X meldet, meldet ihn auch das Validate-Skript.
    """

    def test_validate_script_uses_taxonomy(self) -> None:
        """Indirekter Test: Import des Skripts + Aufruf von _get_valid_values."""
        # scripts/dev/ ist nicht im regulären sys.path — manuell hinzufügen
        import sys

        dev_dir = Path(__file__).resolve().parent.parent / "scripts" / "dev"
        if str(dev_dir) not in sys.path:
            sys.path.insert(0, str(dev_dir))

        from validate_model_cards import _get_valid_values  # type: ignore[import-not-found]

        valid = _get_valid_values("weights_license_tier")
        assert "proprietary" in valid
        assert "open-weights" in valid
        assert "restricted-weights" in valid
        # Wenn diese Assertionen passen, liest das Skript aus der Taxonomie.


# ===========================================================================
# Placeholder-Strings: Schutz gegen Rückfall in alte Workaround-Werte
# ===========================================================================


# Historische Placeholder-Strings, die NICHT mehr in Taxonomie-Feldern
# auftauchen dürfen. Sie waren Workarounds, bevor die Taxonomie SSoT war.
FORBIDDEN_PLACEHOLDERS = {
    "weights_license_tier": ["open-weights-pending", "TODO"],
    "use_case_primary": ["code-generation", "code-gen", "frei", "TODO"],
    "parameter_architecture": ["hybrid-attention", "unknown", "TODO"],
}

# Globale Placeholder-Strings, die in KEINEM Card-String-Feld erscheinen dürfen
GLOBAL_FORBIDDEN_SUBSTRINGS = ["frei"]


class TestNoPlaceholderStrings:
    """Stellt sicher, dass keine Modell-Card die historischen Placeholder-
    Strings verwendet. Diese waren Workarounds, bevor die Taxonomie SSoT
    eingeführt wurde (Phase 2).
    """

    def test_no_forbidden_placeholder_in_taxonomy_fields(self) -> None:
        """Keine Card darf einen verbotenen Placeholder in den Taxonomie-Feldern haben."""
        cards_dir = Path(__file__).resolve().parent.parent / "benchmark_scores" / "model_cards"
        violations: list[str] = []

        for path in sorted(cards_dir.glob("*.json")):
            if path.name == "_index.json":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(data, dict):
                continue

            for field, bad_values in FORBIDDEN_PLACEHOLDERS.items():
                value = data.get(field)
                if value is None:
                    continue
                if value in bad_values:
                    violations.append(
                        f"{path.name}: {field}='{value}' ist verbotener Placeholder"
                    )

        assert not violations, (
            f"Verbotene Placeholder gefunden:\n  " + "\n  ".join(violations)
            + "\n\nVerwende stattdessen die echten Taxonomie-Werte aus config/classification_taxonomy.json."
        )

    # Hinweis: Wir testen KEINE freien Text-Substrings wie "frei", weil das
    # Wort in deutschen Fließtext-Karten (z.B. "frei verfügbar", "frei
    # nutzbar") legitim vorkommt. Der Schutz gegen den historischen
    # Placeholder-Wert "frei" in use_case_primary ist bereits durch
    # test_no_forbidden_placeholder_in_taxonomy_fields abgedeckt.
