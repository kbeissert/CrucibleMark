"""
card_utils.py — SSoT für Model Card Struktur
=============================================
Zentrale Utility für das Erzeugen und Aktualisieren von Model Cards.

Alle Scripts, die Werte in eine Model Card schreiben (Benchmark-Runner,
Thinking-Probe, manuelle Tools), rufen zuerst ``ensure_card()`` auf.
Diese Funktion garantiert, dass die Card vollständig strukturiert ist,
bevor irgendwelche domänenspezifischen Werte eingetragen werden.

Regeln:
  - Existierende Werte werden NIE überschrieben.
  - Nur fehlende Felder werden mit Platzhaltern ergänzt.
  - Idempotent: mehrfacher Aufruf hat keine Nebenwirkungen.
  - ``card_status: "minimal"`` wird auf ``"draft"`` hochgestuft.
"""

from __future__ import annotations

import json
import logging
import yaml  # type: ignore[import-untyped]

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Taxonomie-SSoT (config/classification_taxonomy.json)
# ---------------------------------------------------------------------------
# Single source of truth für kontrollierte Vokabulare. Wird von
# - ensure_card() (Defaults-Validierung)
# - scripts/dev/validate_model_cards.py (Whitelist-Prüfung)
# - utils/model_utils.py:WEIGHTS_TIER_DISPLAY (Runtime-Mapping)
# konsumiert. Valid-Werte NICHT hier duplizieren — nur aus Taxonomie lesen.

_TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "config" / "classification_taxonomy.json"
_TAXONOMY_CACHE: dict[str, dict[str, Any]] | None = None


def load_taxonomy() -> dict[str, dict[str, Any]]:
    """Lädt die Klassifikations-Taxonomie (SSoT) mit Caching.

    Returns:
        Dict[section_name, section_dict] — z.B. {"use_case": {...}, "weights_license_tier": {...}}.

    Raises:
        FileNotFoundError: wenn config/classification_taxonomy.json fehlt.
    """
    global _TAXONOMY_CACHE
    if _TAXONOMY_CACHE is None:
        if not _TAXONOMY_PATH.exists():
            raise FileNotFoundError(
                f"Taxonomie-Datei fehlt: {_TAXONOMY_PATH}. "
                f"Diese ist SSoT für kontrollierte Vokabulare (weights_license_tier, use_case_primary, ...)."
            )
        with _TAXONOMY_PATH.open(encoding="utf-8") as f:
            _TAXONOMY_CACHE = json.load(f)
    assert _TAXONOMY_CACHE is not None
    return _TAXONOMY_CACHE


def get_valid_values(section: str) -> frozenset[str]:
    """Gibt die gültigen Werte einer Taxonomie-Section zurück.

    Args:
        section: Key in classification_taxonomy.json (z.B. "weights_license_tier", "use_case", "parameter_architecture").

    Returns:
        frozenset der erlaubten Werte. Fallback: leeres frozenset wenn Section fehlt.
    """
    try:
        taxonomy = load_taxonomy()
        section_data = taxonomy.get(section, {})
        return frozenset(section_data.get("values", {}).keys())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Taxonomie-Section '%s' nicht ladbar: %s", section, exc)
        return frozenset()


def clear_taxonomy_cache() -> None:
    """Setzt den Taxonomie-Cache zurück (für Tests)."""
    global _TAXONOMY_CACHE
    _TAXONOMY_CACHE = None


# ---------------------------------------------------------------------------
# Card-Vokabular-SSoT (config/card_vocabulary.yaml)
# ---------------------------------------------------------------------------
# Erweiterte Registry für Tag-Vokabulare, Normalisierungen und Reasoning-
# Trigger-Listen. Wird konsumiert von:
#   - scripts/dev/validate_model_cards.py (Tag-Whitelist)
#   - scripts/dev/migrate_architecture_tags.py (Normalisierung)
#   - utils/model_utils.py (Reasoning-Trigger-Liste)
#   - scripts/web_export.py (Tag-Filter)
# Struktur: controlled_fields, reserved_tags, informational_tags,
#           deprecated_tags, reasoning_triggers.

_VOCABULARY_PATH = Path(__file__).resolve().parent.parent / "config" / "card_vocabulary.yaml"
_VOCABULARY_CACHE: dict[str, Any] | None = None


def load_vocabulary() -> dict[str, Any]:
    """Lädt die Card-Vokabular-Registry (SSoT) mit Caching.

    Returns:
        Dict mit Sektionen: controlled_fields, reserved_tags,
        informational_tags, deprecated_tags, reasoning_triggers.

    Raises:
        FileNotFoundError: wenn config/card_vocabulary.yaml fehlt.
    """
    global _VOCABULARY_CACHE
    if _VOCABULARY_CACHE is None:
        if not _VOCABULARY_PATH.exists():
            raise FileNotFoundError(
                f"Vokabular-Registry fehlt: {_VOCABULARY_PATH}. "
                f"Diese ist SSoT für Tag-Vokabulare und Normalisierungen."
            )
        with _VOCABULARY_PATH.open(encoding="utf-8") as f:
            _VOCABULARY_CACHE = yaml.safe_load(f)
    assert _VOCABULARY_CACHE is not None
    return _VOCABULARY_CACHE


def get_reserved_tags() -> frozenset[str]:
    """Gibt alle programmatisch wirksamen Tag-Slugs zurück (Whitelist)."""
    try:
        vocab = load_vocabulary()
        return frozenset(t["slug"] for t in vocab.get("reserved_tags", []))
    except (FileNotFoundError, KeyError) as exc:
        logger.warning("Vokabular-Registry für reserved_tags nicht ladbar: %s", exc)
        return frozenset()


def get_informational_tags() -> frozenset[str]:
    """Gibt alle redaktionellen Tag-Slugs zurück (Whitelist)."""
    try:
        vocab = load_vocabulary()
        return frozenset(t["slug"] for t in vocab.get("informational_tags", []))
    except (FileNotFoundError, KeyError) as exc:
        logger.warning("Vokabular-Registry für informational_tags nicht ladbar: %s", exc)
        return frozenset()


# Mapping from card field names to their taxonomy sections (SSoT).
# Controlled values must be present in classification_taxonomy.json.
_CONTROLLED_FIELDS: dict[str, str] = {
    "weights_license_tier": "weights_license_tier",
    "use_case_primary": "use_case",
    "parameter_architecture": "parameter_architecture",
    "input_modalities": "input_modalities",
    "output_modalities": "output_modalities",
}


def get_all_known_tags() -> frozenset[str]:
    """Vereinigung von reserved + informational + deprecated (für Whitelist-Validierung)."""
    try:
        vocab = load_vocabulary()
        slugs: set[str] = set()
        for section in ("reserved_tags", "informational_tags", "deprecated_tags"):
            slugs.update(t["slug"] for t in vocab.get(section, []))
        return frozenset(slugs)
    except (FileNotFoundError, KeyError) as exc:
        logger.warning("Vokabular-Registry nicht ladbar: %s", exc)
        return frozenset()


def get_deprecated_normalizations() -> dict[str, str | None]:
    """Gibt ein Mapping {alter_slug: normalisierter_slug | None} zurück.

    None bedeutet: Tag wird entfernt (nicht durch einen anderen ersetzt).
    """
    try:
        vocab = load_vocabulary()
        return {
            t["slug"]: t.get("normalized_to")
            for t in vocab.get("deprecated_tags", [])
        }
    except (FileNotFoundError, KeyError) as exc:
        logger.warning("Vokabular-Registry für deprecated_tags nicht ladbar: %s", exc)
        return {}


def get_reasoning_triggers() -> list[str]:
    """Gibt die Liste der Modellname-Substrings zurück, die den 5× Reasoning-Multiplikator triggern."""
    try:
        vocab = load_vocabulary()
        return list(vocab.get("reasoning_triggers", []))
    except (FileNotFoundError, KeyError) as exc:
        logger.warning("Vokabular-Registry für reasoning_triggers nicht ladbar: %s", exc)
        return []


def normalize_tags(tags: list[str]) -> tuple[list[str], list[tuple[str, str | None, str]]]:
    """Normalisiert eine Tag-Liste gemäß Vokabular-Registry.

    Args:
        tags: Rohe Tag-Liste aus einer Card.

    Returns:
        Tuple (normalisierte_tags, migrations_report).
        migrations_report enthält (alter_slug, neuer_slug | None, grund) für jeden migrierten Tag.
        None als neuer_slug bedeutet: Tag wurde entfernt.
    """
    normalizations = get_deprecated_normalizations()
    normalized: list[str] = []
    report: list[tuple[str, str | None, str]] = []

    for tag in tags:
        if tag in normalizations:
            new_value = normalizations[tag]
            # Lookup Grund aus Registry
            try:
                vocab = load_vocabulary()
                reason = next(
                    (t.get("reason", "") for t in vocab.get("deprecated_tags", []) if t["slug"] == tag),
                    "",
                )
            except (FileNotFoundError, KeyError):
                reason = ""
            report.append((tag, new_value, reason))
            if new_value is not None and new_value not in normalized:
                normalized.append(new_value)
        else:
            if tag not in normalized:
                normalized.append(tag)

    return normalized, report


def clear_vocabulary_cache() -> None:
    """Setzt den Vokabular-Cache zurück (für Tests)."""
    global _VOCABULARY_CACHE
    _VOCABULARY_CACHE = None


# ---------------------------------------------------------------------------
# Kanonisches Template — SSoT für Feldstruktur und Reihenfolge
# ---------------------------------------------------------------------------
# Felder sind in der Reihenfolge definiert, in der sie in der JSON-Datei
# erscheinen sollen.  Bestehende nicht-Template-Felder (z.B. tooluse_tested_at)
# werden ans Ende angehängt.

_CARD_TEMPLATE: dict[str, Any] = {
    # ---- Kern-Identität ------------------------------------------------
    "model_id": None,               # wird immer auf model_id gesetzt
    "display_name": "TODO",
    "developer": "TODO",
    "origin_country": "TODO",
    "developer_jurisdiction": "TODO",
    # ---- Deployment & Provenance ---------------------------------------
    "deployment_type": "TODO",
    "local_deployment_possible": None,
    "weights_provenance_risk": "TODO",
    "weights_provenance_risk_rationale": "TODO",
    # ---- Klassifikation ------------------------------------------------
    "model_family": "TODO",
    "vendor": "TODO",
    "primary_focus": "TODO",
    "use_case_primary": "generalist",
    # ---- Architektur ---------------------------------------------------
    "parameter_architecture": "dense",
    "params_total_b": None,
    "params_active_b": None,
    "context_window_k": None,
    "knowledge_cutoff": None,
    # ---- Beschreibung --------------------------------------------------
    "summary": "TODO",
    "strengths": ["TODO"],
    "known_limitations": ["TODO"],
    "judge_context_hint": "TODO",
    "architecture_tags": ["General"],
    # ---- Modalität (SSoT: classification_taxonomy.json#input/output_modalities) --
    "input_modalities": ["text"],
    "output_modalities": ["text"],

    # ---- Tool-Use ------------------------------------------------------
    "supports_tool_use": None,
    "tooluse_tested_at": None,
    "tooluse_score_p1": None,
    "tooluse_score_p2": None,
    "tooluse_recommendation": None,
    # ---- Sampling-Parameter --------------------------------------------
    "temperature": None,
    "system_prompt_override": None,
    "cot_marker_family": None,
    "cot_tags_detected": None,
    "top_p": None,
    "top_k": None,
    "repetition_penalty": None,
    "frequency_penalty": None,
    "presence_penalty": None,
    "seed": None,
    "stop_sequences": None,
    # ---- Lizenz & Kategorisierung --------------------------------------
    "license": "TODO",
    "license_url": None,
    "commercial_use_allowed": None,
    "weights_license_tier": "TODO",
    # ---- Pricing (SSoT) ------------------------------------------------
    "model_version": None,
    "input_price_per_1m": None,
    "output_price_per_1m": None,
    # ---- Metadaten -----------------------------------------------------
    "unknown": False,
    "card_status": "draft",
    "size_class": None,             # wird berechnet falls fehlend
    "generated_at": None,           # wird auf jetzt gesetzt falls fehlend
    # ---- Thinking-Probe ------------------------------------------------
    "thinking_probe_detected": None,
    "thinking_probe_evidence": None,
    "thinking_probe_confidence": None,
    "thinking_probe_at": None,
    "thinking_probe_manual_override": None,
    # ---- Profile-Verifikation (Audit-Trail) ----------------------------
    "profile_verified": False,
    "profile_verified_at": None,
    "profile_verified_by": None,
    "last_modified_at": None,
    # ---- Heritage & Community ------------------------------------------
    "heritage_ids": [],
    "community": None,
}

# Vollständige Feldliste (für externe Validierung)
CARD_FIELD_NAMES: list[str] = list(_CARD_TEMPLATE.keys())


# ---------------------------------------------------------------------------
# Kernfunktion
# ---------------------------------------------------------------------------

def ensure_card(
    model_id: str,
    *,
    card_path: Path | None = None,
    provider: str | None = None,
) -> Path:
    """Stellt sicher, dass die Card für *model_id* alle Strukturfelder enthält.

    Verhalten:
    - Existiert keine Card: erstellt sie komplett mit Platzhaltern.
    - Existiert eine Card: ergänzt nur fehlende Felder — bestehende Werte
      werden nie verändert.
    - ``card_status: "minimal"`` wird auf ``"draft"`` hochgestuft.
    - Nicht-Template-Felder (z.B. ``tooluse_tested_at``) werden erhalten
      und ans Ende der Card gesetzt.

    Args:
        model_id:  Modell-Identifier (wird immer als ``model_id``-Feld in der Card gesetzt).
        card_path: Optionaler expliziter Pfad zur Card-Datei.  Wenn nicht angegeben,
                   wird der kanonische Pfad via ``_card_path(for_write=True)`` bestimmt.
                   Nützlich wenn der Aufrufer den Pfad bereits per ``_find_card`` ermittelt hat.
        provider:  Optionaler Provider-Key (z. B. ``"llamacpp_spark"``, ``"openrouter"``).
                   Wenn übergeben, wird die ID via ``build_card_id`` + ``resolve_unique_card_id``
                   eindeutig gemacht (Schema: ``{base}--{shortcode}``, Konflikt → ``-2``-Suffix).
                   Ohne Provider bleibt das Verhalten wie bisher rückwärtskompatibel
                   (kanonischer Pfad, kein Konflikt-Resolver).

    Returns:
        Pfad zur Card-Datei (nach Aufruf garantiert vorhanden).
    """
    # Importiert hier lokal, um Circular-Import-Risiko zu minimieren.
    from utils.model_utils import (  # noqa: PLC0415
        _card_path,
        build_card_id,
        get_model_size_class,
        resolve_unique_card_id,
    )

    # Wenn ein Provider uebergeben wird, hat das neue ID-Schema
    # ({base}--{shortcode}) Vorrang vor einem expliziten card_path.
    # card_path stammt in Produktion aus _find_card und nutzt das alte
    # Pfad-Schema -- ein Mischen wuerde zu doppelten/verwaisten Karten fuehren.
    if provider:
        # Neues ID-Schema aktiv: {model_base}--{shortcode}, Konflikt-Resolver.
        desired_id = build_card_id(model_id, provider)
        unique_id = resolve_unique_card_id(desired_id)
        # Wenn der Resolver einen anderen Namen liefert als model_id, übernimm
        # diesen — die Card entsteht unter dem neuen Namen.
        if unique_id != model_id:
            # Pfad explizit auf die kanonische Card-Datei des unique_id legen
            # (kein Provider-Shortcode, weil unique_id schon eindeutig ist).
            card_path = _card_path(unique_id, provider=None, for_write=True)
            model_id = unique_id
        else:
            card_path = _card_path(model_id, provider=provider, for_write=True)
    elif card_path is None:
        card_path = _card_path(model_id, for_write=True)

    # Bestehende Card laden (oder leer starten)
    existing: dict[str, Any] = {}
    if card_path.exists():
        try:
            existing = json.loads(card_path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {}
        except (json.JSONDecodeError, OSError):
            existing = {}

    # Ergebnis aufbauen: Template-Felder in kanonischer Reihenfolge
    result: dict[str, Any] = {}

    for key, default in _CARD_TEMPLATE.items():
        if key in existing:
            # Bestehenden Wert beibehalten
            result[key] = existing[key]
        else:
            # Fehlende Felder mit berechneten oder statischen Defaults ergänzen
            if key == "model_id":
                result[key] = model_id
            elif key == "size_class":
                try:
                    result[key] = get_model_size_class(model_id)
                except (FileNotFoundError, json.JSONDecodeError):
                    result[key] = None
            elif key == "generated_at":
                result[key] = datetime.now(timezone.utc).isoformat()
            else:
                # Mutable Defaults deep-kopieren (z.B. Listen)
                result[key] = deepcopy(default)

    # model_id immer korrekt setzen (auch wenn schon vorhanden)
    result["model_id"] = model_id

    # "minimal" → "draft"  (kein Downgrade von "complete")
    if existing.get("card_status") == "minimal":
        result["card_status"] = "draft"

    # Nicht-Template-Felder aus bestehender Card ans Ende anhängen
    for key, value in existing.items():
        if key not in result:
            result[key] = value

    # Whitelist-Check für kontrollierte Vokabulare (SSoT: classification_taxonomy).
    # "TODO" ist explizit als "noch zu befüllen"-Platzhalter erlaubt — keine Warnung.
    # Andere Werte, die nicht in der Taxonomie stehen, lösen eine WARN aus.
    # Das ist ein Hinweis, kein Hard-Error: der Autor kann bewusst abweichen.
    for card_field, taxonomy_section in _CONTROLLED_FIELDS.items():
        value = result.get(card_field)
        if value is None or value == "TODO" or value == "":
            continue
        # Listen-Felder (Modalitäten) vs. Skalar-Felder
        if isinstance(value, list):
            valid = get_valid_values(taxonomy_section)
            invalid_items = [v for v in value if valid and v not in valid]
            if invalid_items:
                logger.warning(
                    "Card '%s': %s enthält ungültige Werte %s. "
                    "Erlaubte Werte: %s.",
                    model_id, card_field, invalid_items, sorted(valid),
                )
        else:
            valid = get_valid_values(taxonomy_section)
            if valid and value not in valid:
                logger.warning(
                    "Card '%s': %s='%s' ist nicht in der Taxonomie-Section '%s'. "
                    "Erlaubte Werte: %s. 'TODO' ist explizit als Platzhalter erlaubt.",
                    model_id, card_field, value, taxonomy_section, sorted(valid),
                )

    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return card_path
