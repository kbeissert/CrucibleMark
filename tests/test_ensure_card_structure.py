"""Regression-Tests fuer `scripts/dev/ensure_card_structure.py`.

Deckt den Fix ab, dass `run_for_card()` keine doppelte Base-Card erzeugt,
wenn eine provider-suffixed Card (z.B. ``--VSPK``, ``--SPRK``) existiert.
Siehe Plan: ``.kilo/plans/1783720871265-ensure-card-structure-duplicate-fix.md``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import scripts.dev.ensure_card_structure as ecs
import utils.model_card_io as model_card_io_module
import utils.model_utils


@pytest.fixture
def isolated_card_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Biegt CARDS_DIR (Script) und CARD_DIR (Module) auf tmp_path um."""
    card_dir = tmp_path / "cards"
    card_dir.mkdir()
    monkeypatch.setattr(ecs, "CARDS_DIR", card_dir)
    monkeypatch.setattr(utils.model_utils, "CARD_DIR", card_dir)
    monkeypatch.setattr(model_card_io_module, "CARD_DIR", card_dir)
    return card_dir


def test_run_for_card_does_not_create_duplicate_base_card(
    isolated_card_dir: Path,
) -> None:
    """run_for_card() darf keine Base-Card erstellen, wenn eine suffixed Card existiert."""
    # Suffixed Card mit fehlenden Feldern anlegen
    suffixed = isolated_card_dir / "qwen3_6-27B--VSPK.json"
    suffixed.write_text(json.dumps({"model_id": "qwen3_6-27B"}), encoding="utf-8")

    changed = ecs.run_for_card(suffixed, dry_run=False)

    assert changed is True
    assert suffixed.exists()
    base = isolated_card_dir / "qwen3_6-27B.json"
    assert not base.exists(), f"Duplicate base card created: {base}"
    # model_id-Feld unverändert (Base-ID, kein Suffix)
    data = json.loads(suffixed.read_text(encoding="utf-8"))
    assert data["model_id"] == "qwen3_6-27B"


def test_run_for_card_strips_shortcode_suffix_from_filename(
    isolated_card_dir: Path,
) -> None:
    """Fehlt model_id im JSON, wird der Shortcode-Suffix aus dem Dateinamen gestript."""
    # Kein model_id-Feld → Fallback auf Dateiname
    suffixed = isolated_card_dir / "qwen3_5-9b--SPRK.json"
    suffixed.write_text("{}", encoding="utf-8")

    changed = ecs.run_for_card(suffixed, dry_run=False)

    assert changed is True
    base = isolated_card_dir / "qwen3_5-9b.json"
    assert not base.exists()
    data = json.loads(suffixed.read_text(encoding="utf-8"))
    # model_id aus gestripptem Dateinamen: --SPRK entfernt, erstes "_" → "/"
    # (Rücktransformation von _safe_name-Namespacing)
    assert data["model_id"] == "qwen3/5-9b"


def test_run_for_card_skips_complete_card(isolated_card_dir: Path) -> None:
    """Eine Card ohne fehlende Felder wird nicht angefasst."""
    from utils.card_utils import CARD_FIELD_NAMES

    complete = {f: "x" for f in CARD_FIELD_NAMES}
    card_path = isolated_card_dir / "complete-model.json"
    card_path.write_text(json.dumps(complete), encoding="utf-8")

    changed = ecs.run_for_card(card_path, dry_run=False)

    assert changed is False


def test_run_for_card_dry_run_does_not_write(isolated_card_dir: Path) -> None:
    """--dry-run schreibt nicht, meldet aber fehlende Felder."""
    suffixed = isolated_card_dir / "qwen3_6-27B--VSPK.json"
    suffixed.write_text(json.dumps({"model_id": "qwen3_6-27B"}), encoding="utf-8")
    original = suffixed.read_text(encoding="utf-8")

    changed = ecs.run_for_card(suffixed, dry_run=True)

    assert changed is True
    # Datei unverändert
    assert suffixed.read_text(encoding="utf-8") == original
    base = isolated_card_dir / "qwen3_6-27B.json"
    assert not base.exists()


def test_main_model_finds_suffixed_card_no_duplicate(
    isolated_card_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--model <base-id>` findet eine existierende suffixed Card und patcht in-place."""
    suffixed = isolated_card_dir / "qwen3_6-27B--VSPK.json"
    suffixed.write_text(json.dumps({"model_id": "qwen3_6-27B"}), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["ensure_card_structure.py", "--model", "qwen3_6-27B"])
    rc = ecs.main()
    out = capsys.readouterr().out

    assert rc == 0
    base = isolated_card_dir / "qwen3_6-27B.json"
    assert not base.exists(), f"Duplicate base card created: {base}"
    assert suffixed.exists()
    assert "1 Card(s)" in out


def test_main_model_creates_new_base_card_when_absent(
    isolated_card_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--model <id>` ohne existierende Card erstellt eine neue Base-Card."""
    monkeypatch.setattr(sys, "argv", ["ensure_card_structure.py", "--model", "brand-new-model"])
    rc = ecs.main()
    out = capsys.readouterr().out

    assert rc == 0
    new_card = isolated_card_dir / "brand-new-model.json"
    assert new_card.exists()
    assert "1 Card(s)" in out


def test_main_model_dry_run_finds_suffixed(
    isolated_card_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--model --dry-run` findet suffixed Card (nicht Base-Card-Pfad)."""
    suffixed = isolated_card_dir / "qwen3_6-27B--VSPK.json"
    suffixed.write_text(json.dumps({"model_id": "qwen3_6-27B"}), encoding="utf-8")
    original = suffixed.read_text(encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["ensure_card_structure.py", "--model", "qwen3_6-27B", "--dry-run"])
    rc = ecs.main()
    out = capsys.readouterr().out

    assert rc == 0
    # Nicht geschrieben
    assert suffixed.read_text(encoding="utf-8") == original
    base = isolated_card_dir / "qwen3_6-27B.json"
    assert not base.exists()
    assert "1 Card(s)" in out
