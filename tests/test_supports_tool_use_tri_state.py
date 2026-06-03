"""Tests für die Tri-State-Semantik von ``supports_tool_use``.

Siehe Plan: ``scripts/dev/migrate_supports_tool_use_tri_state.py`` und
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

        card = self._write_card(tmp_path, "test-model", {"display_name": "Test"})
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        assert update_model_card_tooluse_fields(
            "test-model", True, "2026-06-03T11:00:00Z"
        ) is True
        data = json.loads(card.read_text(encoding="utf-8"))
        assert data["supports_tool_use"] is True
        assert data["tooluse_tested_at"] == "2026-06-03T11:00:00Z"

    def test_false_sets_field_and_tested_at(self, tmp_path, monkeypatch):
        from utils import model_utils

        card = self._write_card(tmp_path, "test-model", {"display_name": "Test"})
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        assert update_model_card_tooluse_fields(
            "test-model", False, "2026-06-03T11:00:00Z"
        ) is True
        data = json.loads(card.read_text(encoding="utf-8"))
        assert data["supports_tool_use"] is False
        assert data["tooluse_tested_at"] == "2026-06-03T11:00:00Z"

    def test_untested_sets_string_and_removes_tested_at(self, tmp_path, monkeypatch):
        from utils import model_utils

        card = self._write_card(
            tmp_path,
            "test-model",
            {
                "display_name": "Test",
                "supports_tool_use": True,  # wird überschrieben
                "tooluse_tested_at": "2026-05-01T00:00:00Z",
            },
        )
        monkeypatch.setattr(model_utils, "_find_card", lambda *a, **kw: card)

        assert update_model_card_tooluse_fields("test-model", "untested", None) is True
        data = json.loads(card.read_text(encoding="utf-8"))
        assert data["supports_tool_use"] == "untested"
        assert "tooluse_tested_at" not in data

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
