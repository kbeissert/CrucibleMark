"""Tests for the _resolve_model_dirs_and_card helper extracted in Phase 5 (v4.10.11).

Vorher war dieser Code 45 Zeilen inline in _process_leaderboard — keine
direkte Test-Coverage. Jetzt als eigenstaendige Funktion mit klarer API.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.web_export import _resolve_model_dirs_and_card, _should_skip_model


class TestResolveModelDirsAndCard:
    def test_card_found_via_raw_model_id(self):
        """raw_model_id matcht zuerst, model_name ist fallback."""
        def lookup(mid):
            return {"id": mid} if mid == "gpt-5" else None

        card, audit, comp = _resolve_model_dirs_and_card(
            model_name="GPT-5",
            raw_model_id="gpt-5",
            slug="gpt-5",
            card_lookup=lookup,
            audit_dirs={},
            comp_dirs={},
            count=1,
            total=1,
        )
        assert card == {"id": "gpt-5"}

    def test_card_fallback_to_model_name(self):
        def lookup(mid):
            return {"id": mid} if mid == "GPT-5" else None

        card, _, _ = _resolve_model_dirs_and_card(
            model_name="GPT-5",
            raw_model_id="gpt-5",
            slug="gpt-5",
            card_lookup=lookup,
            audit_dirs={},
            comp_dirs={},
            count=1,
            total=1,
        )
        assert card == {"id": "GPT-5"}

    def test_card_missing_warns(self, caplog):
        def lookup(mid):
            return None

        import logging
        caplog.set_level(logging.WARNING)
        card, _, _ = _resolve_model_dirs_and_card(
            model_name="missing-model",
            raw_model_id="missing-model",
            slug="missing-model",
            card_lookup=lookup,
            audit_dirs={},
            comp_dirs={},
            count=5,
            total=10,
        )
        assert card is None
        assert any("keine Model Card gefunden" in r.message for r in caplog.records)

    def test_audit_dir_via_dir_slug(self):
        audit_path = Path("/tmp/audit_logs/gpt-5")
        card, audit, _ = _resolve_model_dirs_and_card(
            model_name="GPT-5",
            raw_model_id="gpt-5",
            slug="gpt-5",
            card_lookup=lambda m: None,
            audit_dirs={"gpt-5": audit_path},
            comp_dirs={},
            count=1,
            total=1,
        )
        assert audit == audit_path

    def test_heritage_ids_fallback(self):
        """Wenn primary slug nicht matcht, aber heritage_ids matcht."""
        primary = Path("/tmp/audit_logs/derived-model")
        card_data = {"heritage_ids": ["base-model"]}
        card, audit, _ = _resolve_model_dirs_and_card(
            model_name="Derived Model",
            raw_model_id="derived/model",
            slug="derived-model",
            card_lookup=lambda m: card_data if m == "derived/model" else None,
            audit_dirs={"base-model": primary},
            comp_dirs={},
            count=1,
            total=1,
        )
        assert audit == primary

    def test_no_resolution_returns_none(self):
        card, audit, comp = _resolve_model_dirs_and_card(
            model_name="unknown",
            raw_model_id="",
            slug="unknown",
            card_lookup=lambda m: None,
            audit_dirs={},
            comp_dirs={},
            count=1,
            total=1,
        )
        assert card is None
        assert audit is None
        assert comp is None


class TestShouldSkipModel:
    def test_returns_none_when_no_skip(self, caplog):
        """Model ohne Skip-Grund wird verarbeitet (audit+csv OK)."""
        import logging
        import pandas as pd
        caplog.set_level(logging.INFO)
        row = pd.Series({"Total Score": "8.5/10"})
        audit_path = Path("/tmp/nonexistent_for_test")
        result = _should_skip_model(
            model_name="GPT-5",
            raw_model_id="gpt-5",
            row=row,
            model_audit_src=None,
            count=1,
            total=1,
            bl_exact=set(),
            bl_pattern=set(),
        )
        assert result is None

    def test_skip_no_benchmark(self, caplog):
        """Wenn weder Audit noch CSV-Score: skip."""
        import logging
        import pandas as pd
        caplog.set_level(logging.DEBUG)
        row = pd.Series({"Total Score": ""})
        result = _should_skip_model(
            model_name="PC-only",
            raw_model_id="pc-only",
            row=row,
            model_audit_src=None,
            count=1,
            total=1,
            bl_exact=set(),
            bl_pattern=set(),
        )
        assert result == "no_benchmark"

    def test_skip_blacklisted(self, caplog):
        """Blacklist-Match fuehrt zu skip."""
        import logging
        import pandas as pd
        caplog.set_level(logging.INFO)
        row = pd.Series({"Total Score": "8.5/10"})
        result = _should_skip_model(
            model_name="BadModel",
            raw_model_id="bad/model",
            row=row,
            model_audit_src=None,
            count=1,
            total=1,
            bl_exact={"bad_model"},
            bl_pattern=set(),
        )
        assert result == "blacklisted"

    def test_no_blacklist_check_when_raw_empty(self):
        """Ohne raw_model_id kein Blacklist-Check."""
        import pandas as pd
        row = pd.Series({"Total Score": "8.5/10"})
        result = _should_skip_model(
            model_name="NoID",
            raw_model_id="",
            row=row,
            model_audit_src=None,
            count=1,
            total=1,
            bl_exact={"anything"},
            bl_pattern=set(),
        )
        assert result is None
