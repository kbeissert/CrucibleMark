"""Tests fuer den Card-First-Probe-Trigger in ``_read_card_probe_state``.

Pitfall-Diagnose 2026-06-10: Draft-Cards aus ``ensure_card()`` haben
``thinking_probe_detected: null`` (explizit auf None gesetzt), nicht
"Feld fehlt komplett". ``not in loaded`` wuerde das uebersehen und
die Probe ueberspringen — die Folge war: Gemma-4-12B-Modelle bekamen
kein 5x-Reasoning-Budget, weil Probe nie lief.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.core.unified_runner import UnifiedBenchmarkRunner  # noqa: E402


# --- Test-Helpers ----------------------------------------------------------


def _make_runner() -> UnifiedBenchmarkRunner:
    """Erzeugt einen Runner ohne Konstruktor (reine Helper-Tests)."""
    return UnifiedBenchmarkRunner.__new__(UnifiedBenchmarkRunner)


def _write_card(card_dir: Path, model_id: str, payload: dict) -> Path:
    """Schreibt eine Test-Card in ``card_dir`` und gibt den Pfad zurueck."""
    card_path = card_dir / f"{model_id}.json"
    card_path.write_text(
        json.dumps({"model_id": model_id, **payload}),
        encoding="utf-8",
    )
    return card_path


# --- _read_card_probe_state Tests ------------------------------------------


class TestReadCardProbeState:
    """_read_card_probe_state triggert Probe bei null/missing, nicht bei True/False."""

    def test_null_probe_field_triggers_reprobe(self, tmp_path: Path) -> None:
        """Draft-Card mit ``thinking_probe_detected: null`` MUSS Probe triggern.

        Regression-Test fuer 2026-06-10: vorher lieferte needs_probe=False,
        weil ``"thinking_probe_detected" not in loaded`` den existierenden
        Null-Wert nicht als fehlend erkannte.
        """
        runner = _make_runner()
        card_path = _write_card(tmp_path, "gemma-4-12b-it-ud-q6_k_xl", {
            "thinking_probe_detected": None,
            "thinking_probe_evidence": None,
            "thinking_probe_confidence": None,
            "thinking_probe_at": None,
            "card_status": "draft",
        })

        needs_probe, card_loaded, canonical = runner._read_card_probe_state(
            "gemma-4-12b-it-ud-q6_k_xl", card_path,
        )

        assert needs_probe is True, (
            "Draft-Card mit thinking_probe_detected=null MUSS Probe triggern"
        )
        assert card_loaded is True
        assert canonical == "gemma-4-12b-it-ud-q6_k_xl"

    def test_missing_probe_field_triggers_reprobe(self, tmp_path: Path) -> None:
        """Card OHNE ``thinking_probe_detected``-Feld (Key fehlt komplett)
        muss ebenfalls Probe triggern — bleibt bestehendes Verhalten."""
        runner = _make_runner()
        card_path = _write_card(tmp_path, "test-model", {
            "display_name": "Test",
            "card_status": "draft",
        })
        # Ensure the key is genuinely absent
        data = json.loads(card_path.read_text(encoding="utf-8"))
        assert "thinking_probe_detected" not in data

        needs_probe, card_loaded, canonical = runner._read_card_probe_state(
            "test-model", card_path,
        )

        assert needs_probe is True
        assert card_loaded is True
        assert canonical == "test-model"

    def test_true_probe_field_does_not_trigger_reprobe(self, tmp_path: Path) -> None:
        """Card mit ``thinking_probe_detected: true`` → KEIN Re-Probe noetig."""
        runner = _make_runner()
        card_path = _write_card(tmp_path, "qwen3-4b", {
            "thinking_probe_detected": True,
            "thinking_probe_evidence": "<think>...</think>",
            "thinking_probe_confidence": "high",
            "thinking_probe_at": "2026-06-01T00:00:00Z",
        })

        needs_probe, card_loaded, canonical = runner._read_card_probe_state(
            "qwen3-4b", card_path,
        )

        assert needs_probe is False, (
            "Card mit Probe=true darf keinen Re-Probe ausloesen"
        )
        assert card_loaded is True
        assert canonical == "qwen3-4b"

    def test_false_probe_field_does_not_trigger_reprobe(self, tmp_path: Path) -> None:
        """Card mit ``thinking_probe_detected: false`` → KEIN Re-Probe noetig.

        Wichtig: False ist ein expliziter Wert (nicht None) und signalisiert
        "Probe wurde ausgefuehrt, kein Thinking erkannt". Respektiere das
        Ergebnis, um Endlos-Probes zu vermeiden.
        """
        runner = _make_runner()
        card_path = _write_card(tmp_path, "gemma-3-12b-it", {
            "thinking_probe_detected": False,
            "thinking_probe_evidence": "No CoT signals found",
            "thinking_probe_confidence": "low",
            "thinking_probe_at": "2026-05-15T00:00:00Z",
        })

        needs_probe, card_loaded, canonical = runner._read_card_probe_state(
            "gemma-3-12b-it", card_path,
        )

        assert needs_probe is False, (
            "Card mit Probe=false darf keinen Re-Probe ausloesen "
            "(sonst Endlos-Probe-Loop)"
        )
        assert card_loaded is True
        assert canonical == "gemma-3-12b-it"

    def test_missing_card_file_triggers_probe(self, tmp_path: Path) -> None:
        """Wenn die Card-Datei nicht existiert, MUSS Probe getriggert werden."""
        runner = _make_runner()
        nonexistent = tmp_path / "nope.json"
        assert not nonexistent.exists()

        needs_probe, card_loaded, canonical = runner._read_card_probe_state(
            "nope-model", nonexistent,
        )

        assert needs_probe is True
        assert card_loaded is False
        assert canonical == "nope-model"  # Fallback auf Input

    def test_corrupt_card_triggers_probe_safely(self, tmp_path: Path) -> None:
        """Defekte Card (kein valides JSON) wird nicht gecrasht — Probe laeuft."""
        runner = _make_runner()
        corrupt = tmp_path / "corrupt.json"
        corrupt.write_text("{ this is not valid json", encoding="utf-8")

        needs_probe, card_loaded, canonical = runner._read_card_probe_state(
            "corrupt-model", corrupt,
        )

        # Bei Lesefehler: needs_probe=True (sicherer Default),
        # card_loaded=False (wird spaeter durch ensure_card() neu angelegt)
        assert needs_probe is True
        assert card_loaded is False
        assert canonical == "corrupt-model"

    def test_canonical_model_id_from_card_glob_fallback(self, tmp_path: Path) -> None:
        """Wenn die Card eine andere model_id enthaelt (glob-Fallback), wird
        diese als canonical zurueckgegeben."""
        runner = _make_runner()
        # Card gespeichert unter sicherem Namen, aber model_id weicht ab
        card_path = _write_card(tmp_path, "gemma-4-12b-it-ud-q6_k_xl", {
            "model_id": "gemma-4-12b-it-ud-q6_k_xl",
            "thinking_probe_detected": True,
        })

        needs_probe, card_loaded, canonical = runner._read_card_probe_state(
            "gemma-4-12b-it-ud-q6_k_xl", card_path,
        )

        assert needs_probe is False
        assert card_loaded is True
        assert canonical == "gemma-4-12b-it-ud-q6_k_xl"
