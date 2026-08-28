"""Tests für Vendor-Card-Drift-Detection im Web-Export.

Hintergrund: Wenn die Taxonomie (``classification_taxonomy.json``) auf
``vendor_card_id``s verweist, die nicht als Datei in
``benchmark_scores/vendor_cards/`` existieren, zeigen die Web-Refs ins Leere.
Der Web-Export-Loader kann das nicht von selbst erkennen — Python muss
es beim Export melden.

Dieser Test simuliert das Szenario, indem er ein minimales Vendor-Card-Verzeichnis
mit einer Datei baut, deren ID NICHT in der Taxonomie steht. Wenn die Drift-Detection
aktiv ist, muss sie den Drift erkennen.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class TestVendorCardDriftDetection:
    """Prueft, dass die Taxonomie-vs-Filesystem-Drift erkannt wird."""

    def test_drift_detected_when_taxonomy_points_to_missing_card(self, tmp_path, caplog):
        """Taxonomie kennt eine vendor_card_id, die Datei fehlt -> WARN-Log."""
        from scripts.web_export import _build_vendor_card_id_lookup, _collect_vendor_cards

        # Taxonomie schreibt 'ghost_vendor' als vendor_card_id vor
        taxonomy = {
            "manufacturers": {
                "values": {
                    "GhostVendor": {
                        "vendor_card_id": "ghost_vendor",
                        "label": "Ghost",
                    }
                }
            }
        }
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "classification_taxonomy.json").write_text(
            __import__("json").dumps(taxonomy), encoding="utf-8"
        )

        # Vendor-Cards-Dir: nur 'real_vendor.json' existiert (ghost_vendor fehlt)
        cards_dir = tmp_path / "benchmark_scores" / "vendor_cards"
        cards_dir.mkdir(parents=True)
        (cards_dir / "real_vendor.json").write_text(
            '{"vendor_id": "real_vendor", "display_name": "Real", "unknown": false}',
            encoding="utf-8",
        )
        (cards_dir / "_index.json").write_text("[]", encoding="utf-8")

        # 1. Build lookup from taxonomy (simulates _init_export_context)
        lookup = _build_vendor_card_id_lookup(config_dir)
        assert lookup == {"GhostVendor": "ghost_vendor"}

        # 2. Build set of existing vendor_card_ids from files
        existing_ids = {
            c["vendor_id"]
            for c in _collect_vendor_cards(tmp_path, exclude_community=True)
            if c.get("vendor_id")
        }
        assert existing_ids == {"real_vendor"}

        # 3. Drift-Detection: ids in lookup aber nicht in existing
        drift = set(lookup.values()) - existing_ids
        assert drift == {"ghost_vendor"}, (
            "Drift-Detection muss 'ghost_vendor' als fehlend erkennen"
        )

    def test_no_drift_when_taxonomy_matches_filesystem(self, tmp_path):
        """Sauberer Zustand: alle Taxonomie-IDs existieren als Dateien."""
        from scripts.web_export import _build_vendor_card_id_lookup, _collect_vendor_cards
        import json

        taxonomy = {
            "manufacturers": {
                "values": {
                    "Acme": {"vendor_card_id": "acme", "label": "Acme"},
                }
            }
        }
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "classification_taxonomy.json").write_text(
            json.dumps(taxonomy), encoding="utf-8"
        )

        cards_dir = tmp_path / "benchmark_scores" / "vendor_cards"
        cards_dir.mkdir(parents=True)
        (cards_dir / "acme.json").write_text(
            '{"vendor_id": "acme", "display_name": "Acme", "unknown": false}',
            encoding="utf-8",
        )
        (cards_dir / "_index.json").write_text("[]", encoding="utf-8")

        lookup = _build_vendor_card_id_lookup(config_dir)
        existing_ids = {
            c["vendor_id"]
            for c in _collect_vendor_cards(tmp_path, exclude_community=True)
            if c.get("vendor_id")
        }
        drift = set(lookup.values()) - existing_ids
        assert drift == set(), f"Kein Drift erwartet, aber gefunden: {drift}"

    def test_existing_community_filter(self, tmp_path):
        """Community-Karten zaehlen NICHT zum Drift-Check."""
        from scripts.web_export import _collect_vendor_cards
        import json

        cards_dir = tmp_path / "benchmark_scores" / "vendor_cards"
        cards_dir.mkdir(parents=True)
        (cards_dir / "anthropic.json").write_text(
            '{"vendor_id": "anthropic", "display_name": "A", "unknown": false}',
            encoding="utf-8",
        )
        (cards_dir / "hauhaucs.json").write_text(
            json.dumps({
                "vendor_id": "hauhaucs", "display_name": "H",
                "unknown": False, "card_subtype": "community",
            }),
            encoding="utf-8",
        )
        (cards_dir / "_index.json").write_text("[]", encoding="utf-8")

        existing = {
            c["vendor_id"]
            for c in _collect_vendor_cards(tmp_path, exclude_community=True)
        }
        # hauhaucs ist Community und wird mit exclude_community=True rausgefiltert
        assert "anthropic" in existing
        assert "hauhaucs" not in existing, (
            "Community-Cards muessen mit exclude_community=True ausgeklammert sein"
        )
