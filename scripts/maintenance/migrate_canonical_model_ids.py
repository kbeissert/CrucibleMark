#!/usr/bin/env python3
"""Migration: Bringt alle model_id-Werte auf die kanonische Schreibweise.

Hintergrund: Manche Cards haben als ``model_id`` Werte mit Punkten
(z. B. ``qwen3.5-9b``), während die Card-Dateinamen Punkte durch Underscores
ersetzen (``qwen3_5-9b.json``) und auch die CSV-/Leaderboard-Spalten
Underscores verwenden. Das führte zu Mismatch-Fehlern.

Lösung: ``resolve_canonical_model_id()`` in ``utils/model_utils.py`` löst
Punkt-Eingaben ab sofort korrekt auf. Dieses Script räumt zusätzlich
die zugrundeliegende Card-DB auf, sodass ``model_id`` überall einheitlich
in Underscore-Schreibweise vorliegt.

Was es macht
------------
1. Scannt alle Cards in ``benchmark_scores/model_cards/*.json``.
2. Für jede Card: Wenn ``card["model_id"]`` von der kanonischen Form
   abweicht (Unterschied zu ``_safe_name(card["model_id"])``), wird der
   Wert aktualisiert.
3. Schreibt einen Backup-Stand der Datei, bevor sie überschrieben wird.
4. Gleiches Cleanup für die CSV-Spalten ``model`` in den drei
   Haupt-CSVs (``local``, ``cloud``, ``commercial``) sowie im
   ``tooluse_leaderboard.csv`` (nur die ``model``-Spalte wird normalisiert).

Sicherheit
----------
- Idempotent: Ein zweiter Lauf findet keine Änderungen mehr.
- Backup-Files: Vor dem Schreiben wird ``<file>.bak`` angelegt.
- Dry-Run möglich via ``--dry-run``.

Verwendung
----------
    python scripts/maintenance/migrate_canonical_model_ids.py            # Live-Run
    python scripts/maintenance/migrate_canonical_model_ids.py --dry-run  # Nur Report
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils.model_utils import (  # noqa: E402
    _safe_name,
    normalize_model_id,
    resolve_canonical_model_id,
)

logger = logging.getLogger("migrate_canonical")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)

CARD_DIR = _ROOT / "benchmark_scores" / "model_cards"
CSV_TARGETS = [
    _ROOT / "benchmark_scores" / "local_models_benchmark.csv",
    _ROOT / "benchmark_scores" / "cloud_models_benchmark.csv",
    _ROOT / "benchmark_scores" / "commercial_models_benchmark.csv",
    _ROOT / "benchmark_scores" / "tooluse_leaderboard.csv",
]


def _needs_canonical_fix(model_id: str) -> bool:
    """True wenn die model_id eine sichere safe_name-Normalisierung benötigt.

    Eine model_id ist genau dann KANONISCH-UNSCHARF, wenn sie:
      1. KEIN namespaced Slash enthält (Namespaces wie ``qwen/qwen3.7-max``
         sind OpenRouter-Routing-Schlüssel und dürfen nicht umbenannt werden).
      2. NICHT mit ``:free`` oder ähnlichem Suffix endet (Aliase bleiben
         unverändert, um Card-Aliasing-Semantik zu erhalten).
      3. NICHT kanonisch geschrieben ist (d. h. safe_name() würde Punkte
         durch Underscores ersetzen).
    """
    if not model_id:
        return False
    if "/" in model_id:
        # Namespaced IDs (OpenRouter, Groq) bleiben unverändert.
        return False
    if ":" in model_id:
        # Suffixe (z. B. :free, :latest) bleiben unverändert.
        return False
    normalized = normalize_model_id(model_id)
    if normalized == model_id:
        return _safe_name(model_id) != model_id
    return _safe_name(normalized) != model_id


def migrate_cards(dry_run: bool) -> tuple[int, int]:
    """Aktualisiert inkonsistente model_id-Felder in den Model-Cards.

    Returns:
        (geprüft, geändert)
    """
    checked = 0
    changed = 0
    for card_path in sorted(CARD_DIR.glob("*.json")):
        checked += 1
        try:
            data = json.loads(card_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Card nicht lesbar (%s): %s", card_path.name, exc)
            continue
        if not isinstance(data, dict):
            continue
        model_id = data.get("model_id")
        if not isinstance(model_id, str) or not model_id:
            continue
        if not _needs_canonical_fix(model_id):
            continue

        new_model_id = _safe_name(normalize_model_id(model_id))
        logger.info(
            "Card %s: model_id '%s' → '%s'",
            card_path.name, model_id, new_model_id,
        )
        if dry_run:
            continue

        backup = card_path.with_suffix(card_path.suffix + ".bak")
        if not backup.exists():
            shutil.copy2(card_path, backup)
        data["model_id"] = new_model_id
        # Falls display_name mit alter Schreibweise beginnt, lassen wir ihn
        # bewusst stehen (Anzeige = Marketing-Name, nicht Schlüssel).
        card_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        changed += 1
    return checked, changed


def _is_safe_canonical_fix(raw_model: str, resolved: str) -> bool:
    """Prüft ob die ``model_id`` nur die sichere Punkt→Underscore-Normalisierung braucht.

    Eine Migration ist genau dann SICHER, wenn ``resolved`` exakt
    ``_safe_name(normalize_model_id(raw_model))`` entspricht — also eine
    reine Dateisystem-Normalisierung. Andere Korrekturen (z. B. Card-
    Aliasing, :free-Suffixe) werden NICHT durchgeführt.
    """
    if not raw_model or not resolved:
        return False
    expected = _safe_name(normalize_model_id(raw_model))
    return expected == resolved and expected != raw_model


def _is_plausible_model_id(value: str) -> bool:
    """Prüft ob ein String eine plausible model_id ist (kein Timestamp, keine Zahl).

    Schutz gegen kaputte Zeilen in tooluse_leaderboard.csv (historischer Bug,
    bei dem Commas in Daten die Spalten verschoben haben — die model-Spalte
    enthielt dann Timestamps oder Fragmente wie 'leet', '9', 'e').
    """
    if not value or len(value) < 3 or len(value) > 200:
        return False
    # Pure timestamps or date strings should not be treated as model_ids
    if re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", value):
        return False
    # Pure numbers (column-shifted values) should not be treated as model_ids
    if re.match(r"^\d+(\.\d+)?$", value):
        return False
    return True


def migrate_csvs(dry_run: bool) -> tuple[int, int]:
    """Aktualisiert die ``model``-Spalte in den Benchmark-CSVs.

    Logik pro Zeile: Wenn die ``model``-Spalte eine reine safe_name-
    Normalisierung benötigt (z. B. ``qwen3.5-35b-a3b-q4`` →
    ``qwen3_5-35b-a3b-q4``), wird sie korrigiert. Andere Diskrepanzen
    (z. B. Alias-Auflösungen) bleiben unverändert, um keine
    semantischen Änderungen an Audit-Trails vorzunehmen.

    Hinweis: Das ``tooluse_leaderboard.csv`` wird übersprungen, weil
    es historisch verschobene Spalten enthält (Commas in Daten).
    """
    checked = 0
    changed = 0
    for csv_path in CSV_TARGETS:
        is_tooluse_lb = csv_path.name == "tooluse_leaderboard.csv"
        if not csv_path.exists():
            continue
        rows: list[dict] = []
        try:
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or []
                for row in reader:
                    rows.append(row)
        except (OSError, csv.Error) as exc:
            logger.warning("CSV nicht lesbar (%s): %s", csv_path.name, exc)
            continue
        if not rows:
            continue

        new_rows: list[dict] = []
        seen_keys: set[tuple[str, str]] = set()
        for row in rows:
            checked += 1
            raw_model = row.get("model", "")
            if not raw_model:
                new_rows.append(row)
                continue

            # tooluse_leaderboard.csv: Card-Lookup-basiert statt safe_name-only.
            # Hintergrund: Das ToolUse-Plugin speichert model_ids in
            # Punktschreibweise (z. B. qwen3.5-35b-a3b-q4), die Cards
            # verwenden aber Underscore (qwen3_5-35b-a3b-q4). Hier ist die
            # Card-Lookup-Auflösung legitim — wir wollen, dass der Match
            # funktioniert. Kaputte Zeilen (Timestamp-Werte in model-Spalte)
            # werden mit _is_plausible_model_id() gefiltert.
            if is_tooluse_lb:
                if not _is_plausible_model_id(raw_model):
                    logger.warning(
                        "CSV %s: Zeile mit unplausibler model_id '%s' übersprungen",
                        csv_path.name, raw_model,
                    )
                    new_rows.append(row)
                    continue
                canonical = resolve_canonical_model_id(raw_model)
                if canonical == raw_model:
                    new_rows.append(row)
                    seen_keys.add((raw_model, row.get("asset_id", "")))
                    continue
                logger.info(
                    "CSV %s: model '%s' → '%s' (Card-Lookup-Auflösung)",
                    csv_path.name, raw_model, canonical,
                )
                row["model"] = canonical
                changed += 1
                seen_keys.add((canonical, row.get("asset_id", "")))
                new_rows.append(row)
                continue

            # Standard: Nur Korrekturen, die exakt safe_name der normalisierten
            # Form entsprechen. Heuristische Card-Alias-Resolutionen werden
            # NICHT angewendet (z. B. qwen/qwen3.6-plus → qwen/qwen3.6-plus:free).
            # Namespaced IDs (mit ``/``) und IDs mit Suffix (mit ``:``) bleiben
            # unverändert — das sind semantische Schlüssel, keine Dateinamen.
            if "/" in raw_model or ":" in raw_model:
                new_rows.append(row)
                seen_keys.add((raw_model, row.get("asset_id", "")))
                continue
            expected = _safe_name(normalize_model_id(raw_model))
            if expected == raw_model:
                new_rows.append(row)
                # Deduplizierung sicherheitshalber anwenden
                dedup_key = (raw_model, row.get("asset_id", ""))
                seen_keys.add(dedup_key)
                continue
            logger.info(
                "CSV %s: model '%s' → '%s' (safe_name-Normalisierung)",
                csv_path.name, raw_model, expected,
            )
            row["model"] = expected
            changed += 1
            dedup_key = (expected, row.get("asset_id", ""))
            if dedup_key in seen_keys:
                logger.info(
                    "CSV %s: Duplikat entfernt (model=%s, asset=%s)",
                    csv_path.name, expected, row.get("asset_id"),
                )
                continue
            seen_keys.add(dedup_key)
            new_rows.append(row)

        if dry_run:
            continue

        backup = csv_path.with_suffix(csv_path.suffix + ".bak")
        if not backup.exists():
            shutil.copy2(csv_path, backup)
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(new_rows)
        logger.info(
            "CSV %s: %d Zeilen geschrieben (%d → %d, %d entfernt)",
            csv_path.name, len(new_rows), len(rows), len(new_rows), len(rows) - len(new_rows),
        )
    return checked, changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bringt alle model_id-Werte auf kanonische Schreibweise (Punkte → Underscores).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur reportieren, nicht schreiben.",
    )
    args = parser.parse_args()

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    logger.info("=== Migration mode: %s ===", mode)

    logger.info("--- Cards ---")
    cards_checked, cards_changed = migrate_cards(args.dry_run)
    logger.info(
        "%d Cards geprüft, %d Änderungen %s",
        cards_checked, cards_changed, "(würden gemacht)" if args.dry_run else "",
    )

    logger.info("--- CSVs ---")
    csvs_checked, csvs_changed = migrate_csvs(args.dry_run)
    logger.info(
        "%d Zeilen geprüft, %d Änderungen %s",
        csvs_checked, csvs_changed, "(würden gemacht)" if args.dry_run else "",
    )

    logger.info("=== Migration %s abgeschlossen ===", mode)
    if args.dry_run:
        logger.info("Ohne --dry-run erneut starten, um die Änderungen anzuwenden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
