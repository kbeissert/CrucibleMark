"""Card Template Loader — SSoT-Zugriff auf die YAML-Card-Templates.

Lädt die in ``config/card_template_*.yaml`` definierten Templates und stellt
strukturierte Zugriffsfunktionen für Validator, Generator und Audit-Tools
bereit.

Vorher: Die Feld-Listen für Model und Provider Cards waren redundant
definiert:
- ``utils/card_utils.py::_CARD_TEMPLATE`` (Python-Dict, 38 Felder)
- ``utils/vendor_card_template.py::_PROVIDER_CARD_TEMPLATE`` (Python-Dict, 16 Felder)
- ``scripts/verify_model_cards.py::REQUIRED_FIELDS`` (hardcoded Liste, 38 Felder)
- ``utils/vendor_card_template.py::PROVIDER_CARD_FIELD_NAMES``

Drift-Risiko: REQUIRED_FIELDS in verify_model_cards.py und CARD_TEMPLATE
in card_utils.py müssen manuell synchron gehalten werden. Die YAML-Templates
in ``config/card_template_*.yaml`` sind die neue SSoT: Pflicht, Optional,
Typ, Default, Konsument und Beispiel sind pro Feld annotiert.

Verwendung:
    >>> template = load_card_template("model")
    >>> template.required_field_names
    ['model_id', 'display_name', ...]
    >>> field = template.get_field("model_id")
    >>> field.consumers
    ['risk_calc', 'leaderboard', 'web_export', 'review', 'index']
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

# YAML ist bereits im Projekt verfügbar (siehe requirements.txt)
import yaml

logger = logging.getLogger(__name__)


ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"


# Mapping card_type → YAML-Pfad
_TEMPLATE_PATHS: dict[str, Path] = {
    "model": CONFIG_DIR / "card_template_model.yaml",
    "vendor": CONFIG_DIR / "card_template_vendor.yaml",
}


@dataclass(frozen=True)
class CardFieldSpec:
    """Spec für ein einzelnes Feld in einem Card-Template."""

    name: str
    type: str
    required: bool
    default: Any
    description: str
    consumers: tuple[str, ...]
    since: str
    example: Any = None
    sub_fields_required: tuple[str, ...] = ()

    def is_unknown_sentinel(self, value: Any) -> bool:
        """Prüft ob ein Wert ein Unknown-Sentinel ist ("TODO", null, leerer String).

        Wird vom Validator verwendet um festzustellen, ob ein Pflichtfeld
        semantisch leer ist (auch wenn es den Key gibt).
        """
        if value is None:
            return True
        if isinstance(value, str) and value.strip() in {"", "TODO", "unknown", "Unknown"}:
            return True
        return bool(isinstance(value, list) and len(value) == 0)


@dataclass(frozen=True)
class CardTemplate:
    """Geladenes Card-Template mit allen Feldern und Validierungs-Konfiguration."""

    card_type: str
    version: str
    last_updated: str
    required_fields: tuple[CardFieldSpec, ...]
    optional_fields: tuple[CardFieldSpec, ...]
    validation_config: dict[str, Any] = field(default_factory=dict)

    @property
    def required_field_names(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.required_fields)

    @property
    def all_field_names(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.required_fields) + tuple(
            f.name for f in self.optional_fields
        )

    def get_field(self, name: str) -> CardFieldSpec | None:
        """Gibt die Field-Spec für einen Namen zurück, oder None."""
        for f in self.required_fields:
            if f.name == name:
                return f
        for f in self.optional_fields:
            if f.name == name:
                return f
        return None

    def is_required(self, name: str) -> bool:
        return any(f.name == name for f in self.required_fields)

    def is_known(self, name: str) -> bool:
        """True wenn Feld in required oder optional definiert ist."""
        return self.get_field(name) is not None


def _parse_field_spec(entry: dict[str, Any]) -> CardFieldSpec:
    """Konvertiert einen YAML-Entry in eine CardFieldSpec."""
    return CardFieldSpec(
        name=entry["name"],
        type=entry.get("type", "str"),
        required=bool(entry.get("required", False)),
        default=entry.get("default"),
        description=entry.get("description", ""),
        consumers=tuple(entry.get("consumers", ())),
        since=entry.get("since", ""),
        example=entry.get("example"),
        sub_fields_required=tuple(entry.get("sub_fields_required", ())),
    )


def _load_yaml_template(path: Path) -> CardTemplate:
    """Lädt ein einzelnes YAML-Template und konvertiert es in CardTemplate."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Template {path} ist kein Dict (got {type(raw).__name__})")
    return CardTemplate(
        card_type=raw.get("card_type", path.stem.replace("card_template_", "")),
        version=raw.get("version", "0.0.0"),
        last_updated=raw.get("last_updated", ""),
        required_fields=tuple(
            _parse_field_spec(e) for e in raw.get("required_fields", [])
        ),
        optional_fields=tuple(
            _parse_field_spec(e) for e in raw.get("optional_fields", [])
        ),
        validation_config=raw.get("validation", {}),
    )


@lru_cache(maxsize=4)
def load_card_template(card_type: str) -> CardTemplate:
    """Lädt und cached das Card-Template für den gegebenen Typ.

    Args:
        card_type: "model" oder "vendor"

    Returns:
        CardTemplate mit allen Feldern und Validierungs-Konfiguration.

    Raises:
        ValueError: card_type unbekannt oder Template fehlerhaft.
    """
    if card_type not in _TEMPLATE_PATHS:
        raise ValueError(
            f"Unbekannter card_type '{card_type}'. "
            f"Verfügbar: {sorted(_TEMPLATE_PATHS.keys())}"
        )
    return _load_yaml_template(_TEMPLATE_PATHS[card_type])


def clear_cache() -> None:
    """Löscht den LRU-Cache (für Tests)."""
    load_card_template.cache_clear()


# ---------------------------------------------------------------------------
# Card-Verzeichnis-Lookup (SSoT für Cards-Dir je Typ)
# ---------------------------------------------------------------------------
# Bisher existierte rebuild_provider_index() in utils/vendor_card_template.py,
# aber kein symmetrisches Pendant für Model Cards. Diese SSoT-Funktion
# konsolidiert den Index-Rebuild für beide Card-Typen, sodass Generator- und
# Validate-Skripte dieselbe Pfad- und Schreiblogik nutzen.

_CARDS_DIRS: dict[str, Path] = {
    "model": ROOT_DIR / "benchmark_scores" / "model_cards",
    "vendor": ROOT_DIR / "benchmark_scores" / "vendor_cards",
}


def cards_dir(card_type: str) -> Path:
    """Gibt das Cards-Verzeichnis für den gegebenen Typ zurück.

    Args:
        card_type: "model" oder "vendor"

    Returns:
        Pfad zum entsprechenden Cards-Verzeichnis.

    Raises:
        ValueError: card_type unbekannt.
    """
    if card_type not in _CARDS_DIRS:
        raise ValueError(
            f"Unbekannter card_type '{card_type}'. "
            f"Verfügbar: {sorted(_CARDS_DIRS.keys())}"
        )
    return _CARDS_DIRS[card_type]


def rebuild_card_index(card_type: str) -> int:
    """Baut _index.json aus allen vorhandenen Einzelkarten neu auf.

    Args:
        card_type: "model" oder "vendor"

    Returns:
        Anzahl der aufgenommenen Cards.

    Raises:
        ValueError: card_type unbekannt.
    """
    cards_dir_path = cards_dir(card_type)
    cards: list[dict[str, Any]] = []
    for p in sorted(cards_dir_path.glob("*.json")):
        if p.name == "_index.json":
            continue
        try:
            loaded = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Konnte %s nicht lesen: %s", p.name, exc)
            continue
        if isinstance(loaded, dict):
            cards.append(loaded)

    index_path = cards_dir_path / "_index.json"
    index_path.write_text(
        json.dumps(cards, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(cards)
