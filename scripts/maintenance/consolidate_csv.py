#!/usr/bin/env python3
"""
CSV Consolidation Script
========================
Reduziert Benchmark-CSV-Dateien auf den jeweils letzten (aktuellsten) Eintrag
pro Modell und Asset.

Funktion:
1. Lädt CSV.
2. Sortiert nach Timestamp (neueste zuerst).
3. Dedupliziert basierend auf ['model', 'asset_id'].
4. Validiert jede Zeile gegen Sanitizer-Heuristiken (Phase 9, Defense-in-Depth).
5. Überschreibt die originale CSV mit den bereinigten Daten.

Defense-in-Depth: Die gleichen Heuristiken wie `sanitize_benchmark_csvs.py`
filtern korrupte Zeilen raus, BEVOR sie zurückgeschrieben werden. Verhindert
dass Phase-8-Erfolg durch nachfolgende Maintenance zunichtegemacht wird.

Usage:
    python scripts/consolidate_csv.py
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Füge Projekt-Root zu sys.path hinzu für Imports
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

# Importiere robusten CSV-Loader
from utils.csv_recovery import load_csv_robust
# Defense-in-Depth: wiederverwendbare Sanitizer-Heuristiken
from scripts.maintenance.sanitize_benchmark_csvs import (
    _is_narrative_asset_id,
    _is_invalid_model,
)

# Konfiguration
# Tupel: (Pfad, Deduplizierungs-Schlüsselspalten)
# Benchmark-CSVs: eindeutig pro Modell + Asset
# Leaderboard-CSVs: eindeutig pro Modell (bereits aggregiert, kein asset_id)
CSV_FILES = [
    (Path("benchmark_scores/local_models_benchmark.csv"),      ["model", "asset_id"]),
    (Path("benchmark_scores/cloud_models_benchmark.csv"),      ["model", "asset_id"]),
    (Path("benchmark_scores/commercial_models_benchmark.csv"), ["model", "asset_id"]),
    (Path("benchmark_scores/tooluse_leaderboard.csv"),         ["model"]),
]

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("consolidate")


def _load_csv_robust_with_fallback(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Lädt CSV robust mit Fallback-Strategien.

    Versucht zuerst den robusten Loader, dann Standard pandas mit Fehlertoleranz.
    """
    # Strategie 1: Nutze utils.csv_recovery (robustester Ansatz)
    try:
        df = load_csv_robust(file_path)
        if len(df) > 0:
            logger.info("   📊 Geladen (robust): %d Zeilen", len(df))
            return df
    except Exception as e:
        logger.warning("   ⚠️  Robuster Loader fehlgeschlagen: %s", e)

    # Strategie 2: Standard pandas mit Fehlertoleranz
    try:
        df = pd.read_csv(
            file_path,
            on_bad_lines="skip",
            engine="python",
            encoding="utf-8"
        )
        logger.info("   📊 Geladen (fallback): %d Zeilen", len(df))
        return df
    except Exception as e:
        logger.error("   ❌ Konnte CSV nicht laden: %s", e)
        return None


def _filter_corrupt_rows(df: pd.DataFrame, key_cols: list[str]) -> tuple[pd.DataFrame, dict[str, int]]:
    """Filtert korrupte Zeilen via Sanitizer-Heuristiken (Defense-in-Depth).

    Verwendet exakt die gleichen Prädikate wie ``sanitize_benchmark_csvs._filter_rows``.
    Verhindert dass Header-Repeats, narrative Asset-IDs und ungültige Modelle
    nach einer Konsolidierung zurück in die CSV geschrieben werden.

    Args:
        df: Eingelesener DataFrame (aus _load_csv_robust_with_fallback).
        key_cols: Schlüsselspalten (z. B. ["model", "asset_id"]).

    Returns:
        (df_clean, drop_stats) — bereinigter DataFrame + Counter der Drop-Gründe.
    """
    drop_stats: dict[str, int] = {
        "header_repeat": 0,
        "narrative_asset_id": 0,
        "invalid_model": 0,
    }
    if df.empty:
        return df, drop_stats

    # Header-Repeat: prüfen anhand Werte der ersten Spalte
    # pandas liest CSVs als DataFrame — wir rekonstruieren die Header-Detection
    # via den ursprünglichen Header. Wenn die erste Spalte 'asset_id' ist UND
    # der Wert der Spalte exakt dem Header-Eintrag entspricht → Header-Repeat.
    if "asset_id" in df.columns:
        _header_repeat_mask = df["asset_id"].astype(str) == "asset_id"
        if bool(_header_repeat_mask.any()):
            drop_stats["header_repeat"] = int(_header_repeat_mask.sum())
            df = df.loc[~_header_repeat_mask].copy()

    # Narrative Asset-ID
    if "asset_id" in df.columns:
        _narrative_mask = df["asset_id"].astype(str).apply(_is_narrative_asset_id)
        if bool(_narrative_mask.any()):
            drop_stats["narrative_asset_id"] = int(_narrative_mask.sum())
            df = df.loc[~_narrative_mask].copy()

    # Invalid Model
    if "model" in df.columns:
        def _is_invalid(model_val: object) -> bool:
            invalid, _ = _is_invalid_model(str(model_val) if model_val is not None else "")
            return invalid

        _invalid_mask = df["model"].apply(_is_invalid)
        if bool(_invalid_mask.any()):
            drop_stats["invalid_model"] = int(_invalid_mask.sum())
            df = df.loc[~_invalid_mask].copy()

    return df, drop_stats


def consolidate_file(file_path: Path, key_cols: list[str]):
    """Liest, bereinigt und überschreibt eine einzelne CSV-Datei."""
    if not file_path.exists():
        logger.info("⚠️  Datei nicht gefunden (überspringe): %s", file_path)
        return

    logger.info("Verarbeite: %s", file_path)

    try:
        df = _load_csv_robust_with_fallback(file_path)
        if df is None:
            logger.error("   ❌ Überspringe Datei (nicht lesbar)")
            return

        original_count = len(df)

        if original_count == 0:
            logger.info("   -> Datei ist leer.")
            return

        # Prüfen ob notwendige Spalten existieren
        required_cols = key_cols + (["timestamp"] if "timestamp" in df.columns else [])
        missing = [c for c in key_cols if c not in df.columns]
        if missing:
            logger.error("   ❌ Fehler: Fehlende Schlüsselspalten %s in %s", missing, file_path.name)
            return

        # Defense-in-Depth: korrupte Zeilen via Sanitizer-Heuristiken rausfiltern
        df, drop_stats = _filter_corrupt_rows(df, key_cols)
        sanitized_count = original_count - len(df)
        if sanitized_count > 0:
            for reason, count in sorted(drop_stats.items(), key=lambda x: -x[1]):
                if count:
                    logger.info("   🗑️  Korrupt-Drop: %-22s %6d", reason, count)

        # Sicherstellen, dass Timestamp datetime ist (für korrekte Sortierung)
        if "timestamp" in df.columns:
            # utc=True vermeidet Mixed-Timezone-Probleme
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
            df = df.sort_values(by="timestamp", ascending=False)

        # Deduplizieren: Behalte den ersten (neuesten) Eintrag pro Schlüssel
        df_clean = df.drop_duplicates(subset=key_cols, keep="first")

        cleaned_count = len(df_clean)
        removed_count = original_count - cleaned_count

        if removed_count > 0:
            df_clean.to_csv(file_path, index=False)
            logger.info(
                "   ✅ Bereinigt: %d -> %d Zeilen. (%d alte Einträge entfernt)",
                original_count, cleaned_count, removed_count,
            )
        else:
            logger.info("   ✨ Keine Duplikate gefunden. Datei unverändert.")

    except Exception as e:
        logger.error(
            "   ❌ Kritischer Fehler beim Verarbeiten von %s: %s", file_path, e
        )


def main():
    """Consolidation Main Entry Point."""
    print("🧹 Starte CSV-Konsolidierung (The Crucible Memory Law)...")
    for csv_file, key_cols in CSV_FILES:
        consolidate_file(csv_file, key_cols)
    print("🏁 Fertig.")


if __name__ == "__main__":
    main()
