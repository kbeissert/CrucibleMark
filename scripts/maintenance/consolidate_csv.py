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
4. Überschreibt die originale CSV mit den bereinigten Daten.

Usage:
    python scripts/consolidate_csv.py
"""

import logging
from pathlib import Path
import pandas as pd

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


def consolidate_file(file_path: Path, key_cols: list[str]):
    """Liest, bereinigt und überschreibt eine einzelne CSV-Datei."""
    if not file_path.exists():
        logger.info("⚠️  Datei nicht gefunden (überspringe): %s", file_path)
        return

    logger.info("Verarbeite: %s", file_path)

    try:
        df = pd.read_csv(file_path)
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

        # Sicherstellen, dass Timestamp datetime ist (für korrekte Sortierung)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
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
