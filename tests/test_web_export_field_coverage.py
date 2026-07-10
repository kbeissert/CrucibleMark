"""Tests fuer vollstaendige Score- und Vendor-Field-Konsistenz im WebExport.

Hintergrund: Audit in Session 38 (2026-06-26) ergab Luecken:
  LdbCols hatte nur 7 von 9 CSV-Score-Spalten
  (Synthesis Quality, Tool Execution fehlten)

Diese Tests sichern ab, dass keine CSV-Spalte mehr stillschweigend
verloren geht.

Hinweis: political_bias ist KEIN Score-Modul (Session 58, v4.10.16).
Political Compass-Daten kommen aus political_compass_results.csv und
landen in data.json.political_compass als separate Top-Level-Section.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# Score-Keys: SSoT ist scripts.web_export._SCORES_CONTRACT_KEYS.
# Neue Module werden dort ergaenzt und sind automatisch hier sichtbar.
EXPECTED_SCORE_KEYS: set[str] = set(
    __import__("scripts.web_export", fromlist=["_SCORES_CONTRACT_KEYS"])
    ._SCORES_CONTRACT_KEYS
)


class TestLeaderboardScoreMapping:
    """Prueft, dass alle 9 CSV-Modul-Spalten in data.json.leaderboard.scores landen."""

    def test_ldbcols_has_all_score_columns(self):
        """LdbCols muss Konstanten fuer alle 9 CSV-Modul-Spalten haben."""
        from scripts.web_export import LdbCols
        expected_csv_cols = [
            "Code Quality Audit",
            "CLI Badge",
            "UX Writing & Microcopy",
            "Documentation Quality",
            "Content Transformation & Adaption",
            "Cultural Intelligence",
            "Logical Reasoning",
            "Synthesis Quality",
            "Tool Execution",
        ]
        for csv_col in expected_csv_cols:
            # Suche nach Konstanten mit diesem Wert
            found = False
            for attr in dir(LdbCols):
                if attr.startswith("_"):
                    continue
                if getattr(LdbCols, attr) == csv_col:
                    found = True
                    break
            assert found, f"LdbCols fehlt Konstante fuer CSV-Spalte: {csv_col!r}"

    def test_all_scores_keys_present_in_export(self):
        """data.json.leaderboard.scores muss alle 9 Keys enthalten."""
        m_dir = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "models"
        if not (m_dir / "claude-haiku-4-5" / "data.json").exists():
            pytest.skip("Web-Export noch nicht erstellt")
        data = json.loads((m_dir / "claude-haiku-4-5" / "data.json").read_text())
        scores = data["leaderboard"]["scores"]
        missing = EXPECTED_SCORE_KEYS - set(scores.keys())
        assert not missing, f"data.json.leaderboard.scores fehlt Keys: {missing}"

    def test_no_silent_csv_column_loss(self):
        """Defensive Cross-Check: jede CSV-Modul-Spalte hat einen LdbCols-Eintrag UND
        landet in data.json.leaderboard.scores. Verhindert stille Drift."""
        from scripts.web_export import LdbCols

        # 1. Sammle alle CSV-Modul-Spalten
        csv_path = ROOT / "benchmark_scores" / "benchmark_leaderboard_detailed.csv"
        with csv_path.open() as f:
            csv_cols = csv.DictReader(f).fieldnames
        # Identifiziere Modul-Spalten: alles ohne 'Tokens:', ohne 'Score', ohne 'Tests', etc.
        module_cols = [
            c for c in csv_cols
            if c not in (
                "Rank", "Model Name", "Model ID", "model_id_raw", "Version", "Provider Code",
                "Badge", "Speed Profile", "Thinking Mode", "Performance Tier", "Total Score",
                "Routine Score", "Reasoning Score", "Tokens/s", "Avg Task Duration (s)",
                "Initial Load Time (s)", "P95 Time (s)", "P95", "Max Time (s)",
                "Timeout Count", "Tokens Total", "Cost per 1K (USD)", "Benchmark Cost (USD)",
                "LLM Judge Avg", "LLM Judge Avg (raw)", "LLM Judge Coverage",
                "Vendor", "Size Class", "Type",
                "Code Quality Audit", "CLI Badge", "Logical Reasoning",
                "UX Writing & Microcopy", "Documentation Quality",
                "Content Transformation & Adaption", "Cultural Intelligence",
                "Tool Execution", "Synthesis Quality", "ToolUse Score",
                "Tests Run",
            )
            and not c.startswith("Tokens:")
        ]
        # module_cols sollte leer sein (alle echten Modul-Spalten sind in der Exclusion-Liste)
        assert module_cols == [], f"Unbekannte CSV-Modul-Spalten: {module_cols}"

        # 2. Sammle alle LdbCols-Konstanten, die zu Modul-Spalten gehoeren
        score_attrs = {
            "CODE_QUALITY", "CLI_BADGE", "UX_WRITING", "DOCUMENTATION_QUALITY",
            "CONTENT_TRANSFORMATION", "CULTURAL_INTELLIGENCE", "LOGICAL_REASONING",
            "SYNTHESIS_QUALITY", "TOOL_EXECUTION",
        }
        for attr in score_attrs:
            assert hasattr(LdbCols, attr), f"LdbCols.{attr} fehlt"


class TestDataJsonStructure:
    """Prueft Vollstaendigkeit der per-Modell data.json-Struktur."""

    def test_data_json_has_all_top_level_sections(self):
        """data.json muss alle 4 Top-Level-Sections haben."""
        m_dir = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "models"
        if not (m_dir / "claude-haiku-4-5" / "data.json").exists():
            pytest.skip("Web-Export noch nicht erstellt")
        data = json.loads((m_dir / "claude-haiku-4-5" / "data.json").read_text())
        for section in ("leaderboard", "political_compass", "files", "tooluse"):
            assert section in data, f"data.json fehlt Top-Level-Section: {section}"

    def test_files_has_comparisons_block(self):
        """files-Block enthaelt comparisons (Review/Bias-Review-Referenzen).

        Audit-Logs werden seit dem Dead-Weight-Cleanup nicht mehr exportiert
        (weder als Verzeichnis noch als files.audit_logs/files.audit_logs_flat
        in data.json) — sie werden im Frontend nirgends gerendert.
        report_available wird aus der Quell-Verzeichnisexistenz abgeleitet.
        """
        m_dir = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "models"
        if not (m_dir / "claude-haiku-4-5" / "data.json").exists():
            pytest.skip("Web-Export noch nicht erstellt")
        data = json.loads((m_dir / "claude-haiku-4-5" / "data.json").read_text())
        files = data["files"]
        assert "comparisons" in files
        # Audit-Log-Reste duerfen nach dem Cleanup nicht mehr vorhanden sein
        assert "audit_logs" not in files
        assert "audit_logs_flat" not in files

    def test_leaderboard_model_card_self_contained(self):
        """model_card muss self-contained sein (Pflichtfelder in jeder Card vorhanden).

        Hinweis: ``_strip_none()`` entfernt null-Werte beim Export — wenn ein
        Feld in der Card ``null`` ist, fehlt es im data.json. Templates nutzen
        ``if model.model_card.X`` (Truthy-Check) und verhalten sich korrekt.
        Daher testen wir nur, dass die Felder, die in Card NICHT null sind,
        auch im data.json landen.
        """
        m_dir = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "models"
        if not (m_dir / "claude-haiku-4-5" / "data.json").exists():
            pytest.skip("Web-Export noch nicht erstellt")
        # Original-Card lesen (Quelle der Wahrheit)
        card = json.loads(
            (ROOT / "benchmark_scores" / "model_cards" / "claude-haiku-4-5-20251001.json").read_text()
        )
        data = json.loads((m_dir / "claude-haiku-4-5" / "data.json").read_text())
        model_card = data["leaderboard"]["model_card"]
        # Felder, die in der Card NICHT null sind, muessen im data.json vorhanden sein
        for field in ("display_name", "summary", "context_window_k",
                      "knowledge_cutoff", "input_price_per_1m", "output_price_per_1m",
                      "params_total_b", "params_active_b"):
            if card.get(field) is not None:
                assert field in model_card, f"model_card fehlt {field!r} (war nicht-null in Card)"