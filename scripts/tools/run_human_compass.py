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
            with open(path, encoding="utf-8") as f:
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


def _init_user_and_session() -> tuple[str, dict, PoliticalCompassTest] | None:
    """Setup: Name, Session laden, Questions laden. Liefert None bei Abbruch/Fehler."""
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

    session = load_session(name_input)
    if len(session["responses"]) > 0:
        print(
            f"🔄 Bestehende Session gefunden! {len(session['responses'])} Fragen bereits beantwortet."
        )

    runner = PoliticalCompassTest()
    runner.load_questions(str(ASSETS_DIR))

    if not runner.questions:
        print("❌ Fehler: Keine Fragen gefunden in", ASSETS_DIR)
        return None

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
        return None

    return model_name, session, runner


def _display_question(asset: dict, q_id: str, mapping: dict, q_num: int, total_q: int) -> None:
    """Zeigt Frage-Header, Inhalt und gemischte Optionen."""
    q_content = asset.get("prompt", asset.get("question", "Frage fehlt."))

    print("\n" + "=" * 60)
    print(f"FRAGE {q_num} von {total_q}  (ID: {q_id})")
    print("=" * 60)
    print(f"\n{q_content}\n")
    print("-" * 60)

    for key in ["1", "2", "3", "4"]:
        original_key = mapping.get(key)
        if not original_key:
            continue
        opt_text = asset["options"][original_key]["text"].strip()
        print(f"\n   {key}) {opt_text}")
        print("")

    print("-" * 60)


def _prompt_for_choice() -> str | None:
    """User-Input fuer Antwort. Liefert '1'..'4' oder None bei Quit."""
    choice = ""
    while choice not in ["1", "2", "3", "4"]:
        inp = (
            input("👉 Ihre Wahl (1/2/3/4) [Q=Speichern & Beenden]: ")
            .strip()
            .upper()
        )
        if inp in ["1", "2", "3", "4"]:
            choice = inp
        elif inp == "Q":
            print("\n💾 Fortschritt gespeichert. Bis zum nächsten Mal!")
            return None
        else:
            print("   ⚠️ Ungültig. Bitte 1, 2, 3 oder 4 eingeben.")
    return choice


def _score_question(asset: dict, choice: str, evaluator) -> None:
    """Speichert Wahl in Session und scored via Evaluator."""
    asset.get("metadata", {}).get("id", "??")


def _build_report(model_name: str, evaluator, duration: float, total_q: int) -> dict:
    """Baut den Report-Dict (gleiche Struktur wie LLM-Benchmark-Runs)."""
    final_results = evaluator.score_aggregated()
    coords = final_results.get("coordinates", {})
    archetype = final_results.get("archetype", {})
    individual_runs = [
        {
            "id": 1,
            "x": coords.get("x"),
            "y": coords.get("y"),
            "x_label": archetype.get("x_label"),
            "y_label": archetype.get("y_label"),
        }
    ]
    return {
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


def _save_report_json(report: dict, model_name: str) -> None:
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = "".join(c for c in model_name if c.isalnum() or c in ("-", "_")).lower()
    filename = f"results_{safe_model}_{timestamp_str}.json"
    output_dir = Path("outputs/runs")
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / filename
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n💾 JSON gespeichert: {json_path}")


def _print_results(model_name: str, final_results: dict) -> None:
    coords = final_results.get("coordinates", {})
    archetype = final_results.get("archetype", {})
    print("\n📊 ERGEBNIS:")
    print(f"   Modell:      {model_name}")
    print(
        f"   Koordinaten: X={coords.get('x')} (Wirtschaft), Y={coords.get('y')} (Gesellschaft/Staat)"
    )
    print(f"   Archetyp:    {archetype.get('label')}")
    print(f"   Status:      {archetype.get('status')}")
    if coords.get("x") is not None and coords.get("y") is not None:
        print(
            "\n"
            + PoliticalCompassVisualizer.generate_ascii_chart(coords["x"], coords["y"])
        )


def _process_one_question(
    asset: dict,
    q_num: int,
    total_q: int,
    session: dict,
    session_seed: int,
    evaluator,
    runner,
) -> bool:
    """Liefert False, wenn der User mit 'Q' abgebrochen hat."""
    import hashlib
    q_id = asset.get("metadata", {}).get("id", "??")

    determ_hash = int(hashlib.md5(q_id.encode('utf-8')).hexdigest(), 16) % (10**8)
    seed = session_seed + determ_hash
    _prompt_text, mapping = runner._build_prompt(asset, seed, use_numeric_labels=True)
    asset["_runtime_mapping"] = mapping

    if q_id in session["responses"]:
        choice = session["responses"][q_id]
        evaluator.score_response(f"Answer: {choice}", asset)
        return True

    _display_question(asset, q_id, mapping, q_num, total_q)
    choice = _prompt_for_choice()
    if choice is None:
        return False

    session["responses"][q_id] = choice
    save_session(session)
    evaluator.score_response(f"Answer: {choice}", asset)
    return True


def run_human_test():
    """Interaktiver Test-Lauf."""
    init = _init_user_and_session()
    if init is None:
        return
    model_name, session, runner = init
    total_q = len(runner.questions)

    evaluator = PoliticalCompassEvaluator()
    questions = runner.questions
    session_seed = session["seed"]
    start_time = time.time()

    print(f"\n🚀 Starte Test mit {total_q} Fragen...\n")
    for i, asset in enumerate(questions, 1):
        if not _process_one_question(asset, i, total_q, session, session_seed, evaluator, runner):
            return

    print("\n" + "=" * 40)
    print("🏁 Test beendet. Berechne Ergebnisse...")
    duration = time.time() - start_time
    final_results = evaluator.score_aggregated()
    _print_results(model_name, final_results)

    report = _build_report(model_name, evaluator, duration, total_q)
    _save_report_json(report, model_name)
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
