import csv
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


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
                    ]
                )

    def calculate_cost(
        self, provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Berechnet die Kosten für einen Request basierend auf der Config."""

        provider_config = self.config.get("providers", {}).get(provider)
        if not provider_config:
            # Fallback oder Local Models (kostenlos)
            return 0.0

        # Versuche spezifisches Modell zu finden, sonst Default-Werte suchen (falls vorhanden)
        # Hier gehen wir davon aus, dass die Struktur ist: providers -> provider -> model_name -> costs
        # Manchmal sind Model-Namen ungenau (z.B. Versionen), hier striktes Matching für V1.
        
        model_config = provider_config.get(model)

        # Relaxed matching: If exact model not found, try to match by prefix (e.g. gpt-4o matches gpt-4o-2024-05-13)
        if not model_config:
            for conf_model_key in provider_config:
                if conf_model_key == "daily_budget":
                     continue
                if model.startswith(conf_model_key):
                    model_config = provider_config[conf_model_key]
                    break
        
        if not model_config:
            # Fallback for completely unknown models to avoid 0 cost if we can verify it's the provider
            # Maybe use a "default" rate if configured?
            # For now, just return 0.0
            return 0.0

        input_price = model_config.get("input_cost_per_1k", 0.0)
        output_price = model_config.get("output_cost_per_1k", 0.0)

        cost_input = (input_tokens / 1000) * input_price
        cost_output = (output_tokens / 1000) * output_price

        return round(cost_input + cost_output, 6)

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
        self, provider: str, model: str, input_tokens: int, output_tokens: int
    ):
        """Loggt einen Request und die entstandenen Kosten."""
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
                    ]
                )
        except Exception as e:
            logging.error(f"Failed to write cost log: {e}")

        return cost
