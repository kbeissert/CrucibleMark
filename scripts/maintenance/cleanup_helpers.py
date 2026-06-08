"""SSoT-Helper fuer Backup- und Cleanup-Operationen.

Seit Phase 27 (Backup-System SSoT-Refactor) bündelt dieses Modul die
gemeinsame Logik aller Maintenance-Skripte:

- :func:`canonical_model_slug` — normalisiert einen aus dem Dateisystem
  extrahierten Slug durch die SSoT-Funktionen aus ``utils.model_utils``.
- :func:`pre_backup_hygiene` — aufraeumen vor dem tar-Snapshot (alte
  Crash-Logs, spurious_archives, Backups-von-Backups).
- :func:`move_legacy_backups` — verschiebt alte Backup-Artefakte
  aus ``outputs/`` in ``backups/_pre_clean_YYYYMMDD/``.

Damit wird sichergestellt, dass die ID-SSoT nicht nur an einer Stelle
(:mod:`scripts.maintenance.prune_orphaned_reports`) greift, sondern
einheitlich fuer alle Cleanup-Pfade.
"""

from __future__ import annotations

import logging
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Projekt-Root auf sys.path, damit ``utils.*`` importierbar ist
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.backup_targets import (  # noqa: E402
    UNREACHABLE_LOG_MAX_AGE_DAYS,
)
from utils.model_utils import (  # noqa: E402
    _safe_name,
    resolve_canonical_model_id,
)

logger = logging.getLogger("cleanup_helpers")


# ---------------------------------------------------------------------------
# ID-SSoT
# ---------------------------------------------------------------------------

#: Regex fuer Run-Files: ``results_{model}_{timestamp}.json``.
RUN_FILE_RE = re.compile(r"^results_(.+)_(\d{8}_\d{6})\.json$")


def canonical_model_slug(raw_slug: str) -> str:
    """Normalisiert einen Slug aus dem Dateisystem via ID-SSoT.

    Akzeptiert beliebige Schreibweisen (Punkte, Underscores, Doppelpunkte,
    hf.co/AUTHOR/ Praefixe) und liefert die kanonische Form, die in den
    CSVs und Card-Dateinamen verwendet wird.

    Delegiert an :func:`utils.model_utils.resolve_canonical_model_id`
    (Card-Lookup + ``_safe_name``-Fallback). Liefert ``_safe_name`` als
    reinen Dateinamen-Fallback, falls die SSoT-Funktion fehlschlaegt.

    Args:
        raw_slug: Slug, wie er im Dateinamen vorkommt
                  (z.B. ``qwen3.5-35b-a3b-q4``).

    Returns:
        Kanonischer Slug. Bei unbekanntem Modell: ``_safe_name``-Form.
    """
    if not raw_slug:
        return raw_slug
    try:
        return resolve_canonical_model_id(raw_slug)
    except Exception:  # noqa: BLE001 — defensiv
        return _safe_name(raw_slug)


def canonicalize_run_grouping(files: list[Path]) -> dict[str, list[Path]]:
    """Gruppiert Run-Files nach kanonischer Model-ID.

    Frueher (``Phase < 27``) wurde die Gruppierung direkt aus dem
    Dateinamen-Slug gebildet — was zu Duplikat-Gruppen fuehrte, wenn
    ein Modell mal mit ``qwen3.5`` und mal mit ``qwen_qwen3.5`` im
    Dateinamen stand.

    Args:
        files: Liste von ``results_*.json`` Pfaden.

    Returns:
        Dict ``{canonical_model_id: [paths newest-first]}``.
    """
    grouped: dict[str, list[Path]] = {}
    for f in files:
        m = RUN_FILE_RE.match(f.name)
        if not m:
            continue
        raw_slug, _ts = m.group(1), m.group(2)
        canon = canonical_model_slug(raw_slug)
        grouped.setdefault(canon, []).append(f)

    # Innerhalb jeder Gruppe nach mtime sortieren (neueste zuerst)
    for canon, paths in grouped.items():
        paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return grouped


# ---------------------------------------------------------------------------
# Pre-Backup-Hygiene
# ---------------------------------------------------------------------------

#: Patterns von Output-Pfaden, die vor dem Backup weggeraeumt werden
#: sollen. Reihenfolge ist signifikant (die spezifischeren Patterns
#: zuerst, damit Regex-Matching robust bleibt).
_LEGACY_BACKUP_GLOBS: tuple[str, ...] = (
    "audit_logs_backup_*.tar.gz",
    "audit_logs_legacy_backup_*",
    "audit_logs_spurious_archive",
    "audit_logs.zip",
    "model_cards_backup_*.tar.gz",
    "model_cards_spurious_archive",
)


def _is_older_than(path: Path, days: int) -> bool:
    """Prueft, ob ``path`` aelter als ``days`` Tage ist."""
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return mtime < (datetime.now(tz=timezone.utc) - timedelta(days=days))


def pre_backup_hygiene(
    root: Path = ROOT_DIR,
    *,
    unreachable_max_age_days: int = UNREACHABLE_LOG_MAX_AGE_DAYS,
    dry_run: bool = False,
) -> dict[str, int]:
    """Aufraeumarbeiten VOR dem tar-Snapshot.

    Ausgefuehrte Aktionen (in dieser Reihenfolge):

    1. Alte ``outputs/tooluse_unreachable_*.json`` loeschen
       (aelter als :data:`UNREACHABLE_LOG_MAX_AGE_DAYS`, default 7 Tage).
    2. Verwaiste Backup-Artefakte aus ``outputs/`` nach
       ``backups/_pre_clean_YYYYMMDD/`` verschieben
       (audit_logs_*, model_cards_backup_*, spurious_archives).
    3. Leere ``outputs/temp/``-Session-Files loeschen.

    Args:
        root: Projekt-Wurzelverzeichnis.
        unreachable_max_age_days: Schwellwert fuer Crash-Log-Alter.
        dry_run: Nur protokollieren, nichts verschieben/loeschen.

    Returns:
        Dict mit Aktions-Countern:
        ``{"unreachable_logs_deleted": N, "legacy_backups_moved": N,
           "temp_files_deleted": N}``.
    """
    stats = {
        "unreachable_logs_deleted": 0,
        "legacy_backups_moved": 0,
        "temp_files_deleted": 0,
    }

    outputs_dir = root / "outputs"

    # 1) Alte tooluse_unreachable_*.json
    if outputs_dir.exists():
        for log in outputs_dir.glob("tooluse_unreachable_*.json"):
            if _is_older_than(log, unreachable_max_age_days):
                logger.info("  [unreachable] loesche (alt): %s", log.name)
                if not dry_run:
                    log.unlink()
                stats["unreachable_logs_deleted"] += 1

    # 2) Legacy-Backup-Artefakte in ein safety-Archiv verschieben
    backups_dir = root / "backups"
    safety_dir = backups_dir / f"_pre_clean_{datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    if not dry_run:
        safety_dir.mkdir(parents=True, exist_ok=True)
    for pattern in _LEGACY_BACKUP_GLOBS:
        for path in outputs_dir.glob(pattern) if outputs_dir.exists() else []:
            if not path.exists():
                continue
            target = safety_dir / path.name
            logger.info("  [legacy-backup] verschiebe: %s -> %s",
                        path.relative_to(root), target.relative_to(root))
            if not dry_run:
                try:
                    shutil.move(str(path), str(target))
                except OSError as exc:
                    logger.warning("  [legacy-backup] move fehlgeschlagen: %s", exc)
                    continue
            stats["legacy_backups_moved"] += 1

    # 3) outputs/temp/session_*.json (Wizard-Recovery-Files)
    temp_dir = outputs_dir / "temp" if outputs_dir.exists() else None
    if temp_dir and temp_dir.exists():
        for f in temp_dir.glob("session_*.json"):
            logger.info("  [temp] loesche: %s", f.relative_to(root))
            if not dry_run:
                try:
                    f.unlink()
                except OSError as exc:
                    logger.warning("  [temp] unlink fehlgeschlagen: %s", exc)
                    continue
            stats["temp_files_deleted"] += 1

    return stats


# ---------------------------------------------------------------------------
# Convenience: alle Pre-Backup-Aktionen
# ---------------------------------------------------------------------------

def run_pre_backup_hygiene(root: Path = ROOT_DIR, dry_run: bool = False) -> dict[str, int]:
    """Wrapper, der von :mod:`scripts.maintenance.cleanup_helpers`
    und vom ``make backup-prep``-Target aufgerufen wird.

    Loggt eine kurze Zusammenfassung und gibt die Stats zurueck.
    """
    logger.info("Starte Pre-Backup-Hygiene (dry_run=%s)…", dry_run)
    stats = pre_backup_hygiene(root, dry_run=dry_run)
    logger.info(
        "Hygiene abgeschlossen: %d Crash-Logs, %d Legacy-Backups, %d Temp-Files",
        stats["unreachable_logs_deleted"],
        stats["legacy_backups_moved"],
        stats["temp_files_deleted"],
    )
    return stats


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(
        description="Pre-Backup-Hygiene: alte tooluse_unreachable_*.json, "
                    "Legacy-Backup-Artefakte und Session-Files aufraeumen.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Nur anzeigen, nichts loeschen/verschieben.",
    )
    args = parser.parse_args()
    run_pre_backup_hygiene(dry_run=args.dry_run)
