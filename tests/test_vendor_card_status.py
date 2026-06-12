"""Tests für Phase 22 (Card-Status-Tool) und Phase 23 (Provider-Detection-SSoT)."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest


# ===========================================================================
# Phase 22: Card-Status-Tool
# ===========================================================================


class TestProviderCardStatus:
    """get_vendor_card_status() liefert Audit-Readiness-Report."""

    def _write_card(self, cards_dir: Path, name: str, data: dict) -> Path:
        path = cards_dir / f"{name}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_empty_cards_dir_returns_zero(self, tmp_path: Path) -> None:
        """Leeres Verzeichnis → total=0, alle Counts=0."""
        with patch("utils.vendor_card_template.CARDS_DIR", tmp_path):
            from utils.vendor_card_template import get_vendor_card_status
            report = get_vendor_card_status(stale_days=90)
        assert report["total"] == 0
        assert report["verified"] == 0
        assert report["unknown"] == 0
        assert report["stale"] == 0
        assert report["parse_errors"] == 0
        assert report["by_provider"] == []

    def test_verified_card_recent_timestamp(self, tmp_path: Path) -> None:
        """Card mit recent last_verified_at → status=verified."""
        recent = datetime.now(timezone.utc) - timedelta(days=10)
        card = {
            "vendor_id": "testprov",
            "display_name": "TestProv",
            "deployment": {"cloud_act_exposure": False, "applicable_law": "EU"},
            "last_verified_at": recent.isoformat(),
        }
        self._write_card(tmp_path, "testprov", card)

        with patch("utils.vendor_card_template.CARDS_DIR", tmp_path):
            from utils.vendor_card_template import get_vendor_card_status
            report = get_vendor_card_status(stale_days=90)

        assert report["total"] == 1
        assert report["verified"] == 1
        assert report["stale"] == 0
        assert report["by_provider"][0]["status"] == "verified"

    def test_stale_card_old_timestamp(self, tmp_path: Path) -> None:
        """Card mit last_verified_at älter als stale_days → status=stale."""
        old = datetime.now(timezone.utc) - timedelta(days=120)
        card = {
            "vendor_id": "oldprov",
            "display_name": "OldProv",
            "deployment": {"cloud_act_exposure": False, "applicable_law": "EU"},
            "last_verified_at": old.isoformat(),
        }
        self._write_card(tmp_path, "oldprov", card)

        with patch("utils.vendor_card_template.CARDS_DIR", tmp_path):
            from utils.vendor_card_template import get_vendor_card_status
            report = get_vendor_card_status(stale_days=90)

        assert report["stale"] == 1
        assert report["by_provider"][0]["status"] == "stale"
        assert report["by_provider"][0]["age_days"] >= 120

    def test_unknown_flag_counts_as_unknown(self, tmp_path: Path) -> None:
        """Card mit unknown=true → status=unknown (auch wenn Timestamp neu)."""
        recent = datetime.now(timezone.utc).isoformat()
        card = {
            "vendor_id": "broken",
            "unknown": True,
            "last_verified_at": recent,
        }
        self._write_card(tmp_path, "broken", card)

        with patch("utils.vendor_card_template.CARDS_DIR", tmp_path):
            from utils.vendor_card_template import get_vendor_card_status
            report = get_vendor_card_status(stale_days=90)

        assert report["unknown"] == 1
        assert report["by_provider"][0]["status"] == "unknown"

    def test_missing_timestamp_counts_as_stale(self, tmp_path: Path) -> None:
        """Card ohne generated_at UND ohne last_verified_at → stale (kein-Timestamp)."""
        card = {
            "vendor_id": "notimestamp",
            "display_name": "NoTS",
        }
        self._write_card(tmp_path, "notimestamp", card)

        with patch("utils.vendor_card_template.CARDS_DIR", tmp_path):
            from utils.vendor_card_template import get_vendor_card_status
            report = get_vendor_card_status(stale_days=90)

        assert report["stale"] == 1
        assert report["missing_timestamp"] == 1
        assert report["by_provider"][0]["status"] == "stale"

    def test_parse_error_card_counted(self, tmp_path: Path) -> None:
        """Card mit kaputtem JSON → parse_error-Eintrag."""
        (tmp_path / "broken.json").write_text("{invalid json", encoding="utf-8")

        with patch("utils.vendor_card_template.CARDS_DIR", tmp_path):
            from utils.vendor_card_template import get_vendor_card_status
            report = get_vendor_card_status(stale_days=90)

        assert report["parse_errors"] == 1
        assert report["by_provider"][0]["status"] == "parse_error"

    def test_unknown_deployment_fields_detected(self, tmp_path: Path) -> None:
        """deployment-Felder mit 'unknown' oder -1 werden gemeldet."""
        recent = datetime.now(timezone.utc).isoformat()
        card = {
            "vendor_id": "incomplete",
            "display_name": "Incomplete",
            "deployment": {
                "cloud_act_exposure": False,
                "applicable_law": "EU",
                "data_residency": "EU",
                "gdpr_dpa_available": "unknown",
                "eu_adequacy_decision": True,
                "data_retention_days": -1,  # unknown
                "chinese_nsl_risk": "none",
            },
            "last_verified_at": recent,
        }
        self._write_card(tmp_path, "incomplete", card)

        with patch("utils.vendor_card_template.CARDS_DIR", tmp_path):
            from utils.vendor_card_template import get_vendor_card_status
            report = get_vendor_card_status(stale_days=90)

        assert report["cards_with_unknown_deployment_fields"] == 1
        fields = report["by_provider"][0]["unknown_deployment_fields"]
        assert "gdpr_dpa_available" in fields
        assert "data_retention_days" in fields

    def test_stale_threshold_echo(self, tmp_path: Path) -> None:
        """stale_threshold_days wird im Report zurückgegeben."""
        with patch("utils.vendor_card_template.CARDS_DIR", tmp_path):
            from utils.vendor_card_template import get_vendor_card_status
            report = get_vendor_card_status(stale_days=42)
        assert report["stale_threshold_days"] == 42

    def test_format_status_readable(self, tmp_path: Path) -> None:
        """format_vendor_card_status liefert lesbaren CLI-Output."""
        recent = datetime.now(timezone.utc).isoformat()
        card = {
            "vendor_id": "ok",
            "display_name": "OK Provider",
            "deployment": {"applicable_law": "EU"},
            "last_verified_at": recent,
        }
        self._write_card(tmp_path, "ok", card)

        with patch("utils.vendor_card_template.CARDS_DIR", tmp_path):
            from utils.vendor_card_template import (
                format_vendor_card_status,
                get_vendor_card_status,
            )
            report = get_vendor_card_status(stale_days=90)
            output = format_vendor_card_status(report)

        assert "=== Provider Card Status ===" in output
        assert "Total:" in output
        assert "Verified:" in output
        assert "Checked at:" in output


# ===========================================================================
# Phase 23: Provider-Detection-SSoT
# ===========================================================================


class TestProviderDetection:
    """utils.provider_detection.detect_provider_from_model_id() SSoT."""

    def test_openai_gpt5(self) -> None:
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("gpt-5.4") == "OpenAI"
        assert detect_provider_from_model_id("gpt-4o") == "OpenAI"
        assert detect_provider_from_model_id("gpt-3.5-turbo") == "OpenAI"
        assert detect_provider_from_model_id("o1-preview") == "OpenAI"
        assert detect_provider_from_model_id("o3-mini") == "OpenAI"

    def test_anthropic_claude(self) -> None:
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("claude-3-5-sonnet") == "Anthropic"
        assert detect_provider_from_model_id("claude-opus-4") == "Anthropic"
        assert detect_provider_from_model_id("claude-haiku-4-5") == "Anthropic"

    def test_google(self) -> None:
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("gemini-2.5-pro") == "Google"
        assert detect_provider_from_model_id("gemma-2-9b") == "Google"
        assert detect_provider_from_model_id("gemma") == "Google"

    def test_mistral_variants(self) -> None:
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("mistral-7b-instruct") == "Mistral AI"
        assert detect_provider_from_model_id("codestral-22b") == "Mistral AI"
        assert detect_provider_from_model_id("ministral-3:14b") == "Mistral AI"
        assert detect_provider_from_model_id("pixtral-12b") == "Mistral AI"

    def test_xai_grok(self) -> None:
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("grok-3") == "xAI"
        assert detect_provider_from_model_id("grok-4.1-fast-reasoning") == "xAI"

    def test_deepseek(self) -> None:
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("deepseek-chat") == "DeepSeek"
        assert detect_provider_from_model_id("deepseek-coder") == "DeepSeek"

    def test_alibaba_qwen(self) -> None:
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("qwen2.5-14b") == "Alibaba Cloud"

    def test_moonshot_kimi(self) -> None:
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("kimi-k2") == "Moonshot AI"

    def test_meta_llama(self) -> None:
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("llama-3.3-70b") == "Meta"
        assert detect_provider_from_model_id("llama-2-7b") == "Meta"

    def test_minimax(self) -> None:
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("minimax-M2") == "MiniMax"
        assert detect_provider_from_model_id("minimax-text-01") == "MiniMax"

    def test_unknown_returns_none(self) -> None:
        """Modelle ohne Match → None (vermutlich lokal)."""
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("my-local-llama-fork") is None
        assert detect_provider_from_model_id("random-7b") is None
        assert detect_provider_from_model_id("") is None
        assert detect_provider_from_model_id("gpt") is None  # gpt ohne - muss mit - folgen

    def test_case_insensitive(self) -> None:
        """Prefix-Match ist case-insensitive."""
        from utils.provider_detection import detect_provider_from_model_id
        assert detect_provider_from_model_id("GPT-4O") == "OpenAI"
        assert detect_provider_from_model_id("Claude-3-5-Sonnet") == "Anthropic"
        assert detect_provider_from_model_id("GEMINI-2.5-PRO") == "Google"

    def test_prefix_with_dash_requires_dash(self) -> None:
        """Prefix mit Trailing-Dash: muss mit - gefolgt werden."""
        from utils.provider_detection import detect_provider_from_model_id
        # "gpt" alleine matcht nicht — wir wollen keine false positives
        assert detect_provider_from_model_id("gpt") is None
        # Aber "gpt-..." matcht
        assert detect_provider_from_model_id("gpt-4o") == "OpenAI"

    def test_risk_calculator_uses_ssot(self) -> None:
        """risk_calculator.detect_provider() ruft die SSoT auf."""
        from scripts.analysis.review import risk_calculator
        from utils.provider_detection import detect_provider_from_model_id

        # Beide müssen für dieselbe Eingabe dasselbe liefern
        assert risk_calculator.detect_provider("gpt-4o") == detect_provider_from_model_id("gpt-4o")
        assert risk_calculator.detect_provider("claude-3-5-sonnet") == detect_provider_from_model_id("claude-3-5-sonnet")

    def test_risk_calculator_no_local_map(self) -> None:
        """risk_calculator hat keine eigene _CLOUD_PREFIX_TO_PROVIDER-Map mehr."""
        from scripts.analysis.review import risk_calculator

        # Wenn der Refactor nicht angewendet wurde, gibt es das Modul-Attribut noch.
        assert not hasattr(risk_calculator, "_CLOUD_PREFIX_TO_PROVIDER"), (
            "risk_calculator hat noch eine eigene Prefix-Map — SSoT-Konsolidierung fehlt!"
        )

    def test_prefix_map_is_public(self) -> None:
        """PROVIDER_PREFIX_MAP ist als SSoT öffentlich zugänglich."""
        from utils.provider_detection import PROVIDER_PREFIX_MAP

        assert isinstance(PROVIDER_PREFIX_MAP, dict)
        assert PROVIDER_PREFIX_MAP["gpt-"] == "OpenAI"
        assert PROVIDER_PREFIX_MAP["claude-"] == "Anthropic"
