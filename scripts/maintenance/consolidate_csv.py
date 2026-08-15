#!/usr/bin/env python3
"""CSV Consolidation Script.

Reduziert Benchmark-CSV-Dateien auf den jeweils letzten (aktuellsten)
Eintrag pro Modell und Asset.

Funktion (seit Phase 27):

1. Laedt die CSV-Liste aus :data:`utils.backup_targets.CSV_FILES` (SSoT).
2. Normalisiert die ``model``-Spalte via ``resolve_canonical_model_id``
   BEVOR dedupliziert wird — ``qwen3.5-35b`` und ``qwen_qwen3.5-35b``
   werden als dasselbe Modell gezaehlt.
3. Sortiert nach Timestamp (neueste zuerst).
4. Dedupliziert basierend auf den Schluesselspalten aus
   :data:`utils.backup_targets.CSV_FILES`.
5. Validiert jede Zeile gegen Sanitizer-Heuristiken (Phase 9,
   Defense-in-Depth).
6. Ueberschreibt die originale CSV mit den bereinigten Daten.

Defense-in-Depth: Die gleichen Heuristiken wie
``sanitize_benchmark_csvs.py`` filtern korrupte Zeilen raus, BEVOR sie
zurueckgeschrieben werden. Verhindert dass Phase-8-Erfolg durch
nachfolgende Maintenance zunichtegemacht wird.

Verwendung:
    python scripts/maintenance/consolidate_csv.py
"""

import logging
import sys
from pathlib import Path

# Projekt-Root auf sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd  # noqa: E402

from scripts.maintenance.sanitize_benchmark_csvs import (  # noqa: E402
    _is_narrative_asset_id,
    _is_invalid_model,
)
from utils.backup_targets import CSV_FILES  # noqa: E402
from utils.csv_recovery import load_csv_robust  # noqa: E402
from utils.model_utils import resolve_canonical_model_id  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("consolidate")


def _load_csv_robust_with_fallback(file_path: Path) -> pd.DataFrame | None:
    """Laedt CSV robust mit Fallback-Strategien.

    Versucht zuerst den robusten Loader, dann Standard pandas mit
    Fehlertoleranz.

    Args:
        file_path: Pfad zur CSV-Datei.

    Returns:
        DataFrame oder None bei nicht lesbarer Datei.
    """
    # Strategie 1: Nutze utils.csv_recovery (robustester Ansatz)
    try:
        df = load_csv_robust(file_path)
        if len(df) > 0:
            logger.info("   📊 Geladen (robust): %d Zeilen", len(df))
            return df
    except Exception as e:  # noqa: BLE001
        logger.warning("   ⚠️  Robuster Loader fehlgeschlagen: %s", e)

    # Strategie 2: Standard pandas mit Fehlertoleranz
    try:
        df = pd.read_csv(
            file_path,
            on_bad_lines="skip",
            engine="python",
            encoding="utf-8",
        )
        logger.info("   📊 Geladen (fallback): %d Zeilen", len(df))
        return df
    except Exception as e:  # noqa: BLE001
        logger.error("   ❌ Konnte CSV nicht laden: %s", e)
        return None


def _normalize_model_column(df: pd.DataFrame) -> pd.DataFrame:
    """Normalisiert die ``model``-Spalte via ID-SSoT.

    Dadurch werden Schreibweisenvarianten (``qwen3.5`` vs. ``qwen_qwen3.5``,
    mit/ohne ``hf.co/AUTHOR/``-Prefix) zu einer kanonischen Form
    zusammengefuehrt, BEVOR die Deduplizierung laeuft.

    Phase 27: schliesst die ID-SSoT-Luecke, die vorher nur in
    ``prune_orphaned_reports`` aktiv war.

    Args:
        df: Eingelesener DataFrame.

    Returns:
        Kopie mit normalisierter ``model``-Spalte.
    """
    if "model" not in df.columns or df.empty:
        return df
    df = df.copy()
    # pd.isna-Check vor str() — sonst wird NaN zu 'nan' und korrumpiert die ID.
    df["model"] = df["model"].apply(
        lambda v: resolve_canonical_model_id(str(v)) if not pd.isna(v) else v
    )
    return df


def _filter_corrupt_rows(
    df: pd.DataFrame, key_cols: list[str]
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Filtert korrupte Zeilen via Sanitizer-Heuristiken (Defense-in-Depth).

    Verwendet exakt die gleichen Praedikate wie
    ``sanitize_benchmark_csvs._filter_rows``. Verhindert dass
    Header-Repeats, narrative Asset-IDs und ungueltige Modelle nach einer
    Konsolidierung zurueck in die CSV geschrieben werden.

    Args:
        df: Eingelesener DataFrame.
        key_cols: Schluesselspalten (z.B. ``["model", "asset_id"]``).

    Returns:
        ``(df_clean, drop_stats)`` — bereinigter DataFrame + Counter der
        Drop-Gruende.
    """
    drop_stats: dict[str, int] = {
        "header_repeat": 0,
        "narrative_asset_id": 0,
        "invalid_model": 0,
    }
    if df.empty:
        return df, drop_stats

    if "asset_id" in df.columns:
        _header_repeat_mask = df["asset_id"].astype(str) == "asset_id"
        if bool(_header_repeat_mask.any()):
            drop_stats["header_repeat"] = int(_header_repeat_mask.sum())
            df = df.loc[~_header_repeat_mask].copy()

    if "asset_id" in df.columns:
        _narrative_mask = df["asset_id"].astype(str).apply(_is_narrative_asset_id)
        if bool(_narrative_mask.any()):
            drop_stats["narrative_asset_id"] = int(_narrative_mask.sum())
            df = df.loc[~_narrative_mask].copy()

    if "model" in df.columns:
        def _is_invalid(model_val: object) -> bool:
            invalid, _ = _is_invalid_model(
                str(model_val) if model_val is not None else ""
            )
            return invalid

        _invalid_mask = df["model"].apply(_is_invalid)
        if bool(_invalid_mask.any()):
            drop_stats["invalid_model"] = int(_invalid_mask.sum())
            df = df.loc[~_invalid_mask].copy()

    return df, drop_stats


def _write_consolidated(
    file_path: Path,
    df_clean: pd.DataFrame,
    original_count: int,
    cleaned_count: int,
    removed_count: int,
    *,
    dry_run: bool,
) -> None:
    """Schreibt das bereinigte Ergebnis (oder zeigt es im Dry-Run an)."""
    if dry_run:
        logger.info(
            "   👁️ [DRY-RUN] Wuerde bereinigen: %d -> %d Zeilen "
            "(%d alte Eintraege). Kein Schreibvorgang.",
            original_count, cleaned_count, removed_count,
        )
        return
    df_clean.to_csv(file_path, index=False)
    logger.info(
        "   ✅ Bereinigt: %d -> %d Zeilen. (%d alte Eintraege entfernt)",
        original_count, cleaned_count, removed_count,
    )


def consolidate_file(
    file_path: Path, key_cols: tuple[str, ...], *, dry_run: bool = False,
) -> None:
    """Liest, bereinigt und ueberschreibt eine einzelne CSV-Datei.

    Args:
        file_path: Pfad zur CSV-Datei.
        key_cols: Tuple von Schluesselspalten fuer die Deduplizierung.
        dry_run: Nur anzeigen, nichts schreiben (Review 2026-08-15 —
            vorher schrieb das Skript direkt ohne Preview-Moeglichkeit).
    """
    if not file_path.exists():
        logger.info("⚠️  Datei nicht gefunden (ueberspringe): %s", file_path)
        return

    logger.info("Verarbeite: %s", file_path)

    try:
        df = _load_csv_robust_with_fallback(file_path)
        if df is None:
            logger.error("   ❌ Ueberspringe Datei (nicht lesbar)")
            return

        original_count = len(df)
        if original_count == 0:
            logger.info("   -> Datei ist leer.")
            return

        # Fehlende Schluesselspalten?
        missing = [c for c in key_cols if c not in df.columns]
        if missing:
            logger.error(
                "   ❌ Fehler: Fehlende Schluesselspalten %s in %s",
                missing, file_path.name,
            )
            return

        # Defense-in-Depth: korrupte Zeilen rausfiltern
        df, drop_stats = _filter_corrupt_rows(df, list(key_cols))
        sanitized_count = original_count - len(df)
        if sanitized_count > 0:
            for reason, count in sorted(drop_stats.items(), key=lambda x: -x[1]):
                if count:
                    logger.info("   🗑️  Korrupt-Drop: %-22s %6d", reason, count)

        # Phase 27: Model-Spalte via SSoT normalisieren BEVOR dedupliziert
        if "model" in df.columns:
            df = _normalize_model_column(df)
            logger.info("   🔗 Model-IDs via SSoT normalisiert.")

        # Timestamp korrekt sortieren
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(
                df["timestamp"], errors="coerce", utc=True
            )
            df = df.sort_values(by="timestamp", ascending=False)

        # Deduplizieren: behalte den ersten (neuesten) Eintrag pro Schluessel
        df_clean = df.drop_duplicates(subset=list(key_cols), keep="first")

        cleaned_count = len(df_clean)
        removed_count = original_count - cleaned_count

        if removed_count > 0:
            _write_consolidated(
                file_path, df_clean, original_count, cleaned_count, removed_count,
                dry_run=dry_run,
            )
        else:
            logger.info("   ✨ Keine Duplikate gefunden. Datei unveraendert.")

    except Exception as e:  # noqa: BLE001
        logger.error(
            "   ❌ Kritischer Fehler beim Verarbeiten von %s: %s", file_path, e
        )


def main(dry_run: bool = False) -> None:
    """Consolidation Main Entry Point."""
    mode = " [DRY-RUN]" if dry_run else ""
    print(f"🧹 Starte CSV-Konsolidierung (The Crucible Memory Law){mode}...")
    for csv_file, key_cols in CSV_FILES:
        consolidate_file(csv_file, key_cols, dry_run=dry_run)
    print("🏁 Fertig.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="CSV-Konsolidierung: dedupliziert Benchmark-CSVs "
                    "(SSoT-Liste aus utils.backup_targets.CSV_FILES).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Nur anzeigen was bereinigt wuerde, keine Dateien schreiben.",
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
