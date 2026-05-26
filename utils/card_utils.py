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
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    # ---- Tool-Use ------------------------------------------------------
    "supports_tool_use": None,
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
}

# Vollständige Feldliste (für externe Validierung)
CARD_FIELD_NAMES: list[str] = list(_CARD_TEMPLATE.keys())


# ---------------------------------------------------------------------------
# Kernfunktion
# ---------------------------------------------------------------------------

def ensure_card(model_id: str, *, card_path: Path | None = None) -> Path:
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

    Returns:
        Pfad zur Card-Datei (nach Aufruf garantiert vorhanden).
    """
    # Importiert hier lokal, um Circular-Import-Risiko zu minimieren.
    from utils.model_utils import _card_path, get_model_size_class  # noqa: PLC0415

    if card_path is None:
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
                except Exception:  # noqa: BLE001
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

    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return card_path
