"""SSoT fuer atomare Datei-IO-Operationen.

Extrahiert aus ``scripts/web_export.py`` (Sektion F — Helper-SSoT).
Atomare Writes via Temp-Datei + ``os.replace`` — bei Crash mid-write
bleibt die Zieldatei intakt.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any
import contextlib

logger = logging.getLogger(__name__)


def atomic_write_json(
    path: Path,
    data: Any,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
) -> None:
    """Atomar JSON schreiben: erst in Temp-Datei, dann os.replace.

    Hintergrund: Direktes open(path, "w") ist nicht atomar — bei Crash mid-write
    ist die Zieldatei korrupt und der Web-Build rendert unvollstaendige JSON-Listen.
    Mit Temp-Datei + os.replace ist der Wechsel atomar auf POSIX-Dateisystemen.

    Tests: tests/test_web_export_atomic_writes.py
    """
    target_dir = path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(target_dir),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            f.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise


def atomic_write_text(
    path: Path,
    content: str,
    *,
    encoding: str = "utf-8",
) -> None:
    """Atomar Text schreiben (analog atomic_write_json, aber fuer Markdown/Text).

    Hintergrund: write_text() ist nicht atomar — bei Crash mid-write ist die
    Zieldatei korrupt (z.B. halber Audit-Log). Mit Temp-Datei + os.replace
    ist der Wechsel atomar auf POSIX-Dateisystemen.
    """
    target_dir = path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(target_dir),
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise


def atomic_copy(src: Path, dst: Path) -> None:
    """Atomar Datei kopieren (analog shutil.copy2, aber atomic auf Ziel-Seite).

    shutil.copy2 schreibt direkt in die Zieldatei — bei Crash mid-copy ist
    die Zieldatei korrupt. Diese Funktion kopiert erst in eine Temp-Datei
    im Zielverzeichnis und ersetzt dann atomar via os.replace.
    Erhaelt File-Mode (wie copy2) via shutil.copymode nach dem Replace.
    """
    target_dir = dst.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{dst.name}.",
        suffix=".tmp",
        dir=str(target_dir),
    )
    try:
        with os.fdopen(fd, "wb") as f_out, open(src, "rb") as f_in:
            shutil.copyfileobj(f_in, f_out)
        os.replace(tmp_path, dst)
        shutil.copymode(src, dst)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise
