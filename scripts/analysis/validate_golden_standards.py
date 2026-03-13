import sys
import yaml
import glob
import json
import os
import argparse
from pathlib import Path
from utils.llm_client import LLMClient

def load_benchmark_config():
    with open("benchmark_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_asset_info():
    """Extracts golden standards and metadata IDs from all asset YAML files."""
    assets = []
    yaml_files = glob.glob("benchmark_modules/*/assets/*.yaml")

    for file_path in yaml_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

                # Check if it has a golden standard
                golden_standard = data.get("golden_standard")
                metadata_id = data.get("metadata", {}).get("id")

                if golden_standard and metadata_id:
                    assets.append({
                        "file_path": file_path,
                        "id": metadata_id,
                        "golden_standard": golden_standard
                    })
        except Exception as e:
            print(f"Error parsing YAML {file_path}: {e}")

    return assets

def get_reference_response(asset_id: str, provider: str = "anthropic") -> str | None:
    """Loads the reference proxy response for a given asset ID."""
    reference_path = Path(f"golden_standards/{provider}/{asset_id}.json")

    if not reference_path.exists():
        # Fallback to mistral if anthropic doesn't exist
        fallback_path = Path(f"golden_standards/mistral/{asset_id}.json")
        if fallback_path.exists():
            reference_path = fallback_path
        else:
            return None

    try:
        with open(reference_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("response")
    except Exception as e:
        print(f"Error reading reference {reference_path}: {e}")
        return None

def analyze_golden_standard(asset: dict, reference_response: str, reviewer, model_name: str) -> str:
    """Uses the LLM Reviewer to validate the golden standard against the reference."""
    print(f"  Analyzing {asset['id']}...")

    prompt = f"""Du bist der Lead Quality Assurance Engineer für ein LLM-Benchmark-System (CrucibleMark).
Deine Aufgabe ist es, einen manuell erstellten "Golden Standard" (Musterlösung) gegen eine "100% Referenz-Antwort" abzugleichen.

Hier ist der Kontext:
Asset-ID: {asset['id']}
Asset-Datei: {asset['file_path']}

=== REFERENZ-ANTWORT (Top-Modell Lauf, oft als 100% gewertet) ===
{reference_response}

=== MANUELLER GOLDEN STANDARD (Die aktuell hinterlegte Musterlösung in der Asset-Config) ===
{asset['golden_standard']}

=== DEINE AUFGABE ===
Analysiere kritisch:
1. Fehlen im manuellen Golden Standard kritische Details, Konzepte oder Unterpunkte, die in der Referenz-Antwort vorhanden sind?
2. Ist der Golden Standard detailliert genug, um als unanfechtbare 100%-Musterlösung für einen strengen LLM-Judge zu dienen?
3. Gehe NICHT auf reine Formulierungen ein, sondern auf inhaltliche Vollständigkeit und Struktur.

Gib nur das Wichtigste zurück:
- Ist der Golden Standard optimal? (Ja/Nein)
- MUSS etwas hinzugefügt werden? (Wenn ja, in kurzen Stichpunkten was genau)
- Sei sehr strikt, aber bleib prägnant. Keinen unnötigen Text, am Ende eine klare Handlungsanweisung.
"""

    try:
        response = reviewer.query(
            model="claude-3-haiku-20240307",
            prompt=prompt,
            provider="anthropic",
            temperature=0.2
        )
        return response
    except Exception as e:
        return f"Error during LLM analysis: {e}"

def main():
    parser = argparse.ArgumentParser(description="Validate Golden Standards against Reference Logs")
    parser.add_argument("--dry-run", action="store_true", help="Only map files, don't call LLM")
    parser.add_argument("--module", type=str, help="Filter by module folder (e.g. code_quality)")
    args = parser.parse_args()

    # Load configuration
    config = load_benchmark_config()
    review_config = config.get("llm_review", {}).get("provider", {})
    provider_name = review_config.get("name")
    model_name = review_config.get("model")

    if not provider_name or not model_name:
        print("Error: 'llm_review' missing or incomplete in benchmark_config.yaml")
        sys.exit(1)

    print(f"Loading assets...")
    assets = get_asset_info()

    if args.module:
        assets = [a for a in assets if args.module in a["file_path"]]

    print(f"Found {len(assets)} assets with golden standards.")

    reviewer = None
    if not args.dry_run:
        print(f"Initializing LLM Reviewer ({provider_name} : {model_name})")
        try:
            reviewer = LLMClient(config=config)
        except Exception as e:
            print(f"Error initializing reviewer: {e}")
            sys.exit(1)

    # Output tracking
    output_dir = Path("outputs/audit_logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "golden_standard_validation.md"

    results = []
    missing_refs = 0

    for asset in assets:
        ref_response = get_reference_response(asset["id"])

        if not ref_response:
            print(f"Warning: No reference log found for {asset['id']}")
            missing_refs += 1
            if args.dry_run:
                results.append(f"## {asset['id']}\n- File: `{asset['file_path']}`\n- Status: 🔴 MISSING REFERENCE")
            continue

        if args.dry_run:
            results.append(f"## {asset['id']}\n- File: `{asset['file_path']}`\n- Status: 🟢 MAPPED (Ref Length: {len(ref_response)} chars, Golden Length: {len(asset['golden_standard'])} chars)")
            continue

        # Actual Analysis
        analysis_result = analyze_golden_standard(asset, ref_response, reviewer, model_name)

        results.append(f"## {asset['id']}\n\n- **File:** `{asset['file_path']}`\n- **Golden Standard Length:** {len(asset['golden_standard'])} chars\n\n### Analyse-Ergebnis\n{analysis_result}\n\n---")

    # Save report
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Golden Standard Validation Report\n\n")
        f.write(f"Generated against reference run logs.\n")
        f.write(f"Analyzed {len(assets)} assets.\n\n")
        if missing_refs > 0:
            f.write(f"**Warning:** {missing_refs} assets had no reference files.\n\n")
        f.write("\n".join(results))

    print(f"\n✅ Validation complete. Report saved to {report_file}")

if __name__ == "__main__":
    main()
