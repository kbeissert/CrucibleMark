"""
test_card_sync.py — Tests für utils/card_sync.py (SSoT-Sync zwischen Template und Karten)
==========================================================================================

Deckt ab:
- plan_sync: add / keep / delete Aktionen
- Protected IDs (provider_id, model_id) werden nie gelöscht
- Legacy tooluse_*-Felder in Model Cards werden toleriert
- apply_sync: dry-run schreibt nichts
- apply_sync: yes=True löscht ohne Rückfrage
- apply_sync: confirm_fn Hook für Lösch-Bestätigung
- apply_sync: ohne yes=True und ohne Bestätigung → Skip
- Idempotenz: zweiter Aufruf mit gleichem Template = No-Op
- sync_all: verarbeitet alle Karten
- format_summary: lesbarer Output
"""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from utils.card_sync import (
    SyncAction,
    SyncPlan,
    apply_sync,
    collect_card_paths,
    format_summary,
    get_template_field_names,
    plan_sync,
    sync_all,
)
from utils.card_utils import _CARD_TEMPLATE
from utils.vendor_card_template import _PROVIDER_CARD_TEMPLATE


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_vendor_card(tmp_path: Path) -> Path:
    """Provider-Card-Datei mit minimalen Feldern (zum Testen der Sync-Logik)."""
    card: dict[str, Any] = {
        "vendor_id": "test_provider",
        "display_name": "Test Provider",
    }
    path = tmp_path / "test_provider.json"
    path.write_text(json.dumps(card), encoding="utf-8")
    return path


@pytest.fixture
def tmp_vendor_card_with_drift(tmp_path: Path) -> Path:
    """Provider-Card mit einem Feld, das NICHT im Template ist (für Delete-Tests)."""
    card: dict[str, Any] = {
        "vendor_id": "drift_provider",
        "display_name": "Drift Provider",
        "legacy_field": "some old data",  # nicht im Template
    }
    path = tmp_path / "drift_provider.json"
    path.write_text(json.dumps(card), encoding="utf-8")
    return path


@pytest.fixture
def tmp_provider_dir(tmp_path: Path, monkeypatch) -> Path:
    """Patcht PROVIDER_CARDS_DIR auf ein tmp-Verzeichnis."""
    from utils import card_sync  # noqa: PLC0415
    cards_dir = tmp_path / "vendor_cards"
    cards_dir.mkdir()
    monkeypatch.setattr(card_sync, "PROVIDER_CARDS_DIR", cards_dir)
    return cards_dir


@pytest.fixture
def tmp_model_dir(tmp_path: Path, monkeypatch) -> Path:
    """Patcht MODEL_CARDS_DIR auf ein tmp-Verzeichnis."""
    from utils import card_sync  # noqa: PLC0415
    cards_dir = tmp_path / "model_cards"
    cards_dir.mkdir()
    monkeypatch.setattr(card_sync, "MODEL_CARDS_DIR", cards_dir)
    return cards_dir


# ---------------------------------------------------------------------------
# Template-Lookup
# ---------------------------------------------------------------------------


class TestTemplateLookup:
    def test_provider_template_has_known_fields(self) -> None:
        names = get_template_field_names("vendor")
        assert "vendor_id" in names
        assert "display_name" in names
        assert "deployment" in names
        assert "unknown" in names
        # Hinweis: ab v4.10.12 kein 'stats'-Feld mehr (Provider-Stats-Use-Case stillgelegt)
        assert "stats" not in names

    def test_model_template_has_known_fields(self) -> None:
        names = get_template_field_names("model")
        assert "model_id" in names
        assert "display_name" in names
        assert "supports_tool_use" in names
        assert "card_status" in names

    def test_unknown_card_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unbekannter card_type"):
            get_template_field_names("bogus")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# plan_sync — Aktionen
# ---------------------------------------------------------------------------


class TestPlanSync:
    def test_minimal_card_gets_add_actions(self, tmp_vendor_card: Path) -> None:
        plan = plan_sync(tmp_vendor_card, "vendor")
        adds = [a for a in plan.actions if a.kind == "add"]
        # Minimal hat nur provider_id + display_name, alles andere fehlt
        assert len(adds) > 5
        assert any(a.field == "company" for a in adds)
        assert any(a.field == "deployment" for a in adds)

    def test_complete_card_has_no_changes(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from utils import card_sync  # noqa: PLC0415
        cards_dir = tmp_path / "vendor_cards"
        cards_dir.mkdir()
        monkeypatch.setattr(card_sync, "PROVIDER_CARDS_DIR", cards_dir)

        # Vollständige Card: alle Template-Felder vorhanden
        full_card = deepcopy(_PROVIDER_CARD_TEMPLATE)
        full_card["vendor_id"] = "complete"
        card_path = cards_dir / "complete.json"
        card_path.write_text(json.dumps(full_card), encoding="utf-8")

        plan = plan_sync(card_path, "vendor")
        assert not plan.has_changes
        assert plan.add_count == 0
        assert plan.delete_count == 0

    def test_drift_field_marked_for_delete(
        self, tmp_vendor_card_with_drift: Path
    ) -> None:
        plan = plan_sync(tmp_vendor_card_with_drift, "vendor")
        deletes = [a for a in plan.actions if a.kind == "delete"]
        assert len(deletes) == 1
        assert deletes[0].field == "legacy_field"
        assert "nicht mehr im Template" in deletes[0].reason

    def test_provider_id_protected_from_delete(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from utils import card_sync  # noqa: PLC0415
        cards_dir = tmp_path / "vendor_cards"
        cards_dir.mkdir()
        monkeypatch.setattr(card_sync, "PROVIDER_CARDS_DIR", cards_dir)

        # Karte mit Extras, aber ohne provider_id
        card = {"display_name": "Test", "some_drift": "data"}
        card_path = cards_dir / "noid.json"
        card_path.write_text(json.dumps(card), encoding="utf-8")

        plan = plan_sync(card_path, "vendor")
        # provider_id ist nicht in der Karte → add, nicht delete-keep
        # some_drift ist in Karte, nicht in Template → delete
        deletes = [a for a in plan.actions if a.kind == "delete"]
        assert any(a.field == "some_drift" for a in deletes)
        # provider_id wird in der add-Liste sein
        adds = [a for a in plan.actions if a.kind == "add"]
        assert any(a.field == "vendor_id" for a in adds)

    def test_tooluse_legacy_kept_in_model_cards(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from utils import card_sync  # noqa: PLC0415
        cards_dir = tmp_path / "model_cards"
        cards_dir.mkdir()
        monkeypatch.setattr(card_sync, "MODEL_CARDS_DIR", cards_dir)

        # Model-Card mit tooluse_tested_at (Legacy)
        card = deepcopy(_CARD_TEMPLATE)
        card["model_id"] = "test_model"
        card["tooluse_tested_at"] = "2026-06-01"
        card["tooluse_score_p1"] = 90
        card_path = cards_dir / "test_model.json"
        card_path.write_text(json.dumps(card), encoding="utf-8")

        plan = plan_sync(card_path, "model")
        deletes = [a for a in plan.actions if a.kind == "delete"]
        assert not any(a.field.startswith("tooluse_") for a in deletes)

    def test_index_file_returns_empty_plan(self, tmp_path: Path) -> None:
        plan = plan_sync(tmp_path / "_index.json", "vendor")
        assert not plan.has_changes
        assert plan.actions == []

    def test_unreadable_file_returns_empty_plan(self, tmp_path: Path) -> None:
        path = tmp_path / "broken.json"
        path.write_text("{invalid json", encoding="utf-8")
        plan = plan_sync(path, "vendor")
        assert not plan.has_changes


# ---------------------------------------------------------------------------
# apply_sync — Schreib-Verhalten
# ---------------------------------------------------------------------------


class TestApplySync:
    def test_dry_run_does_not_write(self, tmp_vendor_card_with_drift: Path) -> None:
        before = tmp_vendor_card_with_drift.read_text(encoding="utf-8")
        plan = apply_sync(
            tmp_vendor_card_with_drift, "vendor", dry_run=True, yes=False
        )
        after = tmp_vendor_card_with_drift.read_text(encoding="utf-8")
        assert before == after
        assert plan.has_changes
        assert plan.delete_count == 1

    def test_yes_deletes_without_prompt(
        self, tmp_vendor_card_with_drift: Path
    ) -> None:
        plan = apply_sync(
            tmp_vendor_card_with_drift, "vendor", dry_run=False, yes=True
        )
        data = json.loads(tmp_vendor_card_with_drift.read_text(encoding="utf-8"))
        assert "legacy_field" not in data
        assert "vendor_id" in data
        assert "display_name" in data
        # Adds wurden ebenfalls durchgeführt
        assert "company" in data
        assert plan.delete_count == 1
        assert plan.add_count > 0

    def test_confirm_fn_yes_deletes(self, tmp_vendor_card_with_drift: Path) -> None:
        def confirm(prompt: str) -> bool:
            return True
        plan = apply_sync(
            tmp_vendor_card_with_drift, "vendor",
            dry_run=False, confirm_fn=confirm,
        )
        data = json.loads(tmp_vendor_card_with_drift.read_text(encoding="utf-8"))
        assert "legacy_field" not in data
        assert plan.delete_count == 1

    def test_confirm_fn_no_skips_whole_card(
        self, tmp_vendor_card_with_drift: Path
    ) -> None:
        """Wenn der User Löschungen ablehnt, wird die ganze Karte nicht
        angefasst (atomarer Sync). Adds und Deletes werden zusammen
        ausgeführt oder gar nicht."""

        def confirm(prompt: str) -> bool:
            return False

        plan = apply_sync(
            tmp_vendor_card_with_drift, "vendor",
            dry_run=False, confirm_fn=confirm,
        )
        data = json.loads(tmp_vendor_card_with_drift.read_text(encoding="utf-8"))
        # Karte ist unverändert (weder Adds noch Deletes)
        assert "legacy_field" in data
        assert "company" not in data
        # Im zurückgegebenen Plan sind die Deletes auf 0 gesetzt
        assert plan.delete_count == 0
        assert plan.add_count == 0

    def test_no_changes_no_prompt(self, tmp_path: Path, monkeypatch) -> None:
        from utils import card_sync  # noqa: PLC0415
        cards_dir = tmp_path / "vendor_cards"
        cards_dir.mkdir()
        monkeypatch.setattr(card_sync, "PROVIDER_CARDS_DIR", cards_dir)

        # Vollständige Card (alle Template-Felder)
        full = deepcopy(_PROVIDER_CARD_TEMPLATE)
        full["vendor_id"] = "complete"
        path = cards_dir / "complete.json"
        path.write_text(json.dumps(full), encoding="utf-8")

        prompt_called = []

        def confirm(prompt: str) -> bool:
            prompt_called.append(prompt)
            return True

        plan = apply_sync(path, "vendor", confirm_fn=confirm)
        assert not plan.has_changes
        assert prompt_called == []  # kein Prompt wenn keine Änderungen

    def test_adds_use_template_defaults(
        self, tmp_vendor_card: Path
    ) -> None:
        apply_sync(tmp_vendor_card, "vendor", dry_run=False, yes=False)
        data = json.loads(tmp_vendor_card.read_text(encoding="utf-8"))
        # Default-Werte aus _PROVIDER_CARD_TEMPLATE
        assert data["pricing_model"] == "unknown"
        assert data["api_base_url"] is None
        assert data["deployment"]["cloud_act_exposure"] is False
        assert data["notable_models"] == []


# ---------------------------------------------------------------------------
# Idempotenz
# ---------------------------------------------------------------------------


class TestIdempotency:
    def test_second_run_is_no_op(
        self, tmp_vendor_card_with_drift: Path
    ) -> None:
        # 1. Lauf: löscht legacy_field, ergänzt Adds
        apply_sync(
            tmp_vendor_card_with_drift, "vendor", dry_run=False, yes=True
        )
        # 2. Lauf: nichts zu tun
        plan = apply_sync(
            tmp_vendor_card_with_drift, "vendor", dry_run=False, yes=True
        )
        assert not plan.has_changes


# ---------------------------------------------------------------------------
# sync_all
# ---------------------------------------------------------------------------


class TestSyncAll:
    def test_processes_all_cards_in_dir(
        self, tmp_provider_dir: Path
    ) -> None:
        # Drei Karten anlegen
        for name in ("a", "b", "c"):
            (tmp_provider_dir / f"{name}.json").write_text(
                json.dumps({
                    "vendor_id": name,
                    "display_name": name.upper(),
                    "junk": "drift",
                }),
                encoding="utf-8",
            )
        plans = sync_all("vendor", dry_run=False, yes=True)
        assert len(plans) == 3
        # Alle drei sollten "junk" gelöscht und Adds bekommen haben
        for plan in plans:
            data = json.loads(plan.card_path.read_text(encoding="utf-8"))
            assert "junk" not in data
            assert "company" in data

    def test_empty_dir_returns_empty_list(self, tmp_provider_dir: Path) -> None:
        plans = sync_all("vendor", dry_run=False, yes=True)
        assert plans == []

    def test_collect_card_paths_excludes_index(self, tmp_provider_dir: Path) -> None:
        (tmp_provider_dir / "a.json").write_text("{}", encoding="utf-8")
        (tmp_provider_dir / "_index.json").write_text("[]", encoding="utf-8")
        paths = collect_card_paths("vendor")
        assert len(paths) == 1
        assert paths[0].name == "a.json"


# ---------------------------------------------------------------------------
# format_summary
# ---------------------------------------------------------------------------


class TestFormatSummary:
    def test_summary_shows_counts(self) -> None:
        plans = [
            SyncPlan(
                card_path=Path("a.json"),
                card_type="vendor",
                actions=[
                    SyncAction("add", "company"),
                    SyncAction("add", "deployment"),
                    SyncAction("delete", "junk"),
                ],
            ),
            SyncPlan(card_path=Path("b.json"), card_type="vendor"),
        ]
        out = format_summary(plans)
        assert "Cards verarbeitet:   2" in out
        assert "Cards mit Änderungen: 1" in out
        assert "Adds:    2" in out
        assert "Deletes: 1" in out
        assert "--- a.json" in out
        # b.json hat keine Änderungen → nicht im Detail-Block
        assert "--- b.json" not in out

    def test_summary_no_changes_message(self) -> None:
        plans = [SyncPlan(card_path=Path("x.json"), card_type="vendor")]
        out = format_summary(plans)
        assert "Alle Karten sind synchron" in out
