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
import importlib.util  # noqa: E402
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
    """Pro Modell benchmark → bias, dann einmal tooluse für ALLE Modelle am Ende.

    Design-Entscheidung: tooluse_leaderboard.csv enthält Ollama-Format-IDs
    (z.B. "gemma3:12b"), die nicht mit audit_log-Slugs übereinstimmen.
    Daher wird _run_tooluse_reviews einmal am Ende mit model=None aufgerufen,
    nicht pro Modell.
    """
    # Arrange: Fake-Audit-Log-Verzeichnis mit 2 Modellen
    fake_audit_dir = tmp_path / "outputs" / "audit_logs"
    fake_audit_dir.mkdir(parents=True)
    (fake_audit_dir / "model-a").mkdir()
    (fake_audit_dir / "model-b").mkdir()

    call_sequence: list[tuple[str | None, str]] = []  # (slug, review_type)

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

    # Assert: 2 Modelle × 2 Audit-Calls + 1 Tooluse-Call am Ende = 5 Einträge
    assert len(call_sequence) == 5, f"Erwartet 5 Calls, bekam {len(call_sequence)}: {call_sequence}"

    # Modell A: benchmark → bias
    assert call_sequence[0] == ("model-a", "benchmark")
    assert call_sequence[1] == ("model-a", "bias")

    # Modell B: benchmark → bias
    assert call_sequence[2] == ("model-b", "benchmark")
    assert call_sequence[3] == ("model-b", "bias")

    # Tooluse einmal am Ende mit model=None (iteriert alle IDs aus tooluse_leaderboard.csv)
    assert call_sequence[4] == (None, "tooluse")


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

    # 1 Modell × 2 Audit-Calls + 1 Tooluse-Call mit model=None = 3 Einträge
    assert processed == ["model-b", "model-b", None], \
        f"Erwartet ['model-b', 'model-b', None], bekam {processed}"


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
        # Tooluse wird mit model=None aufgerufen (iteriert alle IDs aus tooluse_leaderboard.csv)
        assert args.model is None, f"Tooluse-args.model war {args.model!r}, erwartet None"

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


# === ID-SSoT Tests (Phase 12+13): Audit-Log-Ordner mit roher Schreibweise ===
#
# Sicherstellen, dass Review-Generierungstoleranz fuer safe_name vs. rohe
# Schreibweise gilt. Drei Repro-Szenarien aus dem Bug-Report:
#   - `_run_audit_reviews` mit --model="gpt-5.4" matcht jetzt "gpt-5.4/" (raw)
#   - `_run_tooluse_reviews` nutzt mid (nicht slug) fuer audit_dir
#   - `_run_per_model_all_reviews` sammelt rohe Ordnernamen


def test_audit_review_matches_unsafename_dir(tmp_path):
    """Mit args.model='gpt-5.4' MUSS das Audit-Dir 'gpt-5.4/' (mit Punkt)
    gefunden werden, _safe_name(subdir.name) == safe_target_model."""
    fake_audit = tmp_path / "outputs" / "audit_logs"
    fake_audit.mkdir(parents=True)
    target_dir = fake_audit / "gpt-5.4"  # raw, mit Punkt
    target_dir.mkdir()
    # Mindestens ein Benchmark-Report, sonst skippt der Bench-Filter
    (target_dir / "code_quality_001.md").write_text(
        "## 3. Evaluation\nscore: 1.0\n", encoding="utf-8"
    )

    fake_review = tmp_path / "docs" / "reviews"
    fake_review.mkdir(parents=True)

    visited: list[str] = []

    def fake_process(subdir, *args, **kwargs):
        visited.append(subdir.name)

    args = _make_args(model="gpt-5.4", auto=True, type="benchmark")

    with patch.object(gr, "ROOT_DIR", tmp_path), \
         patch.object(gr, "_ensure_dependencies", return_value={}), \
         patch.object(gr, "process_model_review", side_effect=fake_process):
        gr._run_audit_reviews(
            args, client=MagicMock(), provider="openai", model_id="gpt-5.4",
            max_tokens=8192, csv_data="", effective_type="benchmark",
        )

    assert visited == ["gpt-5.4"], (
        f"Erwartet dass 'gpt-5.4/' trotz roher Schreibweise gefunden wird, "
        f"bekam {visited}"
    )


def test_tooluse_review_uses_raw_mid_for_audit_dir(tmp_path, monkeypatch):
    """_run_tooluse_reviews MUSS audit_dir aus mid (rohe ID) bauen, nicht aus slug.

    Sonst zeigen Reviews in docs/reviews/<slug>/ auf outputs/audit_logs/<slug>/
    statt auf outputs/audit_logs/<mid>/ und finden keine mtime-Vergleichsbasis.
    """
    # mid mit Punkt, slug mit Underscore — beides muss unterstuetzt werden
    fake_audit = tmp_path / "outputs" / "audit_logs"
    raw_dir = fake_audit / "gpt-5.4"  # rohe mid
    raw_dir.mkdir(parents=True)
    (raw_dir / "tooluse_001.md").write_text("# T", encoding="utf-8")

    fake_review = tmp_path / "docs" / "reviews"
    fake_review.mkdir(parents=True)

    # meta_reviewer_prompt.yaml ins tmp_path/config/ kopieren, weil
    # _run_tooluse_reviews es ueber ROOT_DIR / "config" / ... laedt
    fake_config = tmp_path / "config"
    fake_config.mkdir(parents=True)
    (fake_config / "meta_reviewer_prompt.yaml").write_text(
        (ROOT / "config" / "meta_reviewer_prompt.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    # tooluse_leaderboard.csv in tmp_path/benchmark_scores/ stubben
    fake_scores = tmp_path / "benchmark_scores"
    fake_scores.mkdir(parents=True)
    (fake_scores / "tooluse_leaderboard.csv").write_text(
        "model,score\n" + "gpt-5.4,1.0\n",
        encoding="utf-8",
    )

    # tooluse_context stub: liefert gueltigen ctx
    fake_module = MagicMock()
    fake_module.get_tooluse_leaderboard_row.return_value = {"score": 1.0}
    fake_module.get_all_tooluse_model_ids.return_value = ["gpt-5.4"]
    fake_module.build_tooluse_context.return_value = {
        "tested_model_name": "gpt-5.4",
        "display_model_name": "GPT-5.4",
        "log_data": "",
    }
    monkeypatch.setitem(sys.modules, "utils.export.tooluse_context", fake_module)

    # Card: supports_tool_use=True, sonst skip
    from utils.model_utils import _card_path
    card = _card_path("gpt-5.4", for_write=True)
    card.parent.mkdir(parents=True, exist_ok=True)
    card.write_text('{"supports_tool_use": true, "display_name": "GPT-5.4", "architecture_tags": []}',
                    encoding="utf-8")

    args = _make_args(model="gpt-5.4", auto=True, type="tooluse", force=True)

    # yaml.safe_load monkey-patchen, damit prompt_yaml ein triviales Template
    # liefert. Damit umgehen wir die echte Template-Rendering-Pipeline und
    # testen nur den Pfad-Bug (audit_dir aus mid, nicht slug).
    def fake_safe_load(_stream):
        return {
            "tooluse_reviewer": {
                "system_instructions": "{tested_model_name}",  # minimal
            }
        }

    with patch.object(gr, "ROOT_DIR", tmp_path), \
         patch.object(gr, "yaml") as mock_yaml, \
         patch.object(gr, "_find_card", return_value=card), \
         patch.object(gr, "LLMClient") as mock_client_cls:
        mock_yaml.safe_load.side_effect = fake_safe_load
        mock_client = MagicMock()
        mock_client.query.return_value = "stub response"
        mock_client_cls.return_value = mock_client

        gr._run_tooluse_reviews(
            args, client=mock_client, provider="openai",
            model_id="gpt-5.4", max_tokens=8192,
        )

    # Das Review-File MUSS unter docs/reviews/_safe_name("gpt-5.4") = "gpt-5_4" liegen
    slug = "gpt-5_4"
    review_files = list((fake_review / slug).glob("tooluse_narrative_review_*.md"))
    assert review_files, (
        f"Review-File unter docs/reviews/{slug}/ erwartet, "
        f"bekam: {list((fake_review / slug).iterdir()) if (fake_review / slug).exists() else 'dir fehlt'}"
    )
    # cleanup
    card.unlink()


def test_per_model_iteration_uses_safe_name_dirs(tmp_path):
    """Per-Model-Iteration MUSS ueber alle safe_name-normalisierten Ordner laufen.

    Vor Phase 12 hatten wir 29 Ordner mit roher Schreibweise, die ueber
    `args.model = slug` (safe_name) nicht gefunden wurden. Nach Phase 12
    sind alle Ordner safe_name — also kein 17. Fix 1+3 stellen sicher,
    dass die Iteration trotzdem funktioniert.
    """
    fake_audit = tmp_path / "outputs" / "audit_logs"
    fake_audit.mkdir(parents=True)
    (fake_audit / "gpt-5_4").mkdir()  # safe_name-konform (Punkt -> Underscore)
    (fake_audit / "qwen3_5-9b").mkdir()
    (fake_audit / "hermes-4_3-36b-q6").mkdir()

    call_sequence: list[tuple[str, str]] = []

    def fake_run_audit(args, client, provider, model_id, max_tokens, csv_data, effective_type):
        call_sequence.append((args.model, effective_type))

    def fake_run_tooluse(args, client, provider, model_id, max_tokens):
        call_sequence.append((args.model, "tooluse"))

    args = _make_args(all=True, per_model=True, type="all", auto=True)

    with patch.object(gr, "ROOT_DIR", tmp_path), \
         patch.object(gr, "_run_audit_reviews", side_effect=fake_run_audit), \
         patch.object(gr, "_run_tooluse_reviews", side_effect=fake_run_tooluse), \
         patch.object(gr, "collect_data", return_value=""):
        gr._run_per_model_all_reviews(
            args, client=MagicMock(), provider="openai",
            model_id="gpt-5.4", max_tokens=8192, csv_data="",
        )

    # 3 Modelle × 2 Audit-Calls + 1 Tooluse-Call am Ende = 7 Einträge
    assert len(call_sequence) == 7, f"Erwartet 7 Calls, bekam {len(call_sequence)}: {call_sequence}"
    # Audit-Calls: alle 3 Modelle, je benchmark + bias
    audit_calls = [(m, t) for m, t in call_sequence if t != "tooluse"]
    audit_models = sorted({m for m, _ in audit_calls})
    assert audit_models == ["gpt-5_4", "hermes-4_3-36b-q6", "qwen3_5-9b"], (
        f"Erwartet die 3 safe_name-Ordner in Audit-Calls, bekam {audit_models}"
    )
    # Tooluse einmal am Ende mit model=None
    tooluse_calls = [(m, t) for m, t in call_sequence if t == "tooluse"]
    assert tooluse_calls == [(None, "tooluse")], (
        f"Erwartet genau einen Tooluse-Call mit model=None, bekam {tooluse_calls}"
    )
