import csv
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from utils.pricing_updater import PricingUpdater, DEFAULT_TTL_DAYS


class CostTracker:
    """
    Verfolgt Token-Kosten für kommerzielle APIs und setzt Budget-Limits durch.
    Singleton-Pattern per Modul.
    """

    def __init__(self, config_path: str = "config/cost_limits.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.cost_log_file = Path(
            self.config.get("settings", {}).get("cost_log_file", "outputs/cost_log.csv")
        )

        # Ensure outputs directory exists
        self.cost_log_file.parent.mkdir(parents=True, exist_ok=True)

        self.warning_threshold = self.config.get("settings", {}).get(
            "budget_warning_threshold", 0.8
        )
        self._init_csv()
        self._migrate_csv_add_call_type()

        # Preise bei Bedarf aus LiteLLM Pricing DB aktualisieren.
        # TTL kann in cost_limits.yaml unter settings.pricing_ttl_days überschrieben werden.
        ttl_days = self.config.get("settings", {}).get(
            "pricing_ttl_days", DEFAULT_TTL_DAYS
        )
        self.pricing_updater = PricingUpdater()
        self.pricing_updater.ensure_fresh(ttl_days=ttl_days)

    def _load_config(self) -> Dict[str, Any]:
        """Lädt die Kosten-Konfiguration."""
        if not self.config_path.exists():
            logging.warning(
                f"Cost config not found at {self.config_path}. Using empty config."
            )
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logging.error(f"Error loading cost config: {e}")
            return {}

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
            with open(self.cost_log_file, "r", newline="", encoding="utf-8") as f:
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
          1. LiteLLM Preis-Cache (automatisch aktuell gehalten, 7-Tage-TTL)
          2. cost_limits.yaml (Fallback für manuell gepflegte / noch nicht in
             LiteLLM enthaltene Modelle wie gpt-5, sowie Budget-Limits)
          3. Lokale Modelle / unbekannte Provider → 0.0
        """
        # 1. LiteLLM Preis-Cache
        cached = self.pricing_updater.get_price(model)
        if cached is not None:
            input_price, output_price = cached
            return round(
                (input_tokens / 1000) * input_price
                + (output_tokens / 1000) * output_price,
                6,
            )

        # 2. cost_limits.yaml (manuelle Overrides / unbekannte Modelle)
        provider_config = self.config.get("providers", {}).get(provider)
        if not provider_config:
            return 0.0  # Lokales oder unbekanntes Modell

        model_config = provider_config.get(model)
        if not model_config:
            # Längere Keys zuerst prüfen – verhindert Fehl-Matches bei Präfixen
            # z.B. "kimi-k2.5-0127" darf nicht auf "kimi-k2" statt "kimi-k2.5" matchen
            sorted_keys = sorted(
                (k for k in provider_config if k != "daily_budget"),
                key=len,
                reverse=True,
            )
            for key in sorted_keys:
                if model.startswith(key):
                    model_config = provider_config[key]
                    break

        if not model_config:
            logging.getLogger(__name__).debug(
                "Kein Preis für Modell '%s' (%s) in Cache oder cost_limits.yaml.",
                model,
                provider,
            )
            return 0.0

        input_price = model_config.get("input_cost_per_1k", 0.0)
        output_price = model_config.get("output_cost_per_1k", 0.0)
        return round(
            (input_tokens / 1000) * input_price + (output_tokens / 1000) * output_price,
            6,
        )

    def get_daily_spend(self, provider: str) -> float:
        """Berechnet die heutigen Ausgaben für einen Provider."""
        if not self.cost_log_file.exists():
            return 0.0

        today = datetime.now().strftime("%Y-%m-%d")
        total_spend = 0.0

        try:
            with open(self.cost_log_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["date"] == today and row["provider"] == provider:
                        try:
                            total_spend += float(row["cost_usd"])
                        except ValueError:
                            pass
        except Exception as e:
            logging.error(f"Error reading cost log: {e}")

        return total_spend

    def check_budget(self, provider: str) -> tuple[bool, str]:
        """
        Prüft, ob das Budget für den Provider erschöpft ist.
        Returns: (is_allowed, warning_message)
        """
        provider_config = self.config.get("providers", {}).get(provider, {})
        daily_budget = provider_config.get("daily_budget")

        if daily_budget is None:
            return True, ""

        current_spend = self.get_daily_spend(provider)

        if current_spend >= daily_budget:
            msg = f"⛔️ DAILY BUDGET EXCEEDED for {provider}. Spent: ${current_spend:.4f} / Limit: ${daily_budget:.2f}"
            logging.error(msg)
            return False, msg

        if current_spend >= daily_budget * self.warning_threshold:
            msg = f"⚠️ Budget warning for {provider}: ${current_spend:.4f} / ${daily_budget:.2f} ({int((current_spend / daily_budget) * 100)}%)"
            return True, msg

        return True, ""

    def get_remaining_budget(self, provider: str) -> Optional[float]:
        """Gibt das verbleibende Budget für den Provider zurück."""
        provider_config = self.config.get("providers", {}).get(provider, {})
        daily_budget = provider_config.get("daily_budget")

        if daily_budget is None:
            return None

        current_spend = self.get_daily_spend(provider)
        return max(0.0, daily_budget - current_spend)

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
        self, provider: str, date_str: Optional[str] = None
    ) -> Dict[str, float]:
        """Gibt {call_type: Gesamtkosten} für einen Provider (optional: Tag) zurück."""
        if not self.cost_log_file.exists():
            return {}

        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        breakdown: Dict[str, float] = {}
        try:
            with open(self.cost_log_file, "r", encoding="utf-8") as f:
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
