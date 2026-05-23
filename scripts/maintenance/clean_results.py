#!/usr/bin/env python3
# ruff: noqa: E402
"""
Skript zum gezielten Löschen von Benchmark-Ergebnissen aus den CSV-Caches.
Erlaubt das Entfernen bestimmter Modelle oder Module (Asset-Gruppen).
"""

import shutil
import sys
import argparse
import logging
import re
from pathlib import Path
from typing import List

# Third-party
import yaml
import pandas as pd

# Setup Root Path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Local imports
# pylint: disable=wrong-import-position
from utils.module_registry import get_active_modules
from utils.config_validator import ConfigValidator

# pylint: enable=wrong-import-position

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("clean_results")


def get_module_asset_ids(module_key: str) -> List[str]:
    """
    Ermittelt alle Asset-IDs, die zu einem bestimmten Modul gehören.
    Nutzt die Config und scannt die YAML-Dateien.
    """
    validator = ConfigValidator()
    active_configs = get_active_modules(validator.config)

    target_module = None
    for key, conf, _ in active_configs:
        if key == module_key:
            target_module = conf
            break

    if not target_module:
        logger.error("❌ Modul '%s' nicht in der Konfiguration gefunden.", module_key)
        return []

    # Pfad zu Assets
    module_path = Path(target_module["path"])
    assets_dir = module_path / "assets"

    if not assets_dir.exists():
        # Fallback: Vielleicht ist der Pfad direkt das Asset-Dir oder Batch Mode
        assets_dir = module_path

    ids = []

    # 1. YAML Assets scannen
    if assets_dir.exists():
        for f in assets_dir.glob("*.yaml"):
            try:
                with open(f, "r", encoding="utf-8") as yf:
                    data = yaml.safe_load(yf)
                    if "metadata" in data and "id" in data["metadata"]:
                        ids.append(str(data["metadata"]["id"]))
            except Exception:
                continue

    # 2. Batch-Mode IDs (Hardcoded für bekannte Module falls keine Yamls)
    if module_key == "political_compass":
        ids.append("political_compass_v3")

    return ids


def clean_checkpoints(model: str = None, module_key: str = None, dry_run: bool = False):
    """
    Löscht temporäre Session-Dateien (z.B. für Political Compass).
    """
    # Nur Political Compass nutzt aktuell Sessions
    if module_key and module_key != "political_compass":
        return

    temp_dir = Path("outputs/temp")
    if not temp_dir.exists():
        return

    # Pattern: session_{safe_model}.json
    # Safe Model Logic: re.sub(r"[^a-zA-Z0-9]", "_", model)

    files_to_delete = []

    if model:
        safe_model = re.sub(r"[^a-zA-Z0-9]", "_", model)
        target_file = temp_dir / f"session_{safe_model}.json"
        if target_file.exists():
            files_to_delete.append(target_file)
    elif module_key == "political_compass":
        # Delete ALL sessions if module is explicitly cleared
        files_to_delete = list(temp_dir.glob("session_*.json"))

    if files_to_delete:
        print(
            f"🧹 Bereinige {len(files_to_delete)} Session-Checkpoints (Political Compass)..."
        )
        for f in files_to_delete:
            print(f"   - {f.name}")
            if not dry_run:
                try:
                    f.unlink()
                except OSError as e:
                    print(f"     ❌ Fehler beim Löschen: {e}")

def _norm_dir(s: str) -> str:
    """Normalisiert Model-ID oder Verzeichnisname zum Vergleich.
    Konvention: ':' und '/' → '_', Rest bleibt erhalten."""
    return s.replace("/", "_").replace(":", "_").lower()


def clean_model_output_directories(model: str, dry_run: bool = False):
    """Löscht modellspezifische Verzeichnisse aus outputs/ (audit_logs, comparisons, runs)
    und docs/reviews/."""
    if not model:
        return

    model_norm = _norm_dir(model)

    print(f"🧹 Suche Ausgabeverzeichnisse für Modell '{model}'...")

    for category in ["audit_logs", "comparisons", "runs"]:
        base_dir = ROOT_DIR / "outputs" / category
        if not base_dir.exists():
            continue

        for item in base_dir.iterdir():
            if not item.is_dir() or item.name in (".gitkeep", ".DS_Store"):
                continue

            item_norm = _norm_dir(item.name)
            if item_norm == model_norm or item_norm.endswith(f"_{model_norm}"):
                print(f"   - Lösche {category}/{item.name}")
                if not dry_run:
                    try:
                        shutil.rmtree(item)
                    except OSError as e:
                        print(f"     ❌ Fehler beim Löschen von {item.name}: {e}")

    reviews_dir = ROOT_DIR / "docs" / "reviews"
    if reviews_dir.exists():
        for item in reviews_dir.iterdir():
            if not item.is_dir() or item.name in (".gitkeep", ".DS_Store"):
                continue
            item_norm = _norm_dir(item.name)
            if item_norm == model_norm or item_norm.endswith(f"_{model_norm}"):
                print(f"   - Lösche docs/reviews/{item.name}")
                if not dry_run:
                    try:
                        shutil.rmtree(item)
                    except OSError as e:
                        print(f"     ❌ Fehler beim Löschen von {item.name}: {e}")


def clean_model_card(model: str, dry_run: bool = False):
    """Löscht die Model Card JSON für das angegebene Modell."""
    if not model:
        return
    try:
        from utils.model_utils import _find_card
        card_path = _find_card(model).resolve()
        if card_path.exists():
            try:
                display = card_path.relative_to(ROOT_DIR)
            except ValueError:
                display = card_path
            print(f"   - Lösche model_card: {display}")
            if not dry_run:
                card_path.unlink()
        else:
            print(f"   - model_card: keine Card für '{model}' gefunden.")
    except Exception as e:
        print(f"   ⚠️ Fehler bei Card-Suche: {e}")

def clean_csv(
    file_path: Path,
    model: str = None,
    asset_ids: List[str] = None,
    dry_run: bool = False,
):
    """Löscht Zeilen aus einer CSV basierend auf Filtern."""
    if not file_path.exists():
        return

    try:
        df = pd.read_csv(file_path)
        initial_count = len(df)

        mask = pd.Series([True] * len(df))

        if model:
            # Case-insensitive match für Modellname
            mask = mask & (df["model"] != model)

        if asset_ids and "asset_id" in df.columns:
            # Filter rows where asset_id IS in the list (we want to keep those NOT in list)
            # So mask keeps rows where asset_id is NOT in asset_ids
            mask = mask & (~df["asset_id"].isin(asset_ids))

        df_filtered = df[mask]
        removed_count = initial_count - len(df_filtered)

        if removed_count > 0:
            print(f"   - {file_path.name}: {removed_count} Einträge entfernen...")
            if not dry_run:
                # CSV speichern (ohne Index)
                df_filtered.to_csv(file_path, index=False)
                print("     ✅ Gespeichert.")
            else:
                print("     (Dry Run - keine Änderung)")
        else:
            print(f"   - {file_path.name}: Keine passenden Einträge gefunden.")

    except Exception as e:
        print(f"❌ Fehler bei {file_path.name}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Löscht Benchmark-Ergebnisse aus Cache-CSVs."
    )
    parser.add_argument(
        "--model", type=str, help="Name des Modells, das gelöscht werden soll."
    )
    parser.add_argument(
        "--module",
        type=str,
        help="Key des Moduls, dessen Ergebnisse gelöscht werden sollen.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Zeigt nur an, was gelöscht würde."
    )
    parser.add_argument(
        "--prune-orphans",
        action="store_true",
        help="Findet und löscht verwaiste Report-Verzeichnisse (Modelle nicht mehr in Config/Leaderboard).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ohne Nachfrage löschen (nur zusammen mit --prune-orphans wirksam).",
    )

    args = parser.parse_args()

    # Separater Modus: Verwaiste Reports aufräumen
    if args.prune_orphans:
        from scripts.maintenance.prune_orphaned_reports import (
            find_orphaned_dirs,
            load_known_model_ids,
        )

        dry_run = args.dry_run
        known_ids = load_known_model_ids()
        orphaned = find_orphaned_dirs(known_ids)

        if not orphaned:
            print("✅ Keine verwaisten Report-Verzeichnisse gefunden.")
            return

        mode_label = "[DRY RUN] " if dry_run else ""
        print(f"\n{mode_label}Verwaiste Verzeichnisse:\n")
        for d in orphaned:
            size_kb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) // 1024
            print(f"  🗑️  {d.relative_to(ROOT_DIR)}  ({size_kb} KB)")
        print(f"\nGesamt: {len(orphaned)} Verzeichnisse")

        if dry_run:
            print("\nℹ️  Dry-Run — mit --delete + --prune-orphans wirklich löschen.")
            return

        if not args.force:
            confirm = input("⚠️  Alle löschen? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes", "j", "ja"):
                print("❌ Abbruch.")
                return

        deleted = 0
        errors = 0
        for d in orphaned:
            try:
                shutil.rmtree(d)
                print(f"   ✅ Gelöscht: {d.relative_to(ROOT_DIR)}")
                deleted += 1
            except OSError as e:
                print(f"   ❌ Fehler bei {d.name}: {e}")
                errors += 1
        print(f"\n{'✅' if errors == 0 else '⚠️'} Fertig: {deleted} gelöscht, {errors} Fehler.")
        return

    if not args.model and not args.module:
        print("❌ Bitte --model [NAME] oder --module [KEY] angeben.")
        sys.exit(1)

    print("\n🧹 Starte Bereinigung...")
    if args.dry_run:
        print("   (DRY RUN - Simulation)")

    # Asset IDs auflösen, falls Modul angegeben
    target_assets = []
    if args.module:
        print(f"🔍 Suche Assets für Modul '{args.module}'...")
        target_assets = get_module_asset_ids(args.module)
        if not target_assets:
            print("   Keine Assets gefunden oder Modul existiert nicht.")
            # Wir machen weiter, vielleicht ist nur der Name falsch, aber clean csv logik skipped dann eh
        else:
            print(
                f"   Gefundene Asset-IDs: {len(target_assets)} (z.B. {target_assets[:3]}...)"
            )

    # Checkpoints und Debug-Files bereinigen
    clean_checkpoints(model=args.model, module_key=args.module, dry_run=args.dry_run)

    # Modellspezifische Verzeichnisse löschen (falls Modell angegeben)
    if args.model:
        clean_model_output_directories(model=args.model, dry_run=args.dry_run)
        clean_model_card(model=args.model, dry_run=args.dry_run)

    # Dateien definieren
    files = [
        Path("benchmark_scores/local_models_benchmark.csv"),
        Path("benchmark_scores/cloud_models_benchmark.csv"),
        Path("benchmark_scores/commercial_models_benchmark.csv"),
        Path("benchmark_scores/political_compass_results.csv"),
        Path("benchmark_scores/political_compass_leaderboard.csv"),
    ]

    for f in files:
        clean_csv(f, model=args.model, asset_ids=target_assets, dry_run=args.dry_run)

    # Leaderboard Update triggern, wenn nicht dry run
    if not args.dry_run:
        print("\n📈 Aktualisiere Leaderboard...")
        from scripts.core.generate_leaderboard import main as gen_leaderboard

        try:
            gen_leaderboard()
        except Exception as e:
            print(f"⚠️ Leaderboard-Update fehlgeschlagen: {e}")

    print("\n✅ Fertig.")


if __name__ == "__main__":
    main()
