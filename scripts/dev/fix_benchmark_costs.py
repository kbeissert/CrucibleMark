"""
fix_benchmark_costs.py
----------------------
Retroaktive Kostenkorrektur für Benchmark-CSVs bei denen cost_usd=0.0 steht,
weil der unified_runner.py-Bug „last_cost_usd statt last_request_cost" alle
Kosten auf 0.0 gesetzt hat (gefixt in Commit 6bc33e1).

Token-Split-Heuristik:
  output_tokens ≈ response_length / 4  (chars ÷ mittlerer chars-per-token)
  input_tokens  = max(0, tokens_used - output_tokens)
  Fallback falls response_length fehlt: 70 % input / 30 % output

Lokale Modelle (provider = ollama) werden übersprungen (Kosten bleiben 0.0).

Usage:
    python scripts/dev/fix_benchmark_costs.py [--dry-run]
"""

import csv
import sys
import shutil
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
LOCAL_PROVIDERS = {"ollama"}

TARGET_CSVS = [
    Path("benchmark_scores/commercial_models_benchmark.csv"),
    Path("benchmark_scores/cloud_models_benchmark.csv"),
]

DRY_RUN = "--dry-run" in sys.argv

logging.basicConfig(
    format="%(levelname)s %(message)s",
    level=logging.DEBUG if "--verbose" in sys.argv else logging.INFO,
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val: str | None, default: float = 0.0) -> float:
    try:
        return float(val) if val not in (None, "", "nan") else default
    except (ValueError, TypeError):
        return default


def _estimate_tokens(tokens_used: float, response_length: float) -> tuple[int, int]:
    """Schätzt Input- und Output-Tokens aus Gesamttokens + Response-Länge."""
    total = max(0, int(tokens_used))
    if total == 0:
        return 0, 0

    if response_length > 0:
        # ~4 Zeichen pro Token (grober Durchschnitt für Text/Code-Mix)
        out_est = min(total, int(response_length / 4))
    else:
        # Kein response_length → 70 % Input, 30 % Output
        out_est = int(total * 0.30)

    in_est = max(0, total - out_est)
    return in_est, out_est


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_csv(csv_path: Path, tracker) -> tuple[int, float]:
    """Korrigiert cost_usd in einer CSV. Gibt (Anzahl Fixes, Summe) zurück."""
    if not csv_path.exists():
        log.warning(f"CSV nicht gefunden: {csv_path}")
        return 0, 0.0

    rows: list[dict] = []
    fixed = 0
    total_recovered = 0.0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            provider = row.get("provider", "").strip()
            model = row.get("model", "").strip()
            current_cost = _safe_float(row.get("cost_usd"))
            tokens_used = _safe_float(row.get("tokens_used"))
            response_length = _safe_float(row.get("response_length"))

            # Nur Zeilen mit cost=0.0, nicht-lokaler Provider und bekannten Tokens
            should_fix = (
                current_cost == 0.0
                and provider not in LOCAL_PROVIDERS
                and provider != ""
                and tokens_used > 0
            )

            if should_fix:
                in_tok, out_tok = _estimate_tokens(tokens_used, response_length)
                cost = tracker.calculate_cost(provider, model, in_tok, out_tok)

                if cost > 0.0:
                    log.debug(
                        f"  FIX  {row.get('timestamp', '')[:19]:20s}  "
                        f"{provider:12s}  {model:45s}  "
                        f"in={in_tok:5d} out={out_tok:5d}  → ${cost:.6f}"
                    )
                    if not DRY_RUN:
                        row["cost_usd"] = f"{cost:.6f}"
                    fixed += 1
                    total_recovered += cost
                else:
                    log.debug(
                        f"  SKIP (kein Preis)  {provider}  {model}"
                    )

            rows.append(row)

    if fixed > 0 and not DRY_RUN:
        # Backup
        backup_path = csv_path.with_suffix(".csv.bak")
        shutil.copy2(csv_path, backup_path)
        log.info(f"Backup gespeichert: {backup_path}")

        # Überschreiben
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        log.info(f"✓ {csv_path.name}: {fixed} Einträge korrigiert (${total_recovered:.4f})")
    else:
        log.info(
            f"{'[DRY RUN] ' if DRY_RUN else ''}{csv_path.name}: "
            f"{fixed} Einträge würden korrigiert (${total_recovered:.4f})"
        )

    return fixed, total_recovered


def main() -> None:
    # CostTracker importieren (initialisiert PricingUpdater automatisch)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from utils.cost_tracker import CostTracker

    tracker = CostTracker()

    total_fixed = 0
    total_amount = 0.0

    for csv_path in TARGET_CSVS:
        fixed, amount = process_csv(csv_path, tracker)
        total_fixed += fixed
        total_amount += amount

    print()
    if DRY_RUN:
        print(
            f"--- DRY RUN: {total_fixed} Einträge würden korrigiert, "
            f"${total_amount:.4f} retroaktiv gebucht ---"
        )
    else:
        print(
            f"--- Fertig: {total_fixed} Einträge korrigiert, "
            f"${total_amount:.4f} retroaktiv eingetragen ---"
        )
        if total_fixed > 0:
            print("Hinweis: Führe 'make leaderboard' aus um die Leaderboard-CSVs zu aktualisieren.")


if __name__ == "__main__":
    main()
