"""
One-time migration (Phase 49): bereinigt Quant/Format-Verschmutzung im
``model_version``-Feld und lagert sie in die korrekten Felder aus.

SSoT-Vertrag (utils/model_utils.py:122-125):
    model_version       = reine Versionsnummer ("3.5", "4", "1.0", "r1")
    model_variant       = interne Fein-Tune-/Variant-Bezeichnung ("Ortenzya",
                          "Wordsmith", "MTP", "Coder-MTP", "E4B", "QAT")
    quantization_format = Quant/Format-Token ("Q8_0 GGUF", "FP8", "NVFP4")
    hardware_profile    = bleibt in CSV-Spalte + Karten-Suffix (NICHT im version)

Groupby-Continuity: ``model_version`` ist Leaderboard-Groupby-Key
(score_calculator.py: groupby(["model","model_version","type"])). Daher MUSS
die Migration atomar sein: Karten-Änderung + CSV-``model_version``-Spalte
zusammen, sonst splittet jedes Modell im Leaderboard in zwei Zeilen
(alter Quant-String vs. neue clean Version).

Usage:
    python scripts/maintenance/migrate_model_versions_pollution.py           # Dry-Run
    python scripts/maintenance/migrate_model_versions_pollution.py --apply   # Ausführen
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

CARD_DIR = ROOT / "benchmark_scores" / "model_cards"
CSVS = [
    ROOT / "benchmark_scores" / "commercial_models_benchmark.csv",
    ROOT / "benchmark_scores" / "cloud_models_benchmark.csv",
    ROOT / "benchmark_scores" / "local_models_benchmark.csv",
]

# Explizite Mapping-Tabelle (keine Heuristik — jede Card einzeln geprüft).
# Quellen: model_id + alter model_version-Wert → neue (version, variant, quant).
# Reihenfolge: model_id (kanonisch, wie in Card-Feld "model_id").
MIGRATIONS: dict[str, dict[str, str | None]] = {
    # --- version + quant gemischt (19) ---
    "deepseek-r1-distill-qwen-32b": {"version": "r1", "variant": None, "quant": "Q5_K_M GGUF"},
    "gemma-3-12b-it-q8": {"version": "3", "variant": None, "quant": "Q8_0 GGUF"},
    "gemma-3-12b-it-q8-spark": {"version": "3", "variant": None, "quant": "Q8_0 GGUF"},
    "gemma-3-12b-it-spark": {"version": "3", "variant": None, "quant": "Q4_K_M GGUF"},
    "gemma-3-12b-it": {"version": "3", "variant": None, "quant": "Q4_K_M GGUF"},
    "gemma-4-12b-it-ud-q4_k_xl": {"version": "4", "variant": None, "quant": "Q4_K_XL GGUF"},
    "gemma-4-12b-it-ud-q6_k_xl": {"version": "4", "variant": None, "quant": "Q6_K_XL GGUF"},
    "gemma-4-12b-it-ud-q8_k_xl": {"version": "4", "variant": None, "quant": "Q8_K_XL GGUF"},
    "hermes-3-8b": {"version": "3", "variant": None, "quant": "Q6_K_L GGUF"},
    "ornith-1_0-35B-FP8": {"version": "1.0", "variant": None, "quant": "FP8"},
    "qwable-3_6-27b-q4": {"version": "3.6", "variant": None, "quant": "Q4_K_M GGUF"},
    "qwable-3_6-35b-q5": {"version": "3.6", "variant": None, "quant": "Q5_K_M GGUF"},
    "qwen2_5-coder-7b": {"version": "2.5", "variant": None, "quant": "Q6_K GGUF"},
    "qwen3-14b": {"version": "3", "variant": None, "quant": "Q6_K GGUF"},
    "qwen3-4b": {"version": "3", "variant": None, "quant": "Q6_K GGUF"},
    "qwen3_5-35b-a3b-q4": {"version": "3.5", "variant": None, "quant": "Q4_K_XL GGUF"},
    "qwen3_5-4b-q4": {"version": "3.5", "variant": None, "quant": "UD-Q4_K_XL GGUF"},
    "qwen3_5-4b-q6": {"version": "3.5", "variant": None, "quant": "UD-Q6_K_XL GGUF"},
    "qwen3_5-4b-q8": {"version": "3.5", "variant": None, "quant": "UD-Q8_K_XL GGUF"},
    "qwen3_5-9b": {"version": "3.5", "variant": None, "quant": "UD-Q6_K_XL GGUF"},
    # --- version + hardware /SPRK (3) ---
    "gemma-4-26B-A4B-it-qat-ud-q4": {"version": "4", "variant": "QAT", "quant": "UD-Q4 GGUF"},
    "gemma-4-31B-it-qat-ud-q4": {"version": "4", "variant": "QAT", "quant": "UD-Q4 GGUF"},
    # --- interne Namen / Fein-Tune-Varianten (9) ---
    "Gemma-4-31B-Wordsmith-NVFP4": {"version": "4", "variant": "Ortenzya Wordsmith", "quant": "NVFP4"},
    "gemma-4-31B-it-UD-Q8_K_XL-mtp": {"version": "4", "variant": "MTP", "quant": "UD-Q8_K_XL GGUF"},
    "gemma-4-31b-it-creative-wordsmith-q8": {
        "version": "4",
        "variant": "Ortenzya Creative-Wordsmith-uncensored-heretic",
        "quant": "Q8_0 GGUF",
    },
    "gemma-4-e4b": {"version": "4", "variant": "E4B", "quant": "GGUF"},
    "google/gemma-4-31b-it": {"version": "4", "variant": None, "quant": None},
    "qwen3_6-35b-a3b-mtp-ud-q4": {"version": "3.6", "variant": "MTP", "quant": None},
    "qwen3_6-35b-a3b-mtp-ud-q8": {"version": "3.6", "variant": "MTP", "quant": None},
    "qwopus-3_6-27b-coder-mtp-q8": {"version": "3.6", "variant": "Coder-MTP", "quant": "Q8_0 GGUF"},
    "qwopus3_6-27b-v2-mtp-q8": {"version": "3.6", "variant": "MTP", "quant": "Q8_0 GGUF"},
    # --- bereits bereinigte Cards (model_version="4.0"), CSV noch polluted ---
    # Diese Cards wurden vorab manuell auf "4.0" gesetzt, aber die CSV-Spalte
    # nie mit-migriert → Groupby-Split. Hier nur CSV-Phase wirksam (Card No-Op).
    "hermes-4-14b-abliterated": {"version": "4.0", "variant": "Abliterated", "quant": "Q6_K GGUF"},
    "hermes-4-14b-q4": {"version": "4.0", "variant": None, "quant": "Q4_K_M GGUF"},
}


def _find_card_for_model_id(model_id: str) -> Path | None:
    """Finde die Card-Datei für model_id über _find_card (SSoT-Read-Order)."""
    from utils.model_utils import _find_card

    card = _find_card(model_id, card_dir=CARD_DIR)
    return card if card.exists() else None


def _collect_model_id_variants(model_id: str) -> list[str]:
    """Varianten für CSV-Matching (Slash-Form, Underscore-Form etc.)."""
    variants = [model_id]
    base = model_id.split("/")[-1]
    if base != model_id:
        variants.append(base)
    # Ollama-Form (Doppelpunkt) → CrucibleMark-Form
    if ":" in model_id:
        variants.append(model_id.replace(":", "-"))
    return list(dict.fromkeys(variants))


def _atomic_write_json(path: Path, data: dict) -> None:
    import os
    import tempfile

    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.stem + ".tmp", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        if Path(tmp).exists():
            Path(tmp).unlink()
        raise


def _atomic_write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    import os
    import tempfile

    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.stem + ".tmp", suffix=".csv")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
    except Exception:
        if Path(tmp).exists():
            Path(tmp).unlink()
        raise


def migrate(apply: bool = False) -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ROOT / f".bak_model_version_migration_{ts}"

    print(f"Mode: {'APPLY' if apply else 'DRY-RUN (nur Anzeige)'}")
    print(f"Migrationen geplant: {len(MIGRATIONS)} Cards + korrespondierende CSV-Zeilen")
    print("=" * 78)

    # --- Phase 1: Karten migrieren ---
    print("\n[Phase 1] Karten migrieren")
    card_changes: list[tuple[str, str, str, str, str, str]] = []  # (file, mid, old_ver, new_ver, variant, quant)
    cards_backed_up = 0

    for mid, spec in MIGRATIONS.items():
        card = _find_card_for_model_id(mid)
        if not card:
            print(f"  ✗ Card nicht gefunden für model_id={mid!r}")
            continue
        try:
            data = json.loads(card.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ✗ Card nicht lesbar {card.name}: {e}")
            continue

        old_ver = data.get("model_version")
        old_variant = data.get("model_variant")
        old_quant = data.get("quantization_format")
        new_ver = spec["version"]
        new_variant = spec["variant"]
        new_quant = spec["quant"]

        # Idempotenz-Check: bereits migriert?
        if old_ver == new_ver and old_variant == new_variant and old_quant == new_quant:
            print(f"  ⏭  {card.name}: bereits migriert (version={new_ver!r})")
            continue

        print(
            f"  {'→' if apply else ' '} {card.name}: "
            f"version {old_ver!r}→{new_ver!r}, "
            f"variant {old_variant!r}→{new_variant!r}, "
            f"quant {old_quant!r}→{new_quant!r}"
        )
        card_changes.append((card.name, mid, str(old_ver), str(new_ver), str(new_variant), str(new_quant)))

        if apply:
            if cards_backed_up == 0:
                backup_dir.mkdir(parents=True, exist_ok=True)
                print(f"  Backup-Verzeichnis: {backup_dir}")
            bak = backup_dir / card.name
            shutil.copy2(card, bak)
            cards_backed_up += 1
            data["model_version"] = new_ver
            data["model_variant"] = new_variant
            data["quantization_format"] = new_quant
            _atomic_write_json(card, data)

    print(f"\n  {len(card_changes)} Cards {'geändert' if apply else 'zum Ändern vorgesehen'}.")

    # --- Phase 2: CSV model_version-Spalte migrieren ---
    print("\n[Phase 2] CSV model_version-Spalte migrieren (Groupby-Continuity)")
    total_csv_rows = 0

    # Mapping model_id-Variante → neue version (für CSV-Lookup)
    version_lookup: dict[str, str] = {}
    for mid, spec in MIGRATIONS.items():
        for variant in _collect_model_id_variants(mid):
            version_lookup[variant] = spec["version"]

    for csvp in CSVS:
        if not csvp.exists():
            print(f"  SKIP (nicht vorhanden): {csvp.name}")
            continue
        with open(csvp, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)
        if not rows or "model_version" not in fieldnames or "model" not in fieldnames:
            print(f"  SKIP (keine model/model_version-Spalte): {csvp.name}")
            continue

        changed_rows = 0
        for r in rows:
            model = (r.get("model") or "").strip()
            old_v = (r.get("model_version") or "").strip()
            new_v = version_lookup.get(model)
            if new_v is None:
                # Varianten versuchen (Slash-Form etc.)
                for variant in _collect_model_id_variants(model):
                    if variant in version_lookup:
                        new_v = version_lookup[variant]
                        break
            if new_v is not None and old_v != new_v:
                if apply:
                    r["model_version"] = new_v
                changed_rows += 1

        if changed_rows:
            print(f"  {csvp.name}: {changed_rows} Zeilen {'aktualisiert' if apply else 'zum Aktualisieren'}")
            total_csv_rows += changed_rows
            if apply:
                if not backup_dir.exists():
                    backup_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(csvp, backup_dir / csvp.name)
                _atomic_write_csv(csvp, fieldnames, rows)
        else:
            print(f"  {csvp.name}: keine Änderungen")

    print(f"\n  {total_csv_rows} CSV-Zeilen {'aktualisiert' if apply else 'zum Aktualisieren'}.")

    # --- Zusammenfassung ---
    print("\n" + "=" * 78)
    print(f"Zusammenfassung: {len(card_changes)} Cards, {total_csv_rows} CSV-Zeilen")
    if apply:
        print(f"Backups in: {backup_dir}")
        print("\nNächste Schritte:")
        print("  1. python scripts/maintenance/audit_model_versions.py   (sollte 0 flagged zeigen)")
        print("  2. make leaderboard                                       (regenerieren)")
        print("  3. verify: jedes Modell = 1 Leaderboard-Zeile (kein Split)")
    else:
        print("\nDry-Run. Mit --apply ausführen um zu migrieren.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true", help="Migration ausführen (sonst Dry-Run)")
    args = p.parse_args()
    sys.exit(migrate(apply=args.apply))
