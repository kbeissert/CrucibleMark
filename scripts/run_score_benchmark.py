#!/usr/bin/env python3
"""Score Benchmark Worker.

Dedicated worker for scoring modules (module 1-7) with a stable orchestrator
contract. Excludes political_compass and tooluse by design.

Architektur:
- API-Provider (OpenRouter, Anthropic, etc.): Subprocess-Delegation pro Modul
  (run_benchmark.py --module X --model Y) — jeder Subprozess ist isoliert.
- llama.cpp-Provider (llamacpp, llamacpp_spark, etc.): In-Process-Execution
  via UnifiedBenchmarkRunner — Server bleibt über alle Module eines Modells
  hinweg aktiv, kein Stop/Start-Race zwischen Modulen.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.core.model_discovery import discover_models  # noqa: E402
from scripts.core.runner_contract import write_run_summary, update_leaderboard  # noqa: E402
from scripts.core.unified_runner import UnifiedBenchmarkRunner  # noqa: E402
from utils.config_validator import ConfigValidator  # noqa: E402
from utils.model_utils import resolve_provider  # noqa: E402

# llama.cpp Batch-Orchestrierung
from scripts.core.llamacpp_batch import (  # noqa: E402
    is_llamacpp_provider,
    get_enabled_llamacpp_providers,
    stop_llamacpp_provider_server,
    run_llamacpp_provider_cleanup,
    set_llamacpp_provider_context,
    llamacpp_model_session,
    get_existing_results,
    get_startable_assets,
    load_modules_for_keys,
    LlamaCppSessionError,
)

EXCLUDED_MODULES = {"political_compass", "tooluse"}


def _get_score_modules(config: dict[str, Any], modules_arg: str | None) -> list[str]:
    if modules_arg:
        requested = [m.strip() for m in modules_arg.split(",") if m.strip()]
        return [m for m in requested if m not in EXCLUDED_MODULES]

    module_cfg = config.get("modules", {})
    score_modules: list[str] = []
    for key, entry in module_cfg.items():
        if key in EXCLUDED_MODULES:
            continue
        if isinstance(entry, dict) and entry.get("enabled", False):
            score_modules.append(key)
    return score_modules


def _run_module_subprocess(model_id: str, module_key: str, force: bool, silent: bool) -> bool:
    """Delegiert ein einzelnes Modul an run_benchmark.py als Subprozess.

    Verwendet für API-Provider (isolierte Subprozesse, kein Server-Lifecycle).
    """
    cmd = [
        sys.executable,
        "run_benchmark.py",
        "--module",
        module_key,
        "--model",
        model_id,
    ]
    if force:
        cmd.append("--force")
    if silent:
        cmd.append("--silent")

    env = dict(os.environ)
    env["CRUCIBLE_DELEGATE_PARENT"] = "1"

    result = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, check=False)
    return result.returncode == 0


def _run_modules_inprocess_llamacpp(
    model_id: str,
    provider_key: str,
    module_keys: list[str],
    force: bool,
    silent: bool,
    config: dict[str, Any],
) -> dict[str, bool]:
    """Führt alle Score-Module in-process für einen llama.cpp-Provider aus.

    Server wird EINMAL am Anfang gestartet und am Ende des Batches gestoppt.
    Zwischen den Modulen gibt es keine Server-Restarts — die bestehende
    Cooldown-Phase (Memory Recovery, Adaptive Pause) nach jedem Asset
    sorgt dafür, dass der Server "zur Ruhe kommt".

    Returns:
        Dict module_key -> bool (True = Erfolg)
    """
    from utils.module_registry import load_module_config

    results: dict[str, bool] = {}

    # Module laden
    modules = load_modules_for_keys(config, module_keys)
    if not modules:
        print(f"   ⚠️ Keine Module geladen für {model_id}")
        return results

    # Cache laden
    csv_path = Path(
        config.get("output", {}).get("local_models_csv", "benchmark_scores/local_models_benchmark.csv")
    )
    existing_tests = get_existing_results(csv_path, force=force)

    # Provider-Config ermitteln
    local_cfg = config.get("providers", {}).get("local", {})
    provider_cfg = local_cfg.get(provider_key, {})
    if not provider_cfg:
        print(f"   ❌ Provider-Config für '{provider_key}' nicht gefunden.")
        return {m["key"]: False for m in modules}

    # Runner initialisieren — Cleanup wird vom Context-Manager übernommen
    runner = UnifiedBenchmarkRunner(force=force, audit_mode=not silent)
    runner._skip_llamacpp_cleanup = True  # type: ignore[attr-defined]

    try:
        with llamacpp_model_session(runner, provider_key, provider_cfg, model_id) as _client:
            for module in modules:
                module_key = module["key"]
                print(f"  -> Module: {module_key} (in-process)")

                # Assets ermitteln
                assets_todo = get_startable_assets(module, model_id, existing_tests)
                if not assets_todo:
                    print(f"   ✓ {module['name']} (alle Tests vorhanden)")
                    results[module_key] = True
                    continue

                print(f"   📊 {module['name']} ({len(assets_todo)} neue Tests) ...")

                # Benchmark-Info zusammenbauen (SSOT-paritätisch mit run_benchmark.py)
                internal_config = load_module_config(Path(module["module_path"]))
                benchmark_info = internal_config.copy()
                benchmark_info.update(module)
                benchmark_info.update({
                    "id": module_key,
                    "name": module.get("name", module_key),
                    "path": module.get("path", f"{module['module_path']}/assets"),
                    "module_path": module["module_path"],
                    "test_class": internal_config.get("execution", {}).get("test_class")
                    or module.get("test_class", "CodeQualityTest"),
                    "execution_mode": module.get("execution_mode", "standard"),
                    "min_runs": module.get("min_runs", 1),
                    "benchmarks": internal_config.get("benchmarks", []),
                    "scoring": internal_config.get("scoring", {}),
                })

                try:
                    run_results = runner.run_benchmark(
                        provider=provider_key,
                        model=model_id,
                        benchmark_info=benchmark_info,
                        assets=assets_todo,
                    )
                    # Kurze Pause zwischen Modulen, damit der Server stabilisiert
                    # (verhindert Race-Conditions bei schnellen Modul-Wechseln)
                    time.sleep(3)
                    if run_results:
                        runner.save_results(run_results)
                        results[module_key] = True
                    else:
                        results[module_key] = False
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    print(f"   ❌ Fehler in {module_key}: {exc}")
                    results[module_key] = False

    except LlamaCppSessionError as exc:
        print(f"   ❌ llama.cpp Session-Fehler für {model_id}: {exc}")
        for module in modules:
            results[module["key"]] = False
    except KeyboardInterrupt:
        print("\n⛔  Abbruch durch Benutzer.")
        raise

    return results


def _run_score_batch(
    model_ids: list[str],
    module_keys: list[str],
    force: bool,
    silent: bool,
    config: dict[str, Any],
) -> dict[str, Any]:
    failed_tasks: list[dict[str, str]] = []
    tasks_total = len(model_ids) * len(module_keys)
    tasks_successful = 0

    for midx, model_id in enumerate(model_ids, 1):
        print(f"\n=== Model {midx}/{len(model_ids)}: {model_id} ===")

        # Provider ermitteln
        provider, _resolved_model = resolve_provider(model_id)

        if is_llamacpp_provider(provider):
            # llama.cpp: In-Process mit persistentem Server
            module_results = _run_modules_inprocess_llamacpp(
                model_id=model_id,
                provider_key=provider,
                module_keys=module_keys,
                force=force,
                silent=silent,
                config=config,
            )
            for module_key, ok in module_results.items():
                if ok:
                    tasks_successful += 1
                else:
                    failed_tasks.append({"model": model_id, "module": module_key})
        else:
            # API-Provider: Subprocess pro Modul (bestehendes Verhalten)
            for module_key in module_keys:
                print(f"  -> Module: {module_key} (subprocess)")
                ok = _run_module_subprocess(model_id, module_key, force=force, silent=silent)
                if ok:
                    tasks_successful += 1
                else:
                    failed_tasks.append({"model": model_id, "module": module_key})

    return {
        "models_total": len(model_ids),
        "modules_total": len(module_keys),
        "tasks_total": tasks_total,
        "tasks_successful": tasks_successful,
        "tasks_failed": len(failed_tasks),
        "failed_tasks": failed_tasks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score Benchmark Worker")
    parser.add_argument("--model", type=str, help="Ein einzelnes Modell ausführen")
    parser.add_argument("--models", type=str, help="Kommagetrennte Modellliste")
    parser.add_argument("--all", action="store_true", help="Alle Modelle ausführen")
    parser.add_argument(
        "--provider",
        default="all",
        choices=["all", "local", "commercial"],
        help="Modellscope für Batch-Läufe",
    )
    parser.add_argument(
        "--modules",
        type=str,
        help="Kommagetrennte Modulkeys (Default: alle aktivierten Score-Module)",
    )
    parser.add_argument("--force", action="store_true", help="Cache ignorieren")
    parser.add_argument("--silent", action="store_true", help="Audit-Logs unterdrücken")
    parser.add_argument(
        "--summary-json",
        type=str,
        help="Optionaler Pfad für strukturiertes Run-Summary JSON (Orchestrator-Rückkanal).",
    )
    args = parser.parse_args()

    config = ConfigValidator().config
    module_keys = _get_score_modules(config, args.modules)

    if not module_keys:
        write_run_summary(
            args.summary_json,
            {
                "runner": "score_benchmark",
                "status": "failed",
                "mode": "unknown",
                "message": "Keine Score-Module verfügbar/ausgewählt",
            },
        )
        print("Keine Score-Module verfügbar/ausgewählt.")
        sys.exit(1)

    try:
        if args.model:
            summary = _run_score_batch([args.model], module_keys, force=args.force, silent=args.silent, config=config)
            status = "success" if summary["tasks_failed"] == 0 else "partial"
            update_leaderboard(ROOT_DIR)
            write_run_summary(
                args.summary_json,
                {
                    "runner": "score_benchmark",
                    "status": status,
                    "mode": "single",
                    **summary,
                },
            )
            sys.exit(0 if summary["tasks_failed"] == 0 else 1)

        if args.models:
            model_ids = [m.strip() for m in args.models.split(",") if m.strip()]
            if not model_ids:
                write_run_summary(
                    args.summary_json,
                    {
                        "runner": "score_benchmark",
                        "status": "failed",
                        "mode": "models",
                        "message": "Leere Modellliste über --models",
                    },
                )
                print("Keine Modelle in --models angegeben.")
                sys.exit(1)

            summary = _run_score_batch(model_ids, module_keys, force=args.force, silent=args.silent, config=config)
            status = "success" if summary["tasks_failed"] == 0 else "partial"
            update_leaderboard(ROOT_DIR)
            write_run_summary(
                args.summary_json,
                {
                    "runner": "score_benchmark",
                    "status": status,
                    "mode": "models",
                    **summary,
                },
            )
            sys.exit(0 if summary["tasks_failed"] == 0 else 1)

        if args.all or args.provider != "all":
            model_ids = discover_models(args.provider, config)
            if not model_ids:
                write_run_summary(
                    args.summary_json,
                    {
                        "runner": "score_benchmark",
                        "status": "success",
                        "mode": "all" if args.all else "provider",
                        "models_total": 0,
                        "modules_total": len(module_keys),
                        "tasks_total": 0,
                        "tasks_successful": 0,
                        "tasks_failed": 0,
                        "failed_tasks": [],
                        "message": f"Keine Modelle gefunden (provider={args.provider})",
                    },
                )
                print(f"Keine Modelle gefunden (provider={args.provider}).")
                sys.exit(0)

            summary = _run_score_batch(model_ids, module_keys, force=args.force, silent=args.silent, config=config)
            status = "success" if summary["tasks_failed"] == 0 else "partial"
            update_leaderboard(ROOT_DIR)
            write_run_summary(
                args.summary_json,
                {
                    "runner": "score_benchmark",
                    "status": status,
                    "mode": "all" if args.all else "provider",
                    **summary,
                },
            )
            sys.exit(0 if summary["tasks_failed"] == 0 else 1)

        # Compatibility fallback: preserve legacy interactive behavior.
        cmd = [sys.executable, "run_benchmark.py"]
        if args.modules and "," not in args.modules:
            cmd += ["--module", args.modules]
        if args.force:
            cmd.append("--force")
        if args.silent:
            cmd.append("--silent")

        env = dict(os.environ)
        env["CRUCIBLE_DELEGATE_PARENT"] = "1"

        result = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, check=False)
        write_run_summary(
            args.summary_json,
            {
                "runner": "score_benchmark",
                "status": "success" if result.returncode == 0 else "failed",
                "mode": "wizard",
                "modules_total": len(module_keys),
            },
        )
        sys.exit(result.returncode)

    except KeyboardInterrupt:
        write_run_summary(
            args.summary_json,
            {
                "runner": "score_benchmark",
                "status": "aborted",
                "mode": "unknown",
            },
        )
        print("\n\nScore Benchmark abgebrochen.")
        sys.exit(130)


if __name__ == "__main__":
    main()
