"""Tests für die Vendor-Card-Filterung in scripts/web_export.py.

Hintergrund: Der Web-Export schreibt ``vendor_cards.json`` und
``community_cards.json``. Seit 2026-06-26 werden Placeholder-Karten
(``todo``, ``unknown``) und Karten mit ``unknown=true`` nie in
``vendor_cards.json`` exportiert (Defense-in-Depth gegen JS-Loader-Bugs).
Community-Karten gehen ausschließlich in ``community_cards.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.web_export import (
    _PLACEHOLDER_VENDOR_IDS,
    _collect_community_cards,
    _collect_vendor_cards,
)


@pytest.fixture
def root_dir(tmp_path: Path) -> Path:
    """Synthetisches Repo-Root mit benchmark_scores/vendor_cards/-Struktur.

    Die _collect_vendor_cards-Funktion erwartet den Root-Pfad und haengt
    intern ``benchmark_scores/vendor_cards/`` an.
    """
    cards_dir = tmp_path / "benchmark_scores" / "vendor_cards"
    cards_dir.mkdir(parents=True)

    def write(name: str, data: dict) -> None:
        (cards_dir / name).write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # Kanonischer Hersteller (soll in vendor_cards.json bleiben)
    write("anthropic.json", {
        "vendor_id": "anthropic", "display_name": "Anthropic", "unknown": False,
    })
    # Zweiter kanonischer Hersteller
    write("openai.json", {
        "vendor_id": "openai", "display_name": "OpenAI", "unknown": False,
    })
    # Placeholder via unknown=true
    write("zombie.json", {
        "vendor_id": "zombie", "display_name": "Zombie", "unknown": True,
    })
    # Placeholder via ID-Match
    write("todo.json", {
        "vendor_id": "todo", "display_name": "TODO", "unknown": False,
    })
    write("unknown.json", {
        "vendor_id": "unknown", "display_name": "Unknown", "unknown": False,
    })
    # Community-Card (soll in community_cards.json, nicht in vendor_cards.json)
    write("hauhaucs.json", {
        "vendor_id": "hauhaucs", "display_name": "HauhauCS",
        "unknown": False, "card_subtype": "community",
    })
    write("unsloth.json", {
        "vendor_id": "unsloth", "display_name": "Unsloth",
        "unknown": False, "card_subtype": "community",
    })
    # Index-File (kein vendor_id, soll komplett ignoriert werden)
    write("_index.json", {"entries": ["anthropic", "openai"]})
    # Defekte JSON (soll stillschweigend uebersprungen werden)
    (cards_dir / "broken.json").write_text("not valid json", encoding="utf-8")

    return tmp_path


class TestPlaceholderFilter:
    def test_placeholder_vendor_ids_constant(self):
        """SSoT: nur 'todo' und 'unknown' sind Platzhalter-IDs."""
        assert _PLACEHOLDER_VENDOR_IDS == frozenset({"todo", "unknown"})

    def test_unknown_true_filtered(self, root_dir):
        """Karten mit unknown=true werden in JEDEM Filter-Modus uebersprungen."""
        cards = _collect_vendor_cards(root_dir)
        vids = [c["vendor_id"] for c in cards]
        assert "zombie" not in vids, "unknown=true Card darf nicht exportiert werden"

    def test_todo_unknown_ids_filtered(self, root_dir):
        """Karten mit vendor_id 'todo'/'unknown' werden gefiltert."""
        cards = _collect_vendor_cards(root_dir)
        vids = [c["vendor_id"] for c in cards]
        assert "todo" not in vids
        assert "unknown" not in vids


class TestExcludeCommunity:
    def test_default_includes_community(self, root_dir):
        """Default: Community-Cards sind enthalten."""
        cards = _collect_vendor_cards(root_dir)
        vids = [c["vendor_id"] for c in cards]
        assert "hauhaucs" in vids
        assert "unsloth" in vids

    def test_exclude_community(self, root_dir):
        """``exclude_community=True``: Community-Cards raus, Hersteller-Cards bleiben."""
        cards = _collect_vendor_cards(root_dir, exclude_community=True)
        vids = [c["vendor_id"] for c in cards]
        assert sorted(vids) == ["anthropic", "openai"]
        assert "hauhaucs" not in vids
        assert "unsloth" not in vids

    def test_community_cards_helper(self, root_dir):
        """_collect_community_cards gibt nur Community-Subset zurueck."""
        cards = _collect_community_cards(root_dir)
        vids = sorted([c["vendor_id"] for c in cards])
        assert vids == ["hauhaucs", "unsloth"]


class TestRobustness:
    def test_index_file_ignored(self, root_dir):
        """_index.json ohne 'vendor_id'-Key wird komplett ignoriert."""
        cards = _collect_vendor_cards(root_dir)
        # Weder ein Eintrag mit vendor_id '_index' noch Crashes
        assert all("vendor_id" in c for c in cards)

    def test_broken_json_ignored(self, root_dir):
        """Defekte JSON-Datei fuehrt nicht zum Crash, sondern wird uebersprungen."""
        cards = _collect_vendor_cards(root_dir)
        # Wenn wir hier ankommen, ist der Test bestanden.
        assert isinstance(cards, list)

    def test_empty_dir(self, tmp_path):
        """Leeres vendor_cards/-Verzeichnis liefert leere Liste."""
        (tmp_path / "vendor_cards").mkdir()
        assert _collect_vendor_cards(tmp_path) == []
        assert _collect_vendor_cards(tmp_path, exclude_community=True) == []

    def test_missing_dir(self, tmp_path):
        """Nicht-existierendes vendor_cards/-Verzeichnis liefert leere Liste."""
        assert _collect_vendor_cards(tmp_path) == []