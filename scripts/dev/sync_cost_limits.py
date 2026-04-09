"""
sync_cost_limits.py
-------------------
Gleicht config/cost_limits.yaml mit den Modellen aus benchmark_config.yaml
und den Benchmark-CSVs ab.

Ohne Flag: Bericht, welche Modelle keinen Preiseintrag haben.
Mit --fix:  Platzhalter (null) für fehlende Modelle in cost_limits.yaml eintragen.

Verwendung:
    make sync-cost-limits           # Nur Bericht
    make sync-cost-limits FIX=1     # Platzhalter schreiben
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, Optional, Set

import yaml

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_CONFIG = ROOT / "benchmark_config.yaml"
COST_LIMITS = ROOT / "config" / "cost_limits.yaml"
SCORES_DIR = ROOT / "benchmark_scores"

CSV_FILES = [
    SCORES_DIR / "commercial_models_benchmark.csv",
    SCORES_DIR / "cloud_models_benchmark.csv",
]

# Maps benchmark_config provider key → cost_limits.yaml section key
PROVIDER_SECTION_MAP: Dict[str, str] = {
    "anthropic": "anthropic",
    "openai": "openai",
    "google": "google",
    "mistral": "mistral",
    "xai": "xai",
    "groq": "groq",
    "ollama_cloud": "ollama_cloud",
}


def load_config_models() -> Dict[str, Set[str]]:
    """
    Liest alle explizit gelisteten Modell-IDs aus benchmark_config.yaml.
    Providers mit auto_discover=True werden übersprungen (kommen aus CSV).
    Gibt {section_key: {model_id, ...}} zurück.
    """
    with open(BENCHMARK_CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    result: Dict[str, Set[str]] = {}

    # Alle Provider-Blöcke liegen unter providers: → commercial: (und local:, wird ignoriert)
    providers_cfg = cfg.get("providers", {})
    for provider_key, provider_data in providers_cfg.get("commercial", {}).items():
        if not isinstance(provider_data, dict):
            continue
        # auto_discover-Provider haben keine expliziten IDs → überspringen
        if provider_data.get("auto_discover"):
            continue
        section = PROVIDER_SECTION_MAP.get(provider_key, provider_key)
        for m in provider_data.get("models", []):
            model_id = m.get("id") if isinstance(m, dict) else str(m)
            if model_id:
                result.setdefault(section, set()).add(model_id)

    return result


def load_csv_models() -> Dict[str, Set[str]]:
    """
    Liest Modell-IDs aus den Benchmark-CSVs (für auto-discover-Modelle wie ollama_cloud).
    Gibt {section_key: {model_id, ...}} zurück.
    """
    result: Dict[str, Set[str]] = {}
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


def load_configured_models() -> Dict[str, Set[str]]:
    """
    Liest alle bereits konfigurierten Modell-IDs aus cost_limits.yaml.
    Nur Einträge mit input_cost_per_1k oder output_cost_per_1k werden gezählt.
    Gibt {section_key: {model_id, ...}} zurück.
    """
    with open(COST_LIMITS, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    result: Dict[str, Set[str]] = {}
    for section, models in data.get("providers", {}).items():
        if not isinstance(models, dict):
            continue
        for model_id, model_data in models.items():
            if isinstance(model_data, dict) and (
                "input_cost_per_1k" in model_data or "output_cost_per_1k" in model_data
            ):
                result.setdefault(section, set()).add(model_id)
    return result


def find_missing(
    config_models: Dict[str, Set[str]],
    csv_models: Dict[str, Set[str]],
    configured: Dict[str, Set[str]],
) -> Dict[str, Set[str]]:
    """
    Gibt {section: {model_ids}} zurück, die in config/CSV stehen, aber nicht in cost_limits.yaml.
    Modelle mit null-Preisen werden als "nicht konfiguriert" betrachtet, da sie keinen echten Preis haben.
    """
    combined: Dict[str, Set[str]] = {}
    for section, ids in config_models.items():
        combined.setdefault(section, set()).update(ids)
    for section, ids in csv_models.items():
        combined.setdefault(section, set()).update(ids)

    missing: Dict[str, Set[str]] = {}
    for section, ids in combined.items():
        already = configured.get(section, set())
        diff = ids - already
        if diff:
            missing[section] = diff
    return missing


def insert_placeholders(missing: Dict[str, Set[str]]) -> int:
    """
    Fügt Platzhalter-Einträge (null-Preise) in cost_limits.yaml ein.
    Erhält Kommentare durch Text-Level-Insertion statt YAML-Serialisierung.
    Sucht Sektionen nur innerhalb des providers:-Blocks um Fehlzuordnungen
    zu anderen Top-Level-Keys (z.B. settings:) zu vermeiden.
    Gibt die Anzahl eingefügter Einträge zurück.
    """
    text = COST_LIMITS.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # providers:-Block begrenzen: Start- und End-Index ermitteln
    providers_start: Optional[int] = None
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

    if providers_start is None:
        print("  ❌ providers:-Block nicht gefunden in cost_limits.yaml")
        return 0

    total_inserted = 0

    for section, model_ids in sorted(missing.items()):
        section_header = f"  {section}:"
        section_line_idx: Optional[int] = None

        # Nur im providers:-Block suchen (verhindert Match in settings: o.ä.)
        for i in range(providers_start, providers_end):
            if lines[i].rstrip() == section_header:
                section_line_idx = i
                break

        if section_line_idx is None:
            print(
                f"  ⚠️  Sektion '{section}' fehlt in providers: — "
                f"bitte manuell anlegen für: {sorted(model_ids)}"
            )
            continue

        # Einfügen vor daily_budget oder vor dem nächsten Sektion-Header (2-Leerzeichen-Einzug)
        insert_before: Optional[int] = None
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

        if insert_before is None:
            insert_before = providers_end

        new_lines: list[str] = []
        for model_id in sorted(model_ids):
            new_lines.extend([
                f"    {model_id}:\n",
                f"      input_cost_per_1k: null  # TODO: Preis nachtragen\n",
                f"      output_cost_per_1k: null  # TODO: Preis nachtragen\n",
            ])
            total_inserted += 1
            print(f"  ✅ [{section}] {model_id} → Platzhalter eingetragen")

        lines[insert_before:insert_before] = new_lines
        # providers_end verschieben, da Zeilen eingefügt wurden
        providers_end += len(new_lines)

    COST_LIMITS.write_text("".join(lines), encoding="utf-8")
    return total_inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync cost_limits.yaml mit Modell-Konfiguration")
    parser.add_argument("--fix", action="store_true", help="Platzhalter in cost_limits.yaml eintragen")
    args = parser.parse_args()

    config_models = load_config_models()
    csv_models = load_csv_models()
    configured = load_configured_models()

    missing = find_missing(config_models, csv_models, configured)

    # Gesamtzahlen ermitteln (Union beider Quellen, nicht dict-overwrite)
    combined_all: Dict[str, Set[str]] = {}
    for section, ids in config_models.items():
        combined_all.setdefault(section, set()).update(ids)
    for section, ids in csv_models.items():
        combined_all.setdefault(section, set()).update(ids)
    all_model_count = sum(len(ids) for ids in combined_all.values())
    configured_count = sum(len(ids) for ids in configured.values())
    missing_count = sum(len(ids) for ids in missing.values())

    print("━" * 52)
    print("🔍 CrucibleMark – Cost Limits Sync")
    print("━" * 52)
    print(f"  Modelle in Config / CSVs:   {all_model_count}")
    print(f"  Preise in cost_limits.yaml: {configured_count}")
    print(f"  Fehlende Preiseinträge:     {missing_count}")
    print()

    if not missing:
        print("✅ Alle bekannten Modelle haben einen Preiseintrag.")
        return

    print("Fehlende Modelle (Key = Wert der 'model'-Spalte in CSV):")
    for section in sorted(missing):
        for model_id in sorted(missing[section]):
            print(f"  [{section:<15}]  {model_id}")

    print()
    if args.fix:
        print("💾 Schreibe Platzhalter in config/cost_limits.yaml …")
        count = insert_placeholders(missing)
        print()
        print(f"  {count} Platzhalter eingetragen.")
        print("  ⚠️  Bitte Preise manuell nachtragen: config/cost_limits.yaml")
        print("     (Suche nach '# TODO: Preis nachtragen')")
    else:
        print("Tipp: 'make sync-cost-limits FIX=1' schreibt Platzhalter automatisch ein.")


if __name__ == "__main__":
    main()
