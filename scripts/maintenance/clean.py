#!/usr/bin/env python3
"""
Zentrales Cleanup-Skript für CrucibleMark.
Ermöglicht das komfortable Löschen von Caches, CSVs, Model-Ergebnissen,
Runs und temporären Datein – entweder per CLI-Argumente oder interaktiv.
"""
import sys
import argparse
import shutil
from pathlib import Path

# Setup Root Path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.benchmark_ui import TerminalUI
from scripts.maintenance.cleanup_runs import cleanup_runs
from scripts.maintenance.clean_results import clean_checkpoints

def clean_pycache():
    """Löscht __pycache__ und *.pyc rekursiv ab Projektwurzel."""
    print("🧹 Lösche PyCache und .pyc Dateien...")
    count_dirs = 0
    count_files = 0
    for p in ROOT_DIR.rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p)
            count_dirs += 1
    for p in ROOT_DIR.rglob("*.pyc"):
        if p.is_file():
            p.unlink()
            count_files += 1
    print(f"   -> {count_dirs} Ordner und {count_files} Dateien gelöscht.")

def clean_comparisons_and_audit():
    """Löscht generierte Ausgaben unter outputs (inklusive aller Runs!)."""
    print("🧹 Bereinige generierte Reports und Runs (Comparisons, Audit, Runs)...")
    for dir_name in ["comparisons", "audit_logs", "runs"]:
        target_dir = ROOT_DIR / "outputs" / dir_name
        if target_dir.exists():
            for p in target_dir.iterdir():
                if p.name != ".gitkeep":
                    if p.is_file():
                        p.unlink()
                    elif p.is_dir():
                        shutil.rmtree(p)
    print("   -> Reports und Runs bereinigt.")

def clean_all_csvs():
    """Löscht alle Benchmark-CSVs in benchmark_scores/."""
    print("🗑️  Lösche alle CSV-Resultate...")
    score_dir = ROOT_DIR / "benchmark_scores"
    if score_dir.exists():
        for p in score_dir.glob("*.csv"):
            if "leaderboard" not in p.name:  # Maybe we want to delete all? Actually, standard clean-csv deleted all.
                p.unlink()
                print(f"   - Gelöscht: {p.name}")
            else:
                p.unlink()
                print(f"   - Gelöscht: {p.name}")

def _run_clean_results(model: str | None = None, module: str | None = None):
    import subprocess
    import sys
    cmd = [sys.executable, "scripts/maintenance/clean_results.py"]
    if model:
        cmd.extend(["--model", model])
    if module:
        cmd.extend(["--module", module])
    subprocess.run(cmd, check=False)

def interactive_wizard():
    print("\033[96m========================================\033[0m")
    print("\033[96m   CrucibleMark - Cleanup Wizard\033[0m")
    print("\033[96m========================================\n\033[0m")

    options = [
        "Standard-Cache leeren (PyCache, Reports, Sessions)",
        "Alte Runs bereinigen (Behalte 1 neuesten pro Modell)",
        "Gezielt Ergebnisse eines Modells löschen",
        "Gezielt Ergebnisse eines Moduls löschen",
        "Komplett-Reset: Alle Caches & CSV-Daten löschen (DANGER)"
    ]

    choice = TerminalUI.select_from_list(options, lambda x: x, prompt="Was möchtest du bereinigen?")

    if choice == options[0]:
        clean_pycache()
        clean_comparisons_and_audit()
        clean_checkpoints() # alle sessions
        print("✅ Standard-Cleanup abgeschlossen.")
    elif choice == options[1]:
        cleanup_runs(Path("outputs/runs"), keep=1, force=False, dry_run=False)
    elif choice == options[2]:
        model_name = input("🔍 Modellname (z.B. qwen2.5:14b): ").strip()
        if model_name:
            _run_clean_results(model=model_name)
    elif choice == options[3]:
        module_key = input("🔍 Modul-Key (z.B. cli_benchmark): ").strip()
        if module_key:
            _run_clean_results(module=module_key)
    elif choice == options[4]:
        confirm = input("\033[91m⚠️ WARNUNG: Dies löscht ALLE Resultate. Sicher? [y/N]: \033[0m").strip().lower()
        if confirm in ["y", "yes", "j", "ja"]:
            clean_pycache()
            clean_comparisons_and_audit()
            clean_checkpoints()
            clean_all_csvs()
            print("✅ Hard-Reset abgeschlossen.")
        else:
            print("❌ Abbruch.")

def main():
    parser = argparse.ArgumentParser(description="Zentrales Skript zum Bereinigen von Projektdateien und Ergebnissen.")
    parser.add_argument("--interactive", action="store_true", help="Starte den interaktiven Wizard")
    parser.add_argument("--cache", action="store_true", help="Lösche PyCache und Standard-Dumps")
    parser.add_argument("--csv", action="store_true", help="Lösche alle CSV Resultate")
    parser.add_argument("--sessions", action="store_true", help="Lösche alle temporären Session-Dateien (Political Compass)")
    parser.add_argument("--runs", type=int, metavar="KEEP", help="Lösche alte Runs, behalte N")
    parser.add_argument("--model", type=str, help="Lösche spezifische Modell-Ergebnisse")
    parser.add_argument("--module", type=str, help="Lösche spezifische Modul-Ergebnisse")
    parser.add_argument("--all", action="store_true", help="Lösche Caches + Alle CSVs")
    parser.add_argument("--force", action="store_true", help="Ohne Nachfragen löschen")

    if len(sys.argv) == 1:
        interactive_wizard()
        return

    args = parser.parse_args()

    if args.interactive:
        interactive_wizard()
        return

    if args.all:
        clean_pycache()
        clean_comparisons_and_audit()
        clean_checkpoints()
        clean_all_csvs()
        return

    executed = False

    if args.cache:
        clean_pycache()
        clean_comparisons_and_audit()
        executed = True

    if args.sessions:
        clean_checkpoints()
        executed = True

    if args.csv:
        clean_all_csvs()
        executed = True

    if args.runs is not None:
        cleanup_runs(Path("outputs/runs"), keep=args.runs, force=args.force, dry_run=False)
        executed = True

    if args.model or args.module:
        _run_clean_results(model=args.model, module=args.module)
        executed = True

    if not executed:
        # Fallback falls jemand einfach so was komisches macht
        interactive_wizard()

if __name__ == "__main__":
    main()
