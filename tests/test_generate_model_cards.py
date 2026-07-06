"""Tests für scripts/analysis/generate_model_cards.py

Testet die Public API und Helper-Funktionen des Card-Generators. Verwendet
``conftest.py::_isolate_card_dir`` (autouse), um Card-Leichen im realen
``benchmark_scores/model_cards/`` zu verhindern.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.analysis.generate_model_cards import (
    CardCreationIssue,
    CardCreationReport,
    _build_creation_plan,
    _is_helper_file,
    create_card,
    format_json_report,
    format_text_report,
)
from utils.card_template import cards_dir


# ---------------------------------------------------------------------------
# _is_helper_file
# ---------------------------------------------------------------------------


class TestIsHelperFile:
    def test_index_file_is_helper(self) -> None:
        assert _is_helper_file(Path("model_cards/_index.json")) is True

    def test_true_stem_is_helper(self) -> None:
        assert _is_helper_file(Path("model_cards/True.json")) is True

    def test_false_stem_is_helper(self) -> None:
        assert _is_helper_file(Path("model_cards/False.json")) is True

    def test_null_stem_is_helper(self) -> None:
        assert _is_helper_file(Path("model_cards/null.json")) is True

    def test_none_stem_is_helper(self) -> None:
        assert _is_helper_file(Path("model_cards/None.json")) is True

    def test_normal_card_is_not_helper(self) -> None:
        assert _is_helper_file(Path("model_cards/claude-opus-4-7.json")) is False


# ---------------------------------------------------------------------------
# _build_creation_plan
# ---------------------------------------------------------------------------


class TestBuildCreationPlan:
    def test_missing_file_returns_create(self, tmp_path: Path) -> None:
        p = tmp_path / "missing.json"
        assert _build_creation_plan(p, force=False) == "create"
        assert _build_creation_plan(p, force=True) == "create"

    def test_existing_file_no_force_returns_skip(self, tmp_path: Path) -> None:
        p = tmp_path / "exists.json"
        p.write_text("{}")
        assert _build_creation_plan(p, force=False) == "skip"

    def test_existing_file_with_force_returns_rebuild(self, tmp_path: Path) -> None:
        p = tmp_path / "exists.json"
        p.write_text("{}")
        assert _build_creation_plan(p, force=True) == "rebuild"


# ---------------------------------------------------------------------------
# CardCreationReport / CardCreationIssue
# ---------------------------------------------------------------------------


class TestCardCreationReport:
    def test_initial_state_is_success(self) -> None:
        r = CardCreationReport(
            card_file="x.json", card_id="x", action="created",
        )
        assert r.is_success is True
        assert r.issues == []

    def test_exists_issue_keeps_success(self) -> None:
        r = CardCreationReport(
            card_file="x.json", card_id="x", action="skipped",
        )
        r.add_issue(CardCreationIssue(
            issue_type="exists", field="<file>", message="exists",
        ))
        # exists-Issue ist nur eine Warnung
        assert r.is_success is True

    def test_path_error_sets_failure(self) -> None:
        r = CardCreationReport(
            card_file="x.json", card_id="x", action="failed",
        )
        r.add_issue(CardCreationIssue(
            issue_type="path_error", field="model_id", message="bad",
        ))
        assert r.is_success is False

    def test_parse_error_sets_failure(self) -> None:
        r = CardCreationReport(
            card_file="x.json", card_id="x", action="failed",
        )
        r.add_issue(CardCreationIssue(
            issue_type="parse_error", field="<file>", message="bad",
        ))
        assert r.is_success is False


# ---------------------------------------------------------------------------
# create_card
# ---------------------------------------------------------------------------


class TestCreateCard:
    def test_creates_new_card_in_isolated_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Neue Karte wird im isolierten tmp_path erzeugt."""
        # CARD_DIR auf tmp_path patchen
        import utils.model_utils
        monkeypatch.setattr(utils.model_utils, "CARD_DIR", tmp_path)

        report = create_card("test-model-x", force=False)
        assert report.action == "created"
        assert report.is_success is True
        # Datei wurde im tmp_path erzeugt
        assert (tmp_path / "test-model-x.json").exists()
        # Inhalt prüfen
        data = json.loads((tmp_path / "test-model-x.json").read_text())
        assert data["model_id"] == "test-model-x"
        assert "TODO" in data["display_name"]

    def test_existing_card_is_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Bestehende Karte wird ohne --force übersprungen."""
        import utils.model_utils
        monkeypatch.setattr(utils.model_utils, "CARD_DIR", tmp_path)

        # Erstmal erzeugen
        create_card("test-model-y")
        # Zweiter Aufruf sollte skippen
        report = create_card("test-model-y", force=False)
        assert report.action == "skipped"
        assert any(i.issue_type == "exists" for i in report.issues)

    def test_existing_card_with_force_rebuilds(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Mit --force wird die bestehende Karte gelöscht und neu erzeugt."""
        import utils.model_utils
        monkeypatch.setattr(utils.model_utils, "CARD_DIR", tmp_path)

        create_card("test-model-z")
        report = create_card("test-model-z", force=True)
        assert report.action == "rebuilt"
        assert report.is_success is True

    def test_provider_creates_unique_id_card(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Mit provider= greift das {base}--{shortcode}-Schema."""
        import utils.model_utils
        monkeypatch.setattr(utils.model_utils, "CARD_DIR", tmp_path)

        report = create_card("gemma-3-4b", provider="ollama_local", force=False)
        assert report.action == "created"
        # Datei existiert unter unique-ID-Pfad
        assert any(p.suffix == ".json" for p in tmp_path.glob("*.json"))


# ---------------------------------------------------------------------------
# format_text_report / format_json_report
# ---------------------------------------------------------------------------


class TestFormatReports:
    @pytest.fixture
    def sample_reports(self) -> list[CardCreationReport]:
        r1 = CardCreationReport(
            card_file="a.json", card_id="a", action="created",
        )
        r2 = CardCreationReport(
            card_file="b.json", card_id="b", action="skipped",
        )
        r2.add_issue(CardCreationIssue(
            issue_type="exists", field="<file>", message="b exists",
        ))
        r3 = CardCreationReport(
            card_file="c.json", card_id="c", action="failed",
        )
        r3.add_issue(CardCreationIssue(
            issue_type="path_error", field="x", message="c failed",
        ))
        return [r1, r2, r3]

    def test_text_report_contains_counts(
        self, sample_reports: list[CardCreationReport],
    ) -> None:
        text = format_text_report(sample_reports, "model")
        assert "Total cards:        3" in text
        assert "Created:          1" in text
        assert "Skipped:          1" in text
        assert "Failed:           1" in text

    def test_text_report_shows_failed_cards(
        self, sample_reports: list[CardCreationReport],
    ) -> None:
        text = format_text_report(sample_reports, "model")
        assert "Fehlgeschlagen (1)" in text
        assert "c.json" in text
        assert "path_error" in text

    def test_json_report_structure(
        self, sample_reports: list[CardCreationReport],
    ) -> None:
        js = json.loads(format_json_report(sample_reports, "model"))
        assert js["card_type"] == "model"
        assert js["total"] == 3  # noqa: PLR2004
        assert js["created"] == 1
        assert js["skipped"] == 1
        assert js["failed"] == 1
        assert len(js["cards"]) == 3  # noqa: PLR2004
        # r1: created, is_success=True
        assert js["cards"][0]["action"] == "created"
        assert js["cards"][0]["is_success"] is True
        # r2: skipped, exists-Issue, is_success=True
        assert js["cards"][1]["action"] == "skipped"
        assert js["cards"][1]["is_success"] is True
        # r3: failed, path_error, is_success=False
        assert js["cards"][2]["action"] == "failed"
        assert js["cards"][2]["is_success"] is False
        assert js["cards"][2]["issues"][0]["type"] == "path_error"


# ---------------------------------------------------------------------------
# cards_dir / rebuild_card_index (SSoT in utils.card_template)
# ---------------------------------------------------------------------------


class TestCardsDirSsoT:
    def test_cards_dir_returns_correct_path(self) -> None:
        d = cards_dir("model")
        assert d.name == "model_cards"
        assert d.parent.name == "benchmark_scores"

    def test_cards_dir_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unbekannter card_type"):
            cards_dir("unknown")
