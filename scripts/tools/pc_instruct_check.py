#!/usr/bin/env python3
"""
PC Instruct-Vorab-Check (Coverage-Regel, docs/POLITICAL_COMPASS_KONZEPT.md Abschn. 11)
=======================================================================================
Prüft vor einem Instruct-Ersatz-Lauf:
  1. Content-Hygiene: keine Channel-Token-/Think-Tag-Reste im Content (--reasoning off)
  2. Reasoning-Freiheit: reasoning_tokens == 0 (Instruct-Modus aktiv)
  3. Antwortvergleich: gleiche Fragen + gleiche Seeds wie der Thinking-Run
     (run_seed aus dem Checkpoint) → per-Frage-Agreement + Buchstaben-Verteilung

Verwendung (NACH dem Stoppen des Thinking-Runs — der Server wird automatisch
mit --reasoning off neu gestartet):
    .venv/bin/python scripts/tools/pc_instruct_check.py \
        --model gemma-4-12b-it-ud-q6_k_xl-instruct-spark

Das Thinking-Modell (Checkpoint-Pfad) wird über das Attribution-Mapping
(result_attribution in der PC-Modul-Config) aufgelöst — explizit überschreibbar:
    --thinking-model <original-id>
"""

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from benchmark_modules.political_compass.core.io_manager import (  # noqa: E402
    CheckpointManager,
)
from benchmark_modules.political_compass.test import (  # noqa: E402
    PoliticalCompassTest,
    question_seed,
)
from utils.config_validator import ConfigValidator  # noqa: E402
from utils.llm_client import LLMClient  # noqa: E402
from utils.model_id_base import resolve_provider  # noqa: E402

# Channel-Token-/Think-Reste im Content (Instruct-Modus muss clean sein)
_CONTAMINATION_PATTERNS = (
    re.compile(r"<\|channel\|>"), re.compile(r"<\|start\|>"), re.compile(r"<think>"),
    re.compile(r"</think>"), re.compile(r"<\|message\|>"),
)


def _load_thinking_answers(thinking_model: str) -> tuple[dict[str, str], int | None]:
    """Thinking-Antworten + Run-1-Seed aus dem Thinking-Checkpoint (SSoT-Pfad)."""
    cp_path = CheckpointManager.get_checkpoint_path(thinking_model)
    if not cp_path.exists():
        return {}, None
    cp = json.loads(cp_path.read_text(encoding="utf-8"))
    answers: dict[str, str] = {}
    for key, val in (cp.get("detailed_responses") or {}).items():
        if not key.startswith("1_"):
            continue
        letter = (val.get("answer") or "").strip()[:1]
        if letter and not (val.get("answer") or "").startswith("REFUSAL"):
            answers[val.get("id", "")] = letter
    seeds = cp.get("run_seeds") or {}
    return answers, seeds.get("1")


def _resolve_thinking_model(args: argparse.Namespace) -> str:
    """Thinking-Modell-ID: explizit oder via Attribution-Mapping (SSoT)."""
    if args.thinking_model:
        return args.thinking_model
    from utils.scoring.political_compass_handler import PoliticalCompassHandler
    thinking_model = PoliticalCompassHandler._resolve_result_attribution(args.model)
    if not thinking_model:
        raise SystemExit(
            "Kein Thinking-Modell ableitbar — --thinking-model angeben "
            "(Attributions-Mapping fehlt für diese Instruct-ID)."
        )
    return thinking_model


def _run_checks(
    test: PoliticalCompassTest,
    client: LLMClient,
    args: argparse.Namespace,
    provider: str,
    budget: int,
    thinking_answers: dict[str, str],
    run_seed: int,
) -> dict[str, Any]:
    """Führt die Instruct-Checks aus und liefert die Zähler-Ergebnisse."""
    questions_by_block, sorted_blocks = test._group_questions_by_block()  # pylint: disable=protected-access

    result: dict[str, Any] = {
        "checked": 0, "contaminated": 0, "reasoning_leak": 0,
        "agreements": 0, "compared": 0,
        "instruct_letters": Counter(), "thinking_letters": Counter(),
    }
    print(f"[Instruct-Check] {args.model} · {args.num_questions} Fragen · Seed {run_seed}")
    for block_id in sorted_blocks:
        for asset in questions_by_block[block_id]:
            if result["checked"] >= args.num_questions:
                break
            q_id = asset["metadata"]["id"]
            prompt, mapping = test._build_prompt(asset, seed=question_seed(run_seed, q_id))  # pylint: disable=protected-access

            response = client.query(
                model=args.model, prompt=prompt, provider=provider,
                system="", temperature=0.1, max_tokens=budget,
                _module_key="political_compass",
            )
            metadata = getattr(client, "last_response_metadata", {}) or {}
            reasoning_tokens = int(metadata.get("reasoning_tokens") or 0)
            content = response or ""

            hits = [p.pattern for p in _CONTAMINATION_PATTERNS if p.search(content)]
            letter = test.evaluator_vanilla._parse_choice(  # pylint: disable=protected-access
                content, list(mapping.keys()), strict=True,
            )
            # Display-Buchstabe → Original-Key (der Thinking-Checkpoint speichert
            # Original-Keys, nicht die gemischten Display-Buchstaben)
            orig_letter = mapping.get(letter, letter) if letter else None
            result["checked"] += 1
            if hits:
                result["contaminated"] += 1
            if reasoning_tokens:
                result["reasoning_leak"] += 1
            if orig_letter:
                result["instruct_letters"][orig_letter] += 1
            think_letter = thinking_answers.get(q_id)
            if think_letter:
                result["thinking_letters"][think_letter] += 1
                result["compared"] += 1
                if orig_letter == think_letter:
                    result["agreements"] += 1

            flag = " ⚠️" if (hits or reasoning_tokens or not letter) else ""
            print(
                f"  {q_id}: instruct={letter or '—'} thinking={think_letter or '—'}"
                f" · reasoning={reasoning_tokens} · contamination={hits or 'nein'}{flag}",
                flush=True,
            )
    return result


def _print_summary(result: dict[str, Any]) -> None:
    """Printed die Check-Zusammenfassung und beendet bei Fehlern mit Exit 1."""
    print(f"\n{'=' * 60}")
    print(f"Content-Kontamination: {result['contaminated']}/{result['checked']}  (Ziel: 0)")
    print(f"Reasoning-Leak:        {result['reasoning_leak']}/{result['checked']}  (Ziel: 0)")
    if result["compared"]:
        rate = result["agreements"] / result["compared"]
        print(f"Agreement vs. Thinking: {result['agreements']}/{result['compared']} ({rate:.0%})")
    print(f"Buchstaben-Verteilung  Instruct: {dict(sorted(result['instruct_letters'].items()))}")
    print(f"Buchstaben-Verteilung  Thinking: {dict(sorted(result['thinking_letters'].items()))}")
    if result["contaminated"] or result["reasoning_leak"]:
        print("\n❌ Instruct-Modus NICHT sauber — vor dem Ersatz-Lauf klären "
              "(--reasoning off wirksam? reasoning-format-Konflikt?)")
        sys.exit(1)
    print("\n✅ Instruct-Modus sauber — Ersatz-Lauf kann starten.")


def main() -> None:
    parser = argparse.ArgumentParser(description="PC Instruct-Vorab-Check")
    parser.add_argument("--model", required=True, help="Instruct-Modell-ID")
    parser.add_argument("--num-questions", type=int, default=8,
                        help="Anzahl Fragen (Default 8 = Block 7.1)")
    parser.add_argument("--thinking-model", default=None,
                        help="Thinking-Modell-ID des Checkpoints (Default: "
                             "Attributions-Ziel aus result_attribution)")
    args = parser.parse_args()

    thinking_model = _resolve_thinking_model(args)
    thinking_answers, run_seed = _load_thinking_answers(thinking_model)
    if not thinking_answers or run_seed is None:
        raise SystemExit(f"Kein Thinking-Checkpoint mit Run-1-Seed für '{thinking_model}' gefunden.")

    config = ConfigValidator(str(ROOT_DIR / "benchmark_config.yaml")).config
    budget = int(config.get("token_budgets", {}).get("political_compass", 800))
    provider, _ = resolve_provider(args.model)

    test = PoliticalCompassTest()
    test.load_questions()
    client = LLMClient(config=config)

    result = _run_checks(test, client, args, provider, budget, thinking_answers, run_seed)
    _print_summary(result)


if __name__ == "__main__":
    main()
