"""Tests fuer den Card-First-Vertrag (Phase 4)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.model_utils import (  # noqa: E402
    CARD_DIR,
    enforce_card_first,
    resolve_canonical_model_id,
)


@pytest.fixture
def isolated_card_dir(monkeypatch, tmp_path):
    """CARD_DIR auf tmp_path umlenken, damit Tests keine echten Karten anlegen."""
    monkeypatch.setattr("utils.model_utils.CARD_DIR", tmp_path)
    monkeypatch.setattr("utils.model_card_io.CARD_DIR", tmp_path)
    yield tmp_path


def test_existing_card_returns_has_card_true(isolated_card_dir, caplog):
    """Wenn eine Card existiert, gibt enforce_card_first (canonical, True) zurueck."""
    canonical = "claude-haiku-4-5-20251001"
    (isolated_card_dir / f"{canonical}.json").write_text(
        json.dumps({"model_id": canonical, "display_name": "Haiku"}),
        encoding="utf-8",
    )

    with caplog.at_level("WARNING"):
        canonical_out, has_card = enforce_card_first(canonical)

    assert canonical_out == canonical
    assert has_card is True
    assert not any("Card-First-Vertrag" in rec.message for rec in caplog.records)


def test_missing_card_creates_placeholder_and_warns(isolated_card_dir, caplog):
    """Wenn keine Card existiert, wird ensure_card() aufgerufen und WARNING geloggt."""
    model = "unbekanntes-test-modell"
    with caplog.at_level("WARNING"):
        canonical_out, has_card = enforce_card_first(model)

    # resolve_canonical_model_id nutzt _safe_name-Fallback: "unbekanntes-test-modell"
    assert canonical_out == "unbekanntes-test-modell"
    assert has_card is False

    # ensure_card hat die Platzhalter-Card angelegt
    expected_path = isolated_card_dir / "unbekanntes-test-modell.json"
    assert expected_path.exists()
    data = json.loads(expected_path.read_text(encoding="utf-8"))
    assert data["model_id"] == "unbekanntes-test-modell"
    assert data["card_status"] == "draft"

    # WARNING wurde geloggt (kein Hard-Fail)
    warnings = [rec for rec in caplog.records if rec.levelname == "WARNING"]
    assert any("Card-First-Vertrag" in rec.message for rec in warnings)


def test_idempotent_when_called_twice(isolated_card_dir):
    """Zweiter Aufruf nach Card-Erstellung muss has_card=True liefern."""
    model = "wiederholtes-test-modell"
    _canonical, has_card_first = enforce_card_first(model)
    assert has_card_first is False

    _canonical, has_card_second = enforce_card_first(model)
    assert has_card_second is True


def test_empty_input_returns_empty(isolated_card_dir):
    """Leere/None-Eingabe durchlaufen unveraendert."""
    assert enforce_card_first("") == ("", False)
    assert enforce_card_first(None) == (None, False)  # type: ignore[arg-type]


def test_uses_resolve_canonical_model_id_pipeline(isolated_card_dir):
    """enforce_card_first nutzt die resolve_canonical_model_id-Pipeline (hf.co strip)."""
    model = "hf.co/bartowski/Foo-Base:Q4_K_M"
    canonical, has_card = enforce_card_first(model)

    # hf.co/AUTHOR/-Prefix wird gestrippt; Doppelpunkt/Punkt werden zu Underscore
    assert canonical == resolve_canonical_model_id(model)
    assert has_card is False  # keine Card vorhanden → Platzhalter angelegt
    assert (isolated_card_dir / f"{canonical}.json").exists()
