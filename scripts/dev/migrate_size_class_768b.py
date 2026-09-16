#!/usr/bin/env python3
"""One-off-Migration: Size-Class-Frontier-Grenze 75B → 768B (Session 105, 2026-09-14).

Stellt die Taxonomie-Entscheidung um: Frontier = Datacenter-Niveau
(params_total_b > 768B oder unbekannt bei proprietären/API-only-Modellen).

Begründung (512GB-Single-Box-Anker): 768B × ~0,6 GB/B (Q4_K_M) ≈ 460 GB —
fit in die größte lokale Single-Box-Klasse (Mac Studio Ultra 512GB unified,
1,2 TB/s). Alles darüber erfordert Multi-GPU-Racks/Datacenter. Modelle
36–768B sind lokal auf Server-Klasse betreibbar → Tier "Server".

Was das Skript tut (--apply, sonst Dry-Run):
1. config/classification_taxonomy.json: thresholds_b [4,9,22,35,75] →
   [4,9,22,35,768], Server/Frontier-Beschreibungen, Klassifikationsregeln.
2. Alle Model-Cards: PARAM_FIXES schließt die drei Datenlücken (open-weights
   ohne params_total_b); danach wird size_class params-getrieben neu
   berechnet und nur bei Abweichung atomar geschrieben (SSoT-Writer
   utils.io_helpers.atomic_write_json — indent 2, Trailing-Newline).
3. tests/test_size_class_taxonomy_ssot.py: Grenzfall-Assertions auf die neue
   Schwelle (exakte String-Ersetzungen, Abbruch bei Nicht-Treffer).

Preflight: bricht ab, solange Benchmark-Prozesse laufen (Race-Condition-Regel)
— Override mit --force.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from utils.io_helpers import atomic_write_json, atomic_write_text  # noqa: E402

TAXONOMY_PATH = ROOT / "config" / "classification_taxonomy.json"
CARDS_DIR = ROOT / "benchmark_scores" / "model_cards"
TESTS_PATH = ROOT / "tests" / "test_size_class_taxonomy_ssot.py"

NEW_THRESHOLDS: list[int] = [4, 9, 22, 35, 768]
NON_FALLBACK_TIERS = ("Nano", "Edge", "Desktop", "Workstation", "Server")

# Datenlücken (open-weights ohne params_total_b), Quellen:
# - qwen/qwen3.8-flash: offene Basis Qwen3.8-Flash-Next = 125B-A6B MoE
#   (LLMCheck-Index, offizielle GGUF/NVFP4-Quants; getesteter Build ist der
#   Cloud-Production-Endpoint, Card-Rationale dokumentiert die Basis).
# - z-ai/glm-4.6: 355B/A32B MoE (Unsloth: ~205GB RAM für 4-bit; GLM-4.7-Card
#   hat dieselbe Architektur 355/32). Card hatte fälschlich dense.
# - minimax/minimax-m2.7-20260318: 229B/10B MoE (Groq/NVIDIA/MiniMax-Paper:
#   229-230B total, ~10B aktiv, 256 Experten).
PARAM_FIXES: dict[str, dict[str, Any]] = {
    "qwen/qwen3.8-flash": {
        "params_total_b": 125.0,
        "params_active_b": 6.0,
        "parameter_architecture": "moe",
    },
    "z-ai/glm-4.6": {
        "params_total_b": 355.0,
        "params_active_b": 32.0,
        "parameter_architecture": "moe",
    },
    "minimax/minimax-m2.7-20260318": {
        "params_total_b": 229.0,
        "params_active_b": 10.0,
        "parameter_architecture": "moe",
    },
}

TAXONOMY_SERVER_DESC = (
    "Multi-GPU-Server, dedizierte KI-Server (256–768 GB Speicherklasse) oder "
    "High-End-Cloud-Instanzen. Umfasst große MoE-Modelle (36–768B total), die "
    "dedizierte Server-Hardware erfordern, aber lokal betreibbar bleiben."
)
TAXONOMY_SERVER_GUIDANCE = (
    "Benchmark-Ergebnisse sollten mit Frontier-Modellen konkurrieren. Deutliche "
    "Schwächen sind kritisch zu benennen. Bei MoE (params_active_b << "
    "params_total_b) sind Leistungserwartungen am aktiven Teil kalibrieren — "
    "die Tier-Einordnung folgt der Gesamtgröße (RAM-Bedarf), nicht der Aktivität."
)
TAXONOMY_FRONTIER_LABEL = "Frontier (>768B / Datacenter-Niveau / API-Only)"
TAXONOMY_FRONTIER_DESC = (
    "Modelle jenseits des lokalen Single-Box-Betriebs (params_total_b > 768B — "
    "Q4-Footprint ≈ 460GB+ übersteigt die 512GB-Single-Box-Klasse) oder "
    "proprietäre Cloud-Modelle ohne bekannte Parameterzahl."
)
TAXONOMY_FRONTIER_GUIDANCE = (
    "Höchste Erwartungen. Dies ist die Referenzklasse des Benchmarks. Vergleiche "
    "mit anderen Frontier-Modellen sind der primäre Bewertungsrahmen. Für "
    "Datacenter-MoE (>768B, offene Gewichte) gilt: nicht mehr lokal auf "
    "Single-Box-Hardware betreibbar."
)
RULES_API_ONLY_FALLBACK = (
    "Frontier gilt, wenn params_total_b unbekannt ist (proprietäre/API-only "
    "Cloud-Modelle) oder params_total_b > 768B. Offene Gewichte mit bekannten "
    "params_total_b bekommen den params-basierten Tier unabhängig von der "
    "Cloud-Verfügbarkeit (deployment_type). Offene Gewichte OHNE bekannte "
    "params_total_b lösen eine Validator-Warnung aus statt still in den "
    "Frontier-Fallback zu rutschen."
)
RULES_BOUNDARY_RATIONALE = (
    "Grenze 768B: 768B × ~0,6 GB/B (Q4_K_M) ≈ 460 GB → passt mit Headroom in "
    "die 512GB-Single-Box-Klasse (Mac Studio Ultra 512GB unified, 1,2 TB/s). "
    "Alles darüber erfordert Multi-GPU-Racks/Datacenter und gilt als "
    "Datacenter-Niveau. Entscheidung 2026-09-14 (Session 105), Belege: "
    "DeepSeek-V3 671B >20 tok/s auf 512GB M3 Ultra (Awni Hannun, 2025-03), "
    "GLM-5.3 744B lokal auf 512GB (antirez), Qwen3-235B Q4 ~30 tok/s "
    "Dauereinsatz (HN-Berichte 2026)."
)

TEST_PATCHES: tuple[tuple[str, str], ...] = (
    (
        '    assert sc["thresholds_b"] == [4, 9, 22, 35, 75]',
        '    assert sc["thresholds_b"] == [4, 9, 22, 35, 768]',
    ),
    (
        '    (75.5, "Frontier"),\n'
        '    (120.0, "Frontier"),\n'
        '    (405.0, "Frontier"),  # Llama 3.1 405B\n',
        '    (768.0, "Server"),    # inklusive Grenze (512GB-Single-Box-Anker)\n'
        '    (768.5, "Frontier"),\n'
        '    (120.0, "Server"),    # gpt-oss-120b: lokal betreibbar (MoE, 5.1B aktiv)\n'
        '    (405.0, "Server"),    # Llama 3.1 405B\n'
        '    (1000.0, "Frontier"), # Kimi K2 1T: jenseits 512GB-Single-Box\n',
    ),
    (
        '    assert get_model_size_class("x") == "Frontier"',
        '    assert get_model_size_class("x") == "Server"',
    ),
)


def tier_for_params(params_b: float) -> str:
    """Tier nach NEUEN Schwellwerten (inklusive obere Grenze, Frontier als Fallback)."""
    for threshold, tier in zip(NEW_THRESHOLDS, NON_FALLBACK_TIERS, strict=True):
        if params_b <= threshold:
            return tier
    return "Frontier"


def assert_benchmark_idle(force: bool) -> None:
    """Race-Condition-Regel: keine Migration während eines Benchmark-Laufs."""
    try:
        out = subprocess.run(
            ["pgrep", "-f", r"benchmark_auto\.py|run_benchmark\.py"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return
    pids = [line.strip() for line in out.stdout.splitlines() if line.strip()]
    if pids and not force:
        sys.exit(
            f"ABBRUCH: Benchmark-Prozesse aktiv (PIDs: {', '.join(pids)}). "
            "Race-Condition-Regel — Migration erst nach Batch-Ende anwenden "
            "(oder --force mit Bewusstsein für Judge-Kontext-Drift)."
        )


def patch_taxonomy(data: dict) -> None:
    sc = data["size_class"]
    sc["thresholds_b"] = NEW_THRESHOLDS
    sc["description"] = (
        "Deployment-Hardware-Tier des Modells – leitet sich aus der "
        "Gesamt-Parameterzahl (params_total_b) ab; Frontier (>768B, "
        "Datacenter-Niveau) greift bei unbekannter Parameterzahl nur für "
        "proprietäre/API-only Cloud-Modelle. SSoT für Tier-Reihenfolge, "
        "Schwellwerte, Klassifikationsregeln und Reviewer-Hinweise. Konsumiert "
        "von utils.model_utils.get_model_size_class(), Card-Vocabulary-"
        "Validierung, Card-Validator (validate_model_cards.py) und "
        "Reviewer-Prompt-Generator (format_classification_context)."
    )
    rules = sc["classification_rules"]
    rules["api_only_fallback"] = RULES_API_ONLY_FALLBACK
    rules["boundary_rationale"] = RULES_BOUNDARY_RATIONALE

    server = sc["values"]["Server"]
    server["max_params_b"] = 768
    server["label"] = "Server (36–768B Parameter)"
    server["description"] = TAXONOMY_SERVER_DESC
    server["reviewer_guidance"] = TAXONOMY_SERVER_GUIDANCE

    frontier = sc["values"]["Frontier"]
    frontier["min_params_b"] = 769
    frontier["label"] = TAXONOMY_FRONTIER_LABEL
    frontier["description"] = TAXONOMY_FRONTIER_DESC
    frontier["reviewer_guidance"] = TAXONOMY_FRONTIER_GUIDANCE


def patch_tests() -> bool:
    """Grenzfall-Assertions im SSOT-Test auf 768B heben (exakte Treffer)."""
    text = TESTS_PATH.read_text(encoding="utf-8")
    for old, new in TEST_PATCHES:
        count = text.count(old)
        if count != 1:
            print(f"  [ABBRUCH] Test-Patch-Muster nicht eindeutig gefunden ({count}x): {old!r}")
            return False
        text = text.replace(old, new)
    atomic_write_text(TESTS_PATH, text)
    return True


def _parse_params(params: object) -> float | None:
    """params_total_b als positive Zahl, sonst None (analog Laufzeit-Kaskade)."""
    if params is None:
        return None
    try:
        params_f = float(params)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return params_f if params_f > 0 else None


def migrate_cards(*, write: bool) -> tuple[list[str], list[str]]:
    """Cards params-getrieben neu klassifizieren; nur bei write=True Dateien schreiben."""
    changed: list[str] = []
    warnings: list[str] = []
    for card_path in sorted(CARDS_DIR.glob("*.json")):
        original = json.loads(card_path.read_text(encoding="utf-8"))
        card = dict(original)
        model_id = str(card.get("model_id") or card_path.stem)

        fix = PARAM_FIXES.get(model_id)
        if fix is not None:
            for key, value in fix.items():
                card[key] = value

        params_f = _parse_params(card.get("params_total_b"))
        size_note: str | None = None
        if params_f is not None:
            expected = tier_for_params(params_f)
            if card.get("size_class") != expected:
                size_note = (
                    f"size_class {card.get('size_class')} → {expected} "
                    f"(params={params_f:g}B)"
                )
                card["size_class"] = expected
        elif card.get("weights_license_tier") in ("open-weights", "restricted-weights"):
            warnings.append(
                f"{model_id}: open-weights ohne params_total_b bleibt im "
                "Frontier-Fallback — Datenlücke schließen!"
            )

        if card != original:
            if write:
                atomic_write_json(card_path, card)
            if size_note:
                changed.append(f"{model_id}: {size_note}")
            elif fix is not None:
                changed.append(f"{model_id}: PARAM_FIXES eingetragen (Tier unverändert)")
            else:
                changed.append(f"{model_id}: Felder aktualisiert")
    return changed, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Änderungen schreiben (sonst Dry-Run)")
    parser.add_argument("--force", action="store_true", help="Benchmark-Preflight übersteuern")
    args = parser.parse_args()

    assert_benchmark_idle(args.force)
    data = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))

    print("== Dry-Run ==" if not args.apply else "== Migration (apply) ==")
    patch_taxonomy(data)
    thresholds = data["size_class"]["thresholds_b"]
    print(f"Taxonomie: thresholds_b={thresholds}")

    if args.apply:
        atomic_write_json(TAXONOMY_PATH, data)
        if not patch_tests():
            sys.exit("ABBRUCH: Test-Patch fehlgeschlagen — Taxonomie wurde bereits geschrieben.")
    else:
        print("Tests: 3 exakte Grenzfall-Patches würden angewendet.")

    changed, warnings = migrate_cards(write=args.apply)
    suffix = "" if args.apply else " (Dry-Run — NICHT geschrieben)"
    print(f"\nCards geändert ({len(changed)}){suffix}:")
    if not changed:
        print("  keine — Cards sind bereits auf dem Zielstand.")
    for line in changed:
        print(f"  {line}")
    if warnings:
        print(f"\nWARNUNG — offene Datenlücken ({len(warnings)}):")
        for line in warnings:
            print(f"  {line}")
    print("\nNachlauf empfohlen: make validate-cards && make lint && make test && make leaderboard")


if __name__ == "__main__":
    main()
