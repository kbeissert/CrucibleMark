"""Testet den Flat-Column-Fallback in _load_asset_details() (tooluse_context.py).

Neuere Benchmark-Runs schreiben P1/P2/combined als direkte CSV-Spalten statt
im score_contributions-Dict. Der Fallback muss diese Spalten korrekt lesen.
"""

from __future__ import annotations

import csv
import textwrap
from pathlib import Path

import pytest

import utils.export.tooluse_context as tc


@pytest.fixture()
def _fake_benchmark_csvs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Erzeugt drei leere Benchmark-CSVs mit nur einem tooluse-Asset."""
    csv_dir = tmp_path / "benchmark_scores"
    csv_dir.mkdir(parents=True, exist_ok=True)

    flat_row = {
        "model": "test/model-v1",
        "asset_id": "tooluse001",
        "status": "success",
        "timestamp": "2026-01-01T00:00:00Z",
        # score_contributions bleibt leer — Fallback muss greifen
        "score_contributions": "",
        "p1_score": "85",
        "p2_score": "70",
        "combined_score": "77.5",
        "hallucination_flag": "false",
    }

    for name in ("local_models_benchmark.csv", "cloud_models_benchmark.csv", "commercial_models_benchmark.csv"):
        path = csv_dir / name
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(flat_row))
            writer.writeheader()
            writer.writerow(flat_row)

    monkeypatch.setattr(tc, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(tc, "_BENCHMARK_CSVS", [
        f"benchmark_scores/{name}"
        for name in ("local_models_benchmark.csv", "cloud_models_benchmark.csv", "commercial_models_benchmark.csv")
    ])
    return csv_dir


def test_load_asset_details_fallback_reads_flat_columns(_fake_benchmark_csvs: Path) -> None:
    """_load_asset_details() muss P1/P2/Combined aus flachen CSV-Spalten lesen
    wenn score_contributions leer ist."""
    details = tc._load_asset_details("test/model-v1")

    assert len(details) >= 1, "Mindestens ein Asset muss gefunden werden"
    asset = details[0]
    d = asset["data"]

    assert float(d["p1_score"]) == 85.0
    assert float(d["p2_score"]) == 70.0
    assert float(d["combined_score"]) == 77.5
    assert d["hallucination_flag"] == "false"


def test_load_asset_details_prefers_score_contributions(_fake_benchmark_csvs: Path, tmp_path: Path) -> None:
    """Wenn score_contributions befüllt ist, wird es bevorzugt — kein Fallback."""
    csv_dir = tmp_path / "benchmark_scores"
    row_with_contribs = {
        "model": "test/model-v2",
        "asset_id": "tooluse001",
        "status": "success",
        "timestamp": "2026-01-01T00:00:00Z",
        "score_contributions": str({
            "p1_score": 90, "p2_score": 60, "combined_score": 75.0, "hallucination_flag": True,
        }),
        "p1_score": "85",
        "p2_score": "70",
        "combined_score": "77.5",
        "hallucination_flag": "false",
    }

    for name in ("local_models_benchmark.csv", "cloud_models_benchmark.csv", "commercial_models_benchmark.csv"):
        path = csv_dir / name
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row_with_contribs))
            writer.writeheader()
            writer.writerow(row_with_contribs)

    details = tc._load_asset_details("test/model-v2")
    d = details[0]["data"]

    # score_contributions-Werte bevorzugt (90 statt 85)
    assert float(d["p1_score"]) == 90.0
    assert float(d["p2_score"]) == 60.0
    assert d["hallucination_flag"] is True


def test_load_asset_details_empty_csv_returns_empty(_fake_benchmark_csvs: Path, tmp_path: Path) -> None:
    """Modell ohne Einträge → leere Liste."""
    details = tc._load_asset_details("nonexistent/model")
    assert details == []


def test_load_asset_details_dedup_duplicates(_fake_benchmark_csvs: Path, tmp_path: Path) -> None:
    """Zwei CSV-Zeilen mit unterschiedlicher model-ID aber gleichem kanonischen
    Modell und gleicher asset_id dürfen nicht zu doppelten Assets führen.

    Reales Beispiel: gpt-5.4-nano (Punkt) und gpt-5_4-nano-2026-03-17 (Underscore)
    lösen beide auf denselben kanonischen Namen auf — tooluse001–006 dürfen nur
    je einmal im Ergebnis erscheinen.
    """
    from unittest.mock import patch

    csv_dir = tmp_path / "benchmark_scores"
    fieldnames = ["model", "asset_id", "status", "timestamp",
                  "score_contributions", "p1_score", "p2_score",
                  "combined_score", "hallucination_flag"]
    # Zwei verschiedene Raw-IDs, die denselben kanonischen Namen haben
    rows = [
        {"model": "gpt-5.4-nano", "asset_id": f"tooluse00{i}", "status": "success",
         "timestamp": "2026-01-01T00:00:00Z", "score_contributions": "",
         "p1_score": "80", "p2_score": "50", "combined_score": "65",
         "hallucination_flag": "false"}
        for i in range(1, 4)
    ] + [
        {"model": "gpt-5_4-nano-2026-03-17", "asset_id": f"tooluse00{i}", "status": "success",
         "timestamp": "2026-01-01T00:00:00Z", "score_contributions": "",
         "p1_score": "80", "p2_score": "50", "combined_score": "65",
         "hallucination_flag": "false"}
        for i in range(1, 4)
    ]
    for name in ("local_models_benchmark.csv", "cloud_models_benchmark.csv", "commercial_models_benchmark.csv"):
        path = csv_dir / name
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    # Mock: beide IDs lösen auf denselben kanonischen Namen auf
    with patch.object(tc, "ROOT_DIR", tmp_path), \
         patch.object(tc, "_BENCHMARK_CSVS", [
             f"benchmark_scores/{n}" for n in
             ("local_models_benchmark.csv", "cloud_models_benchmark.csv", "commercial_models_benchmark.csv")
         ]), \
         patch("utils.model_utils.resolve_canonical_model_id",
               side_effect=lambda mid: "gpt-5_4-nano-2026-03-17" if "nano" in mid else mid):
        details = tc._load_asset_details("gpt-5_4-nano-2026-03-17")

    asset_ids = [d["asset_id"] for d in details]
    assert len(details) == 3, f"Expected 3 unique assets, got {len(details)}: {asset_ids}"
    assert len(set(asset_ids)) == 3, f"Duplicate asset_ids found: {asset_ids}"