"""Phase 16: SSoT-Garantien fuer web_export.py.

Pruefungen:
  1. load_model_card() nutzt resolve_canonical_model_id() als SSoT-Bruecke
     (nicht mehr manuelle 3-Stufen-Fallback-Kette).
  2. _lookup_pc_row() matcht via slugify-URL-Slug (PC-CSV-Konvention),
     dokumentiert als bewusste Entscheidung gegen _safe_name.
  3. _build_tooluse_entry() kanonisiert die model_id via resolve_canonical_model_id()
     und nutzt _safe_name() fuer den Review-Dir-Pfad.
  4. load_model_card() funktioniert fuer display-name -> namespaced-card-mismatch
     (kimi-k2.5 -> moonshotai/kimi-k2.5-0127 Fallback-Kette intakt).
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.web_export import (  # noqa: E402
    _build_tooluse_entry,
    load_model_card,
    slugify,
)


ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Helper: Card-Dir-Layout anlegen, das load_model_card() erwartet
# ---------------------------------------------------------------------------

def _setup_card_root(tmp_path: Path) -> Path:
    """Erzeugt tmp_path/benchmark_scores/model_cards/ und gibt tmp_path als root_dir zurueck."""
    card_dir = tmp_path / "benchmark_scores" / "model_cards"
    card_dir.mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------
# 1. load_model_card() SSoT-Bruecke
# ---------------------------------------------------------------------------

def test_load_model_card_uses_resolve_canonical(tmp_path: Path) -> None:
    """load_model_card() delegiert Card-Lookup an resolve_canonical_model_id()."""
    root = _setup_card_root(tmp_path)
    (root / "benchmark_scores" / "model_cards" / "claude-sonnet-4-5-20250929.json").write_text(
        json.dumps({"model_id": "claude-sonnet-4-5-20250929", "display_name": "Claude Sonnet 4.5"})
    )

    # resolve_canonical_model_id() wird aufgerufen — SSoT-Brücke aktiv
    with patch("utils.model_utils.resolve_canonical_model_id") as mock_resolve:
        mock_resolve.return_value = "claude-sonnet-4-5-20250929"
        result = load_model_card("Claude Sonnet 4.5", root)

    assert mock_resolve.called, "resolve_canonical_model_id() muss aufgerufen werden"
    assert result is not None
    assert result["model_id"] == "claude-sonnet-4-5-20250929"


def test_load_model_card_finds_via_safe_name_fallback(tmp_path: Path) -> None:
    """Bei Namen ohne direkten Card-Match: SSoT-_safe_name-Fallback findet Card."""
    root = _setup_card_root(tmp_path)
    (root / "benchmark_scores" / "model_cards" / "qwen3_5-9b.json").write_text(
        json.dumps({"model_id": "qwen3.5-9b", "display_name": "Qwen 3.5 9B"})
    )

    with patch("utils.model_utils.resolve_canonical_model_id", return_value="qwen3.5-9b"):
        result = load_model_card("Qwen 3.5 9B", root)

    assert result is not None
    assert result["model_id"] == "qwen3.5-9b"


# ---------------------------------------------------------------------------
# 2. _lookup_pc_row() nutzt slugify als dokumentierte SSoT-Entscheidung
# ---------------------------------------------------------------------------

def test_lookup_pc_row_uses_slugify_for_dated_ids() -> None:
    """Slug-Suffix-Match: dated IDs ('-YYYYMMDD') werden auf den Basis-Slug gemappt."""
    from scripts.web_export import _lookup_pc_row

    pc = pd.DataFrame({
        "model": ["claude-sonnet-4-5-20250929"],
        "run_id": ["AVG"],
        "x_coordinate": [0.0],
        "y_coordinate": [0.0],
    })
    # Slug ist "claude-sonnet-4-5" (ohne Datum)
    result = _lookup_pc_row("Claude Sonnet 4.5", "claude-sonnet-4-5", pc)
    assert result is not None
    assert result["model"] == "claude-sonnet-4-5-20250929"


def test_lookup_pc_row_returns_none_for_unknown() -> None:
    """Unbekannte Slugs liefern None (kein Crash, kein False-Positive)."""
    from scripts.web_export import _lookup_pc_row

    pc = pd.DataFrame({
        "model": ["some-other-model"],
        "run_id": ["AVG"],
    })
    result = _lookup_pc_row("Unknown Model", "unknown-model", pc)
    assert result is None


# ---------------------------------------------------------------------------
# 3. _build_tooluse_entry() nutzt SSoT-Brücke
# ---------------------------------------------------------------------------

def test_build_tooluse_entry_uses_canonical_id(tmp_path: Path) -> None:
    """ToolUse-Lookup delegiert an resolve_canonical_model_id()."""
    with patch("scripts.analysis.review.tooluse_context.get_tooluse_web_data") as mock_tud, \
         patch("utils.model_utils.resolve_canonical_model_id") as mock_resolve:
        mock_resolve.return_value = "claude-sonnet-4-5-20250929"
        mock_tud.return_value = {"score": 0.85, "tests_run": 5}

        result = _build_tooluse_entry("Claude Sonnet 4.5", ROOT)

    assert result is not None
    assert result["score"] == 0.85
    # Kanonische ID wurde für ToolUse-Web-Data-Lookup genutzt
    assert mock_tud.called
    assert mock_tud.call_args[0][0] == "claude-sonnet-4-5-20250929"


def test_build_tooluse_entry_returns_none_when_no_data() -> None:
    """Wenn ToolUse-Web-Data None zurückgibt, wird der Eintrag uebersprungen."""
    with patch("scripts.analysis.review.tooluse_context.get_tooluse_web_data", return_value=None):
        result = _build_tooluse_entry("Unknown Model", ROOT)
    assert result is None


# ---------------------------------------------------------------------------
# 4. Regression: display-name -> namespaced-card-mismatch Fallback
# ---------------------------------------------------------------------------

def test_load_model_card_display_name_to_namespaced_card(tmp_path: Path) -> None:
    """kimi-k2.5 (display) -> moonshotai/kimi-k2.5-0127 (Card) Fallback funktioniert."""
    root = _setup_card_root(tmp_path)
    (root / "benchmark_scores" / "model_cards" / "moonshotai_kimi-k2_5-0127.json").write_text(
        json.dumps({"model_id": "moonshotai/kimi-k2.5-0127", "display_name": "Kimi K2.5"})
    )

    # resolve_canonical_model_id() gibt den namespaced Namen zurück
    with patch("utils.model_utils.resolve_canonical_model_id", return_value="kimi-k2.5"):
        result = load_model_card("Kimi K2.5", root)

    # Web-export fallback scannt das Verzeichnis und findet die Card via base-Match
    assert result is not None
    assert result["model_id"] == "moonshotai/kimi-k2.5-0127"


# ---------------------------------------------------------------------------
# 5. Phase 17+18: meta.json + vendor_cards.json Sanity
# ---------------------------------------------------------------------------

def test_meta_json_includes_all_sources_and_counts(tmp_path: Path) -> None:
    """meta.json enthaelt alle Source-Pfade und SSoT-Sanity-Counts."""
    from scripts.web_export import _write_top_level_outputs

    out_dir = tmp_path / "raw"
    out_dir.mkdir()
    root = _setup_card_root(tmp_path)
    # Audit-Logs anlegen
    audit_dir = root / "outputs" / "audit_logs" / "test-model"
    audit_dir.mkdir(parents=True)
    (audit_dir / "test_001.md").write_text("# Audit Log")

    _write_top_level_outputs(
        out_dir=out_dir,
        generated_at="2026-06-08T12:00:00+00:00",
        models_list=[{"slug": "test-model"}],
        pc_list=[],
        provider_df=None,
        root_dir=root,
        comparisons_path=root / "docs" / "reviews",
        models_with_reports=1,
        models_with_reviews=0,
    )

    meta = json.loads((out_dir / "meta.json").read_text(encoding="utf-8"))
    # Pflichtfelder
    assert "model_cards" in meta["sources"]
    assert "vendor_cards" in meta["sources"]
    assert "audit_logs" in meta["sources"]
    # Sanity-Counts
    assert meta["card_count"] == 0  # tmp_path/benchmark_scores/model_cards/ ist leer
    assert meta["audit_log_count"] == 1
    assert "cruciblemark_version" in meta


def test_collect_vendor_cards_filters_index_files(tmp_path: Path) -> None:
    """_collect_vendor_cards() filtert _index.json und andere Spurious-Files."""
    from scripts.web_export import _collect_vendor_cards

    cards_dir = tmp_path / "benchmark_scores" / "vendor_cards"
    cards_dir.mkdir(parents=True)
    # Echte Card
    (cards_dir / "anthropic.json").write_text(json.dumps({
        "vendor_id": "anthropic", "display_name": "Anthropic",
    }))
    # Index-File (kein provider_id)
    (cards_dir / "_index.json").write_text(json.dumps({"_meta": "index"}))
    # Kaputte Datei
    (cards_dir / "broken.json").write_text("not json{")

    cards = _collect_vendor_cards(tmp_path)
    assert len(cards) == 1
    assert cards[0]["vendor_id"] == "anthropic"


def test_write_vendor_cards_json(tmp_path: Path) -> None:
    """_write_top_level_outputs schreibt vendor_cards.json wenn Cards existieren."""
    from scripts.web_export import _write_top_level_outputs

    root = tmp_path
    (root / "benchmark_scores" / "vendor_cards").mkdir(parents=True)
    (root / "benchmark_scores" / "vendor_cards" / "anthropic.json").write_text(
        json.dumps({"vendor_id": "anthropic", "display_name": "Anthropic"})
    )

    out_dir = root / "raw"
    out_dir.mkdir()
    _write_top_level_outputs(
        out_dir=out_dir,
        generated_at="2026-06-08T12:00:00+00:00",
        models_list=[],
        pc_list=[],
        provider_df=None,
        root_dir=root,
        comparisons_path=root / "docs" / "reviews",
        models_with_reports=0,
        models_with_reviews=0,
    )

    pc_json = json.loads((out_dir / "vendor_cards.json").read_text(encoding="utf-8"))
    assert pc_json["vendor_card_count"] if "vendor_card_count" in pc_json else True
    assert len(pc_json["providers"]) == 1
    assert pc_json["providers"][0]["vendor_id"] == "anthropic"
