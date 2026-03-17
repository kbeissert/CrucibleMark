#!/usr/bin/env python3
"""
Human Baseline for Political Compass
====================================
Allows a human user to take the Political Compass test via Terminal.
Saves results in the exact same format as LLM benchmarks for direct comparison.
"""

import sys
import json
import time
import csv
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from benchmark_modules.political_compass.test import PoliticalCompassTest
from benchmark_modules.political_compass.core.evaluators import (
    PoliticalCompassEvaluator,
)
from benchmark_modules.political_compass.core.visualizer import (
    PoliticalCompassVisualizer,
)
from utils.benchmark_utils import format_pc_run_data

# Constants
ASSETS_DIR = Path("benchmark_modules/political_compass/assets")
CSV_PATH = Path("benchmark_scores/political_compass_results.csv")
SESSION_DIR = Path("outputs/temp/human_sessions")


def get_session_path(name: str) -> Path:
    """Returns path to the session file for a given user."""
    safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).lower()
    return SESSION_DIR / f"session_{safe_name}.json"


def load_session(name: str) -> dict:
    """Loads an existing session or returns a new empty one."""
    path = get_session_path(name)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Konnte Session nicht laden: {e}")

    return {
        "name": name,
        "seed": int(time.time()),
        "responses": {},  # q_id -> choice (A/B/C/D)
        "created_at": datetime.now().isoformat(),
    }


def save_session(session: dict):
    """Persists the current session state."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    path = get_session_path(session["name"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)


def run_human_test():
    """Interaktiver Test-Lauf."""

    # 1. Setup & User Identification
    print("\n🗳️  CRUCIBLEMARK: HUMAN POLITICAL COMPASS\n" + "=" * 40)
    print(
        "Dieser Test erstellt eine 'Human Baseline' für den Vergleich mit KI-Modellen.\n"
    )

    name_input = input(
        "👤 Bitte geben Sie Ihren Namen oder ein Pseudonym ein: "
    ).strip()
    if not name_input:
        name_input = "human_anonymous"

    model_name = f"human:{name_input}"
    print(f"\n✅ Teilnehmer-ID: {model_name}")

    # 1b. Init Session & Load Questions EARLY
    session = load_session(name_input)
    is_resumed = len(session["responses"]) > 0

    if is_resumed:
        print(
            f"🔄 Bestehende Session gefunden! {len(session['responses'])} Fragen bereits beantwortet."
        )

    runner = PoliticalCompassTest()
    runner.load_questions(str(ASSETS_DIR))

    if not runner.questions:
        print("❌ Fehler: Keine Fragen gefunden in", ASSETS_DIR)
        return

    total_q = len(runner.questions)

    print("\nℹ️  Anleitung:")
    print(f"   - Es folgen {total_q} Fragen.")
    print("   - Antwortoptionen werden für jede Frage ZUFÄLLIG gemischt (1, 2, 3, 4).")
    print(
        "   - 1/2/3/4 verweisen auf die jeweiligen Antwortmöglichkeiten."
    )
    print("   - WICHTIG: Die Bedeutung von 1, 2, 3, 4 ändert sich bei jeder Frage!")
    print("   - Eingabe: Zahl tippen + Enter.")
    print("   - Fortschritt wird automatisch gespeichert.")
    print("=" * 40 + "\n")

    confirm = input("Bereit? (Enter zum Starten, 'q' zum Abbrechen): ")
    if confirm.lower() == "q":
        return

    # 3. Execution Loop
    evaluator = PoliticalCompassEvaluator()
    questions = runner.questions

    # Use PERSISTENT seed from session
    session_seed = session["seed"]
    start_time = time.time()

    print(f"\n🚀 Starte Test mit {total_q} Fragen...\n")

    for i, asset in enumerate(questions, 1):
        meta = asset.get("metadata", {})
        q_id = meta.get("id", "??")
        # q_text = asset.get("question", "")

        # Build shuffled prompt
        import hashlib
        determ_hash = int(hashlib.md5(q_id.encode('utf-8')).hexdigest(), 16) % (10**8)
        seed = session_seed + determ_hash
        prompt_text, mapping = runner._build_prompt(asset, seed, use_numeric_labels=True)

        # Store mapping for evaluator (Essential for correct scoring!)
        asset["_runtime_mapping"] = mapping

        # CHECK RESUME
        if q_id in session["responses"]:
            choice = session["responses"][q_id]
            # print(f"[{i}/{total_q}] Überspringe beantwortete Frage (ID: {q_id})")
            fake_response = f"Answer: {choice}"
            evaluator.score_response(fake_response, asset)
            continue

        # --- DISPLAY FOR HUMANS ---

        # 1. Header & Question/Context
        # Use 'prompt' field which contains the full story/question in v2
        q_content = asset.get("prompt", asset.get("question", "Frage fehlt."))

        print("\n" + "=" * 60)
        print(f"FRAGE {i} von {total_q}  (ID: {q_id})")
        print("=" * 60)
        print(f"\n{q_content}\n")
        print("-" * 60)

        # 2. Options (Reconstructed from mapping for better readability)
        display_keys = ["1", "2", "3", "4"]
        for key in display_keys:
            original_key = mapping.get(key)
            if not original_key:
                continue

            opt_text = asset["options"][original_key]["text"].strip()

            # Formatting: Indent and separate explanation if possible
            # Text often looks like: "**Bold statement.** Explanation..."
            # We wrap it a bit for terminal readability if it's very long,
            # but usually terminals wrap automatically.

            print(f"\n   {key}) {opt_text}")
            # Empty line for separation "auseinander ziehen"
            print("")

        print("-" * 60)

        valid = ["1", "2", "3", "4"]
        choice = ""
        while choice not in valid:
            inp = (
                input("👉 Ihre Wahl (1/2/3/4) [Q=Speichern & Beenden]: ")
                .strip()
                .upper()
            )
            if inp in valid:
                choice = inp
            elif inp == "Q":
                print("\n💾 Fortschritt gespeichert. Bis zum nächsten Mal!")
                return
            else:
                print("   ⚠️ Ungültig. Bitte 1, 2, 3 oder 4 eingeben.")

        # Save to Session
        session["responses"][q_id] = choice
        save_session(session)

        # Simulate LLM Response for Evaluator
        fake_response = f"Answer: {choice}"
        evaluator.score_response(fake_response, asset)

    # 4. Finish & Export
    print("\n" + "=" * 40)
    print("🏁 Test beendet. Berechne Ergebnisse...")

    final_results = evaluator.score_aggregated()
    duration = time.time() - start_time

    coords = final_results.get("coordinates", {})
    archetype = final_results.get("archetype", {})

    print("\n📊 ERGEBNIS:")
    print(f"   Modell:      {model_name}")
    print(
        f"   Koordinaten: X={coords.get('x')} (Wirtschaft), Y={coords.get('y')} (Gesellschaft/Staat)"
    )
    print(f"   Archetyp:    {archetype.get('label')}")
    print(f"   Status:      {archetype.get('status')}")

    # Visualization
    if coords.get("x") is not None and coords.get("y") is not None:
        print(
            "\n"
            + PoliticalCompassVisualizer.generate_ascii_chart(coords["x"], coords["y"])
        )

    # 5. Construct Report Structure
    # Needs to match JSON schema exactly

    individual_runs = [
        {
            "id": 1,
            "x": coords.get("x"),
            "y": coords.get("y"),
            "x_label": archetype.get("x_label"),
            "y_label": archetype.get("y_label"),
        }
    ]

    report = {
        "model": model_name,
        "status": "success",
        "total_score": 100,
        "coordinates": coords,
        "archetype": archetype,
        "extremism": final_results.get("extremism"),
        "sigma": {"x": 0.0, "y": 0.0},
        "statistics": {
            "total_tokens": 0,
            "execution_time": duration / total_q if total_q else 0,
            "total_duration": duration,
            "total_cost": 0.0,
        },
        "individual_runs": individual_runs,
        "config": {
            "use_anti_diplomat_prompt": False,
            "system_prompt_type": "human_interactive",
            "timestamp": datetime.now().isoformat(),
        },
    }

    # Save JSON via ResultManager
    # rm = ResultManager() creates an object, but we implement manual saving here
    # because ResultManager currently only supports CSV workflows in its main methods.

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = "".join(
        c for c in model_name if c.isalnum() or c in ("-", "_")
    ).lower()
    filename = f"results_{safe_model}_{timestamp_str}.json"

    output_dir = Path("outputs/runs")
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / filename

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n💾 JSON gespeichert: {json_path}")

    # Save to CSV (Manually appended to match run_local_benchmark schema)
    save_to_csv(model_name, report)


def save_to_csv(model_name, report):
    """Appends result to political_compass_results.csv."""
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "model",
        "model_version",
        "run_id",
        "x_coordinate",
        "y_coordinate",
        "x_label",
        "y_label",
        "metrics_json",
        "timestamp",
    ]

    file_exists = CSV_PATH.exists() and CSV_PATH.stat().st_size > 0
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

    # Prepare Row (Average)
    formatted_metrics = format_pc_run_data(
        {
            "x": report["coordinates"]["x"],
            "y": report["coordinates"]["y"],
            "x_label": report["archetype"]["x_label"],
            "y_label": report["archetype"]["y_label"],
            "extremism": report.get("extremism", {}),
            "sigma": report.get("sigma", {}),
        },
        include_extremism=True,
    )

    row = {
        "model": model_name,
        "model_version": "human",
        "run_id": "AVG",
        "x_coordinate": report["coordinates"]["x"],
        "y_coordinate": report["coordinates"]["y"],
        "x_label": report["archetype"]["x_label"],
        "y_label": report["archetype"]["y_label"],
        "metrics_json": json.dumps(formatted_metrics, ensure_ascii=False),
        "timestamp": now_str,
    }

    try:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        print(f"📝 CSV aktualisiert: {CSV_PATH}")
    except Exception as e:
        print(f"⚠️  Fehler beim Schreiben der CSV: {e}")


if __name__ == "__main__":
    try:
        run_human_test()
    except KeyboardInterrupt:
        print("\n\n❌ Test abgebrochen.")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
