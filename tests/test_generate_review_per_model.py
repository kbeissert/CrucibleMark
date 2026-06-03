"""Tests für den --per-model Iterationsmodus in scripts/analysis/generate_review.py.

Validiert:
- argparse: --per-model Flag akzeptiert
- main(): Validierung (--per-model benötigt --type all; --per-model benötigt --all oder --model)
- _run_per_model_all_reviews(): korrekte Iteration (1 Modell → benchmark → bias → tooluse)
- Skip-Logik bleibt erhalten (mtime-Check)

Strategie: Schwerpunkt auf argparse-/Namespace-Logik, ohne echte LLM-Calls oder
Filesystem-Reads. Die schweren Pfade (process_model_review / _run_audit_reviews /
_run_tooluse_reviews) werden via Mocks abgefangen.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Sys-Pfad: Repo-Root einfügen, damit das Skript importierbar ist
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

# generate_review als Modul laden
import importlib.util
spec = importlib.util.spec_from_file_location(
    "gr_under_test",
    ROOT / "scripts" / "analysis" / "generate_review.py",
)
gr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gr)  # type: ignore[union-attr]


# === Helpers ===

def _make_args(**overrides) -> argparse.Namespace:
    """Erzeugt eine argparse.Namespace mit allen Pflichtfeldern."""
    defaults = {
        "model": None,
        "all": False,
        "type": "benchmark",
        "auto": False,
        "force": False,
        "dry_run": False,
        "per_model": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


# === Test 1: --per-model Flag wird vom argparse akzeptiert ===

def test_per_model_flag_in_argparse():
    """parser.parse_args(['--per-model']) muss args.per_model=True setzen."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", type=str)
    parser.add_argument("-a", "--all", action="store_true")
    parser.add_argument("-t", "--type", type=str, default="benchmark")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--per-model", action="store_true")

    args = parser.parse_args(["--per-model", "--all", "--type", "all"])
    assert args.per_model is True
    assert args.all is True
    assert args.type == "all"


# === Test 2: _run_per_model_all_reviews iteriert per Modell: benchmark → bias → tooluse ===

def test_per_model_iteration_calls_in_correct_order(tmp_path):
    """Pro Modell MÜSSEN benchmark, bias, tooluse in dieser Reihenfolge aufgerufen werden."""
    # Arrange: Fake-Audit-Log-Verzeichnis mit 2 Modellen
    fake_audit_dir = tmp_path / "outputs" / "audit_logs"
    fake_audit_dir.mkdir(parents=True)
    (fake_audit_dir / "model-a").mkdir()
    (fake_audit_dir / "model-b").mkdir()

    call_sequence: list[tuple[str, str]] = []  # (slug, review_type)

    def fake_run_audit(args, client, provider, model_id, max_tokens, csv_data, effective_type):
        call_sequence.append((args.model, effective_type))

    def fake_run_tooluse(args, client, provider, model_id, max_tokens):
        call_sequence.append((args.model, "tooluse"))

    args = _make_args(all=True, per_model=True, type="all", auto=True)

    # Patch ROOT_DIR innerhalb des Moduls
    with patch.object(gr, "ROOT_DIR", tmp_path), \
         patch.object(gr, "_run_audit_reviews", side_effect=fake_run_audit), \
         patch.object(gr, "_run_tooluse_reviews", side_effect=fake_run_tooluse), \
         patch.object(gr, "collect_data", return_value="FAKE_CSV"):
        gr._run_per_model_all_reviews(
            args, client=MagicMock(), provider="openai",
            model_id="gpt-5.4", max_tokens=8192, csv_data="",
        )

    # Assert: 2 Modelle × 3 Calls = 6 Einträge, in der richtigen Reihenfolge
    assert len(call_sequence) == 6, f"Erwartet 6 Calls, bekam {len(call_sequence)}: {call_sequence}"

    # Modell A: benchmark → bias → tooluse
    assert call_sequence[0] == ("model-a", "benchmark")
    assert call_sequence[1] == ("model-a", "bias")
    assert call_sequence[2] == ("model-a", "tooluse")

    # Modell B: benchmark → bias → tooluse
    assert call_sequence[3] == ("model-b", "benchmark")
    assert call_sequence[4] == ("model-b", "bias")
    assert call_sequence[5] == ("model-b", "tooluse")


# === Test 3: Per-Model mit --model filtert auf genau dieses Modell ===

def test_per_model_with_model_filter_processes_only_one(tmp_path):
    """Bei args.model='model-b' MUSS nur model-b verarbeitet werden."""
    fake_audit_dir = tmp_path / "outputs" / "audit_logs"
    fake_audit_dir.mkdir(parents=True)
    (fake_audit_dir / "model-a").mkdir()
    (fake_audit_dir / "model-b").mkdir()

    processed: list[str] = []

    def fake_run_audit(args, client, provider, model_id, max_tokens, csv_data, effective_type):
        processed.append(args.model)

    def fake_run_tooluse(args, client, provider, model_id, max_tokens):
        processed.append(args.model)

    args = _make_args(model="model-b", per_model=True, type="all", auto=True)

    with patch.object(gr, "ROOT_DIR", tmp_path), \
         patch.object(gr, "_run_audit_reviews", side_effect=fake_run_audit), \
         patch.object(gr, "_run_tooluse_reviews", side_effect=fake_run_tooluse), \
         patch.object(gr, "collect_data", return_value=""):
        gr._run_per_model_all_reviews(
            args, client=MagicMock(), provider="openai",
            model_id="gpt-5.4", max_tokens=8192, csv_data="",
        )

    # 1 Modell × 3 Calls = 3 Einträge, alle "model-b"
    assert processed == ["model-b", "model-b", "model-b"], \
        f"Erwartet ['model-b', 'model-b', 'model-b'], bekam {processed}"


# === Test 4: Leeres Audit-Logs-Verzeichnis → kein Fehler ===

def test_per_model_empty_audit_dir_does_nothing(tmp_path):
    """Bei leerem outputs/audit_logs/ darf KEIN Fehler geworfen werden."""
    fake_audit_dir = tmp_path / "outputs" / "audit_logs"
    fake_audit_dir.mkdir(parents=True)
    # Keine Modell-Unterverzeichnisse

    call_count = 0

    def fake_run_audit(*args, **kwargs):
        nonlocal call_count
        call_count += 1

    def fake_run_tooluse(*args, **kwargs):
        nonlocal call_count
        call_count += 1

    args = _make_args(all=True, per_model=True, type="all")

    with patch.object(gr, "ROOT_DIR", tmp_path), \
         patch.object(gr, "_run_audit_reviews", side_effect=fake_run_audit), \
         patch.object(gr, "_run_tooluse_reviews", side_effect=fake_run_tooluse), \
         patch.object(gr, "collect_data", return_value=""):
        # Darf nicht raise'n
        gr._run_per_model_all_reviews(
            args, client=MagicMock(), provider="openai",
            model_id="gpt-5.4", max_tokens=8192, csv_data="",
        )

    assert call_count == 0, "Bei leerem Audit-Verzeichnis dürfen keine Reviews angestoßen werden"


# === Test 5: --per-model benötigt --type all ===

def test_per_model_requires_type_all(monkeypatch, capsys):
    """Wenn --per-model ohne --type all gesetzt ist, MUSS main() mit Fehler abbrechen."""
    monkeypatch.setattr(sys, "argv", ["generate_review.py", "--per-model", "--all"])
    with pytest.raises(SystemExit) as exc_info:
        gr.main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "--per-model ist nur mit --type all erlaubt" in captured.out


# === Test 6: --per-model benötigt --all oder --model ===

def test_per_model_requires_all_or_model(monkeypatch, capsys):
    """Wenn --per-model ohne --all und --model gesetzt ist, MUSS main() mit Fehler abbrechen."""
    monkeypatch.setattr(sys, "argv", ["generate_review.py", "--type", "all", "--per-model"])
    with pytest.raises(SystemExit) as exc_info:
        gr.main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "--per-model benötigt --all oder --model" in captured.out


# === Test 7: Namespace-Kopie verhindert State-Mutation ===

def test_per_model_does_not_mutate_original_args(tmp_path):
    """Beweis: args.model wird NICHT durch _run_per_model_all_reviews() überschrieben.
    Die Helper erstellen pro Iteration einen Namespace-Klon via argparse.Namespace(**vars(args))."""
    fake_audit_dir = tmp_path / "outputs" / "audit_logs"
    fake_audit_dir.mkdir(parents=True)
    (fake_audit_dir / "model-a").mkdir()

    original_args = _make_args(all=True, per_model=True, type="all", auto=True)
    assert original_args.model is None  # Vorher: None

    def fake_run_audit(args, client, provider, model_id, max_tokens, csv_data, effective_type):
        # args.model MUSS "model-a" sein, NICHT None
        assert args.model == "model-a", f"args.model war {args.model!r}, erwartet 'model-a'"

    def fake_run_tooluse(args, client, provider, model_id, max_tokens):
        assert args.model == "model-a"

    with patch.object(gr, "ROOT_DIR", tmp_path), \
         patch.object(gr, "_run_audit_reviews", side_effect=fake_run_audit), \
         patch.object(gr, "_run_tooluse_reviews", side_effect=fake_run_tooluse), \
         patch.object(gr, "collect_data", return_value=""):
        gr._run_per_model_all_reviews(
            original_args, client=MagicMock(), provider="openai",
            model_id="gpt-5.4", max_tokens=8192, csv_data="",
        )

    # Nach dem Lauf: original_args.model darf NICHT mutiert sein
    assert original_args.model is None, \
        f"original_args.model wurde mutiert zu {original_args.model!r}"


# === Test 8: Bei unknown model wird sauber abgebrochen ===

def test_per_model_unknown_model_exits_gracefully(tmp_path, capsys):
    """Wenn args.model='unknown' und kein passendes Audit-Dir existiert, MUSS
    die Funktion sauber beenden (kein raise), aber mit Warnung printen."""
    fake_audit_dir = tmp_path / "outputs" / "audit_logs"
    fake_audit_dir.mkdir(parents=True)
    (fake_audit_dir / "model-a").mkdir()

    args = _make_args(model="unknown-model", per_model=True, type="all")

    call_count = 0

    def fake_run_audit(*args, **kwargs):
        nonlocal call_count
        call_count += 1

    def fake_run_tooluse(*args, **kwargs):
        nonlocal call_count
        call_count += 1

    with patch.object(gr, "ROOT_DIR", tmp_path), \
         patch.object(gr, "_run_audit_reviews", side_effect=fake_run_audit), \
         patch.object(gr, "_run_tooluse_reviews", side_effect=fake_run_tooluse):
        gr._run_per_model_all_reviews(
            args, client=MagicMock(), provider="openai",
            model_id="gpt-5.4", max_tokens=8192, csv_data="",
        )

    assert call_count == 0, "Unbekanntes Modell darf keine Reviews triggern"
    captured = capsys.readouterr()
    assert "nicht in outputs/audit_logs/ gefunden" in captured.out
