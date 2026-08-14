"""Phase 28: Tests fuer clean_results (SSoT-Anbindung + ID-Normalisierung)."""
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
import yaml

from scripts.maintenance import clean_results
from utils.backup_targets import CSV_FILES


# ---------------------------------------------------------------------------
# clean_csv: ID-Normalisierung
# ---------------------------------------------------------------------------

def test_clean_csv_normalizes_model_id(tmp_path, capsys):
    """ID-SSoT: clean_csv normalisiert Ziel-Modell und CSV-Zellen gleichermassen.

    Verwendet eine ID, die in DIESER Form sowohl als Ziel als auch in der
    CSV vorkommt. resolve_canonical_model_id macht daraus denselben
    kanonischen String, also matcht es.
    """
    csv_path = tmp_path / "local.csv"
    csv_path.write_text(
        "model,asset_id,score\n"
        "qwen3.5-35b,asset_a,90\n"
        "qwen3.5-35b,asset_b,80\n"
        "other-model,asset_c,70\n",
        encoding="utf-8",
    )

    clean_results.clean_csv(
        csv_path, model="qwen3.5-35b", dry_run=False,
    )
    captured = capsys.readouterr()
    # 2 Zeilen raus, 1 Zeile (other-model) bleibt
    assert "2 Eintr" in captured.out
    assert "local.csv" in captured.out

    df = pd.read_csv(csv_path)
    assert list(df["model"]) == ["other-model"]


def test_clean_csv_matches_dotted_and_underscored_target(tmp_path, capsys):
    """Wenn Ziel-ID mit Dots, aber CSV denselben Namen hat (nach Normalisierung), matcht es."""
    csv_path = tmp_path / "local.csv"
    # Beide Schreibweisen werden zu qwen3_5-35b kanonisiert
    csv_path.write_text(
        "model,asset_id,score\n"
        "qwen3.5-35b,asset_a,90\n"
        "other-model,asset_b,80\n",
        encoding="utf-8",
    )
    clean_results.clean_csv(csv_path, model="qwen3.5-35b", dry_run=False)
    df = pd.read_csv(csv_path)
    assert list(df["model"]) == ["other-model"]


def test_clean_csv_keeps_rows_when_no_match(tmp_path, capsys):
    """Wenn das Ziel-Modell nicht in der CSV vorkommt, wird nichts geloescht."""
    csv_path = tmp_path / "local.csv"
    csv_path.write_text(
        "model,asset_id,score\nfoo,asset_a,90\nbar,asset_b,80\n",
        encoding="utf-8",
    )
    clean_results.clean_csv(csv_path, model="not-here", dry_run=False)
    df = pd.read_csv(csv_path)
    assert len(df) == 2


def test_clean_csv_dry_run_does_not_modify(tmp_path, capsys):
    """dry_run=True darf die Datei nicht veraendern."""
    csv_path = tmp_path / "local.csv"
    csv_path.write_text(
        "model,asset_id,score\nfoo,asset_a,90\nbar,asset_b,80\n",
        encoding="utf-8",
    )
    clean_results.clean_csv(csv_path, model="foo", dry_run=True)
    df = pd.read_csv(csv_path)
    assert len(df) == 2  # nichts geloescht
    captured = capsys.readouterr()
    assert "Dry Run" in captured.out


def test_clean_csv_handles_none_model_column():
    """Phase-27-Bug-Schutz: NaN-Model-Werte crashen nicht."""
    csv_path = Path("benchmark_scores/local_models_benchmark.csv")
    if not csv_path.exists():
        pytest.skip("CSV existiert nicht im Test-Setup")
    # Sollte keinen Crash werfen
    clean_results.clean_csv(csv_path, model="nonexistent-test-model", dry_run=True)


# ---------------------------------------------------------------------------
# CLEAN_CSV_FILES: SSoT-Konsistenz
# ---------------------------------------------------------------------------

def test_clean_csv_files_includes_ssm_targets():
    """Alle Benchmark-CSVs aus backup_targets.CSV_FILES sind in CLEAN_CSV_FILES."""
    for path, _ in CSV_FILES:
        assert path in clean_results.CLEAN_CSV_FILES, (
            f"CSV-SSoT-Eintrag fehlt: {path}"
        )


def test_clean_csv_files_includes_pc_csvs():
    """PC-spezifische CSVs sind erweitert (sie haben eigenen Dedup-Key)."""
    assert Path("benchmark_scores/political_compass_results.csv") in clean_results.CLEAN_CSV_FILES
    assert Path("benchmark_scores/political_compass_leaderboard.csv") in clean_results.CLEAN_CSV_FILES


def test_clean_csv_files_dedup():
    """Keine doppelten Eintraege (CSV_FILES + PC_CSV_FILES koennten sich ueberlappen)."""
    assert len(clean_results.CLEAN_CSV_FILES) == len(set(clean_results.CLEAN_CSV_FILES))


# ---------------------------------------------------------------------------
# main_with_args: Direktaufruf ohne Subprozess
# ---------------------------------------------------------------------------

def test_main_with_args_runs_dry_run_without_crash(tmp_path, monkeypatch, capsys):
    """main_with_args akzeptiert ein Namespace-Objekt und laeuft durch."""
    # Benchmark-CSV in tmp verlegen, damit das Live-CSV nicht beruehrt wird
    csv_path = tmp_path / "local.csv"
    csv_path.write_text(
        "model,asset_id,score\nfoo,asset_a,90\nbar,asset_b,80\n",
        encoding="utf-8",
    )

    # CLEAN_CSV_FILES monkeypatchen, damit main_with_args auf tmp zugreift
    monkeypatch.setattr(
        clean_results, "CLEAN_CSV_FILES", (csv_path,),
    )
    # Leaderboard-Update unterbinden (verhindert externe Effekte)
    monkeypatch.setattr(
        "sys.modules", {**__import__("sys").modules,
                        "scripts.core.generate_leaderboard": None},
    )

    args = SimpleNamespace(
        model="foo", module=None, dry_run=True,
        prune_orphans=False, force=False,
    )
    clean_results.main_with_args(args)
    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
    # Output nutzt deutsche Umlaute (Einträge) — partial match vermeidet Unicode-Issues
    assert "Eintr" in captured.out


def test_main_with_args_requires_model_or_module(capsys):
    """Ohne --model und --module muss exit(1) gerufen werden."""
    args = SimpleNamespace(
        model=None, module=None, dry_run=False,
        prune_orphans=False, force=False,
    )
    with pytest.raises(SystemExit):
        clean_results.main_with_args(args)
    captured = capsys.readouterr()
    assert "--model" in captured.out or "Bitte" in captured.out


# ---------------------------------------------------------------------------
# clean_provider_config: Auskommentieren + models-Key-Normalisierung
# ---------------------------------------------------------------------------

_MINI_PROVIDER_YAML = """providers:
  local:
    llamacpp_spark:
      name: LlamaCPP Spark
      models:
      # - id: old-model
      #   name: Old
      - id: keep-me
        name: Keep Me
      - id: victim-model
        name: Victim
        config: Victim
        max_tokens: 8192

        # Interner Kommentar-Block mit Leerzeile davor —
        # gehoert zum Eintrag (YAML erlaubt beides).
        enable_thinking: true
      - id: after-victim
        name: After Victim
"""


def _write_mini_config(tmp_path: Path) -> Path:
    """Legt eine minimale provider_config.yaml unter tmp_path an."""
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir(exist_ok=True)
    pc_path = cfg_dir / "provider_config.yaml"
    pc_path.write_text(_MINI_PROVIDER_YAML, encoding="utf-8")
    return pc_path


def test_clean_provider_config_comments_out_entry(tmp_path, monkeypatch, capsys):
    """Eintrag wird komplett auskommentiert (inkl. Felder nach Leerzeile)."""
    pc_path = _write_mini_config(tmp_path)
    monkeypatch.setattr(clean_results, "ROOT_DIR", tmp_path)

    clean_results.clean_provider_config("victim-model", dry_run=False)

    captured = capsys.readouterr()
    assert "victim-model" in captured.out
    assert "Gespeichert" in captured.out

    text = pc_path.read_text(encoding="utf-8")
    assert "# - id: victim-model" in text
    assert "# enable_thinking: true" in text, (
        "Felder nach interner Leerzeile muessen mitkommentiert werden"
    )
    assert "# Auskommentiert" in text and "make clean-model" in text
    # Nachbarn bleiben aktiv
    assert "- id: keep-me" in text
    assert "- id: after-victim" in text
    # YAML bleibt parsebar
    cfg = yaml.safe_load(text)
    ids = [m["id"] for m in cfg["providers"]["local"]["llamacpp_spark"]["models"]]
    assert ids == ["keep-me", "after-victim"]


def test_clean_provider_config_normalizes_empty_models(tmp_path, monkeypatch, capsys):
    """Letzter aktiver Eintrag raus -> models: [] statt models: (None)."""
    pc_path = _write_mini_config(tmp_path)
    monkeypatch.setattr(clean_results, "ROOT_DIR", tmp_path)

    for mid in ("keep-me", "victim-model", "after-victim"):
        clean_results.clean_provider_config(mid, dry_run=False)

    cfg = yaml.safe_load(pc_path.read_text(encoding="utf-8"))
    models = cfg["providers"]["local"]["llamacpp_spark"]["models"]
    assert models == [], "models muss nach Leerung explizit [] sein, nicht None"


def test_normalize_empty_models_keys_unit():
    """_normalize_empty_models_keys: Look-ahead ueber Kommentare hinweg."""
    lines_active = ["      models:", "      - id: foo"]
    assert clean_results._normalize_empty_models_keys(lines_active) == lines_active

    lines_empty = ["      models:", "      # - id: foo", "    next_key: 1"]
    out = clean_results._normalize_empty_models_keys(lines_empty)
    assert out[0] == "      models: []"
    assert out[1:] == lines_empty[1:]

    assert clean_results._normalize_empty_models_keys(["      models: []"]) == [
        "      models: []"
    ]


def test_clean_provider_config_matches_dotted_config_form(tmp_path, monkeypatch):
    """Underscore-Input (kanonische interne Form) findet Dotted-Config-Eintrag.

    Regression: _collect_model_id_variants deckte die Config-Form (Dot in
    Versions-Segmenten, z.B. ``ornith-1.0-35B-FP8``) nicht ab, wenn die
    interne Form (``ornith-1_0-35B-FP8``) uebergeben wurde — lautes
    "Kein Eintrag gefunden" haette das Modell in der Config aktiv lassen.
    """
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    pc_path = cfg_dir / "provider_config.yaml"
    pc_path.write_text(
        "providers:\n"
        "  local:\n"
        "    vllm_spark:\n"
        "      models:\n"
        "      - id: ornith-1.0-35B-FP8\n"
        "        name: Ornith\n"
        "        config: Ornith1-35B-FP8\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(clean_results, "ROOT_DIR", tmp_path)

    clean_results.clean_provider_config("ornith-1_0-35B-FP8", dry_run=False)

    cfg = yaml.safe_load(pc_path.read_text(encoding="utf-8"))
    assert cfg["providers"]["local"]["vllm_spark"]["models"] == []
    assert "# - id: ornith-1.0-35B-FP8" in pc_path.read_text(encoding="utf-8")
