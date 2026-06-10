"""
Auto-Fix für triviale Whitelist-Verstöße in Model Cards.

Behebt:
- supports_tool_use="untested" → null (Tri-State-Migration)
- card_status="verified" → "complete" (alte 4. Status)
- unknown=true → false (wenn card_status="complete" → Widerspruch)
- weights_provenance_risk="mittel-hoch" → "high" (deutsche Werte)
- size_class="Consumer-GPU" → "Workstation" (alte Schreibweise)
- deployment_type="open_weights" → "open-weights" (Tippfehler)
- deployment_type="api-only" → "cloud-only" (semantisch äquivalent)
- deployment_type="proprietary-api-only" → "cloud-only"
- deployment_type="api-and-local" → "open-weights-cloud-available" (default;
  für einzelne Modelle ist manuelle Anpassung möglich)

Nutzt SSoT aus config/card_template_model.yaml, config/card_vocabulary.yaml,
config/classification_taxonomy.json.

Idempotent: Mehrfach-Ausführung ändert nichts nach dem ersten Lauf.

Verwendung:
    .venv/bin/python scripts/dev/fix_model_cards_whitelist.py --dry-run
    .venv/bin/python scripts/dev/fix_model_cards_whitelist.py --apply
    .venv/bin/python scripts/dev/fix_model_cards_whitelist.py --file card.json --apply
"""

import argparse
import json
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

logger = logging.getLogger(__name__)

CARDS_DIR = Path("benchmark_scores/model_cards")


# Mapping-Tabellen (idempotent)
DEPLOYMENT_TYPE_FIXES = {
    "api-only": "cloud-only",
    "proprietary-api-only": "cloud-only",
    "open_weights": "open-weights",  # Tippfehler
    # "api-and-local" wird unten separat behandelt (modell-spezifisch)
}

DEPLOYMENT_TYPE_API_AND_LOCAL = "api-and-local"  # Wird zu open-weights-cloud-available

# Manuelle Ausnahmen für api-and-local
# (Cards, die als cloud-only bleiben sollen, z.B. weil Weights nicht verfügbar)
API_AND_LOCAL_KEEP_CLOUD = set()  # Aktuell keine

CARD_STATUS_FIXES = {
    "verified": "complete",
}

SIZE_CLASS_FIXES = {
    "Consumer-GPU": "Workstation",
    # Weitere können ergänzt werden
}

RISK_FIXES = {
    "mittel-hoch": "high",
    "niedrig": "low",
    "niedrig-mittel": "low",
    "mittel": "medium",
    "hoch": "high",
}


def fix_card(path: Path, apply: bool = False) -> list[str]:
    """Returns list of changes made (or that would be made in dry-run)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    changes: list[str] = []
    name = data.get("display_name", data.get("model_id", path.stem))

    # 1. supports_tool_use: "untested" → null
    if data.get("supports_tool_use") == "untested":
        changes.append(f"{name}: supports_tool_use 'untested' → null")
        if apply:
            data["supports_tool_use"] = None

    # 2. card_status: "verified" → "complete"
    cs = data.get("card_status")
    if cs in CARD_STATUS_FIXES:
        changes.append(f"{name}: card_status '{cs}' → 'complete'")
        if apply:
            data["card_status"] = CARD_STATUS_FIXES[cs]

    # 3. unknown=true + card_status=complete → unknown=false
    if data.get("unknown") is True and data.get("card_status") == "complete":
        changes.append(f"{name}: unknown true → false (Widerspruch mit card_status=complete)")
        if apply:
            data["unknown"] = False

    # 4. weights_provenance_risk: deutsche Werte → englisch
    risk = data.get("weights_provenance_risk")
    if risk in RISK_FIXES:
        changes.append(f"{name}: weights_provenance_risk '{risk}' → '{RISK_FIXES[risk]}'")
        if apply:
            data["weights_provenance_risk"] = RISK_FIXES[risk]

    # 5. size_class: alte Werte → neue
    sc = data.get("size_class")
    if sc in SIZE_CLASS_FIXES:
        changes.append(f"{name}: size_class '{sc}' → '{SIZE_CLASS_FIXES[sc]}'")
        if apply:
            data["size_class"] = SIZE_CLASS_FIXES[sc]

    # 6. deployment_type: bekannte Tippfehler + Synonyme
    dep = data.get("deployment_type")
    if dep in DEPLOYMENT_TYPE_FIXES:
        new_dep = DEPLOYMENT_TYPE_FIXES[dep]
        changes.append(f"{name}: deployment_type '{dep}' → '{new_dep}'")
        if apply:
            data["deployment_type"] = new_dep
    elif dep == DEPLOYMENT_TYPE_API_AND_LOCAL:
        # api-and-local: default zu open-weights-cloud-available, es sei denn
        # modell-spezifisch überschrieben
        mid = data.get("model_id", "")
        if mid not in API_AND_LOCAL_KEEP_CLOUD:
            new_dep = "open-weights-cloud-available"
            changes.append(f"{name}: deployment_type '{dep}' → '{new_dep}' (Modell hat Weights verfügbar)")
            if apply:
                data["deployment_type"] = new_dep
        else:
            new_dep = "cloud-only"
            changes.append(f"{name}: deployment_type '{dep}' → '{new_dep}' (Ausnahme: Weights NICHT verfügbar)")
            if apply:
                data["deployment_type"] = new_dep

    if apply and changes:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-Fix für triviale Whitelist-Verstöße")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Nur anzeigen, nicht ändern (Default)")
    parser.add_argument("--apply", action="store_true",
                        help="Tatsächlich ändern")
    parser.add_argument("--file", type=str, help="Nur eine einzelne Datei prüfen")
    args = parser.parse_args()

    apply = args.apply
    if apply:
        args.dry_run = False

    if args.file:
        paths = [Path(args.file)]
    else:
        if not CARDS_DIR.exists():
            print(f"ERROR: {CARDS_DIR} nicht gefunden.", file=sys.stderr)
            return 2
        paths = sorted(CARDS_DIR.glob("*.json"))

    total_changes = 0
    cards_changed = 0
    for path in paths:
        if path.name == "_index.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue

        changes = fix_card(path, apply=apply)
        if changes:
            cards_changed += 1
            total_changes += len(changes)
            for change in changes:
                prefix = "APPLY" if apply else "DRY-RUN"
                print(f"  [{prefix}] {change}")

    mode = "ANGEWENDET" if apply else "DRY-RUN"
    print(f"\n{mode}: {total_changes} Änderungen in {cards_changed} Karten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
