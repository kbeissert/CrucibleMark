"""Tests für die Tri-State-Semantik von ``supports_tool_use``.

Siehe Plan: ``scripts/legacy/migrate_supports_tool_use_tri_state.py`` und
``utils/model_utils.normalize_supports_tool_use``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from utils.model_utils import (
    SUPPORT_TOOL_USE_UNTESTED,
    normalize_supports_tool_use,
    update_model_card_tooluse_fields,
)


# ---------------------------------------------------------------------------
# normalize_supports_tool_use
# ---------------------------------------------------------------------------


class TestNormalizeSupportsToolUse:
    @pytest.mark.parametrize("value", [True])
    def test_true_passes_through(self, value):
        assert normalize_supports_tool_use(value) is True

    @pytest.mark.parametrize("value", [False])
    def test_false_passes_through(self, value):
        assert normalize_supports_tool_use(value) is False

    @pytest.mark.parametrize(
        "value",
        ["untested", "UNTESTED", " Untested ", "UNTESTED"],
    )
    def test_string_untested_normalized(self, value):
        assert normalize_supports_tool_use(value) == "untested"

    @pytest.mark.parametrize("value", [None, "false-ish", 42, [], {}])
    def test_unknown_values_become_untested(self, value):
        assert normalize_supports_tool_use(value) == "untested"


# ---------------------------------------------------------------------------
# update_model_card_tooluse_fields
# ---------------------------------------------------------------------------


class TestUpdateModelCardTooluseFields:
    def _write_card(self, tmp_path: Path, name: str, payload: dict) -> Path:
        card = tmp_path / f"{name}.json"
        card.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return card

    def test_true_sets_field_and_tested_at(self, tmp_path, monkeypatch):
        from utils import model_utils

        card = self._write_card(
            tmp_path,
            "test-model",
            {"model_id": "test-model", "display_name": "Test"},
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        assert update_model_card_tooluse_fields(
            "test-model", True, "2026-06-03T11:00:00Z"
        ) is True
        data = json.loads(card.read_text(encoding="utf-8"))
        assert data["supports_tool_use"] is True
        # v4.10.16: nested in tooluse_runs.test-model
        assert data["tooluse_runs"]["test-model"]["tested_at"] == "2026-06-03T11:00:00Z"

    def test_false_sets_field_and_tested_at(self, tmp_path, monkeypatch):
        from utils import model_utils

        card = self._write_card(
            tmp_path,
            "test-model",
            {"model_id": "test-model", "display_name": "Test"},
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        assert update_model_card_tooluse_fields(
            "test-model", False, "2026-06-03T11:00:00Z"
        ) is True
        data = json.loads(card.read_text(encoding="utf-8"))
        assert data["supports_tool_use"] is False
        assert data["tooluse_runs"]["test-model"]["tested_at"] == "2026-06-03T11:00:00Z"

    def test_untested_sets_string_and_removes_tested_at(self, tmp_path, monkeypatch):
        from utils import model_utils

        card = self._write_card(
            tmp_path,
            "test-model",
            {
                "model_id": "test-model",
                "display_name": "Test",
                "supports_tool_use": True,  # wird überschrieben
                "tooluse_runs": {
                    "test-model": {"tested_at": "2026-05-01T00:00:00Z"},
                },
            },
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        assert update_model_card_tooluse_fields("test-model", "untested", None) is True
        data = json.loads(card.read_text(encoding="utf-8"))
        assert data["supports_tool_use"] == "untested"
        # Profil-spezifischer Eintrag entfernt
        assert "test-model" not in data.get("tooluse_runs", {})

    def test_dual_profile_persistence(self, tmp_path, monkeypatch):
        """Regression: zwei Profile (Standard + Thinking) derselben Card dürfen
        sich nicht überschreiben (v4.10.16)."""
        from utils import model_utils

        # Card mit model_id=Basis, profil-sharing via card_model_id-redirect
        card = self._write_card(
            tmp_path,
            "qwen3_6-27B--VSPK",
            {"model_id": "qwen3_6-27B", "display_name": "Qwen3.6 27B"},
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        # Run 1: Standard-Profil
        update_model_card_tooluse_fields(
            model_id="qwen3_6-27B",
            profile_id="qwen3_6-27B",
            supports_tool_use=True,
            tested_at="2026-07-10T08:00:00Z",
            p1_score=72.5,
            p2_score=56.7,
        )
        # Run 2: Thinking-Profil (anderer profile_id auf selbe Card)
        update_model_card_tooluse_fields(
            model_id="qwen3_6-27B",
            profile_id="qwen3_6-27B-thinking",
            supports_tool_use=True,
            tested_at="2026-07-10T09:00:00Z",
            p1_score=19.17,
            p2_score=22.5,
        )

        data = json.loads(card.read_text(encoding="utf-8"))
        runs = data["tooluse_runs"]
        # Beide Einträge并存
        assert runs["qwen3_6-27B"]["score_p1"] == 72.5
        assert runs["qwen3_6-27B"]["tested_at"] == "2026-07-10T08:00:00Z"
        assert runs["qwen3_6-27B-thinking"]["score_p1"] == 19.17
        assert runs["qwen3_6-27B-thinking"]["tested_at"] == "2026-07-10T09:00:00Z"

    def test_preserve_supports_tool_use_keeps_capability(self, tmp_path, monkeypatch):
        """Regression: Path B darf Capability-Flag (manuell/auto-gesetzt) nicht
        überschreiben. Mock-Run mit p1=0 darf NICHT aus true → false setzen."""
        from utils import model_utils

        card = self._write_card(
            tmp_path,
            "openai_gpt-oss-20b",
            {
                "model_id": "openai/gpt-oss-20b",
                "display_name": "GPT-OSS 20B",
                "supports_tool_use": True,  # manuell/auto-gesetzt, Capability
            },
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        # Path B: Mock-Run, p1=0, preserve=True → Capability bleibt erhalten
        update_model_card_tooluse_fields(
            model_id="openai/gpt-oss-20b",
            profile_id="openai/gpt-oss-20b",
            supports_tool_use="untested",  # dummy-Wert, wird durch preserve=True ignoriert
            tested_at="2026-07-10T07:21:11Z",
            p1_score=0.0,
            p2_score=0.0,
            preserve_supports_tool_use=True,
        )

        data = json.loads(card.read_text(encoding="utf-8"))
        # Capability bleibt unverändert
        assert data["supports_tool_use"] is True
        # tooluse_runs-Eintrag wurde aber geschrieben
        assert data["tooluse_runs"]["openai/gpt-oss-20b"]["tested_at"] == "2026-07-10T07:21:11Z"
        assert data["tooluse_runs"]["openai/gpt-oss-20b"]["score_p1"] == 0.0

    def test_preserve_false_keeps_capability(self, tmp_path, monkeypatch):
        """Capability=False wird ebenfalls respektiert."""
        from utils import model_utils

        card = self._write_card(
            tmp_path,
            "deepseek-r1-distill-qwen-32b",
            {
                "model_id": "deepseek-r1-distill-qwen-32b",
                "supports_tool_use": False,
            },
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        update_model_card_tooluse_fields(
            model_id="deepseek-r1-distill-qwen-32b",
            supports_tool_use="untested",
            tested_at="2026-07-10T07:21:11Z",
            p1_score=0.0,
            preserve_supports_tool_use=True,
        )

        data = json.loads(card.read_text(encoding="utf-8"))
        assert data["supports_tool_use"] is False

    def test_no_preserve_overwrites_capability(self, tmp_path, monkeypatch):
        """Default-Verhalten (Path A finalize_model) überschreibt weiterhin."""
        from utils import model_utils

        card = self._write_card(
            tmp_path,
            "test-model",
            {
                "model_id": "test-model",
                "supports_tool_use": True,  # alter Wert
            },
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        # Path A: finalize_model setzt nach Test-Result, kein preserve
        update_model_card_tooluse_fields(
            model_id="test-model",
            supports_tool_use=False,  # Test zeigte: kein Tool-Use
            tested_at="2026-07-10T08:00:00Z",
            p1_score=0.0,
        )

        data = json.loads(card.read_text(encoding="utf-8"))
        # Capability wurde überschrieben (Path A emuliert empirische Verifikation)
        assert data["supports_tool_use"] is False

    # --- Konditionaler Flat-Field-Writer (v4.10.17) ---

    def test_migrated_card_no_flat_recreation(self, tmp_path, monkeypatch):
        """Regression: migrierte Cards (flache Felder entfernt) dürfen flache
        Felder NICHT re-kriegen beim nächsten Write (v4.10.17)."""
        from utils import model_utils

        # Card wurde migriert: hat tooluse_runs, keine flachen Felder
        card = self._write_card(
            tmp_path,
            "test-model",
            {
                "model_id": "test-model",
                "supports_tool_use": True,
                "tooluse_runs": {
                    "test-model": {"tested_at": "2026-06-01T00:00:00Z", "score_p1": 50.0},
                },
                # KEINE tooluse_tested_at / tooluse_score_p1 / tooluse_score_p2
            },
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        update_model_card_tooluse_fields(
            model_id="test-model",
            supports_tool_use=True,
            tested_at="2026-07-10T08:00:00Z",
            p1_score=72.5,
            p2_score=56.7,
        )

        data = json.loads(card.read_text(encoding="utf-8"))
        # Nested wurde aktualisiert
        assert data["tooluse_runs"]["test-model"]["tested_at"] == "2026-07-10T08:00:00Z"
        assert data["tooluse_runs"]["test-model"]["score_p1"] == 72.5
        # Flache Felder wurden NICHT re-kreiert
        assert "tooluse_tested_at" not in data
        assert "tooluse_score_p1" not in data
        assert "tooluse_score_p2" not in data

    def test_unmigrated_card_flat_stays_in_sync(self, tmp_path, monkeypatch):
        """Cards die noch flache Felder haben, werden weiterhin synchron gehalten."""
        from utils import model_utils

        card = self._write_card(
            tmp_path,
            "test-model",
            {
                "model_id": "test-model",
                "supports_tool_use": True,
                "tooluse_tested_at": "2026-06-01T00:00:00Z",
                "tooluse_score_p1": 50.0,
                "tooluse_score_p2": 40.0,
            },
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        update_model_card_tooluse_fields(
            model_id="test-model",
            supports_tool_use=True,
            tested_at="2026-07-10T08:00:00Z",
            p1_score=72.5,
            p2_score=56.7,
        )

        data = json.loads(card.read_text(encoding="utf-8"))
        # Nested wurde geschrieben
        assert data["tooluse_runs"]["test-model"]["score_p1"] == 72.5
        # Flache Felder wurden synchronisiert (bleiben erhalten)
        assert data["tooluse_tested_at"] == "2026-07-10T08:00:00Z"
        assert data["tooluse_score_p1"] == 72.5
        assert data["tooluse_score_p2"] == 56.7

    def test_fresh_card_no_flat_creation(self, tmp_path, monkeypatch):
        """Neue Cards (nie flache Felder gehabt) bekommen auch keine."""
        from utils import model_utils

        card = self._write_card(
            tmp_path,
            "test-model",
            {"model_id": "test-model", "supports_tool_use": True},
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        update_model_card_tooluse_fields(
            model_id="test-model",
            supports_tool_use=True,
            tested_at="2026-07-10T08:00:00Z",
            p1_score=72.5,
        )

        data = json.loads(card.read_text(encoding="utf-8"))
        # Nested wurde geschrieben
        assert data["tooluse_runs"]["test-model"]["score_p1"] == 72.5
        # Flache Felder wurden NICHT kreiert
        assert "tooluse_tested_at" not in data
        assert "tooluse_score_p1" not in data

    def test_invalid_value_raises(self, tmp_path, monkeypatch):
        from utils import model_utils

        card = self._write_card(tmp_path, "test-model", {"display_name": "Test"})
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        with pytest.raises(ValueError, match="supports_tool_use"):
            update_model_card_tooluse_fields("test-model", "invalid", None)

    def test_no_card_returns_false(self, tmp_path, monkeypatch):
        from utils import model_utils

        missing = tmp_path / "does-not-exist.json"
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: missing)

        assert update_model_card_tooluse_fields("missing-model", True, "2026-06-03") is False


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------


def test_untested_constant_is_string():
    assert SUPPORT_TOOL_USE_UNTESTED == "untested"
    assert isinstance(SUPPORT_TOOL_USE_UNTESTED, str)
