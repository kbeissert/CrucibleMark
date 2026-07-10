"""Regression-Tests fuer scripts/legacy/migrate_architecture_tags.py.

Insbesondere der Bug, dass das Walrus-Pattern `data := json.loads(...)` die
in-Memory normalisierten Tags ueberschrieb und die Karte un-migriert
zurueckschrieb (Beispiel-Bug, der am 2026-06-10 gefunden wurde).
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_MIGRATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts" / "legacy" / "migrate_architecture_tags.py"
)
_spec = importlib.util.spec_from_file_location(
    "migrate_architecture_tags", _MIGRATE_PATH
)
mig_mod = importlib.util.module_from_spec(_spec)
sys.modules["migrate_architecture_tags"] = mig_mod
_spec.loader.exec_module(mig_mod)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _make_card(tmp_path: Path, tags: list[str], model_id: str = "test-model") -> Path:
    p = tmp_path / f"{model_id}.json"
    p.write_text(
        json.dumps(
            {
                "model_id": model_id,
                "architecture_tags": tags,
                "input_modalities": ["text"],
                "output_modalities": ["text"],
            }
        ),
        encoding="utf-8",
    )
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_long_context_is_migrated_to_kebab_case(tmp_path):
    """'Long Context' (DEPRECATED) wird zu 'Long-Context' migriert UND auf Disk geschrieben."""
    p = _make_card(tmp_path, ["General", "Long Context"])
    report = mig_mod.migrate_card(p)
    # Report enthaelt die normalisierten Daten
    assert "data" in report, "Report muss normalisierte Daten enthalten"
    assert "Long-Context" in report["data"]["architecture_tags"]
    assert "Long Context" not in report["data"]["architecture_tags"]


def test_normalized_data_actually_written_to_disk(tmp_path, monkeypatch):
    """REGRESSION: Disk-Datei enthaelt nach main()-Lauf die normalisierten Tags.

    Bug vor 2026-06-10: Walrus-Pattern `data := json.loads(...)` las die
    Originaldatei erneut und ueberschrieb die in-Memory normalisierten Tags.
    """
    # monkeypatche CARDS_DIR, damit main() nur auf tmp_path arbeitet
    monkeypatch.setattr(mig_mod, "CARDS_DIR", tmp_path)
    p = _make_card(tmp_path, ["General", "Long Context", "MoE"])

    rc = mig_mod.main(dry_run=False)
    assert rc == 0

    written = json.loads(p.read_text(encoding="utf-8"))
    tags = written["architecture_tags"]

    # 'Long Context' -> 'Long-Context', 'MoE' -> entfernt
    assert "Long-Context" in tags, f"Long-Context fehlt in {tags}"
    assert "Long Context" not in tags, f"Long Context nicht migriert: {tags}"
    assert "MoE" not in tags, f"MoE nicht entfernt: {tags}"
    assert "General" in tags


def test_dry_run_does_not_write(tmp_path, monkeypatch):
    """--dry-run aequivalent: main(dry_run=True) schreibt KEINE Dateien."""
    monkeypatch.setattr(mig_mod, "CARDS_DIR", tmp_path)
    p = _make_card(tmp_path, ["Long Context"])
    original = p.read_text(encoding="utf-8")

    mig_mod.main(dry_run=True)
    after = p.read_text(encoding="utf-8")
    assert original == after, "dry_run darf die Datei nicht veraendern"


def test_already_normalized_card_is_unchanged(tmp_path, monkeypatch):
    """Bereits normalisierte Karten werden nicht erneut geschrieben."""
    monkeypatch.setattr(mig_mod, "CARDS_DIR", tmp_path)
    p = _make_card(tmp_path, ["General", "Long-Context"])
    mtime_before = p.stat().st_mtime_ns

    # Kurze Pause, damit mtime sich unterscheiden kann
    import time
    time.sleep(0.01)

    mig_mod.main(dry_run=False)
    mtime_after = p.stat().st_mtime_ns
    # Wenn keine Aenderung, sollte die Datei nicht neu geschrieben worden sein
    assert mtime_before == mtime_after, "Karte ohne Aenderungen wurde geschrieben"


def test_modalities_backfilled_if_missing(tmp_path, monkeypatch):
    """Fehlende input/output_modalities werden heuristisch ergaenzt."""
    monkeypatch.setattr(mig_mod, "CARDS_DIR", tmp_path)
    p = tmp_path / "vision-model.json"
    p.write_text(
        json.dumps(
            {
                "model_id": "vision-model",
                "architecture_tags": ["Vision-Capable"],
                # input/output_modalities FEHLT absichtlich
            }
        ),
        encoding="utf-8",
    )

    mig_mod.main(dry_run=False)
    written = json.loads(p.read_text(encoding="utf-8"))
    assert "input_modalities" in written
    assert "image" in written["input_modalities"]
