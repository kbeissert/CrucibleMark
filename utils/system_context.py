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
Dieses lokale Modell wurde native auf folgendem lokalen Referenzsystem evaluiert: {desc}. Da es auf lokaler Hardware läuft, sind Parameter-Größen und VRAM-Grenzen extrem relevant.

REGELN FÜR DEIN REVIEW IN BEZUG AUF HARDWARE:
1. Erwähne diese exakte Hardware-Spezifikation ({desc}) genau EINMAL einführend im Fazit oder im Abschnitt zur Geschwindigkeit. Verweise darauf, dass es sich um ein LOKALES Modell handelt.
2. Nutze im restlichen Text ausschließlich den neutralen Begriff "das Testsystem".
3. Minimiere Aussagen über absolute Dauer. Nutze stattdessen die bereitgestellten t/s (Tokens per Second) als primäre Metrik und setze sie ins Verhältnis zur Speichergrenze von {ram}GB (Swapping-Risiken bei großen Modellen)."""

        elif run_type == "commercial":
            return """WICHTIGER KONTEXT ZUR PERFORMANCE (KOMMERZIELL/CLOUD):
Dieses kommerzielle/API-basierte Modell der großen Anbieter (z.B. OpenAI, Anthropic, Google) erzeugt Kosten und läuft in der Cloud. Lokale Hardware spielt KEINE Rolle.

REGELN FÜR DEIN REVIEW IN BEZUG AUF CLOUD-HARDWARE:
1. Erwähne explizit, dass es sich um ein kommerzielles Cloud-Modell handelt.
2. Erwähne auf keinen Fall lokale Hardware (z.B. "Apple Silicon M4" oder VRAM-Bezug). Das Modell lief nicht auf lokaler Hardware!
3. Evaluiere die Geschwindigkeit (API-Latenz in t/s) primär in Relation zur Preis-Leistung (Preis pro 1M Token), der Latenz und der Stabilität der API."""

        elif run_type == "cloud_open_weights":
            return """WICHTIGER KONTEXT ZUR PERFORMANCE (CLOUD OPEN-WEIGHTS / PROXY):
Dieses Modell ist ein auf offenen Gewichten basierendes Modell (Open-Weights), das über einen Cloud-Anbieter (wie Groq, Hyperbolic) oder als API-Proxy läuft. Die Rechenlast wird vollständig in die Cloud ausgelagert.

REGELN FÜR DEIN REVIEW IN BEZUG AUF CLOUD-HARDWARE:
1. Mache unbedingt für den Leser klar, dass es sich hier um ein "Cloud Open-Weights"-Modell handelt.
2. Erwähne auf keinen Fall lokale Hardware (wie "Apple Silicon M4" oder VRAM-Swapping-Risiken). Das Modell lief nicht lokal auf der Hardware des Nutzers! Die t/s geben bei diesen Modellen meist die enorme Rechengeschwindigkeit hochoptimierter Cloud-Cluster (z.B. LPU bei Groq) plus Netzwerk-Latenz wieder.
3. Behandle die ermittelte Geschwindigkeit (t/s) daher als Benchmark für den jeweiligen Cloud-Infrastruktur-Anbieter."""

        return ""
