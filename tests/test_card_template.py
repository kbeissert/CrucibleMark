"""Tests für Card Template Loader und Validator."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.card_template import (
    CardFieldSpec,
    CardTemplate,
    clear_cache,
    load_card_template,
)


# ===========================================================================
# Loader-Tests
# ===========================================================================


class TestLoadCardTemplate:
    def setup_method(self) -> None:
        clear_cache()

    def test_model_template_loads(self) -> None:
        t = load_card_template("model")
        assert t.card_type == "model"
        assert t.version == "1.0.0"
        assert len(t.required_fields) > 30  # 39 erwartet

    def test_provider_template_loads(self) -> None:
        t = load_card_template("vendor")
        assert t.card_type == "vendor"
        assert t.version == "1.1.0"
        # 17 (vor v4.10.12 waren es 18 inkl. 'stats' — Stats-Feld entfernt)
        assert len(t.required_fields) == 17
        assert len(t.optional_fields) >= 3

    def test_unknown_card_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unbekannter card_type"):
            load_card_template("xyz")

    def test_required_field_names(self) -> None:
        t = load_card_template("model")
        assert "model_id" in t.required_field_names
        assert "display_name" in t.required_field_names
        assert "developer" in t.required_field_names

    def test_get_field_returns_spec(self) -> None:
        t = load_card_template("model")
        f = t.get_field("model_id")
        assert isinstance(f, CardFieldSpec)
        assert f.type == "str"
        assert f.required is True
        assert "risk_calc" in f.consumers

    def test_get_field_returns_none_for_unknown(self) -> None:
        t = load_card_template("model")
        assert t.get_field("nonexistent_field_xyz") is None

    def test_is_required_and_is_known(self) -> None:
        t = load_card_template("model")
        assert t.is_required("model_id") is True
        assert t.is_required("temperature") is False  # optional
        assert t.is_known("temperature") is True
        assert t.is_known("totally_unknown_xyz") is False

    def test_provider_deployment_sub_fields(self) -> None:
        t = load_card_template("vendor")
        f = t.get_field("deployment")
        assert f is not None
        assert "cloud_act_exposure" in f.sub_fields_required
        assert "applicable_law" in f.sub_fields_required
        assert len(f.sub_fields_required) == 7

    def test_template_caching(self) -> None:
        t1 = load_card_template("model")
        t2 = load_card_template("model")
        assert t1 is t2  # LRU-Cache


# ===========================================================================
# CardFieldSpec.is_unknown_sentinel
# ===========================================================================


class TestIsUnknownSentinel:
    def _spec(self) -> CardFieldSpec:
        return CardFieldSpec(
            name="x", type="str", required=True, default="TODO",
            description="", consumers=(), since="v1",
        )

    def test_none_is_sentinel(self) -> None:
        assert self._spec().is_unknown_sentinel(None) is True

    def test_todo_string_is_sentinel(self) -> None:
        assert self._spec().is_unknown_sentinel("TODO") is True

    def test_unknown_string_is_sentinel(self) -> None:
        assert self._spec().is_unknown_sentinel("unknown") is True

    def test_empty_string_is_sentinel(self) -> None:
        assert self._spec().is_unknown_sentinel("") is True
        assert self._spec().is_unknown_sentinel("   ") is True

    def test_real_value_is_not_sentinel(self) -> None:
        assert self._spec().is_unknown_sentinel("OpenAI") is False
        assert self._spec().is_unknown_sentinel(42) is False
        assert self._spec().is_unknown_sentinel(False) is False
        assert self._spec().is_unknown_sentinel(["item"]) is False

    def test_empty_list_is_sentinel(self) -> None:
        assert self._spec().is_unknown_sentinel([]) is True


# ===========================================================================
# Validator-Tests
# ===========================================================================


class TestValidateCard:
    def setup_method(self) -> None:
        # Lokale Imports damit patches pro Test aktiv sind
        from scripts.analysis import validate_cards as vc_module
        self.vc = vc_module
        clear_cache()

    def _write_card(self, cards_dir: Path, name: str, data: dict) -> Path:
        path = cards_dir / f"{name}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_valid_card_passes(self, tmp_path: Path) -> None:
        from utils.card_template import load_card_template
        template = load_card_template("vendor")
        card = {
            "vendor_id": "testprov",
            "display_name": "TestProv",
            "company": "Test Inc",
            "headquarters": "Test City",
            "founding_year": 2020,
            "pricing_model": "pay-per-token",
            "api_base_url": "https://api.testprov.example",
            "api_documentation_url": "https://docs.testprov.example",
            "deployment": {
                "cloud_act_exposure": False,
                "applicable_law": "EU",
                "data_residency": "EU",
                "gdpr_dpa_available": True,
                "eu_adequacy_decision": True,
                "data_retention_days": 30,
                "chinese_nsl_risk": "none",
            },
            "privacy_note": "Test note",
            "notable_models": ["TestProv-1"],
            "unknown": False,
            "generated_at": "2026-01-01T00:00:00+00:00",
            "last_verified_at": "2026-01-01",
            "verification_source": "https://example.com",
            "profile_verified": True,
            "profile_verified_at": "2026-01-01",
        }
        path = self._write_card(tmp_path, "testprov", card)
        report = self.vc.validate_card(path, template)
        assert report.is_valid, [i.message for i in report.issues]

    def test_missing_required_field_detected(self, tmp_path: Path) -> None:
        from utils.card_template import load_card_template
        template = load_card_template("model")
        # Karte ohne model_id
        card = {"display_name": "X", "developer": "Y"}
        path = self._write_card(tmp_path, "testmodel", card)
        report = self.vc.validate_card(path, template)
        assert not report.is_valid
        assert any(i.issue_type == "missing_required" for i in report.issues)

    def test_todo_sentinel_detected(self, tmp_path: Path) -> None:
        from utils.card_template import load_card_template
        template = load_card_template("model")
        card = {
            "model_id": "testmodel",
            "display_name": "TODO",  # Unknown-Sentinel
            "developer": "Y",
        }
        path = self._write_card(tmp_path, "testmodel", card)
        report = self.vc.validate_card(path, template)
        assert not report.is_valid
        assert any(i.issue_type == "unknown_sentinel" for i in report.issues)

    def test_extras_field_detected(self, tmp_path: Path) -> None:
        from utils.card_template import load_card_template
        template = load_card_template("vendor")
        card = {
            "vendor_id": "testprov",
            "display_name": "X",
            "company": "X",
            "headquarters": "X",
            "founding_year": 2020,
            "pricing_model": "unknown",
            "api_base_url": None,
            "api_documentation_url": None,
            "deployment": {},
            "privacy_note": "X",
            "notable_models": [],
            "stats": {},
            "unknown": False,
            "generated_at": None,
            "last_verified_at": None,
            "verification_source": None,
            "some_extra_field": "should be flagged",  # Drift
        }
        path = self._write_card(tmp_path, "testprov", card)
        report = self.vc.validate_card(path, template)
        drift = [i for i in report.issues if i.issue_type == "drift_extras"]
        assert any(i.field == "some_extra_field" for i in drift)

    def test_tooluse_extras_tolerated(self, tmp_path: Path) -> None:
        from utils.card_template import load_card_template
        template = load_card_template("model")
        card = {"model_id": "x", "display_name": "X", "tooluse_custom": "legacy"}
        path = self._write_card(tmp_path, "x", card)
        report = self.vc.validate_card(path, template)
        # tooluse_-Prefix ist toleriert
        drift = [i for i in report.issues if i.issue_type == "drift_extras" and i.field == "tooluse_custom"]
        assert drift == []

    def test_missing_sub_field_detected(self, tmp_path: Path) -> None:
        from utils.card_template import load_card_template
        template = load_card_template("vendor")
        card = {
            "vendor_id": "p", "display_name": "P", "company": "C",
            "headquarters": "HQ", "founding_year": 2020, "pricing_model": "unknown",
            "api_base_url": None, "api_documentation_url": None,
            "deployment": {"cloud_act_exposure": False},  # nur 1 von 7 Sub-Feldern
            "privacy_note": "n", "notable_models": [], "stats": {},
            "unknown": False, "generated_at": None, "last_verified_at": None,
            "verification_source": None,
        }
        path = self._write_card(tmp_path, "p", card)
        report = self.vc.validate_card(path, template)
        missing_sub = [i for i in report.issues if i.issue_type == "missing_sub_field"]
        assert len(missing_sub) == 6  # 7 - 1 vorhanden

    def test_parse_error_on_invalid_json(self, tmp_path: Path) -> None:
        from utils.card_template import load_card_template
        template = load_card_template("model")
        path = tmp_path / "bad.json"
        path.write_text("{invalid json", encoding="utf-8")
        report = self.vc.validate_card(path, template)
        assert not report.is_valid
        assert any(i.issue_type == "parse_error" for i in report.issues)

    def test_index_files_skipped(self, tmp_path: Path) -> None:
        """_index.json und ähnliche Helper werden ignoriert."""
        with patch.object(self.vc, "MODEL_CARDS_DIR", tmp_path):
            with patch.object(self.vc, "PROVIDER_CARDS_DIR", tmp_path):
                self._write_card(tmp_path, "_index", ["list", "not", "dict"])
                self._write_card(tmp_path, "True", {"m": 1})
                self._write_card(tmp_path, "real_card", {"model_id": "r"})
                reports = self.vc.validate_all("model")
                # _index und True werden gefiltert
                names = {r.card_file for r in reports}
                assert "_index.json" not in names
                assert "True.json" not in names
                assert "real_card.json" in names


# ===========================================================================
# CLI / Format-Tests
# ===========================================================================


class TestFormatReports:
    def test_text_report_summary(self) -> None:
        from scripts.analysis.validate_cards import (
            CardIssue, CardReport, format_text_report,
        )
        r1 = CardReport(card_file="a.json", card_id="a", is_valid=True)
        r2 = CardReport(card_file="b.json", card_id="b")
        r2.add_issue(CardIssue(
            card_file="b.json", card_id="b",
            issue_type="missing_required", field="x", message="missing x",
        ))
        out = format_text_report([r1, r2], "model")
        assert "MODEL" in out
        assert "Total cards:        2" in out
        assert "Valid:            1" in out
        assert "Invalid:          1" in out
        assert "missing_required" in out

    def test_json_report_structure(self) -> None:
        import json as _json
        from scripts.analysis.validate_cards import (
            CardIssue, CardReport, format_json_report,
        )
        r = CardReport(card_file="x.json", card_id="x")
        r.add_issue(CardIssue(
            card_file="x.json", card_id="x",
            issue_type="drift_extras", field="y", message="y drift",
        ))
        out = _json.loads(format_json_report([r], "vendor"))
        assert out["card_type"] == "vendor"
        assert out["total"] == 1
        assert out["invalid"] == 1
        assert out["cards"][0]["issues"][0]["field"] == "y"
