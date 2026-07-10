"""
vendor_card_template.py — SSoT für Provider Card Struktur
===========================================================
Zentrale Utility für das Erzeugen und Aktualisieren von Provider Cards.

Im Gegensatz zur Model Card (siehe ``utils/card_utils.py``) beschreibt die
Provider Card ausschließlich **Provider- bzw. Deployment-Eigenschaften**:

- Wer betreibt die API? (Unternehmen, Sitz, Gründung)
- Welches Recht gilt beim API-Call? (Deployment-Subobjekt)

Ab v4.10.12: Performance-Statistiken (``stats``-Feld) sind entfernt — die
frühere Datenquelle ``benchmark_scores/provider_leaderboard.csv`` wurde
stillgelegt, weil der Web-Export keine Provider-Stats mehr anzeigt und das
Konzept "Provider-Speed-Vergleich" nicht weiterverfolgt wird.

Modell-spezifische Informationen (developer, origin_country, summary, strengths,
known_limitations, …) leben ausschließlich in der Model Card. Diese Trennung
ist die kanonische Architekturentscheidung — siehe ``docs/ARCHITECTURE.md``.

Regeln:
  - Existierende Werte werden NIE überschrieben.
  - Nur fehlende Felder werden mit Platzhaltern ergänzt.
  - Idempotent: mehrfacher Aufruf hat keine Nebenwirkungen.
  - ``unknown: true`` wird bei fehlenden Pflichtfeldern nicht eigenmächtig gesetzt.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------
# Analog zu utils/ollama_config.py: ROOT_DIR wird hier lokal definiert, um
# zirkuläre Imports zu vermeiden.
ROOT_DIR = Path(__file__).parent.parent
CARDS_DIR = ROOT_DIR / "benchmark_scores" / "vendor_cards"


def _cards_dir() -> Path:
    return CARDS_DIR


# ---------------------------------------------------------------------------
# Kanonisches Template — SSoT für Feldstruktur und Reihenfolge
# ---------------------------------------------------------------------------
# Felder sind in der Reihenfolge definiert, in der sie in der JSON-Datei
# erscheinen sollen.

_PROVIDER_CARD_TEMPLATE: dict[str, Any] = {
    # ---- Identität (Provider-spezifisch, nicht in Model Card) -----------
    "vendor_id": None,                 # slug, wird auf provider_id gesetzt
    "display_name": "TODO",
    "company": "TODO",
    "headquarters": "TODO",
    "founding_year": None,
    # ---- API / Geschäftsmodell (Provider-spezifisch) --------------------
    "pricing_model": "unknown",
    "api_base_url": None,
    "api_documentation_url": None,
    # ---- Deployment / Compliance (KERN — aktiv genutzt in risk_calculator)
    "deployment": {
        "cloud_act_exposure": False,
        "applicable_law": "Unknown",
        "data_residency": "Unknown",
        "gdpr_dpa_available": "unknown",
        "eu_adequacy_decision": "unknown",
        "data_retention_days": -1,
        "chinese_nsl_risk": "none",
    },
    # ---- Datenschutz-Hinweis (provider-spezifisch) -----------------------
    "privacy_note": "TODO",
    # ---- Redaktioneller Kontext (Provider-übergreifend) -----------------
    "notable_models": [],
    # ---- Metadaten -------------------------------------------------------
    "unknown": False,
    "generated_at": None,
    "last_verified_at": None,
    "verification_source": None,
}

# Vollständige Feldliste (für externe Validierung)
PROVIDER_CARD_FIELD_NAMES: list[str] = list(_PROVIDER_CARD_TEMPLATE.keys())

# Deployment-Sub-Felder, die validiert werden müssen
_DEPLOYMENT_FIELD_NAMES: list[str] = list(_PROVIDER_CARD_TEMPLATE["deployment"].keys())


def _safe_id(name: str) -> str:
    """Konvertiert einen Provider-Namen in einen sicheren Dateinamen / ID.

    Identisch zur Konvention in ``scripts/analysis/generate_vendor_cards.py``.
    """
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def _card_path(provider_id: str) -> Path:
    """Gibt den kanonischen Pfad zu einer Provider Card zurück."""
    return _cards_dir() / f"{_safe_id(provider_id)}.json"


# ---------------------------------------------------------------------------
# Kernfunktion
# ---------------------------------------------------------------------------

def ensure_vendor_card(provider_id: str, *, card_path: Path | None = None) -> Path:
    """Stellt sicher, dass die Provider Card für *provider_id* alle Strukturfelder enthält.

    Verhalten:
    - Existiert keine Card: erstellt sie komplett mit Platzhaltern.
    - Existiert eine Card: ergänzt nur fehlende Felder — bestehende Werte
      werden nie verändert.
    - Nicht-Template-Felder werden erhalten und ans Ende der Card gesetzt.
    - ``unknown: true`` wird **nicht** eigenmächtig gesetzt — das ist Aufgabe
      eines Validators / Reviewers.

    Args:
        provider_id:  Slug des Providers (z.B. ``"anthropic"``).
        card_path:    Optionaler expliziter Pfad. Wenn nicht angegeben, wird
                      der kanonische Pfad ``benchmark_scores/vendor_cards/{slug}.json``
                      verwendet.

    Returns:
        Pfad zur Card-Datei (nach Aufruf garantiert vorhanden).
    """
    if card_path is None:
        card_path = _card_path(provider_id)

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

    for key, default in _PROVIDER_CARD_TEMPLATE.items():
        if key in existing:
            # Bestehenden Wert beibehalten
            result[key] = existing[key]
        elif key == "deployment":
            # Deployment-Sub-Objekt: mergen — bestehende Felder erhalten, fehlende ergänzen
            existing_dep = existing.get("deployment", {})
            if not isinstance(existing_dep, dict):
                existing_dep = {}
            result[key] = {**default, **existing_dep}
        else:
            # Fehlende Felder mit statischen Defaults ergänzen
            result[key] = deepcopy(default)

    # provider_id immer korrekt setzen
    result["vendor_id"] = _safe_id(provider_id)

    # generated_at setzen, falls weder im existing noch im Template ein Wert steht
    if not result.get("generated_at"):
        result["generated_at"] = datetime.now(UTC).isoformat()

    # Nicht-Template-Felder aus bestehender Card ans Ende anhängen
    for key, value in existing.items():
        if key not in result:
            result[key] = value

    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return card_path


def load_vendor_card(provider_id: str) -> dict[str, Any] | None:
    """Lädt eine Provider Card und gibt sie als Dict zurück (oder None, wenn nicht vorhanden)."""
    path = _card_path(provider_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def normalize_vendor_card_data(card_data: dict[str, Any]) -> dict[str, Any]:
    """Normalisiert ein Provider-Card-Dict gegen das kanonische Template.

    Wird vom Generator (``scripts/analysis/generate_vendor_cards.py``) und
    von Migration-Scripten verwendet, um rohe Dicts (z.B. LLM-Output) in das
    kanonische Schema zu überführen.

    Regeln:
    - Felder aus ``card_data`` werden übernommen, wenn sie im Template sind.
    - Fehlende Felder werden mit Default-Werten aus dem Template ergänzt.
    - ``deployment``-Sub-Felder werden gemergt (nicht ersetzt).
    - Felder, die **nicht** im Template sind (z.B. Legacy ``origin_country``,
      ``developer_jurisdiction``, ``summary``, ``strengths``,
      ``known_limitations``, ``developer``), werden verworfen — diese Felder
      gehören in die Model Card, siehe :mod:`utils.card_utils`.
    - ``provider_id`` wird auf den kanonischen Slug normalisiert.
    - ``generated_at`` wird auf jetzt gesetzt, falls nicht vorhanden.

    Returns:
        Normalisiertes Dict (Reihenfolge wie im Template).
    """
    if not isinstance(card_data, dict):
        card_data = {}

    result: dict[str, Any] = {}

    for key, default in _PROVIDER_CARD_TEMPLATE.items():
        if key in card_data:
            result[key] = card_data[key]
        elif key == "deployment":
            existing_dep = card_data.get("deployment", {})
            if not isinstance(existing_dep, dict):
                existing_dep = {}
            result[key] = {**default, **existing_dep}
        else:
            result[key] = deepcopy(default)

    # provider_id immer auf kanonischen Slug setzen
    if "vendor_id" in card_data and isinstance(card_data["vendor_id"], str):
        result["vendor_id"] = _safe_id(card_data["vendor_id"])

    # generated_at setzen, falls nicht vorhanden
    if not result.get("generated_at"):
        result["generated_at"] = datetime.now(UTC).isoformat()

    return result


# ---------------------------------------------------------------------------
# Card-Status (Phase 22)
# ---------------------------------------------------------------------------
# Liefert einen Audit-Readiness-Report über alle Provider Cards:
# - total / verified / unknown / stale / parse_errors
# - stale: last_verified_at (oder generated_at) älter als stale_days
# - unknown_fields: deployment.Sub-Felder mit "unknown" oder NSL-Mismatch
#
# Konsument: ``make vendor-cards-status`` + Audit-Hooks.

_DEPLOYMENT_FIELDS_REQUIRING_VERIFICATION: list[str] = [
    "cloud_act_exposure",
    "applicable_law",
    "data_residency",
    "gdpr_dpa_available",
    "eu_adequacy_decision",
    "data_retention_days",
    "chinese_nsl_risk",
]


def _parse_iso_timestamp(value: str | None) -> datetime | None:
    """Toleranter ISO-8601-Parser. Gibt None zurück bei ungültigen Werten.

    Normalisiert naive datetimes auf UTC, damit Subtraktionen gegen ``now``
    (timezone-aware) konsistent funktionieren.
    """
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _is_deployment_field_unknown(card: dict[str, Any], field: str) -> bool:
    """Prüft ob ein deployment.Sub-Feld als 'unknown' markiert oder leer ist."""
    dep = card.get("deployment", {})
    if not isinstance(dep, dict):
        return True
    value = dep.get(field)
    if value in (None, "", "unknown", "Unknown"):
        return True
    if field == "data_retention_days" and value == -1:
        return True
    if field == "chinese_nsl_risk" and value == "unknown":
        return True
    return False


def get_vendor_card_status(stale_days: int = 90) -> dict[str, Any]:
    """Audit-Readiness-Report über alle Provider Cards.

    Args:
        stale_days: Schwellwert (Tage) für ``stale``-Klassifikation. Cards ohne
                    ``last_verified_at`` (oder ohne ``generated_at``) zählen
                    immer als stale.

    Returns:
        Dict mit:
            - total: int (Anzahl gefundener Karten)
            - verified: int (last_verified_at vorhanden und nicht stale)
            - unknown: int (unknown=true auf Card-Ebene)
            - stale: int (älter als stale_days oder ohne Timestamp)
            - missing_timestamp: int (weder generated_at noch last_verified_at)
            - parse_errors: int (JSON-Parse-Fehler)
            - cards_with_unknown_deployment_fields: int
            - by_provider: list[dict] (Detail pro Provider)
            - stale_threshold_days: int (echo des Parameters)
            - checked_at: ISO-8601-Timestamp
    """
    now = datetime.now(UTC)
    cards_dir = _cards_dir()
    by_provider: list[dict[str, Any]] = []
    counts = {
        "verified": 0,
        "unknown": 0,
        "stale": 0,
        "missing_timestamp": 0,
        "parse_errors": 0,
        "cards_with_unknown_deployment_fields": 0,
    }

    for path in sorted(cards_dir.glob("*.json")):
        if path.name == "_index.json":
            continue
        provider_id = path.stem

        try:
            card = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            counts["parse_errors"] += 1
            by_provider.append({
                "vendor_id": provider_id,
                "status": "parse_error",
            })
            continue

        last_verified = _parse_iso_timestamp(card.get("last_verified_at"))
        generated_at = _parse_iso_timestamp(card.get("generated_at"))
        timestamp = last_verified or generated_at

        missing_ts = timestamp is None
        is_stale = missing_ts
        if timestamp is not None:
            age = now - timestamp
            is_stale = age.days > stale_days

        is_unknown = bool(card.get("unknown"))
        unknown_fields = [
            f for f in _DEPLOYMENT_FIELDS_REQUIRING_VERIFICATION
            if _is_deployment_field_unknown(card, f)
        ]

        if is_unknown:
            status = "unknown"
            counts["unknown"] += 1
        elif is_stale:
            status = "stale"
            counts["stale"] += 1
        else:
            status = "verified"
            counts["verified"] += 1

        if missing_ts:
            counts["missing_timestamp"] += 1
        if unknown_fields:
            counts["cards_with_unknown_deployment_fields"] += 1

        by_provider.append({
            "vendor_id": provider_id,
            "display_name": card.get("display_name", provider_id),
            "status": status,
            "last_verified_at": card.get("last_verified_at"),
            "generated_at": card.get("generated_at"),
            "age_days": (now - timestamp).days if timestamp else None,
            "unknown_deployment_fields": unknown_fields,
        })

    return {
        "total": len(by_provider),
        **counts,
        "stale_threshold_days": stale_days,
        "checked_at": now.isoformat(),
        "by_provider": by_provider,
    }


def format_vendor_card_status(report: dict[str, Any]) -> str:
    """Formatiert einen get_vendor_card_status-Report als lesbaren CLI-Output."""
    lines: list[str] = []
    lines.append("=== Provider Card Status ===")
    lines.append(f"Total:                  {report['total']}")
    lines.append(f"  Verified:             {report['verified']}")
    lines.append(f"  Unknown:              {report['unknown']}")
    lines.append(f"  Stale (>{report['stale_threshold_days']}d):     {report['stale']}")
    lines.append(f"  Missing timestamp:    {report['missing_timestamp']}")
    lines.append(f"  Parse errors:         {report['parse_errors']}")
    lines.append(f"  Unknown dep-fields:   {report['cards_with_unknown_deployment_fields']}")
    lines.append("")

    # Gruppierung nach Status
    by_status: dict[str, list[dict[str, Any]]] = {}
    for entry in report.get("by_provider", []):
        by_status.setdefault(entry["status"], []).append(entry)

    if by_status.get("unknown"):
        lines.append(f"--- Unknown ({len(by_status['unknown'])}) ---")
        for e in by_status["unknown"]:
            lines.append(f"  • {e['vendor_id']}  (display_name: {e.get('display_name', 'n/a')})")
        lines.append("")

    if by_status.get("stale"):
        lines.append(f"--- Stale ({len(by_status['stale'])}) ---")
        for e in by_status["stale"]:
            age = f"age={e['age_days']}d" if e.get("age_days") is not None else "no-timestamp"
            lines.append(f"  • {e['vendor_id']}  ({age})")
        lines.append("")

    if by_status.get("parse_error"):
        lines.append(f"--- Parse errors ({len(by_status['parse_error'])}) ---")
        for e in by_status["parse_error"]:
            lines.append(f"  • {e['vendor_id']}")
        lines.append("")

    if report["cards_with_unknown_deployment_fields"] > 0:
        lines.append("--- Cards mit unknown deployment-Sub-Feldern ---")
        for e in report.get("by_provider", []):
            if e.get("unknown_deployment_fields"):
                fields = ", ".join(e["unknown_deployment_fields"])
                lines.append(f"  • {e['vendor_id']}: {fields}")
        lines.append("")

    lines.append(f"Checked at: {report['checked_at']}")
    return "\n".join(lines)
