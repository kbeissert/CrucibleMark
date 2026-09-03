#!/usr/bin/env python3
"""
Political-Compass Token-Budget-Kalibrierung (PC v3)
====================================================
Zwei Modi:

1. **Fixed-Budget-Messung** (Default): Läuft N Fragen (Default 12) über 2
   Themenblöcke für EIN Modell mit dem konfigurierten PC-Budget und misst die
   Reasoning-/Output-Token-Verteilung. Ziel (Plan PC v3, Task 9):
   P95(reasoning) + 200 ≤ Budget, Truncation-Rate < 5 %.

2. **Gestufter Token-Probe** (``--probe``): Kalibriert das Budget pro Modell
   nach dem Thinking-Probe-Pattern — Stufen [300, 600, 1200, 2400],
   dreiwertige Klassifikation (self_limiting / inconsistent /
   greedy_uncapped). Ergebnis via ``--write-card`` in die Model Card
   persistieren (``pc_token_calibration`` + ``pc_profile``) —
   resolve_token_budget honoriert es automatisch (Card-First).

   Hinweis: Der PC-Benchmark-Runner führt die Probe automatisch aus, wenn
   die Card keinen Eintrag hat (Card-First-Hook,
   ``benchmark_modules/political_compass/core/pc_probe_hook.py``). Dieses
   Tool dient der manuellen Kalibrierung / Wiederholung.

Direkter Client-Query — kein save_results, keine CSV-Berührung, kein Checkpoint.

Verwendung:
    # Token-Probe + Card-Write (empfohlener Workflow vor dem ersten PC-Run)
    .venv/bin/python scripts/tools/pc_calibrate.py --model <id> --probe --write-card

    # Fixed-Budget-Messung (Verteilung + Empfehlung, kein Card-Write)
    .venv/bin/python scripts/tools/pc_calibrate.py --model gemma-4-12b-it-ud-q6_k_xl-spark
    .venv/bin/python scripts/tools/pc_calibrate.py --model <id> --provider vllm_spark --num-questions 16
    .venv/bin/python scripts/tools/pc_calibrate.py --model <id> --budget 1200
"""

import argparse
import logging
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from benchmark_modules.political_compass.core.constants import (  # noqa: E402
    PC_SLEEP_BETWEEN_REQUESTS,
)
from benchmark_modules.political_compass.core.pc_probe_hook import (  # noqa: E402
    run_pc_token_probe,
    write_pc_calibration_to_card,
)
from benchmark_modules.political_compass.core.token_probe import (  # noqa: E402
    PcProbeError,
)
from benchmark_modules.political_compass.test import (  # noqa: E402
    STANDARD_PROMPT,
    PoliticalCompassTest,
)
from utils.benchmark_utils import token_distribution  # noqa: E402
from utils.config_validator import ConfigValidator  # noqa: E402
from utils.llm_client import LLMClient  # noqa: E402
from utils.model_id_base import resolve_provider  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Empfehlungs-Formel (Plan Task 9): P95(reasoning) + Sicherheitsmarge.
RECOMMENDATION_MARGIN = 200
TRUNCATION_RATE_TARGET = 0.05


def _collect_questions(test: PoliticalCompassTest, num_questions: int) -> list[dict[str, Any]]:
    """Erste N Fragen aus den ersten 2 Themenblöcken (deterministisch)."""
    test.load_questions()
    if not test.questions:
        raise SystemExit("Keine PC-Fragen geladen — Assets-Verzeichnis prüfen.")
    questions_by_block, sorted_blocks = test._group_questions_by_block()  # pylint: disable=protected-access
    selected: list[dict[str, Any]] = []
    for block_id in sorted_blocks[:2]:
        for asset in questions_by_block[block_id]:
            if len(selected) >= num_questions:
                break
            selected.append(asset)
    if len(selected) < num_questions:
        logger.warning(
            "Nur %d von %d Fragen über 2 Blöcke verfügbar.", len(selected), num_questions,
        )
    return selected


def _query_question(
    client: LLMClient,
    model: str,
    provider: str,
    prompt: str,
    budget: int,
) -> dict[str, Any]:
    """Ein Kalibrierungs-Query mit PC-v3-Wiring; misst Token + Truncation."""
    start = time.time()
    response = client.query(
        model=model,
        prompt=prompt,
        provider=provider,
        system=STANDARD_PROMPT,
        temperature=0.1,
        max_tokens=budget,
        _module_key="political_compass",
    )
    duration = time.time() - start
    metadata = getattr(client, "last_response_metadata", {}) or {}
    finish_reason = metadata.get("finish_reason")
    return {
        "response": response or "",
        "reasoning_tokens": int(metadata.get("reasoning_tokens") or 0),
        "output_tokens": int(getattr(client, "last_output_tokens", 0) or 0),
        "finish_reason": str(finish_reason) if finish_reason else None,
        "truncated": str(finish_reason).lower() in ("length", "max_tokens") if finish_reason else False,
        "duration_s": duration,
    }


def _print_report(
    model: str,
    provider: str,
    budget: int,
    results: list[dict[str, Any]],
) -> int:
    """Printed Verteilung + Empfehlung; Return = empfohlenes Budget."""
    reasoning = [r["reasoning_tokens"] for r in results]
    output = [r["output_tokens"] for r in results]
    durations = [r["duration_s"] for r in results]
    truncation_count = sum(1 for r in results if r["truncated"])
    truncation_rate = truncation_count / len(results) if results else 0.0

    reasoning_dist = token_distribution(reasoning)
    output_dist = token_distribution(output)
    recommended = reasoning_dist["p95"] + RECOMMENDATION_MARGIN

    print(f"\n{'=' * 62}")
    print(f"PC v3 Kalibrierung: {model} (provider={provider})")
    print(f"{'=' * 62}")
    print(f"Fragen: {len(results)} · Budget: {budget} · Modul-Key: political_compass")
    print(f"\nReasoning-Tokens: Median {reasoning_dist['median']} · "
          f"P95 {reasoning_dist['p95']} · Max {reasoning_dist['max']}")
    print(f"Output-Tokens:    Median {output_dist['median']} · "
          f"P95 {output_dist['p95']} · Max {output_dist['max']}")
    if durations:
        print(f"Antwortzeit:      Median {statistics.median(durations):.1f}s · "
              f"Max {max(durations):.1f}s")
    print(f"Truncation:       {truncation_count}/{len(results)} "
          f"({truncation_rate:.1%}, Ziel < {TRUNCATION_RATE_TARGET:.0%})")

    print(f"\nEmpfehlung (P95 + {RECOMMENDATION_MARGIN} Marge): "
          f"token_budgets.political_compass = {recommended}")
    if recommended > budget:
        print(f"⚠️  Aktuelles Budget ({budget}) zu knapp — Empfehlung: {recommended}")
    elif truncation_rate >= TRUNCATION_RATE_TARGET:
        print("⚠️  Truncation-Rate über Ziel trotz ausreichendem Budget — "
              "Modell terminiert CoT nicht sauber (Thinking-Off-Re-Ask prüfen).")
    else:
        print(f"✅ Budget {budget} ausreichend (Empfehlung {recommended}).")

    print("\nHinweis: Wert in benchmark_config.yaml UND "
          "token_budgets_reasoning_models.political_compass synchron anpassen.")
    return recommended


def _print_probe_report(calibration: Any, model: str) -> None:
    """Printed das Probe-Ergebnis mit Block-Report und Handlungsempfehlung."""
    print(f"\n{'=' * 62}")
    print(f"PC v3 Token-Probe: {model}")
    print(f"{'=' * 62}")
    for block_entry in calibration.block_report:
        status = block_entry.get("status", "?")
        stage = block_entry.get("converged_stage")
        stage_str = f"@ {stage}" if stage else ""
        print(f"  Block {block_entry['block']:<28} {status:<12} {stage_str}")
    print(f"\nProfil: {calibration.profile}")
    print(f"Klassifikation: {calibration.classification}")
    print(f"Kalibriertes Budget: {calibration.budget}")
    if calibration.notes:
        print(f"Notiz: {calibration.notes}")

    if calibration.profile == "instruct":
        print("\nHandlungsempfehlung:")
        print("  - vLLM: PC-Lauf läuft automatisch im Instruct-Modus (Thinking-Off per Request).")
        print("  - llama.cpp: Instruct-Profil in provider_config.yaml anlegen")
        print("    (enable_thinking: false) — siehe Coverage-Regel, Konzept-Doc Abschn. 11.")
    elif calibration.profile == "hybrid_dual":
        print("\nHandlungsempfehlung (hybrid_dual):")
        print("  - ZWEI Läufe: Thinking (kalibriertes Budget, partiell) + Instruct-Profil.")
        print("  - Der Shift-Vergleich zwischen beiden Modi ist die Bonus-Erkenntnis")
        print("    (misst empirisch, ob Reasoning die gemessene Position verschiebt).")
        print("  - llama.cpp: Instruct-Profil als eigene Modell-ID anlegen (Dual-Profil-Pattern).")
    else:
        print("\nHandlungsempfehlung: Ein Thinking-Lauf mit dem kalibrierten Budget.")


def run_probe_mode(args: argparse.Namespace, config: dict[str, Any]) -> int:
    """Stratifizierter zweistufiger Token-Probe (Card-First-Pattern).

    SSoT für Probe-Orchestrierung + Card-Write:
    ``benchmark_modules/political_compass/core/pc_probe_hook.py`` (geteilt
    mit dem Runner-Hook — kein Duplikat).
    """
    provider = args.provider or resolve_provider(args.model)[0]
    client = LLMClient(config=config)
    try:
        calibration = run_pc_token_probe(args.model, provider, client)
    except PcProbeError as exc:
        # Fast-Fail-Guard: systematische Provider-Fehler — bewusst kein
        # Card-Write (sonst würde z. B. greedy_uncapped/Budget-None persistiert).
        print(f"\n❌ {exc}", file=sys.stderr, flush=True)
        print("   Kein Card-Write. Provider/Modell prüfen und Probe wiederholen.",
              file=sys.stderr, flush=True)
        return 1
    _print_probe_report(calibration, args.model)

    if args.write_card:
        card_path = write_pc_calibration_to_card(args.model, calibration, provider=provider)
        print(f"\n✅ Card aktualisiert: {card_path}")
        print("   resolve_token_budget honoriert das kalibrierte Budget automatisch.")
    else:
        print("\n(Hinweis: --write-card zum Persistieren in die Model Card)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="PC v3 Token-Budget-Kalibrierung / Token-Probe")
    parser.add_argument("--model", required=True, help="Modell-ID (z.B. gemma-4-12b-it-ud-q6_k_xl-spark)")
    parser.add_argument("--provider", default=None, help="Provider-Key (Default: Auto-Resolution)")
    parser.add_argument("--num-questions", type=int, default=12, help="Anzahl Fragen im Fixed-Budget-Modus (Default 12)")
    parser.add_argument("--budget", type=int, default=None,
                        help="Test-Budget im Fixed-Budget-Modus (Default: token_budgets.political_compass)")
    parser.add_argument("--probe", action="store_true",
                        help="Gestufter Token-Probe (Stufen 300/600/1200/2400, Klassifikation)")
    parser.add_argument("--write-card", action="store_true",
                        help="Probe-Ergebnis in die Model Card persistieren (pc_token_calibration)")
    args = parser.parse_args()

    config = ConfigValidator(str(ROOT_DIR / "benchmark_config.yaml")).config

    if args.probe:
        sys.exit(run_probe_mode(args, config))

    provider = args.provider or resolve_provider(args.model)[0]
    budget = args.budget or int(
        config.get("token_budgets", {}).get("political_compass", 800)
    )

    test = PoliticalCompassTest()
    questions = _collect_questions(test, args.num_questions)

    client = LLMClient(config=config)
    results: list[dict[str, Any]] = []
    print(f"[PC-Calibrate] {args.model} · {len(questions)} Fragen · Budget {budget} …")
    for idx, asset in enumerate(questions, 1):
        q_id = asset.get("metadata", {}).get("id", f"q{idx}")
        prompt, _mapping = test._build_prompt(asset, seed=42 + idx)  # pylint: disable=protected-access
        result = _query_question(client, args.model, provider, prompt, budget)
        results.append(result)
        trunc_flag = " [TRUNC]" if result["truncated"] else ""
        print(
            f"  [{idx}/{len(questions)}] {q_id}: "
            f"reasoning={result['reasoning_tokens']} output={result['output_tokens']} "
            f"({result['duration_s']:.1f}s){trunc_flag}",
            flush=True,
        )
        time.sleep(PC_SLEEP_BETWEEN_REQUESTS)

    _print_report(args.model, provider, budget, results)


if __name__ == "__main__":
    main()
