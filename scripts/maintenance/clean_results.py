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

# Third-party
import yaml
import pandas as pd

# Setup Root Path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Local imports
# pylint: disable=wrong-import-position
from utils.model_utils import (  # noqa: E402
    _safe_name,
    _find_card,
    resolve_canonical_model_id,
    CARD_DIR,
)
from utils.module_registry import get_active_modules
from utils.config_validator import ConfigValidator
from utils.backup_targets import CSV_FILES  # noqa: E402

# pylint: enable=wrong-import-position

#: PC-spezifische CSVs (nicht in ``CSV_FILES``, weil sie andere
#: Deduplizierungs-Schluessel als ``(model, asset_id)`` verwenden).
PC_CSV_FILES: tuple[Path, ...] = (
    Path("benchmark_scores/political_compass_results.csv"),
    Path("benchmark_scores/political_compass_leaderboard.csv"),
)

#: Konsolidierte Clean-Liste: Benchmark-CSVs aus SSoT + PC-CSVs.
#: (Sub-Family-Leaderboards gemma_leaderboard.csv/qwen_leaderboard.csv wurden
#: in v4.10.15 entfernt — das Konzept war verwaist: die Dateien wurden nie
#: generiert und nie in git getrackt. provider_leaderboard.csv wurde bereits
#: in v4.10.12 stillgelegt.)
CLEAN_CSV_FILES: tuple[Path, ...] = (
    tuple(path for path, _ in CSV_FILES) + PC_CSV_FILES
)

#: Cost-Log (nicht in CSV_FILES, da kein Benchmark-Ergebnis-CSV).
COST_LOG_PATH: Path = Path("outputs/cost_log.csv")

#: Benchmark-Leaderboards (generiert, nicht in CSV_FILES).
LEADERBOARD_CSVS: tuple[Path, ...] = (
    Path("benchmark_scores/benchmark_leaderboard.csv"),
    Path("benchmark_scores/benchmark_leaderboard_detailed.csv"),
)


def _extend_variants_with_safe_and_hyphen(variants: set[str]) -> None:
    """Erweitert ``variants`` um _safe_name- und Punkt-zu-Hyphen-Varianten.

    Wird mehrfach in :func:`_collect_model_id_variants` aufgerufen, um
    zusaetzlich gefundene IDs (z.B. aus Card-Cross-Discovery) in die
    Normalisierungs-Pipelines aufzunehmen.
    """
    for v in list(variants):
        variants.add(_safe_name(v))
        if "." in v:
            variants.add(v.replace(".", "-"))


def _discover_cross_variant_ids(variants: set[str], safe_variants: set[str]) -> None:
    """Ergänzt ``variants`` um IDs aus Card-inhalten (model_id, heritage_ids).

    Findet z.B. "grok-4.1-fast-reasoning" in der Card wenn Input
    "grok-4_1-fast-reasoning" war (Underscore ohne Card-Lookup).
    Scannt AUCH heritage_ids — wenn eine Card umbenannt wurde (z.B.
    gpt-oss:120b-cloud → openai/gpt-oss-120b), steht der alte Name
    nur noch in heritage_ids und muss trotzdem gefunden werden.
    """
    try:
        import json as _json
        for card_file in CARD_DIR.glob("*.json"):
            try:
                data = _json.loads(card_file.read_text(encoding="utf-8"))
                card_mid = data.get("model_id", "")
                if card_mid and _safe_name(card_mid) in safe_variants:
                    variants.add(card_mid)
                # heritage_ids: alte kanonische IDs, die auf diese Card zeigen
                for hid in (data.get("heritage_ids") or []):
                    if isinstance(hid, str) and (
                        hid in variants or _safe_name(hid) in safe_variants
                    ):
                        if card_mid:
                            variants.add(card_mid)
                        variants.add(hid)
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass


def _collect_model_id_variants(model: str) -> set[str]:
    """Sammt ALLE Schreibweisen einer Model-ID fuer variant-aware Cleanup.

    Beruecksichtigt:
    - Eingabe selbst
    - Kanonische Form (via resolve_canonical_model_id / Card-Lookup)
    - _safe_name-Form (Punkte/Doppelpunkte/Slashes → Underscores)
    - Punkt-zu-Hyphen-Variante (fuer provider_config-Schreibweise)
    - Underscore-Form (fuer _safe_name-basierte Dateinamen)
    - model_id-Feld aus existierenden Cards (fuer Cross-Variant-Discovery)

    Returns set of all non-empty variants.
    """
    variants: set[str] = set()
    if not model:
        return variants

    # 1. Eingabe selbst
    variants.add(model)

    # 2. Kanonische Form (Card-Lookup)
    try:
        canonical = resolve_canonical_model_id(model)
        variants.add(canonical)
    except Exception:  # noqa: BLE001
        pass

    # 3+4. _safe_name + Punkt-zu-Hyphen
    _extend_variants_with_safe_and_hyphen(variants)

    # 5. Cross-Variant-Discovery aus Card-Inhalten
    safe_variants = {_safe_name(v) for v in variants}
    _discover_cross_variant_ids(variants, safe_variants)

    # 6. Erneut _safe_name + Hyphen fuer alle neuen Varianten
    _extend_variants_with_safe_and_hyphen(variants)

    variants.discard("")
    return variants


def _variant_match(text: str, variants: set[str]) -> bool:
    """Prueft ob text exakt einer der Varianten entspricht (case-sensitive)."""
    return text in variants

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("clean_results")


def get_module_asset_ids(module_key: str) -> list[str]:
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
                with open(f, encoding="utf-8") as yf:
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
        safe_model = _safe_name(model)
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

def clean_tooluse_metrics_jsonl(model: str | None = None, dry_run: bool = False) -> None:
    """Bereinigt outputs/tooluse_metrics.jsonl.

    model=None  → gesamte Datei leeren (z.B. bei --module tooluse).
    model=<id>  → nur Einträge für dieses Modell entfernen (Feld: model_id).
    """
    import json  # pylint: disable=import-outside-toplevel

    jsonl_path = ROOT_DIR / "outputs" / "tooluse_metrics.jsonl"
    if not jsonl_path.exists():
        return

    raw_lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    initial_count = sum(1 for ln in raw_lines if ln.strip())

    if model is None:
        kept: list[str] = []
    else:
        kept = []
        for line in raw_lines:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
                if entry.get("model_id") != model:
                    kept.append(stripped)
            except json.JSONDecodeError:
                kept.append(stripped)  # fehlerhafte Zeilen behalten

    removed_count = initial_count - len(kept)
    if removed_count > 0:
        print(f"   - tooluse_metrics.jsonl: {removed_count} Einträge entfernen...")
        if not dry_run:
            content = "\n".join(kept) + ("\n" if kept else "")
            jsonl_path.write_text(content, encoding="utf-8")
            print("     ✅ Gespeichert.")
        else:
            print("     (Dry Run - keine Änderung)")
    else:
        print("   - tooluse_metrics.jsonl: Keine passenden Einträge gefunden.")


def clean_cost_log(model: str | None = None, dry_run: bool = False) -> None:
    """Bereinigt outputs/cost_log.csv.

    model=None  → gesamte Datei leeren.
    model=<id>  → nur Einträge für dieses Modell entfernen (Spalte: model).
    """
    if not COST_LOG_PATH.exists():
        return

    df = pd.read_csv(COST_LOG_PATH, dtype=str)
    initial_count = len(df)

    if model is None:
        df_filtered = df.iloc[0:0]  # nur Header
    else:
        variants = _collect_model_id_variants(model)
        # cost_log hat 'model' als Spalte
        df_filtered = df[~df["model"].isin(variants)] if "model" in df.columns else df

    removed_count = initial_count - len(df_filtered)
    if removed_count > 0:
        print(f"   - cost_log.csv: {removed_count} Einträge entfernen...")
        if not dry_run:
            df_filtered.to_csv(COST_LOG_PATH, index=False)
            print("     ✅ Gespeichert.")
        else:
            print("     (Dry Run - keine Änderung)")
    else:
        print("   - cost_log.csv: Keine passenden Einträge gefunden.")


def _norm_dir(s: str) -> str:
    """Normalisiert Model-ID oder Verzeichnisname zum Vergleich.

    Delegiert an SSoT ``_safe_name`` aus utils.model_utils und normalisiert
    zusätzlich auf lower-case, damit die Verzeichnis-Slugs case-insensitiv
    verglichen werden können.
    """
    return _safe_name(s).lower()


def _extract_model_from_dispatch_summary(stem: str) -> str | None:
    """Extrahiert den Modell-Anteil aus einem dispatch_summaries-Dateinamen.

    Bekannte Datei-Formate:
      - ``political_compass_<model>``
      - ``tooluse_<model>``
      - ``tooluse_backlog_<model>``
      - ``score_<module>_<provider>_<model>``  (z.B. score_cli_benchmark_anthropic_claude-haiku-4-5)
      - ``score_<module>_<model>``              (z.B. score_cultural_intelligence_claude-haiku-4-5)

    Returns:
        Der Modell-Slug (ohne Suffix), oder None wenn nicht erkannt.
    """
    # Bekannte Modul-Keys (SSoT aus benchmark_modules/)
    _MODULE_KEYS = {
        "cli_benchmark", "code_quality", "content_transformation",
        "cultural_intelligence", "documentation_quality", "political_compass",
        "reasoning_logic", "tooluse", "ux_writing",
    }
    # Bekannte Provider-Praefixe
    _PROVIDER_KEYS = {
        "anthropic", "openai", "google", "xai", "mistral", "deepseek", "qwen",
        "nousresearch", "moonshotai", "nvidia", "xiaomi", "minimax", "groq",
        "z-ai", "z_ai", "openrouter",
    }

    if stem.startswith("political_compass_"):
        return stem[len("political_compass_"):]
    if stem.startswith("tooluse_backlog_"):
        return stem[len("tooluse_backlog_"):]
    if stem.startswith("tooluse_"):
        return stem[len("tooluse_"):]
    if stem.startswith("score_"):
        rest = stem[len("score_"):]
        # Skip Modul-Key (kann mehrere Segmente haben, z.B. cultural_intelligence)
        for mod_key in sorted(_MODULE_KEYS, key=len, reverse=True):
            if rest == mod_key or rest.startswith(mod_key + "_"):
                rest = rest[len(mod_key):].lstrip("_")
                break
        # Skip Provider-Praefix wenn vorhanden
        if "_" in rest:
            first_seg = rest.split("_", 1)[0]
            if first_seg in _PROVIDER_KEYS:
                rest = rest.split("_", 1)[1]
        return rest
    return None


def _remove_model_directory(item, label: str, dry_run: bool) -> None:
    """Loescht ein Verzeichnis im 'rmtree'-Pfad mit Logging/Error-Handling.

    Shared helper for category-subdir + reviews cleanup.
    """
    print(f"   - Lösche {label}/{item.name}")
    if not dry_run:
        try:
            shutil.rmtree(item)
        except OSError as e:
            print(f"     ❌ Fehler beim Löschen von {item.name}: {e}")


def _remove_model_file(item, label: str, dry_run: bool) -> None:
    """Loescht eine Datei mit Logging/Error-Handling.

    Shared helper for results_* + dispatch_summaries cleanup.
    """
    print(f"   - Lösche {label}/{item.name}")
    if not dry_run:
        try:
            item.unlink()
        except OSError as e:
            print(f"     ❌ Fehler beim Löschen von {item.name}: {e}")


def _item_matches_variant(item_name: str, variants_norm: set[str]) -> bool:
    """Variant-aware Match für Verzeichnis-/Dateinamen gegen die Model-Norm-Set."""
    item_norm = _norm_dir(item_name)
    return item_norm in variants_norm or any(
        item_norm.endswith(f"_{v}") for v in variants_norm
    )


def _scan_category_subdirs(
    base_dir: Path, category: str, variants_norm: set[str], dry_run: bool
) -> None:
    """Loescht modell-spezifische Sub-Directories einer outputs/-Kategorie."""
    for item in base_dir.iterdir():
        if not item.is_dir() or item.name in (".gitkeep", ".DS_Store"):
            continue
        if _item_matches_variant(item.name, variants_norm):
            _remove_model_directory(item, category, dry_run)


def _extract_model_part_from_results_name(name: str) -> str | None:
    """Extrahiert den Modell-Slug aus einem ``results_<model>_<date>.json``-Namen."""
    rest = name[len("results_"):]
    date_match = re.search(r"_\d{8}_\d{6}\.json$", rest)
    if date_match:
        return rest[:date_match.start()]
    return rest.replace(".json", "")


def _scan_results_files(
    base_dir: Path, category: str, variants_norm: set[str], dry_run: bool
) -> None:
    """Loescht ``results_<model>_<date>.json``-Dateien in outputs/runs/."""
    for item in base_dir.iterdir():
        if not item.is_file() or item.name == ".gitkeep":
            continue
        if not item.name.startswith("results_"):
            continue
        model_part = _extract_model_part_from_results_name(item.name)
        if _norm_dir(model_part) in variants_norm:
            _remove_model_file(item, category, dry_run)


def _scan_dispatch_summaries(
    ds_dir: Path, category: str, variants_norm: set[str], dry_run: bool
) -> None:
    """Loescht dispatch_summary-Dateien, deren Modell-Slug zu den Varianten passt."""
    for item in ds_dir.iterdir():
        if not item.is_file():
            continue
        model_part = _extract_model_from_dispatch_summary(item.stem)
        if model_part is None:
            continue
        if _norm_dir(model_part) in variants_norm:
            _remove_model_file(item, f"{category}/dispatch_summaries", dry_run)


def _scan_reviews_dir(variants_norm: set[str], dry_run: bool) -> None:
    """Loescht modell-spezifische Verzeichnisse unter docs/reviews/."""
    reviews_dir = ROOT_DIR / "docs" / "reviews"
    if not reviews_dir.exists():
        return
    for item in reviews_dir.iterdir():
        if not item.is_dir() or item.name in (".gitkeep", ".DS_Store"):
            continue
        if _item_matches_variant(item.name, variants_norm):
            _remove_model_directory(item, "docs/reviews", dry_run)


def clean_model_output_directories(model: str, dry_run: bool = False):
    """Löscht modellspezifische Verzeichnisse aus outputs/ (audit_logs, comparisons, runs)
    und docs/reviews/.

    Zusätzlich werden modell-spezifische Dateien in ``outputs/runs/`` und
    ``outputs/runs/dispatch_summaries/`` aufgeräumt:
      - ``results_<model>_<date>.json`` (PC-Run-Ergebnisse)
      - ``political_compass_<model>.json`` (PC-Dispatch-Summary)
      - ``tooluse_<model>.json`` (ToolUse-Dispatch-Summary)
      - ``score_<module>_<model>.json`` (Score-Dispatch-Summary je Modul)

    Variant-aware: findet Verzeichnisse unabhängig von der Schreibweise
    (Underscore, Hyphen, Punkt) durch Abgleich mit _collect_model_id_variants().
    """
    if not model:
        return

    variants = _collect_model_id_variants(model)
    variants_norm = {_norm_dir(v) for v in variants}

    print(f"🧹 Suche Ausgabeverzeichnisse für Modell '{model}'...")
    if len(variants) > 1:
        print(f"   Varianten: {', '.join(sorted(variants))}")

    for category in ["audit_logs", "comparisons", "runs"]:
        base_dir = ROOT_DIR / "outputs" / category
        if not base_dir.exists():
            continue
        _scan_category_subdirs(base_dir, category, variants_norm, dry_run)
        if category == "runs":
            _scan_results_files(base_dir, category, variants_norm, dry_run)
            ds_dir = base_dir / "dispatch_summaries"
            if ds_dir.exists():
                _scan_dispatch_summaries(ds_dir, category, variants_norm, dry_run)

    _scan_reviews_dir(variants_norm, dry_run)


def _collect_cards_by_direct_filename(safe_variants: set[str]) -> set[Path]:
    """Sammelt Karten via direkter Dateinamen-Match (z.B. ``<slug>.json``)."""
    out: set[Path] = set()
    for sv in safe_variants:
        p = CARD_DIR / f"{sv}.json"
        if p.exists():
            out.add(p.resolve())
    return out


def _collect_cards_by_find_card(variants: set[str]) -> set[Path]:
    """Sammelt Karten via ``_find_card`` (beruecksichtigt Prefixed-Pfade)."""
    out: set[Path] = set()
    for v in variants:
        try:
            p = _find_card(v)
            if p.exists():
                out.add(p.resolve())
        except Exception:  # noqa: BLE001
            pass
    return out


def _collect_cards_by_glob(safe_variants: set[str]) -> set[Path]:
    """Sammelt Karten via Glob-Prefix (fuer date-suffixed Cards)."""
    out: set[Path] = set()
    for sv in safe_variants:
        for p in CARD_DIR.glob(f"{sv}*.json"):
            out.add(p.resolve())
    return out


def _collect_cards_by_model_id_content(safe_variants: set[str]) -> set[Path]:
    """Sammelt Cards, deren Inhalt eine Variante als ``model_id`` enthaelt.

    Z.B. Dateiname ``grok-4-1-fast-reasoning.json`` aber
    model_id=``grok-4.1-fast-reasoning`` im Inhalt.
    """
    out: set[Path] = set()
    for card_file in CARD_DIR.glob("*.json"):
        try:
            import json as _json
            data = _json.loads(card_file.read_text(encoding="utf-8"))
            card_mid = data.get("model_id", "")
            if card_mid and _safe_name(card_mid) in safe_variants:
                out.add(card_file.resolve())
        except Exception:  # noqa: BLE001
            continue
    return out


def _delete_card_paths(cards_to_delete: set[Path], model: str, dry_run: bool) -> None:
    """Loescht die gesammelten Card-Pfade mit Logging und Error-Handling."""
    for card_path in sorted(cards_to_delete):
        try:
            display = card_path.relative_to(ROOT_DIR)
        except ValueError:
            display = card_path
        print(f"   - Lösche model_card: {display}")
        if not dry_run:
            try:
                card_path.unlink()
            except OSError as e:
                print(f"     ❌ Fehler beim Löschen: {e}")


def clean_model_card(model: str, dry_run: bool = False):
    """Löscht ALLE Model-Card-Varianten für das Modell (Underscore, Hyphen, Dot).

    Findet Cards unabhängig der Schreibweise in Dateinamen oder model_id-Feld.
    """
    if not model:
        return

    variants = _collect_model_id_variants(model)
    # _safe_name-Varianten fuer Dateinamen-Matching
    safe_variants = {_safe_name(v) for v in variants}

    cards_to_delete: set[Path] = set()
    cards_to_delete |= _collect_cards_by_direct_filename(safe_variants)
    cards_to_delete |= _collect_cards_by_find_card(variants)
    cards_to_delete |= _collect_cards_by_glob(safe_variants)

    # 4. Dateinamen-Matching: Auch Cards finden, die eine Schreibweise
    #    des model_id-FELDS enthalten (Fallback wenn 1-3 nichts finden).
    if not cards_to_delete:
        cards_to_delete |= _collect_cards_by_model_id_content(safe_variants)

    if not cards_to_delete:
        print(f"   - model_card: keine Card für '{model}' gefunden.")
        return

    _delete_card_paths(cards_to_delete, model, dry_run)

def clean_csv(
    file_path: Path,
    model: str = None,
    asset_ids: list[str] = None,
    dry_run: bool = False,
):
    """Löscht Zeilen aus einer CSV basierend auf Filtern.

    Phase 28: Modell-Match via ``resolve_canonical_model_id`` (ID-SSoT).
    Phase 29: Variant-aware — sammelt alle Schreibweisen (Underscore, Hyphen,
    Punkt) via ``_collect_model_id_variants`` und matched direkt, damit auch
    nach Card-Löschung alle Einträge gefunden werden.

    Unterstützt mehrere Spaltennamen fuer Modell-IDs:
    ``model``, ``Model ID``, ``model_id_raw``.
    """
    if not file_path.exists():
        return

    try:
        df = pd.read_csv(file_path)
        initial_count = len(df)

        mask = pd.Series([True] * len(df))

        if model:
            variants = _collect_model_id_variants(model)
            target_canon = resolve_canonical_model_id(model)

            # Alle moeglichen Modell-Spalten pruefen
            model_cols = [c for c in df.columns if c in ("model", "Model ID", "model_id_raw")]

            for col in model_cols:
                # Varianten-Direktmatch
                col_mask_direct = ~df[col].isin(variants)

                # Kanonischer Match (fuer Faelle wie qwen3.5-35b == qwen_qwen3.5-35b)
                df_model_canon = df[col].apply(
                    lambda v: resolve_canonical_model_id(str(v)) if pd.notna(v) else v
                )
                col_mask_canon = df_model_canon != target_canon

                # Zeile wird entfernt wenn in irgendeiner Spalte ein Match vorliegt
                mask = mask & (col_mask_direct & col_mask_canon)

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
        logging.exception("Fehler bei %s", file_path.name)
        print(f"❌ Fehler bei {file_path.name}: {e}")


def main_with_args(args) -> None:
    """Phase 28: Direktaufruf mit Namespace-Objekt (kein argparse, kein Subprozess).

    Wird von ``clean.py._run_clean_results`` und den Tests aufgerufen.
    """
    _run_clean_logic(args)


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
    _run_clean_logic(args)


def _dead_model_info(model: str) -> None:
    """Zeigt eine Warnung wenn das Modell als tot markiert ist.

    Prüft web_export_blacklist.yaml und provider_config.yaml (auskommentierte Einträge).
    Rein informativ — löscht nichts.
    """
    import re as _re

    variants = _collect_model_id_variants(model)

    # 1. Blacklist prüfen
    bl_path = ROOT_DIR / "config" / "web_export_blacklist.yaml"
    if bl_path.exists():
        try:
            bl_data = yaml.safe_load(bl_path.read_text(encoding="utf-8"))
            blacklisted = set()
            if isinstance(bl_data, dict):
                for v in (bl_data.get("blacklist") or []):
                    if isinstance(v, str):
                        blacklisted.add(v)
            if blacklisted & variants:
                print(f"   ⚠️  Modell '{model}' steht in der Web-Export-Blacklist.")
        except Exception:  # noqa: BLE001
            pass

    # 2. Provider-Config prüfen (auskommentierte Einträge)
    pc_path = ROOT_DIR / "config" / "provider_config.yaml"
    if pc_path.exists():
        try:
            content = pc_path.read_text(encoding="utf-8")
            for v in variants:
                # Suche nach auskommentierten Einträgen: # - id: <variant>
                if _re.search(rf"#\s*- id:\s*{_re.escape(v)}\b", content):
                    print(f"   ⚠️  Modell '{model}' ist in provider_config.yaml auskommentiert.")
                    return
        except Exception:  # noqa: BLE001
            pass


def _run_prune_orphans(args) -> None:
    """Prune-Orphans-Submodus: sucht und loescht verwaiste Report-Verzeichnisse.

    Wird von :func:`_run_clean_logic` aufgerufen wenn ``args.prune_orphans`` gesetzt
    ist und kehrt vor dem normalen Clean-Flow zurueck.
    """
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


def _clean_tooluse_module(dry_run: bool) -> None:
    """Bereinigt das tooluse-Modul als Ganzes (Header-only + jsonl komplett leeren)."""
    lb_path = Path("benchmark_scores/tooluse_leaderboard.csv")
    if lb_path.exists():
        import pandas as pd  # pylint: disable=import-outside-toplevel
        header_df = pd.read_csv(lb_path).iloc[0:0]
        print(f"   - tooluse_leaderboard.csv: komplette Bereinigung ({len(pd.read_csv(lb_path))} Zeilen) ...")
        if not dry_run:
            header_df.to_csv(lb_path, index=False)
            print("     ✅ Gespeichert.")
        else:
            print("     (Dry Run - keine Änderung)")
    clean_tooluse_metrics_jsonl(model=None, dry_run=dry_run)


def _resolve_target_assets(args) -> list[str]:
    """Loest Asset-IDs fuer ``args.module`` auf und loggt das Ergebnis.

    Returns leere Liste wenn kein Modul angegeben oder keine Assets gefunden.
    """
    if not args.module:
        return []
    print(f"🔍 Suche Assets für Modul '{args.module}'...")
    assets = get_module_asset_ids(args.module)
    if not assets:
        print("   Keine Assets gefunden oder Modul existiert nicht.")
        return []
    print(f"   Gefundene Asset-IDs: {len(assets)} (z.B. {assets[:3]}...)")
    return assets


def _run_model_artifact_cleanup(args) -> None:
    """Fuehrt alle modell-spezifischen Cleanup-Schritte aus.

    Reihenfolge bewusst: CSVs brauchen die Card (resolve_canonical_model_id),
    Cards werden daher ZULETZT geloescht.
    """
    clean_model_output_directories(model=args.model, dry_run=args.dry_run)
    clean_cost_log(model=args.model, dry_run=args.dry_run)
    clean_tooluse_metrics_jsonl(model=args.model, dry_run=args.dry_run)
    # Cards ZULETZT löschen (nach CSV-Bereinigung).
    clean_model_card(model=args.model, dry_run=args.dry_run)


def _run_clean_logic(args) -> None:
    """Phase 28: Ausgelagerte Clean-Logik, geteilt zwischen main() und main_with_args()."""

    # Separater Modus: Verwaiste Reports aufräumen
    if args.prune_orphans:
        _run_prune_orphans(args)
        return

    if not args.model and not args.module:
        print("❌ Bitte --model [NAME] oder --module [KEY] angeben.")
        sys.exit(1)

    print("\n🧹 Starte Bereinigung...")
    if args.dry_run:
        print("   (DRY RUN - Simulation)")

    # Dead-Model-Check: Info wenn Modell in Blacklist oder Provider-Config markiert
    if args.model:
        _dead_model_info(args.model)

    target_assets = _resolve_target_assets(args)

    # Checkpoints und Debug-Files bereinigen
    clean_checkpoints(model=args.model, module_key=args.module, dry_run=args.dry_run)

    # Phase 29: CSVs ZUERST bereinigen (brauchen Cards fuer resolve_canonical_model_id).
    # Reihenfolge: Benchmark-CSVs → PC-CSVs → Leaderboards.
    for f in CLEAN_CSV_FILES:
        clean_csv(f, model=args.model, asset_ids=target_assets, dry_run=args.dry_run)
    for f in LEADERBOARD_CSVS:
        clean_csv(f, model=args.model, dry_run=args.dry_run)

    if args.model:
        _run_model_artifact_cleanup(args)
    elif args.module == "tooluse":
        _clean_tooluse_module(args.dry_run)

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
