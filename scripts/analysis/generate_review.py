#!/usr/bin/env python3
"""
Meta-Reviewer für den Audit-Modus
Generiert einen detaillierten redaktionellen Artikel über die Stärken und Schwächen pro Modell,
basierend auf der Benchmark-Leaderboard-CSV und den qualitativen Audit-Logs pro Modell.
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

def load_config() -> dict:
    config_path = ROOT_DIR / "benchmark_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_latest_audit_dir(base_dir: Path) -> Path:
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

def process_model_review(model_dir: Path, csv_data: str, client: LLMClient, provider: str, model_id: str):
    """Liest Audit-Logs für ein spezifisch getestetes LLM und generiert eine Review."""
    tested_model_name = model_dir.name
    print(f"\n📥 Sammle Logs für Modell: {tested_model_name}...")

    extracted_logs = []
    for md_file in model_dir.rglob("*.md"):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple Extraktion via Regex (suche nach Judge Evaluation Blöcken unten)
            judge_section_match = re.search(r'\*\*LLM Judge Score \(Raw\):\*\*.*', content, re.DOTALL)

            if judge_section_match:
                extracted = judge_section_match.group(0).strip()
                extracted_logs.append(f"--- Datei: {md_file.name} ---\n{extracted}")
            else:
                extracted_logs.append(f"--- Datei: {md_file.name} ---\n{content[-1500:]}")
        except Exception as e:
            continue

    if not extracted_logs:
        print(f"⚠️ Keine Logs gefunden für {tested_model_name}, überspringe.")
        return

    log_data = "\n\n".join(extracted_logs)

    max_log_chars = 30000
    if len(log_data) > max_log_chars:
        log_data = log_data[-max_log_chars:]

    prompt = f"""Du bist ein erfahrener Tech-Journalist und Senior Software-Architekt.
Analysiere die folgenden Benchmark-Ergebnisse und qualitativen Judge-Protokolle speziell für das KI-Modell: **{tested_model_name}**.
Schreibe ein detailliertes Review (als Markdown), das die Stärken und Schwächen dieses spezifischen Modells beleuchtet.

Gehe speziell auf Kategorien wie Code Quality, Logik, Security und Halluzinationen ein.
Ziehe ein klares, professionell begründetes Fazit (mit Empfehlungen für Einsatzzwecke).
Nutze die qualitativen Protokolle, um echte Beispiele (z. B. aufgetretene Fehler, Missverständnisse, gute Workarounds) zu nennen.

### Benchmark Leaderboard (Alle Modelle zur Einordnung):
{csv_data}

### Qualitative Judge-Protokolle (Auszüge für {tested_model_name}):
{log_data}

Schreibe nun deinen umfassenden, redaktionellen Bericht in Deutsch, nutze Überschriften (Markdown) und gestalte ihn ansprechend. Beginne direkt mit dem generierten Artikel. Verzichte strikt auf Begrüßungsfloskeln, Einleitungssätze wie "Hier ist das Review" oder Bestätigungen wie "Absolut. Als...". Beginne sofort mit der #-Hauptüberschrift.
"""

    print(f"🤖 Generiere Review für {tested_model_name} mit {provider}/{model_id}...")

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
    out_file = out_dir / f"review_{timestamp}.md"

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(response)

    print(f"✅ Review gespeichert unter: {out_file.relative_to(ROOT_DIR)}")


def main():
    parser = argparse.ArgumentParser(description="Generiert qualitative LLM-Reviews basierend auf den Audit-Logs.")
    parser.add_argument("-m", "--model", type=str, help="Generiere den Review nur für dieses spezifische Modell (z.B. claude-haiku-4-5-20251001)")
    parser.add_argument("-a", "--all", action="store_true", help="Generiere Reviews für alle Modelle mit gefundenen Audit-Logs")
    args = parser.parse_args()

    if not args.model and not args.all:
        print("❌ Bitte gib ein Modell an (-m <modell>) oder nutze --all für alle Modelle.")
        sys.exit(1)

    print("📰 Starte Meta-Reviewer Auswertung...")

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

    csv_data = collect_data()

    audit_base_dir = ROOT_DIR / "outputs" / "audit_logs"

    if not audit_base_dir.exists():
        print("❌ Keine Audit-Logs gefunden.")
        return

    print("📁 Durchsuche Audit-Logs nach Modellen...")

    found_models = False
    # Iteriere über die Modell-Ordner (z.B. mistral-medium-latest) im Audit-Root
    for subdir in audit_base_dir.iterdir():
        if subdir.is_dir() and subdir.name != ".DS_Store":
            if args.model and subdir.name != args.model:
                continue
            found_models = True
            process_model_review(subdir, csv_data, client, provider, model_id)

    if not found_models:
        print("⚠️ Keine Audit-Logs für das spezifizierte Modell gefunden.")


if __name__ == "__main__":
    main()
