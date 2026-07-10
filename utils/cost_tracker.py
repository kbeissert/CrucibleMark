import csv
import logging
from pathlib import Path
from datetime import datetime



class CostTracker:
    """Verfolgt Token-Kosten für kommerzielle APIs."""

    def __init__(self):
        self.cost_log_file = Path("outputs/cost_log.csv")

        # Ensure outputs directory exists
        self.cost_log_file.parent.mkdir(parents=True, exist_ok=True)

        self._init_csv()
        self._migrate_csv_add_call_type()

    def _init_csv(self):
        """Initialisiert die CSV-Logdatei, falls sie nicht existiert."""
        if not self.cost_log_file.exists():
            with open(self.cost_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "date",
                        "provider",
                        "model",
                        "input_tokens",
                        "output_tokens",
                        "cost_usd",
                        "call_type",
                    ]
                )

    def _migrate_csv_add_call_type(self):
        """Fügt die Spalte 'call_type' zu bestehenden CSV-Dateien ohne diese Spalte hinzu."""
        if not self.cost_log_file.exists():
            return
        try:
            with open(self.cost_log_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and "call_type" in reader.fieldnames:
                    return  # Bereits migriert
                rows = list(reader)
            # Neue Datei mit call_type-Spalte schreiben
            backup = self.cost_log_file.with_suffix(".csv.bak_migration")
            import shutil

            shutil.copy2(self.cost_log_file, backup)
            with open(self.cost_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "date",
                        "provider",
                        "model",
                        "input_tokens",
                        "output_tokens",
                        "cost_usd",
                        "call_type",
                    ]
                )
                for row in rows:
                    writer.writerow(
                        [
                            row.get("timestamp", ""),
                            row.get("date", ""),
                            row.get("provider", ""),
                            row.get("model", ""),
                            row.get("input_tokens", 0),
                            row.get("output_tokens", 0),
                            row.get("cost_usd", "0.000000"),
                            row.get("call_type", "benchmark"),  # Altdaten → benchmark
                        ]
                    )
            logging.getLogger(__name__).info(
                "cost_log.csv migriert: call_type-Spalte hinzugefügt (%d Zeilen). Backup: %s",
                len(rows),
                backup.name,
            )
        except Exception as e:
            logging.getLogger(__name__).error("CSV-Migration fehlgeschlagen: %s", e)

    def calculate_cost(
        self, provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Berechnet die Kosten für einen Request.

        Lookup-Reihenfolge:
          1. Model Card JSON (benchmark_scores/model_cards/*.json) — SSoT
          2. Kein Preis gefunden → Warning-Log, return 0.0
        """
        # 1. Model Card (SSoT)
        try:
            from utils.model_utils import _find_card  # lazy import – avoids circular
            import json as _json

            card_path = _find_card(model)
            if card_path.exists():
                with open(card_path, encoding="utf-8") as f:
                    card = _json.load(f)
                in_per_m = card.get("input_price_per_1m")
                out_per_m = card.get("output_price_per_1m")
                if isinstance(in_per_m, (int, float)) and isinstance(out_per_m, (int, float)):
                    return round(
                        (input_tokens / 1_000_000) * float(in_per_m)
                        + (output_tokens / 1_000_000) * float(out_per_m),
                        6,
                    )
                # Card vorhanden, aber keine Preise (z.B. lokales Modell)
                logging.getLogger(__name__).debug(
                    "Keine Preise für Modell '%s' (%s): Model Card vorhanden "
                    "aber input_price_per_1m/output_price_per_1m=0.0 (lokales GGUF-Modell). "
                    "Kosten werden mit 0.0 USD berechnet.",
                    model,
                    provider,
                )
                return 0.0
        except Exception:
            pass

        logging.getLogger(__name__).info(
            "Keine Model Card für '%s' (%s): Preis nicht angegeben, Kosten werden mit 0.0 USD berechnet.",
            model,
            provider,
        )
        return 0.0

    def track_request(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        call_type: str = "benchmark",
    ):
        """Loggt einen Request und die entstandenen Kosten.

        Args:
            call_type: Art des Aufrufs.
                - ``"benchmark"``            – Reguläre Benchmark-Auswertung
                - ``"overhead_ping"``         – Konnektivitäts-Ping (make list-models)
        """
        cost = self.calculate_cost(provider, model, input_tokens, output_tokens)

        now = datetime.now()
        timestamp = now.isoformat()
        date_str = now.strftime("%Y-%m-%d")

        try:
            with open(self.cost_log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        timestamp,
                        date_str,
                        provider,
                        model,
                        input_tokens,
                        output_tokens,
                        f"{cost:.6f}",
                        call_type,
                    ]
                )
        except Exception as e:
            logging.error(f"Failed to write cost log: {e}")

        return cost

    def get_spend_breakdown(
        self, provider: str, date_str: str | None = None
    ) -> dict[str, float]:
        """Gibt {call_type: Gesamtkosten} für einen Provider (optional: Tag) zurück."""
        if not self.cost_log_file.exists():
            return {}

        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        breakdown: dict[str, float] = {}
        try:
            with open(self.cost_log_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("date") != date_str or row.get("provider") != provider:
                        continue
                    ctype = row.get("call_type", "benchmark")
                    try:
                        breakdown[ctype] = breakdown.get(ctype, 0.0) + float(
                            row["cost_usd"]
                        )
                    except (ValueError, KeyError):
                        pass
        except Exception as e:
            logging.error(f"Error reading cost log for breakdown: {e}")

        return breakdown
