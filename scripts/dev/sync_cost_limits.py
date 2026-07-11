"""
sync_cost_limits.py
-------------------
Gleicht die Preis-Konfiguration mit den Modellen aus benchmark_config.yaml
und den Benchmark-CSVs ab.

Preisquelle (Priorität):
  1. Model Card JSON (benchmark_scores/model_cards/*.json) — input_price_per_1m
  2. cost_limits.yaml providers.*.{model} — input_cost_per_1k (Legacy-Fallback)

Ohne Flag: Bericht, welche Modelle keinen Preiseintrag haben.
Mit --fix:  Platzhalter (null) in cost_limits.yaml eintragen als temporärer
            Fallback, bis eine vollständige Model Card angelegt wird.

Verwendung:
    make sync-cost-limits           # Nur Bericht
    make sync-cost-limits FIX=1     # Platzhalter in cost_limits.yaml schreiben
"""

import argparse
import csv
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_CONFIG = ROOT / "benchmark_config.yaml"
COST_LIMITS = ROOT / "config" / "cost_limits.yaml"
SCORES_DIR = ROOT / "benchmark_scores"
CARD_DIR = SCORES_DIR / "model_cards"

CSV_FILES = [
    SCORES_DIR / "commercial_models_benchmark.csv",
    SCORES_DIR / "cloud_models_benchmark.csv",
]

# Maps benchmark_config provider key → cost_limits.yaml section key
PROVIDER_SECTION_MAP: dict[str, str] = {
    "anthropic": "anthropic",
    "openai": "openai",
    "google": "google",
    "mistral": "mistral",
    "xai": "xai",
    "groq": "groq",
    "ollama_cloud": "ollama_cloud",
}


def load_config_models() -> dict[str, set[str]]:
    """
    Liest alle explizit gelisteten Modell-IDs aus benchmark_config.yaml.
    Providers mit auto_discover=True werden übersprungen (kommen aus CSV).
    Gibt {section_key: {model_id, ...}} zurück.

    SSoT: ConfigValidator merged provider_config.yaml automatisch ein
    (Thinking-Profile-Expansion, Duplicate-ID-Checks).
    """
    from utils.config_validator import ConfigValidator
    cfg = ConfigValidator(str(BENCHMARK_CONFIG)).config

    result: dict[str, set[str]] = {}

    # Alle Provider-Blöcke liegen unter providers: → commercial: (und local:, wird ignoriert)
    providers_cfg = cfg.get("providers", {})
    for provider_key, provider_data in providers_cfg.get("commercial", {}).items():
        if not isinstance(provider_data, dict):
            continue
        # auto_discover-Provider haben keine expliziten IDs → überspringen
        if provider_data.get("auto_discover"):
            continue
        section = PROVIDER_SECTION_MAP.get(str(provider_key), str(provider_key))
        for m in provider_data.get("models", []):
            model_id = (m.get("id") or "") if isinstance(m, dict) else str(m)
            if model_id:
                result.setdefault(section, set()).add(model_id)

    return result


def load_csv_models() -> dict[str, set[str]]:
    """
    Liest Modell-IDs aus den Benchmark-CSVs (für auto-discover-Modelle wie ollama_cloud).
    Gibt {section_key: {model_id, ...}} zurück.
    """
    result: dict[str, set[str]] = {}
    for path in CSV_FILES:
        if not path.exists():
            continue
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                model = (row.get("model") or "").strip()
                provider = (row.get("provider") or "").strip()
                if not model:
                    continue
                # Ollama-Cloud-Proxies: provider=ollama, model endet mit :cloud
                if provider == "ollama" and model.endswith(":cloud"):
                    section = "ollama_cloud"
                else:
                    section = PROVIDER_SECTION_MAP.get(provider, "")
                if section:
                    result.setdefault(section, set()).add(model)
    return result


def load_configured_models() -> dict[str, set[str]]:
    """
    Sammelt alle Modell-IDs, für die bereits ein Preis konfiguriert ist.

    Reihenfolge:
      1. Model Card JSON mit gesetztem input_price_per_1m-Feld (primäre SSoT).
         Der section_key wird über PROVIDER_SECTION_MAP aus dem 'provider'-Feld
         der Card ermittelt, sofern vorhanden; andernfalls als 'unknown' markiert.
      2. cost_limits.yaml providers.*.{model} mit input_cost_per_1k (Legacy).

    Gibt {section_key: {model_id, ...}} zurück.
    """
    result: dict[str, set[str]] = {}

    # 1. Model Cards (primäre SSoT)
    for card_path in CARD_DIR.glob("*.json"):
        try:
            with open(card_path, encoding="utf-8") as f:
                card = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(card, dict):
            continue
        model_id = card.get("model_id")
        if not model_id:
            continue
        if not isinstance(card.get("input_price_per_1m"), (int, float)):
            continue
        # Abbildung auf section_key via provider-Feld der Card
        card_provider = (card.get("provider") or "").lower()
        section = PROVIDER_SECTION_MAP.get(card_provider, card_provider or "unknown")
        result.setdefault(section, set()).add(model_id)

    # 2. cost_limits.yaml Legacy-Fallback (für Modelle ohne Card)
    try:
        with open(COST_LIMITS, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for section, models in data.get("providers", {}).items():
            if not isinstance(models, dict):
                continue
            for model_id, model_data in models.items():
                if isinstance(model_data, dict) and (
                    "input_cost_per_1k" in model_data or "output_cost_per_1k" in model_data
                ):
                    result.setdefault(section, set()).add(model_id)
    except (OSError, yaml.YAMLError):
        pass

    return result


def find_missing(
    config_models: dict[str, set[str]],
    csv_models: dict[str, set[str]],
    configured: dict[str, set[str]],
) -> dict[str, set[str]]:
    """
    Gibt {section: {model_ids}} zurück, die in config/CSV stehen, aber keinen Preis haben.
    Der Vergleich erfolgt section-agnostisch: eine Model-ID gilt als konfiguriert,
    sobald sie in irgendeiner Card oder YAML-Sektion einen Preiseintrag hat.
    """
    combined: dict[str, set[str]] = {}
    for section, ids in config_models.items():
        combined.setdefault(section, set()).update(ids)
    for section, ids in csv_models.items():
        combined.setdefault(section, set()).update(ids)

    # Flat-Set aller konfigurierten Model-IDs (über alle Sektionen hinweg)
    configured_flat: set[str] = set()
    for ids in configured.values():
        configured_flat.update(ids)

    missing: dict[str, set[str]] = {}
    for section, ids in combined.items():
        diff = ids - configured_flat
        if diff:
            missing[section] = diff
    return missing


def _find_providers_block(lines: list[str]) -> tuple[int | None, int]:
    providers_start: int | None = None
    providers_end: int = len(lines)
    for i, line in enumerate(lines):
        if line.rstrip() == "providers:":
            providers_start = i
        elif (
            providers_start is not None
            and line
            and not line[0].isspace()
            and not line.startswith("#")
        ):
            providers_end = i
            break
    return providers_start, providers_end


def _find_section_line(lines: list[str], section_header: str, start: int, end: int) -> int | None:
    for i in range(start, end):
        if lines[i].rstrip() == section_header:
            return i
    return None


def _find_insert_index(lines: list[str], section_line_idx: int, providers_end: int) -> int:
    insert_before: int | None = None
    for i in range(section_line_idx + 1, providers_end):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.startswith("daily_budget:"):
            insert_before = i
            break
        if indent <= 2 and stripped and not stripped.startswith("#"):
            insert_before = i
            break
    return providers_end if insert_before is None else insert_before


def _build_placeholder_lines(model_ids: set[str]) -> tuple[list[str], int]:
    new_lines: list[str] = []
    inserted = 0
    for model_id in sorted(model_ids):
        new_lines.extend([
            f"    {model_id}:\n",
            "      input_cost_per_1k: null  # TODO: Preis nachtragen\n",
            "      output_cost_per_1k: null  # TODO: Preis nachtragen\n",
        ])
        inserted += 1
        print(f"  ✅ [{model_id}] → Platzhalter eingetragen")
    return new_lines, inserted


def _insert_section_placeholders(
    lines: list[str],
    providers_start: int,
    providers_end: int,
    section: str,
    model_ids: set[str],
) -> tuple[int, int]:
    section_header = f"  {section}:"
    section_line_idx = _find_section_line(lines, section_header, providers_start, providers_end)
    if section_line_idx is None:
        print(
            f"  ⚠️  Sektion '{section}' fehlt in providers: — "
            f"bitte manuell anlegen für: {sorted(model_ids)}"
        )
        return providers_end, 0

    insert_before = _find_insert_index(lines, section_line_idx, providers_end)
    new_lines, inserted = _build_placeholder_lines(model_ids)
    lines[insert_before:insert_before] = new_lines
    return providers_end + len(new_lines), inserted


def insert_placeholders(missing: dict[str, set[str]]) -> int:
    """
    Fügt Platzhalter-Einträge (null-Preise) in cost_limits.yaml ein.
    Erhält Kommentare durch Text-Level-Insertion statt YAML-Serialisierung.
    Sucht Sektionen nur innerhalb des providers:-Blocks um Fehlzuordnungen
    zu anderen Top-Level-Keys (z.B. settings:) zu vermeiden.
    Gibt die Anzahl eingefügter Einträge zurück.
    """
    text = COST_LIMITS.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    providers_start, providers_end = _find_providers_block(lines)
    if providers_start is None:
        print("  ❌ providers:-Block nicht gefunden in cost_limits.yaml")
        return 0

    total_inserted = 0
    for section, model_ids in sorted(missing.items()):
        providers_end, inserted = _insert_section_placeholders(
            lines, providers_start, providers_end, section, model_ids,
        )
        total_inserted += inserted

    COST_LIMITS.write_text("".join(lines), encoding="utf-8")
    return total_inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Preis-Konfiguration mit Modell-Konfiguration")
    parser.add_argument("--fix", action="store_true", help="Platzhalter in cost_limits.yaml eintragen (Legacy-Fallback bis eine Card angelegt wird)")
    args = parser.parse_args()

    config_models = load_config_models()
    csv_models = load_csv_models()
    configured = load_configured_models()

    missing = find_missing(config_models, csv_models, configured)

    # Gesamtzahlen ermitteln (Union beider Quellen, nicht dict-overwrite)
    combined_all: dict[str, set[str]] = {}
    for section, ids in config_models.items():
        combined_all.setdefault(section, set()).update(ids)
    for section, ids in csv_models.items():
        combined_all.setdefault(section, set()).update(ids)
    all_model_count = sum(len(ids) for ids in combined_all.values())
    configured_count = sum(len(ids) for ids in configured.values())
    missing_count = sum(len(ids) for ids in missing.values())

    print("━" * 52)
    print("🔍 CrucibleMark – Preis-Sync (Cards + cost_limits.yaml)")
    print("━" * 52)
    print(f"  Modelle in Config / CSVs:         {all_model_count}")
    print(f"  Preise konfiguriert (Card/YAML):  {configured_count}")
    print(f"  Fehlende Preiseinträge:           {missing_count}")
    print()

    if not missing:
        print("✅ Alle bekannten Modelle haben einen Preiseintrag (Card oder cost_limits.yaml).")
        return

    print("Fehlende Modelle (kein input_price_per_1m in Card, kein input_cost_per_1k in cost_limits.yaml):")
    for section in sorted(missing):
        for model_id in sorted(missing[section]):
            print(f"  [{section:<15}]  {model_id}")

    print()
    if args.fix:
        print("💾 Schreibe Platzhalter in config/cost_limits.yaml …")
        print("   ⚠️  Empfehlung: Model Card anlegen statt Platzhalter in YAML.")
        count = insert_placeholders(missing)
        print()
        print(f"  {count} Platzhalter eingetragen. Bitte migrate_prices_to_cards.py nutzen sobald Cards vorhanden.")
        print("  ⚠️  Bitte Preise manuell nachtragen: config/cost_limits.yaml")
        print("     (Suche nach '# TODO: Preis nachtragen')")
    else:
        print("Tipp: 'make sync-cost-limits FIX=1' schreibt Platzhalter automatisch ein.")


if __name__ == "__main__":
    main()
