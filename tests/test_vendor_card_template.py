"""Tests für utils.vendor_card_template."""
from __future__ import annotations

import json
import tempfile


from utils.vendor_card_template import (
    PROVIDER_CARD_FIELD_NAMES,
    ensure_vendor_card,
    load_vendor_card,
    normalize_vendor_card_data,
)


class TestNormalizeProviderCardData:
    """normalize_vendor_card_data entfernt Legacy-Felder und ergänzt fehlende."""

    def test_legacy_fields_removed(self) -> None:
        """origin_country, summary, strengths, known_limitations, developer_jurisdiction,
        developer dürfen NICHT in der normalisierten Card erscheinen — sie gehören in
        die Model Card."""
        legacy = {
            "vendor_id": "anthropic",
            "origin_country": "USA",
            "developer_jurisdiction": "US",
            "summary": "Sollte weg sein",
            "strengths": ["Auch weg"],
            "known_limitations": ["Weg"],
            "developer": "Anthropic",
            "company": "Anthropic PBC",
            "headquarters": "San Francisco, CA, USA",
            "founding_year": 2021,
            "pricing_model": "free-tier+pay-per-token",
            "api_base_url": "https://api.anthropic.com",
            "deployment": {
                "cloud_act_exposure": True,
                "applicable_law": "US (CLOUD Act)",
                "data_residency": "USA",
                "gdpr_dpa_available": True,
                "eu_adequacy_decision": True,
                "data_retention_days": 30,
                "chinese_nsl_risk": "none",
            },
            "privacy_note": "Test note",
            "notable_models": ["Claude 3.5 Sonnet"],
            "verification_source": "https://www.anthropic.com/legal/privacy",
        }
        result = normalize_vendor_card_data(legacy)

        assert "origin_country" not in result
        assert "summary" not in result
        assert "strengths" not in result
        assert "known_limitations" not in result
        assert "developer_jurisdiction" not in result
        assert "developer" not in result

    def test_new_fields_preserved(self) -> None:
        """Korrekte Provider-Felder bleiben erhalten."""
        legacy = {
            "vendor_id": "anthropic",
            "display_name": "Anthropic",
            "company": "Anthropic PBC",
            "headquarters": "San Francisco, CA, USA",
            "founding_year": 2021,
            "pricing_model": "free-tier+pay-per-token",
            "api_base_url": "https://api.anthropic.com",
            "api_documentation_url": "https://docs.anthropic.com",
            "deployment": {
                "cloud_act_exposure": True,
                "applicable_law": "US (CLOUD Act)",
                "data_residency": "USA",
                "gdpr_dpa_available": True,
                "eu_adequacy_decision": True,
                "data_retention_days": 30,
                "chinese_nsl_risk": "none",
            },
            "privacy_note": "Test note",
            "notable_models": ["Claude 3.5 Sonnet"],
            "verification_source": "https://www.anthropic.com/legal/privacy",
            "stats": {},
            "unknown": False,
            "generated_at": "2026-06-02T21:00:00.000000+00:00",
            "last_verified_at": "2026-06-02",
        }
        result = normalize_vendor_card_data(legacy)

        assert result["vendor_id"] == "anthropic"
        assert result["privacy_note"] == "Test note"
        assert result["deployment"]["cloud_act_exposure"] is True
        assert result["unknown"] is False

    def test_all_template_fields_present(self) -> None:
        """Nach Normalisierung enthält die Card alle 16 Felder des Templates."""
        minimal = {"vendor_id": "test", "unknown": True}
        result = normalize_vendor_card_data(minimal)

        for field in PROVIDER_CARD_FIELD_NAMES:
            assert field in result, f"Feld {field!r} fehlt in normalisierter Card"


class TestEnsureProviderCard:
    """ensure_vendor_card erstellt eine saubere Default-Card oder ergänzt nur fehlende."""

    def test_creates_new_card(self, tmp_path: tempfile.TemporaryDirectory) -> None:
        """Bei nicht-existierender Datei wird eine komplette Default-Card geschrieben."""
        from utils.vendor_card_template import _cards_dir

        test_path = _cards_dir() / "_test_new_provider.json"
        if test_path.exists():
            test_path.unlink()

        ensure_vendor_card("new_provider", card_path=test_path)

        assert test_path.exists()
        data = json.loads(test_path.read_text(encoding="utf-8"))
        assert data["vendor_id"] == "new_provider"
        assert "deployment" in data
        assert data["deployment"]["cloud_act_exposure"] is False
        assert data["deployment"]["applicable_law"] == "Unknown"
        assert data["unknown"] is False

        test_path.unlink()

    def test_preserves_existing_values(self, tmp_path: tempfile.TemporaryDirectory) -> None:
        """Bestehende Felder bleiben erhalten; nur fehlende werden ergänzt."""
        from utils.vendor_card_template import _cards_dir

        test_path = _cards_dir() / "_test_preserve.json"
        test_path.write_text(
            json.dumps(
                {
                    "vendor_id": "preserve_test",
                    "display_name": "Existing Name",
                    "company": "Existing Co",
                    "privacy_note": "Existing note",
                    "unknown": False,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        ensure_vendor_card("preserve_test", card_path=test_path)

        data = json.loads(test_path.read_text(encoding="utf-8"))
        assert data["display_name"] == "Existing Name"
        assert data["company"] == "Existing Co"
        assert data["privacy_note"] == "Existing note"
        # Neue Default-Felder
        assert data["headquarters"] == "TODO"
        assert data["founding_year"] is None

        test_path.unlink()


class TestLoadProviderCard:
    """load_vendor_card liest existierende Cards korrekt."""

    def test_load_anthropic_card(self) -> None:
        """anthropic.json existiert und enthält alle erwarteten Felder."""
        card = load_vendor_card("anthropic")
        assert card is not None
        assert card["vendor_id"] == "anthropic"
        assert "deployment" in card
        assert card["deployment"]["cloud_act_exposure"] is True
        assert card["deployment"]["applicable_law"] == "US (CLOUD Act)"
        assert "origin_country" not in card
        assert "summary" not in card
        assert not card["unknown"]
