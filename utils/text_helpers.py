"""SSoT fuer Text-Parsing- und Normalisierungs-Helper.

Extrahiert aus ``scripts/web_export.py`` (Sektion F — Helper-SSoT).
Diese Module sind die kanonische Definition; ``web_export.py`` importiert
von hier und re-exportiert fuer Backward-Kompatibilitaet.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_PENDING_SENTINELS = frozenset({
    "Pending", "—", "–", "", "n/a", "N/A", "NA", "null", "None", "none",
})

_EMOJI_RE = re.compile(
    "["
    "\U00002300-\U000027BF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F900-\U0001FAFF"
    "\U0001FA00-\U0001FA9F"
    "\U0000FE0F"
    "\U0000FE0E"
    "\U0000200D"
    "]",
    flags=re.UNICODE,
)


def slugify(s: str) -> str:
    """URL-safe slug fuer Strings (kein SSoT fuer sicheres File-Naming).

    Verwendungszweck: Hugo-Web-URL-Pfade. Bindestriche aus Sonderzeichen,
    Slash-Suffix wird abgeschnitten (rsplit auf letztes Segment).
    """
    name = str(s).rsplit('/', maxsplit=1)[-1].lower()
    return re.sub(r'[^a-z0-9]+', '-', name).strip('-')


def sanitize_audit_log(content: str) -> str:
    """Removes Section 3 (LLM-Judge evaluation) from audit logs before web export.
    Preserves header, prompt, model response, and Modul-Metriken block.
    Handles two cases: section 3 followed by Modul-Metriken, or section 3 at EOF."""
    result = re.sub(
        r'## 3\. Evaluation / LLM-Judge / Scorer.*?(?=\n---\n\n### 📦 Modul-Metriken)',
        '', content, flags=re.DOTALL
    )
    result = re.sub(
        r'\n*## 3\. Evaluation / LLM-Judge / Scorer.*$',
        '', result, flags=re.DOTALL
    )
    return result


def normalize_pending(val: Any) -> float | str | None:
    """Normalisiert CSV-Werte zu Zahlen oder None.

    Bekannte Sentinel-Strings (em-dash, en-dash, n/a, etc.) werden zu None.
    Zahlen werden als float zurueckgegeben. Alles andere durchgereicht — aber
    das sollte nicht passieren, da nicht-numerische Strings in Score-Spalten
    ein CSV-Datenproblem sind.
    """
    if pd.isna(val): return None
    val_str = str(val).strip()
    if val_str in _PENDING_SENTINELS: return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return val_str


def parse_compact_number(val: Any) -> float | int | None:
    """Parst kompakte Zahlen mit Suffix (z.B. '83.7K' → 83700, '1.2M' → 1200000).
    Liefert immer eine Zahl — nie einen String. Das ist Vertrags-Pflicht fuer den
    Web-Export: Formatierung gehoert in die Darstellungsschicht, nicht ins JSON.
    """
    if pd.isna(val): return None
    val_str = str(val).strip()
    if val_str in ("Pending", "—", ""): return None
    multiplier = 1
    upper = val_str.upper()
    if upper.endswith("K"):
        multiplier = 1_000
        val_str = val_str[:-1]
    elif upper.endswith("M"):
        multiplier = 1_000_000
        val_str = val_str[:-1]
    try:
        f = float(val_str) * multiplier
        if math.isnan(f): return None
        return int(f) if f == int(f) else f
    except (ValueError, TypeError):
        return None


def parse_percent(val: Any) -> float | None:
    """Parst Prozent-Strings (z.B. '100%' → 100.0) zu Zahlen."""
    if pd.isna(val): return None
    val_str = str(val).strip().rstrip("%")
    if val_str in ("Pending", "—", ""): return None
    try:
        f = float(val_str)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


def parse_int(val: Any) -> int | None:
    """Parst Ganzzahlen — liefert int, nie float (z.B. Timeout Count)."""
    if pd.isna(val): return None
    val_str = str(val).strip()
    if val_str in ("Pending", "—", ""): return None
    try:
        return int(float(val_str))
    except (ValueError, TypeError):
        return None


def parse_star_float(val) -> float | None:
    """Parst '4.0 ★' oder '3.8 ★' zu einem float. Gibt None bei fehlenden Werten zurueck."""
    if pd.isna(val): return None
    val_str = str(val).strip().replace('★', '').strip()
    if val_str in ("Pending", "—", ""): return None
    try:
        f = float(val_str)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


def extract_badge_tier(val) -> str | None:
    if pd.isna(val) or not str(val).strip(): return None
    val_str = str(val).strip()
    return val_str.rsplit(' ', maxsplit=1)[-1] if ' ' in val_str else val_str


def extract_version(val) -> str | None:
    if pd.isna(val): return None
    v = str(val).strip()
    return None if not v or v == "unknown" else v


def strip_emojis(obj: Any) -> Any:
    """Entfernt Emojis rekursiv aus dicts, lists und strings."""
    if isinstance(obj, str):
        cleaned = _EMOJI_RE.sub("", obj).strip()
        return cleaned
    if isinstance(obj, dict):
        return {k: strip_emojis(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [strip_emojis(item) for item in obj]
    return obj


def strip_none(obj: Any) -> Any:
    """Entfernt None-Werte rekursiv aus dicts. Listen und Skalare bleiben erhalten."""
    if isinstance(obj, dict):
        return {k: strip_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [strip_none(item) for item in obj]
    return obj
