#!/usr/bin/env python3
"""
Zentrales Cleanup-Skript fuer CrucibleMark.
Ermoeglicht das komfortable Loeschen von Caches, CSVs, Model-Ergebnissen,
Runs und temporaeren Datein -- entweder per CLI-Argumente oder interaktiv.

Seit Phase 27 (Backup-System SSoT-Refactor) delegiert ``--runs`` an
:func:`scripts.maintenance.cleanup_runs.cleanup_runs` (SSoT-Refactor)
und nutzt :data:`utils.backup_targets.RUNS_KEEP_DEFAULT` als Default
(5, nicht mehr 1).
"""
import sys
import argparse
import shutil
from pathlib import Path

# Setup Root Path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.benchmark_ui import TerminalUI
from utils.backup_targets import RUNS_KEEP_DEFAULT  # noqa: E402
from scripts.maintenance.cleanup_runs import cleanup_runs
from scripts.maintenance.clean_results import clean_checkpoints


def clean_pycache():
    """Loescht __pycache__ und *.pyc rekursiv ab Projektwurzel."""
    print("🧹 Loesche PyCache und .pyc Dateien...")
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
    print(f"   -> {count_dirs} Ordner und {count_files} Dateien geloescht.")


def clean_comparisons_and_audit():
    """Loescht generierte Ausgaben unter outputs (inklusive aller Runs!)."""
    print("🧹 Bereinige generierte Reports und Runs (Comparisons, Audit, Runs, WebExport-Check)...")
    for dir_name in ["comparisons", "audit_logs", "runs", "web_export_check"]:
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
    """Loescht alle Benchmark-CSVs in benchmark_scores/."""
    print("🗑️  Loesche alle CSV-Resultate...")
    score_dir = ROOT_DIR / "benchmark_scores"
    if score_dir.exists():
        for p in score_dir.glob("*.csv"):
            p.unlink()
            print(f"   - Geloescht: {p.name}")


def _run_clean_results(
    model: str | None = None,
    module: str | None = None,
    dry_run: bool = False,
):
    """Delegiert an clean_results (Phase 28: direkter Aufruf statt Subprozess).

    Spart den zweiten Python-Start (~250 ms Overhead) und teilt den
    Logger mit dem Dispatcher.
    """
    # pylint: disable=import-outside-toplevel
    from scripts.maintenance import clean_results

    # Namespace bauen statt main() aufzurufen, damit wir keine globale
    # argparse-Optionen vermischen.
    class _Args:
        pass

    ns = _Args()
    ns.model = model
    ns.module = module
    ns.dry_run = dry_run
    ns.prune_orphans = False
    ns.force = False
    clean_results.main_with_args(ns)


def interactive_wizard():
    print("\033[96m========================================\033[0m")
    print("\033[96m   CrucibleMark - Cleanup Wizard\033[0m")
    print("\033[96m========================================\n\033[0m")

    options = [
        "Standard-Cache leeren (PyCache, Reports, Sessions)",
        f"Alte Runs bereinigen (Behalte {RUNS_KEEP_DEFAULT} neueste pro Modell)",
        "Gezielt Ergebnisse eines Modells loeschen",
        "Gezielt Ergebnisse eines Moduls loeschen",
        "Komplett-Reset: Alle Caches & CSV-Daten loeschen (DANGER)"
    ]

    choice = TerminalUI.select_from_list(options, lambda x: x, prompt="Was moechtest du bereinigen?")

    if choice == options[0]:
        clean_pycache()
        clean_comparisons_and_audit()
        clean_checkpoints()  # alle sessions
        print("✅ Standard-Cleanup abgeschlossen.")
    elif choice == options[1]:
        cleanup_runs(
            Path("outputs/runs"),
            keep=RUNS_KEEP_DEFAULT,
            force=False,
            dry_run=False,
        )
    elif choice == options[2]:
        model_name = input("🔍 Modellname (z.B. qwen2.5:14b): ").strip()
        if model_name:
            _run_clean_results(model=model_name)
    elif choice == options[3]:
        module_key = input("🔍 Modul-Key (z.B. cli_benchmark): ").strip()
        if module_key:
            _run_clean_results(model=module_key)
    elif choice == options[4]:
        confirm = input(
            "\033[91m⚠️ WARNUNG: Dies loescht ALLE Resultate. Sicher? [y/N]: \033[0m"
        ).strip().lower()
        if confirm in ["y", "yes", "j", "ja"]:
            clean_pycache()
            clean_comparisons_and_audit()
            clean_checkpoints()
            clean_all_csvs()
            print("✅ Hard-Reset abgeschlossen.")
        else:
            print("❌ Abbruch.")


def main():
    parser = argparse.ArgumentParser(
        description="Zentrales Skript zum Bereinigen von Projektdateien und Ergebnissen."
    )
    parser.add_argument("--interactive", action="store_true", help="Starte den interaktiven Wizard")
    parser.add_argument("--cache", action="store_true", help="Loesche PyCache und Standard-Dumps")
    parser.add_argument("--csv", action="store_true", help="Loesche alle CSV Resultate")
    parser.add_argument(
        "--sessions", action="store_true",
        help="Loesche alle temporaeren Session-Dateien (Political Compass)",
    )
    parser.add_argument(
        "--runs", type=int, metavar="KEEP",
        help=f"Loesche alte Runs, behalte N (default: {RUNS_KEEP_DEFAULT})",
    )
    parser.add_argument("--model", type=str, help="Loesche spezifische Modell-Ergebnisse")
    parser.add_argument("--module", type=str, help="Loesche spezifische Modul-Ergebnisse")
    parser.add_argument("--all", action="store_true", help="Loesche Caches + Alle CSVs")
    parser.add_argument("--force", action="store_true", help="Ohne Nachfragen loeschen")
    parser.add_argument("--dry-run", action="store_true", help="Zeigt nur an, was geloescht wuerde.")

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
        cleanup_runs(
            Path("outputs/runs"),
            keep=args.runs,
            force=args.force,
            dry_run=False,
        )
        executed = True

    if args.model or args.module:
        _run_clean_results(model=args.model, module=args.module, dry_run=args.dry_run)
        executed = True

    if not executed:
        # Fallback falls jemand einfach so was komisches macht
        interactive_wizard()


if __name__ == "__main__":
    main()
