"""Tests fuer die Web-Export-Blacklist (config/web_export_blacklist.yaml).

SSoT-Tests: Pruefen, dass
  1. _load_export_blacklist() die Config robust laedt (fehlend/leer/parse-error)
  2. Exakte und Pattern-Eintraege korrekt getrennt werden
  3. _is_blacklisted() exact + fnmatch-Pattern korrekt matched
  4. Der Hauptloop in main() geblacklistete Modelle ueberspringt
  5. meta.json den Blacklist-Block mit total_entries + skipped_in_run enthaelt
"""
import json
import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.web_export import (  # noqa: E402
    _is_blacklisted,
    _load_export_blacklist,
    _write_top_level_outputs,
)


ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# 1. _load_export_blacklist() — Robustheit
# ---------------------------------------------------------------------------

def test_load_blacklist_missing_file_returns_empty(tmp_path: Path) -> None:
    """Fehlende Datei -> leeres Set, file_loaded=False (graceful default)."""
    exact, pattern, total, loaded = _load_export_blacklist(tmp_path / "does_not_exist.yaml")
    assert exact == set()
    assert pattern == set()
    assert total == 0
    assert loaded is False


def test_load_blacklist_empty_file(tmp_path: Path) -> None:
    """Leere YAML-Datei -> file_loaded=True, total=0 (geladen, aber leer)."""
    bl_path = tmp_path / "web_export_blacklist.yaml"
    bl_path.write_text("", encoding="utf-8")
    exact, pattern, total, loaded = _load_export_blacklist(bl_path)
    assert exact == set()
    assert pattern == set()
    assert total == 0
    assert loaded is True


def test_load_blacklist_malformed_yaml_warns_and_returns_empty(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Parse-Error -> WARNING-Log, leeres Set, NICHT fatal."""
    bl_path = tmp_path / "bad.yaml"
    bl_path.write_text("blacklist: [unclosed", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="scripts.web_export"):
        exact, pattern, total, loaded = _load_export_blacklist(bl_path)
    assert exact == set()
    assert pattern == set()
    assert total == 0
    assert loaded is False
    assert any("nicht lesbar" in m for m in caplog.messages), (
        f"Erwarteter WARNING nicht gefunden in: {caplog.messages}"
    )


def test_load_blacklist_top_level_not_dict_warns(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Top-Level kein dict (z.B. eine Liste) -> WARNING + leeres Set."""
    bl_path = tmp_path / "list_root.yaml"
    bl_path.write_text("- a\n- b\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="scripts.web_export"):
        exact, pattern, total, loaded = _load_export_blacklist(bl_path)
    assert exact == set()
    assert pattern == set()
    assert total == 0
    assert loaded is False
    assert any("ungueltiges Format" in m for m in caplog.messages)


def test_load_blacklist_key_not_list_warns(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """blacklist-Key ist kein list -> WARNING + leeres Set."""
    bl_path = tmp_path / "bad_key.yaml"
    bl_path.write_text("blacklist: not-a-list\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="scripts.web_export"):
        exact, pattern, total, loaded = _load_export_blacklist(bl_path)
    assert exact == set()
    assert pattern == set()
    assert loaded is False
    assert any("keine Liste" in m for m in caplog.messages)


# ---------------------------------------------------------------------------
# 2. _load_export_blacklist() — Trennung exakt vs. Pattern
# ---------------------------------------------------------------------------

def test_load_blacklist_splits_exact_and_pattern(tmp_path: Path) -> None:
    """Eintraege mit Wildcards landen in pattern_set, exakte in exact_set."""
    bl_path = tmp_path / "bl.yaml"
    bl_path.write_text(
        "blacklist:\n"
        '  - "qwen3.5-35b-a3b-q4_k_m"     # exakt\n'
        '  - "qwen3.5-35b-a3b-q8"         # exakt\n'
        '  - "qwen3.5-35b-a3b-*"         # pattern\n'
        '  - "test-?"                     # pattern\n'
        '  - "*-experimental"             # pattern\n',
        encoding="utf-8",
    )
    exact, pattern, total, loaded = _load_export_blacklist(bl_path)
    assert loaded is True
    assert exact == {
        "qwen3.5-35b-a3b-q4_k_m",
        "qwen3.5-35b-a3b-q8",
    }
    assert pattern == {
        "qwen3.5-35b-a3b-*",
        "test-?",
        "*-experimental",
    }
    assert total == 5


def test_load_blacklist_ignores_empty_and_non_string_entries(tmp_path: Path) -> None:
    """Leere Strings und Nicht-String-Items werden uebergangen."""
    bl_path = tmp_path / "bl.yaml"
    bl_path.write_text(
        "blacklist:\n"
        '  - ""\n'
        '  - "   "\n'
        '  - 42\n'
        '  - null\n'
        '  - "valid-id"\n',
        encoding="utf-8",
    )
    exact, pattern, total, _ = _load_export_blacklist(bl_path)
    assert exact == {"valid-id"}
    assert pattern == set()
    assert total == 1


# ---------------------------------------------------------------------------
# 3. _is_blacklisted() — Match-Logik
# ---------------------------------------------------------------------------

def test_is_blacklisted_exact_match_returns_true() -> None:
    exact = {"qwen3.5-35b-a3b-q4_k_m"}
    pattern: set[str] = set()
    assert _is_blacklisted("qwen3.5-35b-a3b-q4_k_m", exact, pattern) is True


def test_is_blacklisted_exact_no_match_returns_false() -> None:
    exact = {"some-other-model"}
    pattern: set[str] = set()
    assert _is_blacklisted("qwen3.5-35b-a3b-q4_k_m", exact, pattern) is False


def test_is_blacklisted_pattern_star_matches() -> None:
    exact: set[str] = set()
    pattern = {"qwen3.5-35b-a3b-*"}
    assert _is_blacklisted("qwen3.5-35b-a3b-q4_k_m", exact, pattern) is True
    assert _is_blacklisted("qwen3.5-35b-a3b-q8", exact, pattern) is True
    assert _is_blacklisted("qwen3.5-35b-a3b-fp16", exact, pattern) is True


def test_is_blacklisted_pattern_question_mark() -> None:
    """fnmatch '?' matcht genau ein Zeichen."""
    exact: set[str] = set()
    pattern = {"test-?"}
    assert _is_blacklisted("test-1", exact, pattern) is True
    assert _is_blacklisted("test-a", exact, pattern) is True
    assert _is_blacklisted("test-12", exact, pattern) is False  # zu lang


def test_is_blacklisted_empty_sets_always_false() -> None:
    assert _is_blacklisted("any-model", set(), set()) is False


def test_is_blacklisted_exact_takes_precedence_over_pattern() -> None:
    """Wenn ein Eintrag sowohl exakt als auch als Pattern matched: True (egal welcher)."""
    exact = {"specific-model"}
    pattern = {"*"}  # matcht alles
    assert _is_blacklisted("specific-model", exact, pattern) is True
    assert _is_blacklisted("other-model", exact, pattern) is True


# ---------------------------------------------------------------------------
# 4. Integration: meta.json enthaelt Blacklist-Block
# ---------------------------------------------------------------------------

def test_meta_json_includes_blacklist_block(tmp_path: Path) -> None:
    """_write_top_level_outputs() schreibt den blacklist-Block in meta.json."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir).joinpath("models").mkdir()  # Dummy models dir
    root = tmp_path / "root"
    root.mkdir()

    _write_top_level_outputs(
        out_dir=out_dir,
        generated_at="2026-06-09T00:00:00+00:00",
        models_list=[],
        pc_list=[],
        provider_df=None,
        root_dir=root,
        comparisons_path=root / "docs" / "reviews",
        models_with_reports=0,
        models_with_reviews=0,
        models_skipped_blacklist=3,
        blacklist_total_entries=5,
        blacklist_source="config/web_export_blacklist.yaml",
    )

    meta = json.loads((out_dir / "meta.json").read_text(encoding="utf-8"))
    assert "blacklist" in meta
    assert meta["blacklist"]["source"] == "config/web_export_blacklist.yaml"
    assert meta["blacklist"]["total_entries"] == 5
    assert meta["blacklist"]["skipped_in_run"] == 3


def test_meta_json_blacklist_block_default_when_omitted(tmp_path: Path) -> None:
    """Default-Args (models_skipped_blacklist=0, total_entries=0) -> leerer Block, kein Fehler."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    root = tmp_path / "root"
    root.mkdir()

    _write_top_level_outputs(
        out_dir=out_dir,
        generated_at="2026-06-09T00:00:00+00:00",
        models_list=[],
        pc_list=[],
        provider_df=None,
        root_dir=root,
        comparisons_path=root / "docs" / "reviews",
        models_with_reports=0,
        models_with_reviews=0,
        # Keine Blacklist-Args uebergeben -> Defaults
    )

    meta = json.loads((out_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["blacklist"]["total_entries"] == 0
    assert meta["blacklist"]["skipped_in_run"] == 0
    assert meta["blacklist"]["source"] == "config/web_export_blacklist.yaml"


# ---------------------------------------------------------------------------
# 5. Integration: Hauptloop in main() ruft _is_blacklisted() auf
# ---------------------------------------------------------------------------

def test_main_loop_calls_is_blacklisted_for_each_model(tmp_path: Path) -> None:
    """SSoT: Der Hauptloop prueft jedes Modell gegen die Blacklist.

    Wir monkey-patchen alle externen Calls (CSV-Load, Card-Load, File-Write)
    und verifizieren, dass _is_blacklisted fuer jedes Leaderboard-Row aufgerufen wird.
    """
    import scripts.web_export as we

    # Echte tmp_path-Struktur: models_dir muss existieren, weil main() darin mkdir aufruft.
    output_root = tmp_path / "out" / "raw"
    models_dir = output_root / "models"
    models_dir.mkdir(parents=True)

    # Fake-Blacklist-Datei (leer) damit _load_export_blacklist file_loaded=True liefert
    # und der Logging-Pfad 'Blacklist: Datei geladen, leer.' genommen wird.
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "web_export_blacklist.yaml").write_text("", encoding="utf-8")

    # Minimaler Fake-DataFrame mit 3 Modellen
    import pandas as pd
    fake_df = pd.DataFrame({
        "Model Name": ["Model A", "Model B", "Model C"],
        "Model ID": ["vendor-a", "vendor-b", "vendor-c"],
        "Total Score": ["80.0", "75.0", "70.0"],
        "Type": ["X", "X", "X"],
        "Badge": ["Gold", "Silver", "Bronze"],
        "Size Class": ["M", "M", "M"],
        "Speed Profile": ["fast", "fast", "fast"],
    })

    with patch.object(we, "_setup_output_dirs", return_value=(
            output_root, models_dir, tmp_path)), \
         patch.object(we, "_load_sources", return_value=(fake_df, None, None, None)), \
         patch.object(we, "_build_pc_lookups", return_value=({}, {})), \
         patch.object(we, "_load_pc_block_meta", return_value={}), \
         patch.object(we, "_build_benchmark_run_dates", return_value={}), \
         patch.object(we, "build_provider_map", return_value={}), \
         patch.object(we, "load_model_card", return_value=None), \
         patch.object(we, "_resolve_dir", return_value=None), \
         patch.object(we, "_export_model_files", return_value=([], {"review": None, "bias_review": None})), \
         patch.object(we, "_build_leaderboard_entry", return_value={"slug": "x"}), \
         patch.object(we, "_build_tooluse_entry", return_value=None), \
         patch.object(we, "_write_top_level_outputs", return_value=None), \
         patch.object(we, "_is_blacklisted", return_value=False) as mock_bl, \
         patch("sys.argv", ["web_export.py", "--output", str(tmp_path / "out")]):
        we.main()

    # Genau 3 Modelle geprueft
    assert mock_bl.call_count == 3
    # IDs muessen an _is_blacklisted uebergeben worden sein
    checked_ids = {call.args[0] for call in mock_bl.call_args_list}
    assert checked_ids == {"vendor-a", "vendor-b", "vendor-c"}


def test_main_loop_skips_blacklisted_model(tmp_path: Path) -> None:
    """Integration: Modell A ist geblacklistet, wird uebersprungen (kein data.json)."""
    import scripts.web_export as we
    import pandas as pd

    # Echte tmp_path-Struktur mit Blacklist-Datei
    output_root = tmp_path / "out" / "raw"
    models_dir = output_root / "models"
    models_dir.mkdir(parents=True)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "web_export_blacklist.yaml").write_text(
        "blacklist:\n  - \"blacklisted-id\"\n",
        encoding="utf-8",
    )

    fake_df = pd.DataFrame({
        "Model Name": ["Model A", "Model B"],
        "Model ID": ["blacklisted-id", "ok-id"],
        "Total Score": ["80.0", "75.0"],
        "Type": ["X", "X"],
        "Badge": ["Gold", "Silver"],
        "Size Class": ["M", "M"],
        "Speed Profile": ["fast", "fast"],
    })

    written_data: list[str] = []

    def _capture_write(model_out, audit_src, comp_src):
        written_data.append(model_out.name)
        return [], {"review": None, "bias_review": None}

    with patch.object(we, "_setup_output_dirs", return_value=(
            output_root, models_dir, tmp_path)), \
         patch.object(we, "_load_sources", return_value=(fake_df, None, None, None)), \
         patch.object(we, "_build_pc_lookups", return_value=({}, {})), \
         patch.object(we, "_load_pc_block_meta", return_value={}), \
         patch.object(we, "_build_benchmark_run_dates", return_value={}), \
         patch.object(we, "build_provider_map", return_value={}), \
         patch.object(we, "load_model_card", return_value=None), \
         patch.object(we, "_resolve_dir", return_value=None), \
         patch.object(we, "_export_model_files", side_effect=_capture_write), \
         patch.object(we, "_build_leaderboard_entry", return_value={"slug": "x"}), \
         patch.object(we, "_build_tooluse_entry", return_value=None), \
         patch.object(we, "_write_top_level_outputs") as mock_write, \
         patch("sys.argv", ["web_export.py", "--output", str(tmp_path / "out")]):
        # _is_blacklisted unkontrolliert — Real-Funktion liest Blacklist aus tmp_path/config/
        we.main()

    # Nur Model B wurde exportiert (Model A ist blacklisted)
    assert written_data == ["model-b"], f"Erwartet nur 'model-b', geschrieben: {written_data}"
    # models_skipped_blacklist wurde an _write_top_level_outputs uebergeben
    assert mock_write.call_args.kwargs["models_skipped_blacklist"] == 1
    assert mock_write.call_args.kwargs["blacklist_total_entries"] == 1
