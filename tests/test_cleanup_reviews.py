"""Phase 27: Tests fuer ``scripts/maintenance/cleanup_reviews.py``.

Sichert:
- ``find_old_reviews()`` markiert nur non-latest Reviews zur Loeschung.
- Pro Kategorie (Benchmark, Bias, Tool-Use) wird nur 1 behalten.
- ``.gitkeep`` und ``.DS_Store`` werden ignoriert.
- Verzeichnisnamen mit Sonderzeichen werden via ``_safe_name`` normalisiert.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.maintenance import cleanup_reviews  # noqa: E402


# ---------------------------------------------------------------------------
# find_old_reviews
# ---------------------------------------------------------------------------

def test_find_old_reviews_empty_dir(tmp_path):
    """Leeres reviews/-Verzeichnis liefert leere Liste."""
    reviews_dir = tmp_path / "reviews"
    reviews_dir.mkdir()
    assert cleanup_reviews.find_old_reviews(reviews_dir) == []


def test_find_old_reviews_nonexistent_dir(tmp_path):
    """Nicht existierendes reviews/-Verzeichnis liefert leere Liste."""
    reviews_dir = tmp_path / "does_not_exist"
    assert cleanup_reviews.find_old_reviews(reviews_dir) == []


def test_find_old_reviews_keeps_latest_of_each_category(tmp_path):
    """Pro Modell und Kategorie wird nur der neueste Review behalten."""
    model_dir = tmp_path / "model_a"
    model_dir.mkdir()

    # 3 Benchmark-Reviews (1 sollte bleiben, 2 loeschen)
    (model_dir / "review_20260101_120000.md").write_text("v1")
    (model_dir / "review_20260201_120000.md").write_text("v2")
    (model_dir / "review_20260301_120000.md").write_text("v3")

    # 2 Bias-Reviews (1 sollte bleiben, 1 loeschen)
    (model_dir / "bias_review_20260101_120000.md").write_text("b1")
    (model_dir / "bias_review_20260201_120000.md").write_text("b2")

    # 2 Tool-Use-Reviews (1 sollte bleiben, 1 loeschen)
    (model_dir / "tooluse_narrative_review_20260101_120000.md").write_text("t1")
    (model_dir / "tooluse_narrative_review_20260201_120000.md").write_text("t2")

    to_delete = cleanup_reviews.find_old_reviews(tmp_path)

    # 2 + 1 + 1 = 4 Loeschungen
    assert len(to_delete) == 4
    names = {f.name for f in to_delete}
    assert "review_20260101_120000.md" in names
    assert "review_20260201_120000.md" in names
    assert "bias_review_20260101_120000.md" in names
    assert "tooluse_narrative_review_20260101_120000.md" in names
    # Neueste bleiben NICHT in der Loeschliste
    assert "review_20260301_120000.md" not in names
    assert "bias_review_20260201_120000.md" not in names
    assert "tooluse_narrative_review_20260201_120000.md" not in names


def test_find_old_reviews_keeps_only_one_when_no_timestamp(tmp_path):
    """Dateien ohne Timestamp bekommen Default-Wert — die lexikographisch spaeteste gewinnt."""
    model_dir = tmp_path / "model_a"
    model_dir.mkdir()
    (model_dir / "review_no_ts.md").write_text("x")
    to_delete = cleanup_reviews.find_old_reviews(tmp_path)
    # Kein Match in der Sortierung → keine Loeschung
    assert to_delete == []


def test_find_old_reviews_handles_multiple_models(tmp_path):
    """Mehrere Modell-Verzeichnisse werden unabhaengig voneinander bereinigt."""
    for m in ("model_a", "model_b"):
        d = tmp_path / m
        d.mkdir()
        (d / "review_20260101_120000.md").write_text("x")
        (d / "review_20260201_120000.md").write_text("x")

    to_delete = cleanup_reviews.find_old_reviews(tmp_path)
    # Pro Modell 1 Loeschung → 2 total
    assert len(to_delete) == 2
    # Alle beide Modell-Verzeichnisse vertreten
    parents = {f.parent.name for f in to_delete}
    assert parents == {"model_a", "model_b"}


def test_find_old_reviews_ignores_gitkeep_and_ds_store(tmp_path):
    """.gitkeep und .DS_Store werden ignoriert (auch als pseudo-Dateien)."""
    # Pseudo-Dateien mit .gitkeep / .DS_Store Namen anlegen
    (tmp_path / ".gitkeep").write_text("x")
    (tmp_path / ".DS_Store").write_text("x")
    to_delete = cleanup_reviews.find_old_reviews(tmp_path)
    # .gitkeep und .DS_Store werden nicht durchgegangen
    assert to_delete == []


def test_find_old_reviews_handles_model_dir_with_special_chars(tmp_path):
    """Verzeichnisnamen mit Sonderzeichen werden via _safe_name normalisiert (kein Crash)."""
    # Wichtig: das ist Phase 27 — _safe_name wird aufgerufen, der Slug darf
    # nicht in der Loeschung landen (er wird nur als Key berechnet)
    model_dir = tmp_path / "qwen3.5-35b-a3b-q8"
    model_dir.mkdir()
    (model_dir / "review_20260101_120000.md").write_text("v1")
    (model_dir / "review_20260201_120000.md").write_text("v2")
    to_delete = cleanup_reviews.find_old_reviews(tmp_path)
    assert len(to_delete) == 1
    assert to_delete[0].name == "review_20260101_120000.md"


def test_find_old_reviews_returns_list_of_paths():
    """find_old_reviews() gibt eine Liste von Path-Objekten zurueck."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        to_delete = cleanup_reviews.find_old_reviews(td_path)
        assert isinstance(to_delete, list)
        for f in to_delete:
            assert isinstance(f, Path)


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

def test_sort_key_extracts_timestamp():
    """_sort_key() extrahiert den Timestamp oder gibt Default zurueck."""
    p1 = Path("review_20260101_120000.md")
    p2 = Path("review_20260201_120000.md")
    p3 = Path("no_timestamp.md")
    assert cleanup_reviews._sort_key(p1) == "20260101_120000"
    assert cleanup_reviews._sort_key(p2) == "20260201_120000"
    assert cleanup_reviews._sort_key(p3) == "00000000_000000"


def test_reviews_dir_constant_points_to_docs_reviews():
    """REVIEWS_DIR ist docs/reviews im Projekt-Root."""
    assert cleanup_reviews.REVIEWS_DIR.name == "reviews"
    assert cleanup_reviews.REVIEWS_DIR.parent.name == "docs"
