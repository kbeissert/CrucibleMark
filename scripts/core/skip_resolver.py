"""Batch-Loop Skip-Resolver für benchmark_auto.py.

Separation-of-Concerns: Skip/Abort-Entscheidungen und die Failure-Skip-Logik
der Batch-Loops sind aus den Provider-spezifischen Runnern ausgegliedert.
Das Muster ``assets_todo → run_module → status-check → abort/continue``
ist in ``_run_llamacpp_model_modules``, ``_run_vllm_model_modules`` und
``_run_ollama_model_modules`` identisch und hier zentralisiert.

``_run_module_for_model`` bleibt in benchmark_auto.py und wird als Callback
übergeben, um zirkuläre Imports zu vermeiden.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Callable


RunModuleFn = Callable[..., str]


def run_module_or_abort(
    run_module: RunModuleFn,
    module: dict[str, Any],
    model: str,
    existing_tests: set[tuple[str, str]],
    runner: Any,
    force: bool,
    audit: bool,
    mcp_mode: str,
    provider: str,
) -> bool:
    """Führt ein einzelnes Benchmark-Modul aus und entscheidet über Skip/Abbruch.

    Wird vom Batch-Loop für jedes Modul aufgerufen. Bei echtem Fehler und
    offenen Assets wird ``False`` zurückgegeben (Abbruch des Modell-Loops).
    Bei "ran" oder "skipped" (inkl. Leaderboard-Skip) wird ``True``
    zurückgegeben (Loop geht weiter).

    Returns:
        True wenn der Loop fortgesetzt werden soll, False bei Abbruch.
    """
    from scripts.core.benchmark_auto import get_startable_assets  # Deferred: vermeidet Circular-Import zum Modul-Load

    assets_todo = get_startable_assets(module, model, existing_tests)
    status = run_module(
        runner, model, module, existing_tests,
        force=force, audit=audit, mcp_mode=mcp_mode, provider=provider,
    )
    if status == "failed" and assets_todo:
        print(
            f"   ⚠️  Modul '{module.get('key', 'unknown')}' für '{model}' "
            "fehlgeschlagen (mit offenen Assets). "
            "Restliche Module für dieses Modell werden übersprungen."
        )
        return False
    return True
