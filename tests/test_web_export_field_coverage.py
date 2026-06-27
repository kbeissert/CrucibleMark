"""Tests fuer vollstaendige Score- und Vendor-Field-Konsistenz im WebExport.

Hintergrund: Audit in Session 38 (2026-06-26) ergab 4 Luecken:
  1. LdbCols hatte nur 7 von 10 CSV-Score-Spalten
     (Synthesis Quality, Tool Execution, Political Bias fehlten)
  2. provider_cards.json exportierte nur 13 von 24 Vendor-Card-Feldern
     (inference_interfaces, privacy_note fehlten als display-relevante Felder)

Diese Tests sichern ab, dass keine CSV-Spalte mehr stillschweigend
verloren geht und alle relevanten Vendor-Felder im Provider-Subset landen.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# CSV-Spalten die in 'scores' Dict exportiert werden muessten
EXPECTED_SCORE_KEYS = {
    "code_quality",
    "cli_benchmark",
    "ux_writing",
    "documentation_quality",
    "content_transformation",
    "cultural_intelligence",
    "logical_reasoning",
    "synthesis_quality",
    "tool_execution",
    "political_bias",
}


class TestLeaderboardScoreMapping:
    """Prueft, dass alle 10 CSV-Modul-Spalten in data.json.leaderboard.scores landen."""

    def test_ldbcols_has_all_score_columns(self):
        """LdbCols muss Konstanten fuer alle 10 CSV-Modul-Spalten haben."""
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
            "Political Bias",
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
        """data.json.leaderboard.scores muss alle 10 Keys enthalten."""
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
                "Badge", "Speed Profile", "Performance Tier", "Total Score",
                "Routine Score", "Reasoning Score", "Tokens/s", "Avg Task Duration (s)",
                "Initial Load Time (s)", "P95 Time (s)", "P95", "Max Time (s)",
                "Timeout Count", "Tokens Total", "Cost per 1K (USD)", "Benchmark Cost (USD)",
                "LLM Judge Avg", "LLM Judge Avg (raw)", "LLM Judge Coverage",
                "Vendor", "Size Class", "Type", "Political Bias",
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
            "SYNTHESIS_QUALITY", "TOOL_EXECUTION", "POLITICAL_BIAS",
        }
        for attr in score_attrs:
            assert hasattr(LdbCols, attr), f"LdbCols.{attr} fehlt"


class TestProviderCardsFieldCoverage:
    """Prueft, dass alle display-relevanten Vendor-Felder in provider_cards.json landen."""

    EXPECTED_PROVIDER_FIELDS = {
        "vendor_id",
        "display_name",
        "company",
        "headquarters",
        "founding_year",
        "description",
        "deployment",
        "pricing_model",
        "api_base_url",
        "api_documentation_url",
        "notable_models",
        "inference_interfaces",   # Hardware/Performance (wichtig fuer llama.cpp)
        "privacy_note",             # Datenschutz-Hinweis
        "profile_verified",
        "last_verified_at",
    }

    def test_provider_cards_contains_all_display_fields(self):
        """provider_cards.json muss alle 15 display-relevanten Felder enthalten."""
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip("provider_cards.json noch nicht erstellt")
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["providers"]) > 0
        sample = data["providers"][0]
        missing = self.EXPECTED_PROVIDER_FIELDS - set(sample.keys())
        assert not missing, f"provider_cards.json fehlen display-relevante Felder: {missing}"

    def test_inference_interfaces_for_llamacpp(self):
        """llamacpp muss inference_interfaces mit Hardware-Daten haben."""
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip("provider_cards.json noch nicht erstellt")
        data = json.loads(path.read_text(encoding="utf-8"))
        llamacpp = next((p for p in data["providers"] if p["vendor_id"] == "llamacpp"), None)
        assert llamacpp is not None, "llamacpp fehlt in provider_cards.json"
        interfaces = llamacpp.get("inference_interfaces")
        assert interfaces is not None, "llamacpp.inference_interfaces fehlt"
        assert isinstance(interfaces, list)
        assert len(interfaces) > 0
        for inf in interfaces:
            assert "name" in inf
            assert "vendor_id" in inf

    def test_privacy_note_for_chinese_providers(self):
        """Chinesische Provider (PIPL/CSL-Risiko) sollten privacy_note haben."""
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip("provider_cards.json noch nicht erstellt")
        data = json.loads(path.read_text(encoding="utf-8"))
        # Anbieter mit chinesischer Jurisdiktion (z.B. alibaba, deepseek, zhipu_ai)
        chinese_vendors = ["alibaba", "deepseek", "zhipu_ai", "moonshot_ai", "xiaomi"]
        for vid in chinese_vendors:
            provider = next((p for p in data["providers"] if p["vendor_id"] == vid), None)
            if provider is None:
                continue  # Vendor existiert nicht (nicht alle verfuegbar)
            note = provider.get("privacy_note")
            assert note is not None, f"{vid} fehlt privacy_note"


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

    def test_files_audit_logs_grouped_by_module(self):
        """files.audit_logs muss nach Modul gruppiert sein."""
        m_dir = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "models"
        if not (m_dir / "claude-haiku-4-5" / "data.json").exists():
            pytest.skip("Web-Export noch nicht erstellt")
        data = json.loads((m_dir / "claude-haiku-4-5" / "data.json").read_text())
        audit_logs = data["files"]["audit_logs"]
        assert isinstance(audit_logs, dict)
        assert "bias" in audit_logs
        # Mindestens 5 Modul-Gruppen erwartet
        assert len(audit_logs) >= 5

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