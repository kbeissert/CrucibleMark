from typing import Optional
#!/usr/bin/env python3
"""
Meta-Reviewer für den Audit-Modus
Generiert einen detaillierten redaktionellen Artikel über die Stärken und Schwächen pro Modell,
oder, falls als bias spezifiziert, einen fokussierten Bias-Review basierend auf dem Political Compass.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
import yaml

# Setup import path to allow imports from root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.llm_client import LLMClient
from utils.model_utils import get_model_specialization

def load_config() -> dict:
    config_path = ROOT_DIR / "benchmark_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_model_metrics(model_name: str) -> dict:
    import csv
    detailed_csv = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard_detailed.csv"
    if not detailed_csv.exists():
        return {}

    def normalize(s):
        return s.replace(":", "_").replace("-", "_").lower()

    norm_target = normalize(model_name)
    try:
        with open(detailed_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_model = row.get("Model Name", "")
                norm_csv = normalize(csv_model)
                if norm_target == norm_csv or norm_target.startswith(f"{norm_csv}_"):
                    return row
    except Exception:
        pass
    return {}

def get_latest_audit_dir(base_dir: Path) -> Optional[Path]:
    """Findet das zuletzt aktualisierte Audit-Verzeichnis."""
    subdirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name != ".DS_Store"]
    if not subdirs:
        return None
    return max(subdirs, key=os.path.getmtime)

def collect_data() -> str:
    """Liest die Leaderboard.csv."""
    csv_path = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard.csv"
    if not csv_path.exists():
        return "Keine Leaderboard-Daten gefunden."

    with open(csv_path, "r", encoding="utf-8") as f:
        return f.read()

def process_model_review(model_dir: Path, csv_data: str, client: LLMClient, provider: str, model_id: str, review_type: str = "benchmark"):
    """Liest Audit-Logs für ein spezifisch getestetes LLM und generiert eine Review."""
    tested_model_name = model_dir.name
    print(f"\n📥 Sammle Logs für Modell: {tested_model_name} (Typ: {review_type})...")

    extracted_logs = []
    for md_file in model_dir.rglob("*.md"):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            is_bias_file = md_file.name in ['00_bias_report.md', 'pol_comp_report.md']

            # Filter logic based on review type
            if review_type == "bias" and not is_bias_file:
                continue
            if review_type == "benchmark" and is_bias_file:
                continue

            # Simple Extraktion via Regex (suche nach Judge Evaluation Blöcken unten)
            judge_section_match = re.search(r'## 3\. Evaluation.*', content, re.DOTALL)

            # Suche nach System-Infos und Warnungen
            system_info_match = re.search(r'> \[!(?:WARNING|CAUTION)\].*', content)
            system_info_text = f"\n\n{system_info_match.group(0)}" if system_info_match else ""

            # Suche explizit nach harten Safety-Filter Blöcken, die in "2. Model Response" auftauchen
            safety_filter_match = re.search(r'## 2\. Model.*?Error: Content blocked by safety filters\.', content, re.DOTALL)
            if safety_filter_match:
                system_info_text += "\n\n> ⚠️ **[SAFETY FILTER TRIGGERED]** The model refused to answer due to extreme safety filters."

            if is_bias_file:
                extracted_logs.append(f"--- Datei: {md_file.name} ---\n{content}")
            elif judge_section_match:
                extracted = judge_section_match.group(0).strip()
                extracted_logs.append(f"--- Datei: {md_file.name} ---{system_info_text}\n{extracted}")
            else:
                extracted_logs.append(f"--- Datei: {md_file.name} ---{system_info_text}\n{content[-1500:]}")
        except Exception:
            continue

    if not extracted_logs:
        print(f"⚠️ Keine zutreffenden Logs gefunden für {tested_model_name} im Modus {review_type}, überspringe.")
        return

    log_data = "\n\n".join(extracted_logs)

    max_log_chars = 30000
    if len(log_data) > max_log_chars:
        if review_type == "bias":
            log_data = log_data[:max_log_chars]
        else:
            log_data = log_data[-max_log_chars:]


    try:
        from utils.system_context import SystemContextManager
        from utils.model_utils import get_model_category

        context_manager = SystemContextManager()

        _config = load_config()
        # Single Source of Truth
        # Zuerst prüfen, ob es in der kommerziellen Liste ist
        commercial_models = []
        for p_config in _config.get("providers", {}).get("commercial", {}).values():
            if p_config.get("enabled", False):
                commercial_models.extend([m["id"] for m in p_config.get("models", [])])

        source_context = "commercial" if tested_model_name in commercial_models else "local"

        category = get_model_category(tested_model_name, source_context)

        if category == "Commercial":
            run_type = "commercial"
        elif category == "Local Cloud":
            run_type = "local_cloud"
        else:
            run_type = "local"

        hardware_context = context_manager.get_editor_prompt_injection(run_type)
    except Exception as e:
        hardware_context = "Achte auf Performance und Effizienz bezüglich Token-Kosten."

    # Load tier definitions from config
    tier_metaphor_rules = ""
    try:
        import yaml
        with open(ROOT_DIR / "benchmark_config.yaml", "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f)
            _tiers = _config.get("scoring_tiers", {})
            _tier_lines = []

            # Create a sorted list based on thresholds
            sorted_tiers = sorted(_tiers.items(), key=lambda item: item[1].get('threshold', 0.0), reverse=True)

            for i, (key, data) in enumerate(sorted_tiers):
                threshold = data.get('threshold', 0.0)
                desc = data.get('prompt_description', '')
                next_threshold = sorted_tiers[i-1][1].get('threshold', 100.0) if i > 0 else 100.0

                # Format exactly as configured
                desc = desc.replace('{threshold}', str(threshold)).replace('{next_threshold}', str(next_threshold))
                _tier_lines.append(desc)

            tier_metaphor_rules = "\n".join(_tier_lines)
    except Exception:
        tier_metaphor_rules = "- **Ab 90%:** Platin\n- **Ab 75%:** Gold\n- **Ab 60%:** Silber\n- **Ab 50%:** Bronze\n- **Unter 50%:** Standard"


    if review_type == "benchmark":
        try:
            import yaml
            with open(ROOT_DIR / "config" / "meta_reviewer_prompt.yaml", "r", encoding="utf-8") as f:
                prompt_yaml = yaml.safe_load(f)
                prompt_template = prompt_yaml.get("meta_reviewer", {}).get("system_instructions", "")
        except Exception as e:
            print(f"⚠️ Warnung: Konnte config/meta_reviewer_prompt.yaml nicht laden: {e}")
            prompt_template = """Fehler beim Laden des Prompts."""
    else:
        try:
            import yaml
            with open(ROOT_DIR / "config" / "meta_reviewer_prompt.yaml", "r", encoding="utf-8") as f:
                prompt_yaml = yaml.safe_load(f)
                prompt_template = prompt_yaml.get("bias_reviewer", {}).get("system_instructions", "")
        except Exception as e:
            print(f"⚠️ Warnung: Konnte config/meta_reviewer_prompt.yaml nicht laden: {e}")
            prompt_template = """Fehler beim Laden des Prompts."""

    model_metrics = get_model_metrics(tested_model_name)

    def safe_round(val):
        try:
            return str(round(float(val), 2))
        except (ValueError, TypeError):
            return "n/a"

    timeout_count = model_metrics.get("Timeout Count", "n/a")
    tests_run = model_metrics.get("Tests Run", "n/a")
    if tests_run != "n/a" and "/" in tests_run:
        tests_run = tests_run.split("/")[-1]

    timeout_rate_str = f"{timeout_count}/{tests_run}" if timeout_count != "n/a" else "n/a"

    template_vars = {
        "tested_model_name": tested_model_name,
        "hardware_context": hardware_context,
        "csv_data": csv_data,
        "log_data": log_data,
        "tier_metaphor_rules": tier_metaphor_rules,
        "model_specialization": get_model_specialization(tested_model_name),
        "model_p95_time": safe_round(model_metrics.get("P95 Time (s)")),
        "model_tokens_per_second": safe_round(model_metrics.get("Performance/s")),
        "model_timeout_rate": timeout_rate_str,
        "model_provider_type": model_metrics.get("Type", "n/a")
    }

    try:
        prompt = prompt_template.format(**template_vars)
    except KeyError as e:
        print(f"⚠️ Warnung im Prompt-Template: Fehlende Variable {e}")
        template_vars[e.args[0]] = "n/a"
        prompt = prompt_template.format(**template_vars)

    print(f"🤖 Generiere {review_type.capitalize()}-Review für {tested_model_name} mit {provider}/{model_id}...")

    try:
        response = client.query(
            model=model_id,
            prompt=prompt,
            provider=provider,
            temperature=0.7 # Ein bisschen Kreativität für einen Artikel
        )
    except Exception as e:
        print(f"❌ Fehler bei der Generierung für {tested_model_name}: {e}")
        return

    # Speichern in separatem Modell-Ordner
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT_DIR / "outputs" / "comparisons" / tested_model_name
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix = "bias_review" if review_type == "bias" else "review"
    out_file = out_dir / f"{prefix}_{timestamp}.md"

    # Zeitstempel in Bericht einfügen, am besten in der zweiten Zeile
    display_time = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
    lines = response.splitlines()
    if lines:
        lines.insert(1, f"\n> **Erstellt am:** {display_time}\n")
    else:
        lines.append(f"\n> **Erstellt am:** {display_time}\n")
    response_with_timestamp = "\n".join(lines)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(response_with_timestamp)

    print(f"✅ Review gespeichert unter: {out_file.relative_to(ROOT_DIR)}")


def main():
    parser = argparse.ArgumentParser(description="Generiert qualitative LLM-Reviews basierend auf den Audit-Logs.")
    parser.add_argument("-m", "--model", type=str, help="Generiere den Review nur für dieses spezifische Modell (z.B. claude-haiku-4-5-20251001)")
    parser.add_argument("-a", "--all", action="store_true", help="Generiere Reviews für alle Modelle mit gefundenen Audit-Logs")
    parser.add_argument("-t", "--type", type=str, choices=["benchmark", "bias"], default="benchmark", help="Art des Reviews: 'benchmark' (standard) oder 'bias'")
    args = parser.parse_args()

    if not args.model and not args.all:
        print("❌ Bitte gib ein Modell an (-m <modell>) oder nutze --all für alle Modelle.")
        sys.exit(1)

    print(f"📰 Starte Meta-Reviewer Auswertung ({args.type.upper()}-Modus)...")

    # Init config and client
    config = load_config()
    client = LLMClient(config=config)

    # Lade die neue llm_review Config anstelle der Judge-Config!
    review_config = config.get("llm_review", {}).get("provider", {})
    provider = review_config.get("name", "google")
    model_id = review_config.get("model", "gemini-2.5-pro")

    # Falls die neue Config block fälschlicherweise nicht gefunden wird (Fallback)
    if not provider or not model_id:
        print("⚠️ Warnung: 'llm_review' Konfiguration fehlt in benchmark_config.yaml, nutze Google Gemini als Fallback.")
        provider = "google"
        model_id = "gemini-2.5-pro"

    print(f"🔧 Konfigurierter Reviewer: {provider}/{model_id}")

    csv_data = ""
    if args.type == "benchmark":
        csv_data = collect_data()

    audit_base_dir = ROOT_DIR / "outputs" / "audit_logs"

    if not audit_base_dir.exists():
        print("❌ Keine Audit-Logs gefunden.")
        return

    print("📁 Durchsuche Audit-Logs nach Modellen...")

    found_models = False

    # Safe model name for comparison (matching benchmark_utils.py)
    safe_target_model = args.model.replace(":", "_").replace("/", "_") if args.model else None

    # Iteriere über die Modell-Ordner (z.B. mistral-medium-latest) im Audit-Root
    for subdir in audit_base_dir.iterdir():
        if subdir.is_dir() and subdir.name != ".DS_Store":
            if safe_target_model and subdir.name != safe_target_model:
                continue
            found_models = True
            process_model_review(subdir, csv_data, client, provider, model_id, args.type)

    if not found_models:
        print("⚠️ Keine Audit-Logs für das spezifizierte Modell gefunden.")


if __name__ == "__main__":
    main()
