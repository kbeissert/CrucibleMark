"""
provider_card_template.py — SSoT für Provider Card Struktur
===========================================================
Zentrale Utility für das Erzeugen und Aktualisieren von Provider Cards.

Im Gegensatz zur Model Card (siehe ``utils/card_utils.py``) beschreibt die
Provider Card ausschließlich **Provider- bzw. Deployment-Eigenschaften**:

- Wer betreibt die API? (Unternehmen, Sitz, Gründung)
- Welches Recht gilt beim API-Call? (Deployment-Subobjekt)
- Welche Performance-Statistiken wurden gemessen? (stats, aus provider_leaderboard.csv)

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------
# Analog zu utils/ollama_config.py: ROOT_DIR wird hier lokal definiert, um
# zirkuläre Imports zu vermeiden.
ROOT_DIR = Path(__file__).parent.parent
CARDS_DIR = ROOT_DIR / "benchmark_scores" / "provider_cards"


def _cards_dir() -> Path:
    return CARDS_DIR


# ---------------------------------------------------------------------------
# Kanonisches Template — SSoT für Feldstruktur und Reihenfolge
# ---------------------------------------------------------------------------
# Felder sind in der Reihenfolge definiert, in der sie in der JSON-Datei
# erscheinen sollen.

_PROVIDER_CARD_TEMPLATE: dict[str, Any] = {
    # ---- Identität (Provider-spezifisch, nicht in Model Card) -----------
    "provider_id": None,                 # slug, wird auf provider_id gesetzt
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
    # ---- Gemessene Performance (aus provider_leaderboard.csv) ------------
    "stats": {},
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

    Identisch zur Konvention in ``scripts/analysis/generate_provider_cards.py``.
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

def ensure_provider_card(provider_id: str, *, card_path: Path | None = None) -> Path:
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
                      der kanonische Pfad ``benchmark_scores/provider_cards/{slug}.json``
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
    result["provider_id"] = _safe_id(provider_id)

    # generated_at setzen, falls weder im existing noch im Template ein Wert steht
    if not result.get("generated_at"):
        result["generated_at"] = datetime.now(timezone.utc).isoformat()

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


def load_provider_card(provider_id: str) -> dict[str, Any] | None:
    """Lädt eine Provider Card und gibt sie als Dict zurück (oder None, wenn nicht vorhanden)."""
    path = _card_path(provider_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def normalize_provider_card_data(card_data: dict[str, Any]) -> dict[str, Any]:
    """Normalisiert ein Provider-Card-Dict gegen das kanonische Template.

    Wird vom Generator (``scripts/analysis/generate_provider_cards.py``) und
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
    if "provider_id" in card_data and isinstance(card_data["provider_id"], str):
        result["provider_id"] = _safe_id(card_data["provider_id"])

    # generated_at setzen, falls nicht vorhanden
    if not result.get("generated_at"):
        result["generated_at"] = datetime.now(timezone.utc).isoformat()

    return result


def rebuild_provider_index() -> int:
    """Baut _index.json aus allen vorhandenen Einzelkarten neu auf.

    Returns:
        Anzahl der aufgenommenen Provider-Cards.
    """
    cards_dir = _cards_dir()
    cards: list[dict[str, Any]] = []
    for p in sorted(cards_dir.glob("*.json")):
        if p.name == "_index.json":
            continue
        try:
            cards.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue

    index_path = cards_dir / "_index.json"
    index_path.write_text(
        json.dumps(cards, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(cards)
