#!/usr/bin/env python3
"""Verify all model cards for completeness."""
import json
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "model_id", "display_name", "developer", "origin_country",
    "developer_jurisdiction", "deployment_type", "local_deployment_possible",
    "weights_provenance_risk", "weights_provenance_risk_rationale",
    "model_family", "primary_focus", "summary", "strengths",
    "known_limitations", "judge_context_hint", "architecture_tags",
    "unknown", "generated_at", "card_status", "size_class",
    "thinking_probe_detected", "thinking_probe_evidence",
    "thinking_probe_confidence", "thinking_probe_at",
    "supports_tool_use", "license", "license_url",
    "commercial_use_allowed", "vendor", "weights_license_tier",
    "model_version", "input_price_per_1m", "output_price_per_1m",
    "use_case_primary", "parameter_architecture", "params_total_b",
    "context_window_k", "knowledge_cutoff",
]


def _load_canonical_vendors() -> set[str]:
    """Liest die kanonische Hersteller-Liste aus config/classification_taxonomy.json.

    Gibt ein leeres Set zurück wenn die Datei nicht geladen werden kann (graceful).
    """
    taxonomy_path = Path(__file__).parent.parent / "config" / "classification_taxonomy.json"
    try:
        with open(taxonomy_path, encoding="utf-8") as f:
            taxonomy = json.load(f)
        return set(taxonomy.get("manufacturers", {}).get("values", {}).keys())
    except (OSError, json.JSONDecodeError, KeyError):
        return set()


def _load_vendor_card_id_map() -> dict[str, str]:
    """Gibt ein dict vendor_name → vendor_card_id aus der Taxonomy zurück.

    Nur Hersteller mit gesetztem vendor_card_id-Feld werden aufgeführt.
    Graceful: leeres Dict bei Ladefehler.
    """
    taxonomy_path = Path(__file__).parent.parent / "config" / "classification_taxonomy.json"
    try:
        with open(taxonomy_path, encoding="utf-8") as f:
            taxonomy = json.load(f)
        result: dict[str, str] = {}
        for name, entry in taxonomy.get("manufacturers", {}).get("values", {}).items():
            vid = entry.get("vendor_card_id")
            if vid:
                result[name] = vid
        return result
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def verify_cards():
    cards_dir = Path(__file__).parent.parent / "benchmark_scores" / "model_cards"
    issues = []
    all_model_ids = set()

    # Kanonische Hersteller-Liste + Vendor-Card-ID-Mapping laden (SSoT)
    canonical_vendors = _load_canonical_vendors()
    vendor_card_id_map = _load_vendor_card_id_map()
    vendor_cards_dir = Path(__file__).parent.parent / "benchmark_scores" / "vendor_cards"

    for card_file in sorted(cards_dir.glob("*.json")):
        with open(card_file) as f:
            data = json.load(f)
        
        if isinstance(data, list):
            issues.append(f"📁 {card_file.stem}: enthält Liste statt Dict, überspringe")
            continue
        
        model_id = data.get("model_id", card_file.stem)
        all_model_ids.add(model_id)
        
        # Pflichtfelder prüfen
        for field in REQUIRED_FIELDS:
            if field not in data:
                issues.append(f"❌ {card_file.stem}: missing field '{field}'")
            elif data[field] is None or (isinstance(data[field], str) and data[field].strip() == ""):
                issues.append(f"⚠️  {card_file.stem}: empty/null value for '{field}'")
        
        # Vendor gegen kanonische Liste validieren
        vendor_val = data.get("vendor")
        if canonical_vendors and vendor_val is not None and vendor_val not in canonical_vendors:
            issues.append(
                f"🏭 {card_file.stem}: vendor='{vendor_val}' ist nicht in der "
                f"kanonischen Hersteller-Liste (config/classification_taxonomy.json "
                f"→ manufacturers). Bitte Hersteller eintragen oder Alias ergänzen."
            )

        # Vendor-Card vorhanden? (v4.9.1 SSoT-Link Taxonomy → vendor_cards/)
        if vendor_val and vendor_val in vendor_card_id_map:
            expected_file = vendor_cards_dir / f"{vendor_card_id_map[vendor_val]}.json"
            if not expected_file.exists():
                issues.append(
                    f"🗂️  {card_file.stem}: vendor='{vendor_val}' hat vendor_card_id="
                    f"'{vendor_card_id_map[vendor_val]}' in der Taxonomy, aber keine "
                    f"Vendor Card unter benchmark_scores/vendor_cards/"
                    f"{vendor_card_id_map[vendor_val]}.json"
                )

        # Verifikations-Status prüfen (optional, aber empfohlen — v4.9.0)
        if "profile_verified" not in data:
            issues.append(f"🔍 {card_file.stem}: profile_verified fehlt (noch nicht migriert, jq-Migration ausführen)")
        elif not data.get("profile_verified"):
            issues.append(f"🔍 {card_file.stem}: profile_verified=false (Inhalt noch nicht manuell verifiziert)")

        # card_status prüfen
        if data.get("card_status") != "complete":
            issues.append(f"📝 {card_file.stem}: card_status='{data.get('card_status', 'MISSING')}'")
    
    # Gegen provider_config auf fehlende Cards prüfen (grep-basiert, keine yaml-Abhängigkeit)
    config_path = Path(__file__).parent.parent / "config" / "provider_config.yaml"
    if config_path.exists():
        config_text = config_path.read_text()
        import re
        config_model_ids = set(re.findall(r'^\s+- id:\s+(.+)$', config_text, re.MULTILINE))
        
        missing_in_cards = config_model_ids - all_model_ids
        if missing_in_cards:
            issues.append("\n📋 Modelle in config, aber keine Card vorhanden:")
            for mid in sorted(missing_in_cards):
                issues.append(f"   ❌ {mid}")
        else:
            issues.append(f"\n✅ Alle {len(config_model_ids)} Konfigurationsmodelle haben Cards.")
    
    if issues:
        print("\n".join(issues))
        return 1
    else:
        print("✅ Alle Model Cards vollständig.")
        return 0

if __name__ == "__main__":
    sys.exit(verify_cards())
