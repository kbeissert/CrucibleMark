import yaml

class SystemContextManager:
    """Manages the context around the hardware testing system and commercial costs."""

    def __init__(self, config_path: str = "benchmark_config.yaml"):
        # Load from config, defaulting to an empty dict if not found
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        except Exception:
            self.config = {}

        env = self.config.get("runner_environment", {})
        active = env.get("active_profile", "unknown")
        self.profile = env.get("profiles", {}).get(active, {})

    @staticmethod
    def calculate_tps(tokens_used: int, execution_time_s: float) -> float:
        """Kalkuliert Tokens per Second, fängt Division durch 0 ab."""
        if execution_time_s <= 0 or not tokens_used:
            return 0.0
        return round(float(tokens_used) / float(execution_time_s), 2)

    def get_editor_prompt_injection(self, run_type: str = "local") -> str:
        """Baut den System-Prompt-Zusatz für das Meta-Review-Skript."""
        if run_type == "local":
            desc = self.profile.get("description", "Apple Silicon M4, 24GB Unified Memory")
            ram = self.profile.get("ram_gb", "24")

            return f"""WICHTIGER SYSTEM-KONTEXT ZUR PERFORMANCE:
Dieses lokale Modell wurde auf folgendem Referenzsystem evaluiert: {desc}.

REGELN FÜR DEIN REVIEW IN BEZUG AUF HARDWARE:
1. Erwähne diese exakte Hardware-Spezifikation ({desc}) genau EINMAL einführend im Fazit oder im Abschnitt zur Geschwindigkeit.
2. Nutze im restlichen Text ausschließlich den neutralen Begriff "das Testsystem".
3. Minimiere Aussagen über absolute Dauer. Nutze stattdessen die bereitgestellten t/s (Tokens per Second) als primäre Metrik und setze sie ins Verhältnis zur Speichergrenze von {ram}GB (Swapping-Risiken bei großen Modellen)."""
        elif run_type == "commercial":
            return """WICHTIGER KONTEXT ZUR PERFORMANCE (KOMMERZIELL):
Dieses kommerzielle/API-basierte Modell erzeugt Kosten. Evaluiere die Geschwindigkeit (API-Latenz in t/s) immer in Relation zur Preis-Leistung (Preis pro 1M Token)."""

        return ""
