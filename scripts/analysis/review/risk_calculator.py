"""Sovereign risk calculation and provider card context for the review pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.model_utils import _find_card
from utils.vendor_card_template import _safe_id, load_vendor_card
from utils.provider_detection import detect_provider_from_model_id

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _resolve_vendor_card_id(name: str | None) -> str | None:
    """Löst Hersteller-/Vendor-Namen via Taxonomy-Alias-Map auf vendor_card_id auf.

    Analog zu _build_vendor_alias_map + _build_vendor_card_id_lookup in web_export.py.
    Nutzt classification_taxonomy.json/manufacturers für kanonische Normalisierung
    (z.B. "Google" → "google_deepmind", "Mistral" → "mistral_ai").

    Fallback: _safe_id() wenn kein Taxonomy-Eintrag gefunden (z.B. Community-Vendors).
    """
    if not name:
        return None
    try:
        taxonomy_path = ROOT_DIR / "config" / "classification_taxonomy.json"
        taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        for canonical, entry in taxonomy.get("manufacturers", {}).get("values", {}).items():
            if name == canonical or name in entry.get("aliases", []):
                vid = entry.get("vendor_card_id")
                return vid if vid else _safe_id(canonical)
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    # Fallback: direkte _safe_id-Konvertierung (Community-Vendors ohne Taxonomy-Eintrag)
    return _safe_id(name)


def detect_provider(model_id: str) -> str | None:
    """Infer cloud provider from model ID prefix. Returns None for local models.

    SSoT-Bridge zu :func:`utils.provider_detection.detect_provider_from_model_id`.
    """
    return detect_provider_from_model_id(model_id)


def compute_sovereign_risk(model_card: dict, provider_card: dict | None) -> tuple[str, str]:
    """Calculate combined sovereign risk at render time (worst-case principle).

    Returns (risk_level, rationale) — never stored statically.
    """
    risks: list[tuple[str, str]] = []

    wprov = (model_card.get("weights_provenance_risk") or "").lower()
    wprov_rationale = model_card.get("weights_provenance_risk_rationale", "")
    if wprov in _RISK_ORDER:
        risks.append((wprov, f"Weights-Provenienz: {wprov_rationale or wprov}"))

    if provider_card:
        dep = provider_card.get("deployment", {})
        cloud_act = dep.get("cloud_act_exposure", False)
        applicable_law = dep.get("applicable_law", "Unknown")
        nsl = (dep.get("chinese_nsl_risk") or "none").lower()

        if nsl == "high":
            risks.append(("high", f"Provider unterliegt chinesischem NSL ({provider_card.get('display_name', '')})"))
        elif cloud_act:
            eu_adequacy = dep.get("eu_adequacy_decision", False)
            level = "medium" if eu_adequacy else "high"
            risks.append((level, f"US CLOUD Act anwendbar via {provider_card.get('display_name', '')} ({'mit SCCs/DPA' if eu_adequacy else 'ohne EU-Absicherung'})"))
        elif applicable_law == "EU (GDPR)":
            risks.append(("low", f"EU-Jurisdiktion via {provider_card.get('display_name', '')} (DSGVO)"))
        elif applicable_law == "N/A (lokal only)":
            if wprov == "high":
                risks.append(("medium", "Lokal betrieben – kein Datentransfer, aber Weights stammen von riskantem Entwickler"))
            else:
                risks.append(("low", "Vollständig lokal, kein Datentransfer"))
    elif wprov == "high":
        risks.append(("medium", "Kein Provider zugeordnet (vermutlich lokal) – Weights-Risiko bleibt"))
    else:
        risks.append(("low", "Kein Cloud-Provider zugeordnet"))

    if not risks:
        return ("medium", "Unbekannte Risikokombination")

    best = max(risks, key=lambda r: _RISK_ORDER.get(r[0], 0))
    return best


def get_vendor_card_context(model_id: str) -> str:
    """Load vendor card, compute sovereign risk, return a formatted Markdown block."""
    model_card_path = _find_card(model_id)
    model_card: dict = {}
    vendor_name: str | None = None
    if model_card_path.exists():
        try:
            model_card = json.loads(model_card_path.read_text(encoding="utf-8"))
            # vendor (normalisierter Hersteller-Name) hat Vorrang vor developer.
            # Taxonomy-Lookup über _resolve_vendor_card_id() garantiert korrekten
            # Dateinamen auch bei Alias-Abweichungen (z.B. "Google" → google_deepmind.json).
            vendor_name = model_card.get("vendor") or model_card.get("developer")
        except Exception:
            pass

    provider_card: dict | None = None
    if vendor_name:
        # SSoT: Taxonomy-gestützter Lookup analog zu web_export.py.
        # Normalisiert Aliases (z.B. "Google DeepMind" → "google_deepmind").
        card_id = _resolve_vendor_card_id(vendor_name)
        if card_id:
            loaded = load_vendor_card(card_id)
            if loaded and not loaded.get("unknown"):
                provider_card = loaded

    if not model_card and not provider_card:
        return ""

    risk_level, risk_rationale = compute_sovereign_risk(model_card, provider_card)

    lines: list[str] = []
    if provider_card:
        dep = provider_card.get("deployment", {})
        lines += [
            f"### Vendor Card: {provider_card.get('display_name', vendor_name)}",
            f"- **Unternehmen:** {provider_card.get('company', 'n/a')} | **Sitz:** {provider_card.get('headquarters', 'n/a')}",
            f"- **Anwendbares Recht:** {dep.get('applicable_law', 'n/a')} | **Datenstandort:** {dep.get('data_residency', 'n/a')}",
            f"- **GDPR DPA:** {dep.get('gdpr_dpa_available', 'unknown')} | **Datenspeicherung:** {dep.get('data_retention_days', 'unknown')} Tage",
        ]
        privacy_note = provider_card.get("privacy_note", "")
        if privacy_note:
            lines.append(f"- **Deployment-Datenschutz:** {privacy_note}")

    lines.append(f"- **Berechnetes Sovereign Risk (Model × Provider):** `{risk_level.upper()}` — {risk_rationale}")

    # Die Weights-Provenienz-Information ist bereits in `risk_rationale`
    # enthalten (siehe compute_sovereign_risk) — eine separate Zeile wäre redundant.

    return "\n".join(lines)
