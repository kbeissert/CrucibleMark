"""
fix_cost_log.py
---------------
Retroaktive Kostenkorrektur für Benchmark-Runs bei denen cost_usd=0 geloggt wurde,
weil das Modell noch nicht in cost_limits.yaml eingetragen war.

Berechnet die Kosten aus den korrekt geloggten input_tokens / output_tokens neu
und überschreibt die cost_usd-Spalte für betroffene Zeilen.

Usage:
    python scripts/dev/fix_cost_log.py [--dry-run]
"""

import csv
import sys
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Konfiguration: Preise pro 1k Tokens
# ---------------------------------------------------------------------------
PRICES = {
    "anthropic": {
        "claude-sonnet-4-6": {"in": 0.003, "out": 0.015},
        "claude-opus-4-6": {"in": 0.015, "out": 0.075},
        "claude-sonnet-4-5-20250929": {"in": 0.003, "out": 0.015},
        "claude-opus-4-5-20251101": {"in": 0.015, "out": 0.075},
        "claude-haiku-4-5-20251001": {"in": 0.00025, "out": 0.00125},
        "claude-3-haiku-20240307": {"in": 0.00025, "out": 0.00125},
    },
}

COST_LOG = Path("outputs/cost_log.csv")
DRY_RUN = "--dry-run" in sys.argv


def calculate(provider: str, model: str, inp: int, out: int) -> float:
    p = PRICES.get(provider, {}).get(model)
    if not p:
        # Prefix-Match (z.B. claude-sonnet-4-6 trifft claude-sonnet-4-6-xxx)
        for key, rates in PRICES.get(provider, {}).items():
            if model.startswith(key):
                p = rates
                break
    if not p:
        return 0.0
    return round((inp / 1000) * p["in"] + (out / 1000) * p["out"], 6)


def main():
    rows = []
    fixed = 0
    total_recovered = 0.0

    with open(COST_LOG, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if float(row["cost_usd"]) == 0.0 and row["provider"] in PRICES:
                inp = int(row["input_tokens"])
                out = int(row["output_tokens"])
                if inp > 0 or out > 0:
                    cost = calculate(row["provider"], row["model"], inp, out)
                    if cost > 0.0:
                        if DRY_RUN:
                            print(
                                f"  WOULD FIX  {row['timestamp'][:19]}  "
                                f"{row['model']:40s}  "
                                f"in={inp:5d} out={out:5d}  "
                                f"→ ${cost:.6f}"
                            )
                        row["cost_usd"] = f"{cost:.6f}"
                        fixed += 1
                        total_recovered += cost
            rows.append(row)

    if DRY_RUN:
        print(
            f"\n--- DRY RUN: {fixed} Einträge würden korrigiert, "
            f"${total_recovered:.4f} retroaktiv gebucht ---"
        )
        return

    # Backup anlegen
    backup = COST_LOG.with_suffix(".csv.bak_cost_fix")
    shutil.copy(COST_LOG, backup)
    print(f"Backup angelegt: {backup}")

    with open(COST_LOG, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"✅ {fixed} Einträge korrigiert — ${total_recovered:.4f} retroaktiv nachgebucht."
    )
    print(f"   Log: {COST_LOG}")


if __name__ == "__main__":
    main()
