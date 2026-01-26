"""
Utility module for recovering and parsing robust benchmark CSV data.
Handles heuristic extraction of data from malformed LLM outputs.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import pandas as pd  # pylint: disable=import-error

# Fallback models used for heuristic extraction
KNOWN_MODELS = [
    "mistral",
    "qwen",
    "gpt",
    "claude",
    "llama",
    "ministral",
    "deepseek",
    "gemini",
]

MAX_PERCENTAGE = 100
MIN_FLOATS_FOR_GUESS = 3


def load_csv_robust(filepath: Path) -> pd.DataFrame:
    """Lädt CSV-Datei robust (Legacy Helper)."""
    return pd.read_csv(filepath, on_bad_lines="skip", engine="python")


def get_csv_header_idx(header: List[str]) -> Dict[str, int]:
    """Generates a mapping of column names to indices."""
    # Map all columns found in header to their index
    return {col: i for i, col in enumerate(header)}


def parse_row_robust(
    parts: List[str], header_idx: Dict[str, int]
) -> Optional[Dict[str, Any]]:
    """Legacy helper: Tries to parse a single row, recovering it if broken."""
    # Strategy 1: Standard - Length matches
    if len(parts) == len(header_idx):
        row = {}
        for name, idx in header_idx.items():
            if idx < len(parts):
                row[name] = parts[idx]
        return row

    # Strategy 2: Heuristic for broken rows
    return _recover_broken_row(parts)


def _extract_model_from_parts(
    parts: List[str], exclude_values: List[str]
) -> Optional[str]:
    """Sucht nach dem Modellnamen in den CSV-Teilen."""
    for p in parts:
        if p in exclude_values:
            continue
        if any(x in p for x in KNOWN_MODELS):
            return p
    return None


def _guess_percentage(row: Dict[str, Any], floats: List[float]) -> float:
    """Versucht den Percentage-Wert zu raten, falls er fehlt."""
    if "percentage" in row:
        return float(row["percentage"])

    # Wir nehmen an, der höchste Wert <= 100 ist der Score
    valid_pcts = [f for f in floats if 0 <= f <= MAX_PERCENTAGE]
    if len(floats) >= MIN_FLOATS_FOR_GUESS and valid_pcts:
        return max(valid_pcts)
    return 0.0


def _extract_basic_fields(parts: List[str]) -> Dict[str, Any]:
    """Extrahiert Asset ID, Tier, Status und Timestamp."""
    row: Dict[str, Any] = {}
    for p in parts:
        if (
            "code_quality" in p or "ux_writing" in p or "documentation_quality" in p
        ) and "_" in p:
            row["asset_id"] = p
        elif "Tier 1" in p or "Tier 2" in p:
            row["tier"] = p
        elif p.startswith("202") and ":" in p:
            row["timestamp"] = p

    if "success" in parts:
        row["status"] = "success"
    elif "failed" in parts:
        row["status"] = "failed"

    return row


def _recover_broken_row(parts: List[str]) -> Optional[Dict[str, Any]]:
    """Attempts to rescue data from a row that doesn't match the header."""
    # 1. Basis-Felder extrahieren
    row = _extract_basic_fields(parts)

    if "status" not in row:
        return None  # Ohne Status unbrauchbar

    # 2. Model suchen
    exclude = [
        str(row.get("asset_id")),
        str(row.get("status")),
        str(row.get("timestamp")),
        str(row.get("tier")),
    ]
    model = _extract_model_from_parts(parts, exclude)
    if model:
        row["model"] = model

    # 3. Metriken extrahieren
    floats = []
    for p in parts:
        try:
            floats.append(float(p))
        except ValueError:
            continue

    if "model" in row and "asset_id" in row:
        row["percentage"] = _guess_percentage(row, floats)
        row["execution_time"] = row.get("execution_time", 0.0)
        row["timestamp"] = row.get("timestamp", pd.Timestamp.now())
        return row

    return None
