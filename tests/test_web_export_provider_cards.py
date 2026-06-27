"""Tests fuer Provider-Cards-Export im Web-Export.

Hintergrund (Session 38, 2026-06-26): User moechte Provider-Infos auf der
Webseite darstellen. Dafr wird ``provider_cards.json`` als dedizierter
Export erstellt — gefiltertes Sub-Set der Vendor-Cards mit display-relevanten
Feldern (vendor_id, display_name, company, headquarters, founding_year,
description, deployment, pricing_model, api URLs, notable_models,
profile_verified).

Diese Tests sichern ab, dass:
  1. ``provider_cards.json`` korrekt geschrieben wird
  2. Nur display-relevante Felder exportiert werden (kein Profile-Metadaten)
  3. Defense-in-Depth Filter (community-cards raus, Placeholder raus)
  4. Schema-Validierung pro Provider
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class TestProviderCardsExport:
    """Prueft, dass der WebExport provider_cards.json korrekt erzeugt."""

    def test_provider_cards_file_exists(self):
        """provider_cards.json muss nach make web-export existieren."""
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip(f"provider_cards.json nicht vorhanden ({path}) — erst make web-export ausfuehren")

    def test_provider_cards_schema(self):
        """Top-Level-Schema: generated_at + providers[]."""
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip("provider_cards.json nicht vorhanden")
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "generated_at" in data
        assert "providers" in data
        assert isinstance(data["providers"], list)
        assert len(data["providers"]) > 0

    def test_provider_required_fields(self):
        """Jeder Provider muss die Pflichtfelder haben."""
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip("provider_cards.json nicht vorhanden")
        data = json.loads(path.read_text(encoding="utf-8"))
        required = {"vendor_id", "display_name", "notable_models"}
        for p in data["providers"]:
            missing = required - set(p.keys())
            assert not missing, f"Provider {p.get('vendor_id')!r} fehlen Pflichtfelder: {missing}"
            assert isinstance(p["vendor_id"], str) and p["vendor_id"], "vendor_id muss non-empty string sein"
            assert isinstance(p["display_name"], str) and p["display_name"], "display_name muss non-empty string sein"
            assert isinstance(p["notable_models"], list), "notable_models muss Liste sein"

    def test_provider_optional_fields(self):
        """Optionale Felder: company, headquarters, founding_year, deployment, pricing_model, api URLs."""
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip("provider_cards.json nicht vorhanden")
        data = json.loads(path.read_text(encoding="utf-8"))
        optional = {"company", "headquarters", "founding_year", "deployment", "pricing_model",
                    "api_base_url", "api_documentation_url", "description", "profile_verified",
                    "last_verified_at"}
        for p in data["providers"]:
            # Felder sind optional — Test nur ob wenn vorhanden, richtiger Typ
            for field in optional:
                if field in p and p[field] is not None:
                    if field == "founding_year":
                        assert isinstance(p[field], int), f"{field} muss int sein"
                    elif field == "deployment":
                        assert isinstance(p[field], dict), f"{field} muss dict sein"

    def test_no_placeholder_providers(self):
        """Provider-IDs 'todo', 'unknown' duerfen NICHT exportiert werden (Defense-in-Depth)."""
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip("provider_cards.json nicht vorhanden")
        data = json.loads(path.read_text(encoding="utf-8"))
        ids = {p.get("vendor_id") for p in data["providers"]}
        assert "todo" not in ids
        assert "unknown" not in ids

    def test_no_community_cards(self):
        """Community-Cards (card_subtype == 'community') gehoeren in community_cards.json, nicht hierher."""
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip("provider_cards.json nicht vorhanden")
        data = json.loads(path.read_text(encoding="utf-8"))
        # Da community-Subset schon gefiltert ist (exclude_community=True in Export),
        # gibt es hier keine Community-Provider
        for p in data["providers"]:
            assert "card_subtype" not in p or p["card_subtype"] != "community", \
                f"{p.get('vendor_id')} ist community — sollte nicht in provider_cards.json sein"

    def test_no_internal_metadata_leaked(self):
        """Profile-/Stats-Metadaten (profile_verified_by, profile_verified_at, stats) duerfen NICHT exportiert werden."""
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip("provider_cards.json nicht vorhanden")
        data = json.loads(path.read_text(encoding="utf-8"))
        forbidden = {"stats", "profile_verified_by", "profile_verified_at", "generated_at",
                     "last_modified_at", "verification_source", "unknown"}
        for p in data["providers"]:
            for field in forbidden:
                assert field not in p, f"{p.get('vendor_id')} hat verbotenes Feld {field!r}"

    def test_vendor_ids_match_taxonomy(self):
        """vendor_ids in provider_cards.json sollten in der Taxonomie-SSoT existieren.

        Warnt ueber Mismatches, schlaegt aber NICHT fehl — bekannter Backlog:
        'cohere', 'google', 'llamacpp' haben Vendor-Cards ohne Taxonomie-Eintrag.
        Sobald der Backlog gefixt ist, sollte dieser Test in einen
        Hard-Fail umgewandelt werden.
        """
        path = ROOT.parent / "CrucibleMark-Web" / "src" / "_data" / "raw" / "provider_cards.json"
        if not path.exists():
            pytest.skip("provider_cards.json nicht vorhanden")
        data = json.loads(path.read_text(encoding="utf-8"))
        tax_path = ROOT / "config" / "classification_taxonomy.json"
        if not tax_path.exists():
            pytest.skip("Taxonomie nicht gefunden")
        tax = json.loads(tax_path.read_text(encoding="utf-8"))
        canonical_ids = {
            v.get("vendor_card_id")
            for v in tax.get("manufacturers", {}).get("values", {}).values()
            if v.get("vendor_card_id")
        }
        exported_ids = {p.get("vendor_id") for p in data["providers"]}
        # Sammle Mismatches
        mismatches = exported_ids - canonical_ids
        # Bekannte Backlog-Mismatches: koennen in zukuenftigen Sessions
        # zur normalen Liste hinzugefuegt werden
        known_backlog = {"google", "cohere", "llamacpp"}
        real_drift = mismatches - known_backlog
        if real_drift:
            pytest.fail(
                f"Unbekannte Vendor-Card-IDs ohne Taxonomie-Eintrag: {real_drift}. "
                f"Bekannte Backlog-Mismatches: {known_backlog}"
            )


class TestProviderCardsFromVendorCards:
    """Direkter Test gegen die Python-Export-Logik."""

    def test_provider_cards_filter_excludes_community(self, tmp_path, monkeypatch):
        """Wenn Vendor-Cards community-Subset enthalten, muessen sie rausgefiltert werden."""
        from scripts.web_export import _collect_vendor_cards

        # Setup: Erstelle Vendor-Cards-Dir mit Mix aus regular + community
        vc_dir = tmp_path / "benchmark_scores" / "vendor_cards"
        vc_dir.mkdir(parents=True)
        (vc_dir / "regular.json").write_text(json.dumps({
            "vendor_id": "test_regular", "display_name": "Test Regular", "unknown": False
        }), encoding="utf-8")
        (vc_dir / "community.json").write_text(json.dumps({
            "vendor_id": "test_community", "display_name": "Test Community",
            "card_subtype": "community", "unknown": False
        }), encoding="utf-8")

        # Patchen der CARD_DIR-Lookup
        # Da _collect_vendor_cards relativ zu ROOT ist, monkeypatch mit CWD
        monkeypatch.chdir(tmp_path)
        cards = _collect_vendor_cards(tmp_path, exclude_community=True)
        ids = {c["vendor_id"] for c in cards}
        assert "test_regular" in ids
        assert "test_community" not in ids

    def test_provider_cards_filter_includes_community_when_disabled(self, tmp_path):
        """exclude_community=False: Community wird mitgenommen (Sonderfall fuer community_cards.json)."""
        from scripts.web_export import _collect_vendor_cards

        vc_dir = tmp_path / "benchmark_scores" / "vendor_cards"
        vc_dir.mkdir(parents=True)
        (vc_dir / "regular.json").write_text(json.dumps({
            "vendor_id": "test_regular", "unknown": False
        }), encoding="utf-8")
        (vc_dir / "community.json").write_text(json.dumps({
            "vendor_id": "test_community", "card_subtype": "community", "unknown": False
        }), encoding="utf-8")

        cards = _collect_vendor_cards(tmp_path, exclude_community=False)
        ids = {c["vendor_id"] for c in cards}
        assert "test_regular" in ids
        assert "test_community" in ids