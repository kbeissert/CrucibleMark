"""
Tests fuer den CSV-Hygiene-Sanitizer.

Verifiziert die Filter-Heuristiken sowie den Dry-Run/Apply-Lifecycle
inklusive Backup-Strategie und Idempotenz.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

# pylint: disable=wrong-import-position
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.maintenance import sanitize_benchmark_csvs as sbc  # noqa: E402


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    """Schreibt eine Test-CSV mit gegebenem Header und Datenzeilen."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def _standard_header() -> list[str]:
    """Erzeugt einen Header, der alle Sanitizer-Spalten enthaelt."""
    return [
        "asset_id", "module", "category", "task", "timestamp", "model", "provider",
        "model_version", "prompt", "response", "score", "max_score", "judge_score",
        "judge_confidence", "cost_usd", "tokens_input", "tokens_output",
        "exec_time_s", "retry_count", "response_length", "truncated", "language",
        "status", "error", "refusal_flag", "refusal_type", "refusal_note",
    ]


def _row(
    asset_id: str,
    model: str,
    status: str = "success",
    module: str = "code_quality",
    score: str = "4.0",
) -> list[str]:
    """Erzeugt eine Standard-Datenzeile (Status success, score 4.0)."""
    header = _standard_header()
    return [
        asset_id, module, "test", asset_id, "2026-06-08T00:00:00Z", model,
        "ollama", "latest", "prompt", "response", score, "5.0", "0.0", "0.0",
        "0.0", "100", "200", "1.0", "0", "50", "False", "en", status, "",
        "False", "", "",
    ]


# ---------------------------------------------------------------------------
# Header-Repeat-Erkennung
# ---------------------------------------------------------------------------

class TestIsHeaderRepeat:
    """`_is_header_repeat` muss Header-Zeilen korrekt identifizieren."""

    def test_first_col_asset_id_is_header(self) -> None:
        assert sbc._is_header_repeat(["asset_id", "model", "score"]) is True

    def test_normal_data_row_is_not_header(self) -> None:
        assert sbc._is_header_repeat(["code_quality_001", "gpt-5", "4.0"]) is False

    def test_empty_parts_is_not_header(self) -> None:
        assert sbc._is_header_repeat([]) is False

    def test_whitespace_is_stripped_before_check(self) -> None:
        assert sbc._is_header_repeat(["  asset_id  ", "model"]) is True

    def test_first_col_must_be_asset_id_exactly(self) -> None:
        # Andere Spaltennamen mit aehnlicher Bedeutung sind KEIN Trigger.
        assert sbc._is_header_repeat(["Asset_ID", "model"]) is False


# ---------------------------------------------------------------------------
# Narrative-Asset-ID-Erkennung
# ---------------------------------------------------------------------------

class TestIsNarrativeAssetId:
    """`_is_narrative_asset_id` filtert Romananfaenge, Markdown und Overlong."""

    def test_normal_asset_id_passes(self) -> None:
        assert sbc._is_narrative_asset_id("code_quality_005") is False

    def test_cli_benchmark_id_passes(self) -> None:
        assert sbc._is_narrative_asset_id("cli_benchmark_007") is False

    def test_tooluse_id_passes(self) -> None:
        assert sbc._is_narrative_asset_id("tooluse_001") is False

    def test_empty_is_narrative(self) -> None:
        assert sbc._is_narrative_asset_id("") is True

    def test_overlong_id_is_narrative(self) -> None:
        long_id = "a" * (sbc.MAX_VALID_ASSET_ID_LEN + 1)
        assert sbc._is_narrative_asset_id(long_id) is True

    def test_exactly_max_len_passes(self) -> None:
        # Grenzwert-Test: exakt MAX_VALID_ASSET_ID_LEN Zeichen ist OK.
        ok_id = "a" * sbc.MAX_VALID_ASSET_ID_LEN
        assert sbc._is_narrative_asset_id(ok_id) is False

    @pytest.mark.parametrize("prefix", [
        "the ", "for ", "final:", "this ", "these ", "model ", "models ",
        "first,", "second,", "however,", "moreover,", "therefore,",
        "in summary,", "to summarize,",
    ])
    def test_narrative_prefixes_detected(self, prefix: str) -> None:
        assert sbc._is_narrative_asset_id(f"{prefix}quick brown fox") is True

    def test_prefix_match_is_case_insensitive(self) -> None:
        assert sbc._is_narrative_asset_id("THE quick brown fox") is True

    @pytest.mark.parametrize("marker", ["##", "###", "---", "***", "==="])
    def test_markdown_markers_detected(self, marker: str) -> None:
        assert sbc._is_narrative_asset_id(f"section {marker} title") is True

    def test_real_id_with_unrelated_substring_passes(self) -> None:
        # '##' als Substring in 'ab##c' wuerde feuern — das ist gewollt,
        # weil kein reales Asset-ID dieses Pattern haben sollte.
        assert sbc._is_narrative_asset_id("culture_intelligence_2") is False


# ---------------------------------------------------------------------------
# Invalid-Model-Erkennung
# ---------------------------------------------------------------------------

class TestIsInvalidModel:
    """`_is_invalid_model` prueft Model-Identifier auf leere/Boolean-Werte."""

    def test_normal_model_passes(self) -> None:
        assert sbc._is_invalid_model("gpt-5") == (False, "")

    def test_qualified_model_passes(self) -> None:
        assert sbc._is_invalid_model("moonshotai/kimi-k2-0711") == (False, "")

    def test_empty_string_is_invalid_empty(self) -> None:
        assert sbc._is_invalid_model("") == (True, "empty")

    def test_whitespace_only_is_invalid_empty(self) -> None:
        assert sbc._is_invalid_model("   ") == (True, "empty")

    @pytest.mark.parametrize("sentinel", ["nan", "NaN", "None", "null", "NULL"])
    def test_pandas_sentinels_are_invalid_empty(self, sentinel: str) -> None:
        assert sbc._is_invalid_model(sentinel) == (True, "empty")

    def test_lowercase_true_is_invalid_boolean(self) -> None:
        assert sbc._is_invalid_model("true") == (True, "boolean")

    def test_lowercase_false_is_invalid_boolean(self) -> None:
        assert sbc._is_invalid_model("false") == (True, "boolean")

    def test_uppercase_true_is_invalid_boolean(self) -> None:
        # Case-Insensitive: 'True' / 'TRUE' sind ebenfalls Boolean-Strings.
        assert sbc._is_invalid_model("TRUE") == (True, "boolean")

    def test_unknown_value_passes(self) -> None:
        # 'unknown' ist KEIN Trigger (nur in Kombination mit status != success,
        # das wird in `_filter_rows` entschieden).
        assert sbc._is_invalid_model("unknown") == (False, "")


# ---------------------------------------------------------------------------
# Filter-Pipeline (kombinierte Logik)
# ---------------------------------------------------------------------------

class TestFilterRows:
    """`_filter_rows` wendet alle Filter in der korrekten Reihenfolge an."""

    def test_clean_data_passes(self, tmp_path: Path) -> None:
        path = tmp_path / "ok.csv"
        _write_csv(path, _standard_header(), [
            _row("code_quality_001", "gpt-5"),
            _row("code_quality_002", "claude-sonnet-4-5-20251001"),
        ])
        header, rows = sbc._read_csv_with_header(path)
        clean, reasons = sbc._filter_rows(header, rows)
        assert len(clean) == 2
        assert not reasons

    def test_header_repeat_dropped(self, tmp_path: Path) -> None:
        path = tmp_path / "ok.csv"
        _write_csv(path, _standard_header(), [
            _row("code_quality_001", "gpt-5"),
            ["asset_id", "model", "score"],  # Header-Repeat
            _row("code_quality_002", "gpt-5"),
        ])
        header, rows = sbc._read_csv_with_header(path)
        clean, reasons = sbc._filter_rows(header, rows)
        assert len(clean) == 2
        assert reasons["header_repeat"] == 1

    def test_narrative_asset_id_dropped(self, tmp_path: Path) -> None:
        path = tmp_path / "ok.csv"
        _write_csv(path, _standard_header(), [
            _row("code_quality_001", "gpt-5"),
            _row("the quick brown fox jumps over", "gpt-5"),
            _row("section ## title here", "gpt-5"),
            _row("a" * 80, "gpt-5"),
            _row("code_quality_002", "gpt-5"),
        ])
        header, rows = sbc._read_csv_with_header(path)
        clean, reasons = sbc._filter_rows(header, rows)
        assert len(clean) == 2
        assert reasons["narrative_asset_id"] == 3

    def test_invalid_model_in_success_status_dropped(self, tmp_path: Path) -> None:
        path = tmp_path / "ok.csv"
        _write_csv(path, _standard_header(), [
            _row("code_quality_001", "gpt-5"),
            _row("code_quality_002", "True", status="success"),
            _row("code_quality_003", "False", status="success"),
        ])
        header, rows = sbc._read_csv_with_header(path)
        clean, reasons = sbc._filter_rows(header, rows)
        assert len(clean) == 1
        # 2 Drops, beide als invalid_model_boolean klassifiziert.
        assert reasons["invalid_model_boolean"] == 2

    def test_invalid_model_in_failed_status_dropped(self, tmp_path: Path) -> None:
        path = tmp_path / "ok.csv"
        _write_csv(path, _standard_header(), [
            _row("code_quality_001", "gpt-5"),
            _row("code_quality_002", "", status="error"),
        ])
        header, rows = sbc._read_csv_with_header(path)
        clean, reasons = sbc._filter_rows(header, rows)
        assert len(clean) == 1
        assert reasons["invalid_model_empty_non_success"] == 1

    def test_drop_reasons_are_counter(self, tmp_path: Path) -> None:
        path = tmp_path / "ok.csv"
        _write_csv(path, _standard_header(), [
            _row("asset_id", "gpt-5"),  # header_repeat
            _row("the answer is yes", "gpt-5"),  # narrative
        ])
        header, rows = sbc._read_csv_with_header(path)
        _, reasons = sbc._filter_rows(header, rows)
        assert reasons["header_repeat"] == 1
        assert reasons["narrative_asset_id"] == 1

    def test_no_assets_to_evaluate_returns_empty_clean(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.csv"
        _write_csv(path, _standard_header(), [])
        header, rows = sbc._read_csv_with_header(path)
        clean, reasons = sbc._filter_rows(header, rows)
        assert not clean
        assert not reasons


# ---------------------------------------------------------------------------
# Backup-Strategie
# ---------------------------------------------------------------------------

class TestBackupCsv:
    """`_backup_csv` erstellt ein idempotentes .bak-Backup."""

    def test_first_backup_creates_file(self, tmp_path: Path) -> None:
        path = tmp_path / "data.csv"
        path.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
        backup = sbc._backup_csv(path)
        assert backup.exists()
        assert backup.suffix == ".bak"
        assert backup.read_text(encoding="utf-8") == "a,b,c\n1,2,3\n"

    def test_second_backup_is_idempotent(self, tmp_path: Path) -> None:
        path = tmp_path / "data.csv"
        path.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
        first = sbc._backup_csv(path)
        # Original danach aendern.
        path.write_text("a,b,c\n9,9,9\n", encoding="utf-8")
        second = sbc._backup_csv(path)
        assert first == second
        # Backup darf NICHT ueberschrieben werden (idempotent).
        assert first.read_text(encoding="utf-8") == "a,b,c\n1,2,3\n"


# ---------------------------------------------------------------------------
# Atomic-Write
# ---------------------------------------------------------------------------

class TestWriteCsvAtomic:
    """`_write_csv_atomic` schreibt vollstaendig oder gar nicht."""

    def test_write_replaces_existing(self, tmp_path: Path) -> None:
        path = tmp_path / "out.csv"
        _write_csv(path, _standard_header(), [_row("code_quality_001", "gpt-5")])
        sbc._write_csv_atomic(path, _standard_header(), [
            _row("ux_writing_001", "claude-sonnet-4-5-20251001"),
        ])
        # Alte Daten weg, neue da.
        with path.open(encoding="utf-8") as f:
            lines = f.readlines()
        assert "ux_writing_001" in lines[1]
        assert "code_quality_001" not in "".join(lines)

    def test_no_tmp_file_lingers(self, tmp_path: Path) -> None:
        path = tmp_path / "out.csv"
        sbc._write_csv_atomic(path, _standard_header(), [])
        leftover = list(tmp_path.glob("*.tmp"))
        assert not leftover

    def test_round_trip_via_csv_reader(self, tmp_path: Path) -> None:
        path = tmp_path / "rt.csv"
        original = [
            _row("code_quality_001", "gpt-5"),
            _row("ux_writing_001", "claude-sonnet-4-5-20251001"),
        ]
        sbc._write_csv_atomic(path, _standard_header(), original)
        with path.open(encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            data = list(reader)
        assert header[0] == "asset_id"
        assert len(data) == 2
        assert data[0][_standard_header().index("model")] == "gpt-5"


# ---------------------------------------------------------------------------
# End-to-End via main()
# ---------------------------------------------------------------------------

@pytest.fixture
def patched_target_csvs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Patcht die SSoT-CSV-Pfade auf tmp_path Varianten."""
    paths = {
        "local": tmp_path / "local_models_benchmark.csv",
        "cloud": tmp_path / "cloud_models_benchmark.csv",
        "commercial": tmp_path / "commercial_models_benchmark.csv",
    }
    monkeypatch.setattr(sbc, "LOCAL_CSV", paths["local"])
    monkeypatch.setattr(sbc, "CLOUD_CSV", paths["cloud"])
    monkeypatch.setattr(sbc, "COMMERCIAL_CSV", paths["commercial"])
    monkeypatch.setattr(sbc, "TARGET_CSVS",
                        (paths["local"], paths["cloud"], paths["commercial"]))
    return paths


class TestMainDryRun:
    """Dry-Run aendert nichts."""

    def test_dry_run_creates_no_backup(self, patched_target_csvs) -> None:
        for path in patched_target_csvs.values():
            _write_csv(path, _standard_header(), [_row("a_001", "gpt-5")])
        # Default-Modus ist Dry-Run (kein --apply Flag).
        exit_code = sbc.main([])
        assert exit_code == 0
        for path in patched_target_csvs.values():
            assert not path.with_suffix(path.suffix + ".bak").exists()

    def test_dry_run_does_not_modify_csv(self, patched_target_csvs) -> None:
        target = patched_target_csvs["local"]
        _write_csv(target, _standard_header(), [
            _row("a_001", "gpt-5"),
            _row("asset_id", "gpt-5"),  # corrupt
        ])
        original = target.read_text(encoding="utf-8")
        sbc.main([])
        assert target.read_text(encoding="utf-8") == original

    def test_clean_csv_returns_no_drops(self, patched_target_csvs) -> None:
        for path in patched_target_csvs.values():
            _write_csv(path, _standard_header(), [_row("a_001", "gpt-5")])
        # Exit-Code 0 + keine Meldung "wuerden entfernt werden".
        assert sbc.main([]) == 0


class TestMainApply:
    """Apply-Modus schreibt bereinigte CSVs und legt Backups an."""

    def test_apply_writes_cleaned_csv(self, patched_target_csvs) -> None:
        target = patched_target_csvs["local"]
        _write_csv(target, _standard_header(), [
            _row("a_001", "gpt-5"),
            _row("the answer is yes", "gpt-5"),  # narrative
            _row("a_002", "claude-sonnet-4-5-20251001"),
        ])
        sbc.main(["--apply"])
        with target.open(encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # header
            rows = list(reader)
        assert len(rows) == 2
        assert all("the answer" not in r[0] for r in rows)

    def test_apply_creates_backup_with_original(self, patched_target_csvs) -> None:
        target = patched_target_csvs["local"]
        _write_csv(target, _standard_header(), [
            _row("a_001", "gpt-5"),
            _row("corrupt_id_##_section", "gpt-5"),
        ])
        original = target.read_text(encoding="utf-8")
        sbc.main(["--apply"])
        backup = target.with_suffix(target.suffix + ".bak")
        assert backup.exists()
        # Backup enthaelt die unveraenderte Original-Datei.
        assert backup.read_text(encoding="utf-8") == original

    def test_apply_is_idempotent_second_run_no_changes(self, patched_target_csvs) -> None:
        target = patched_target_csvs["local"]
        _write_csv(target, _standard_header(), [
            _row("a_001", "gpt-5"),
            _row("corrupt_id_##_section", "gpt-5"),
        ])
        sbc.main(["--apply"])
        first_lines = target.read_text(encoding="utf-8")
        # Zweiter Lauf darf nichts mehr aendern.
        sbc.main(["--apply"])
        assert target.read_text(encoding="utf-8") == first_lines

    def test_missing_csv_is_skipped(self, patched_target_csvs) -> None:
        # Nur local existiert.
        target = patched_target_csvs["local"]
        _write_csv(target, _standard_header(), [_row("a_001", "gpt-5")])
        assert sbc.main(["--apply"]) == 0
        # Andere CSVs wurden nicht angelegt (Skip, nicht Create).
        assert not patched_target_csvs["cloud"].exists()
        assert not patched_target_csvs["commercial"].exists()

    def test_combined_corruption_pattern(self, patched_target_csvs) -> None:
        """Kombiniertes Szenario: Header-Repeat + Narrative + Boolean + leer."""
        target = patched_target_csvs["local"]
        _write_csv(target, _standard_header(), [
            _row("a_001", "gpt-5"),
            ["asset_id", "model", "score"],  # header_repeat
            _row("the quick brown fox", "gpt-5"),  # narrative
            _row("a_002", "True", status="success"),  # boolean
            _row("a_003", "", status="error"),  # empty + non_success
            _row("a_004", "claude-sonnet-4-5-20251001"),
        ])
        sbc.main(["--apply"])
        with target.open(encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            rows = list(reader)
        # Nur a_001 und a_004 bleiben.
        assert len(rows) == 2
        kept_ids = {r[0] for r in rows}
        assert kept_ids == {"a_001", "a_004"}
