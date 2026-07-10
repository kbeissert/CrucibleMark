"""Size-Class-Klassifikation basierend auf ``classification_taxonomy.json``.

Importiert aus ``model_card_io`` (für Card-Lookups).
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from utils.model_card_io import _find_card

_SIZE_CLASS_TAXONOMY_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "classification_taxonomy.json"
)


@lru_cache(maxsize=1)
def _load_size_class_taxonomy() -> dict:
    """Laedt die size_class-Sektion aus classification_taxonomy.json (SSoT).

    Wirft RuntimeError, wenn die Datei fehlt oder die Struktur unvollstaendig
    ist — ein fehlender Tier-Tuple ist ein harter Build-Fehler, kein Fallback.

    Returns:
        dict mit Schluesseln 'thresholds_b' (list[float]), 'tier_order'
        (list[str]) und 'values' (dict[str, dict]). Struktur siehe
        config/classification_taxonomy.json#size_class.
    """
    try:
        data = json.loads(_SIZE_CLASS_TAXONOMY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Size-Class-Taxonomie nicht gefunden: {_SIZE_CLASS_TAXONOMY_PATH}"
        ) from e
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Size-Class-Taxonomie in {_SIZE_CLASS_TAXONOMY_PATH} ist kein gueltiges JSON: {e}"
        ) from e

    sc = data.get("size_class")
    if not isinstance(sc, dict):
        raise RuntimeError(
            f"size_class-Sektion fehlt in {_SIZE_CLASS_TAXONOMY_PATH}"
        )
    if "thresholds_b" not in sc or "tier_order" not in sc:
        raise RuntimeError(
            f"size_class in {_SIZE_CLASS_TAXONOMY_PATH} braucht 'thresholds_b' und 'tier_order'"
        )
    return sc


_sc = _load_size_class_taxonomy()
_SIZE_CLASS_VALID = set(_sc["tier_order"])

# Parameter-to-size-class mapping (upper bound in billions, class name).
# Aus SSoT (classification_taxonomy.json#size_class) abgeleitet; Frontier ist
# Fallback und hat keine obere Schwelle.
_SIZE_CLASS_THRESHOLDS: tuple[tuple[float, str], ...] = tuple(
    (float(threshold), tier)
    for threshold, tier in zip(_sc["thresholds_b"], _sc["tier_order"][:-1], strict=True)
)


def _param_b_to_size_class(param_b: float) -> str:
    return next(
        (cls for threshold, cls in _SIZE_CLASS_THRESHOLDS if param_b <= threshold),
        "Frontier",
    )


def _size_class_from_card_override(model_name: str) -> str | None:
    """Card-Override hat Priorität (SSoT für Modelle ohne klare Size-Tags)."""
    card_path = _find_card(model_name)
    if not card_path.exists():
        return None
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
        sc = card.get("size_class")
        if isinstance(sc, str) and sc in _SIZE_CLASS_VALID:
            return sc
    except (json.JSONDecodeError, OSError):
        return None
    return None


def _size_class_from_name_tag(model_name: str) -> str | None:
    """Extrahiert Size-Class aus Ollama-Style (``:e<N>b``) oder Dash-Suffix (``:70b``)."""
    # 2. Ollama-style colon tag: 'model:e?<N>b' (case-insensitive for edge-prefix)
    match = re.search(r":e?(\d+(?:\.\d+)?)[bB]", model_name, re.IGNORECASE)
    if match:
        try:
            return _param_b_to_size_class(float(match.group(1)))
        except ValueError:
            pass

    # 3. Dash/dot-separated suffix: 'llama-3.3-70b', 'qwen3-32b', 'scout-17b-16e'
    match = re.search(r"(?:[\-_\.])(\d+(?:\.\d+)?)[bB](?:[\-_\.]|$)", model_name, re.IGNORECASE)
    if match:
        try:
            return _param_b_to_size_class(float(match.group(1)))
        except ValueError:
            pass
    return None


def get_model_size_class(model_name: str) -> str:
    """
    Determines the hardware-deployment size class of a model based on its name tag.

    Tier-Reihenfolge, Schwellwerte und Reviewer-Labels werden aus
    ``config/classification_taxonomy.json`` geladen (SSoT). Tier-Namen und
    Spannen sind dort pflegbar; diese Funktion nimmt keine Hardcodes mehr an.

    Priority:
        1. Model-Card field ``size_class`` (single source of truth for overrides)
        2. Ollama-style tag regex (e.g. 'qwen3:4b', 'phi3.5:3.8b', 'gemma4:E4B')
        3. Dash/dot-separated size suffix (e.g. 'llama-3.3-70b', 'qwen3-32b')
        4. Fallback: 'Frontier' (API-only or size unknown)

    Returns:
        Ein Tier aus tier_order in classification_taxonomy.json (z.B.
        'Nano', 'Edge', 'Desktop', 'Workstation', 'Server', 'Frontier').
    """
    card_class = _size_class_from_card_override(model_name)
    if card_class is not None:
        return card_class

    name_class = _size_class_from_name_tag(model_name)
    if name_class is not None:
        return name_class

    # No size tag → API-only or very large (commercial model, cloud proxy)
    return "Frontier"
