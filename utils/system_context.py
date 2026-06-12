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

    def get_editor_prompt_injection(self, run_type: str = "local", hardware_profile_key: str = "") -> str:
        """Baut den System-Prompt-Zusatz für das Meta-Review-Skript.

        hardware_profile_key: Optionaler Key aus provider_config.yaml (hardware_profile-Feld).
            Wenn gesetzt, wird das zugehörige Profil aus runner_environment.profiles geladen
            statt dem active_profile des laufenden Rechners. Dies ist der SSOT-Pfad für
            lokale Modelle, die auf einem anderen System getestet wurden (z.B. DGX Spark).
        """
        if run_type == "local":
            # SSOT: hardware_profile_key aus provider_config.yaml hat Vorrang vor active_profile.
            # So wird das Testsystem des Modells beschrieben, nicht der Review-Rechner.
            if hardware_profile_key:
                profiles = self.config.get("runner_environment", {}).get("profiles", {})
                profile = profiles.get(hardware_profile_key, self.profile)
            else:
                profile = self.profile

            desc = profile.get("description", "Apple Silicon M4, 24GB Unified Memory")
            ram = profile.get("ram_gb", "24")

            return f"""WICHTIGER SYSTEM-KONTEXT ZUR PERFORMANCE:
Dieses lokale Modell wurde native auf folgendem lokalen Referenzsystem evaluiert: {desc}. Da es auf lokaler Hardware läuft, sind Parameter-Größen und VRAM-Grenzen extrem relevant.

REGELN FÜR DEIN REVIEW IN BEZUG AUF HARDWARE:
1. Erwähne diese exakte Hardware-Spezifikation ({desc}) genau EINMAL einführend im Fazit oder im Abschnitt zur Geschwindigkeit. Verweise darauf, dass es sich um ein LOKALES Modell handelt.
2. Nutze im restlichen Text ausschließlich den neutralen Begriff "das Testsystem".
3. Minimiere Aussagen über absolute Dauer. Nutze stattdessen die bereitgestellten t/s (Tokens per Second) als primäre Metrik und setze sie ins Verhältnis zur Speichergrenze von {ram}GB (Swapping-Risiken bei großen Modellen)."""

        elif run_type == "commercial":
            return """WICHTIGER KONTEXT ZUR PERFORMANCE (KOMMERZIELL/CLOUD):
Dieses kommerzielle/API-basierte Modell der großen Anbieter (z.B. OpenAI, Anthropic, Google, Mistral, xAI) erzeugt Kosten und läuft vollständig in der Cloud des Herstellers. Lokale Hardware spielt KEINE Rolle.

REGELN FÜR DEIN REVIEW IN BEZUG AUF CLOUD-HARDWARE:
1. Erwähne explizit, dass es sich um ein kommerzielles Cloud-Modell handelt und nenne den Hersteller (z.B. "Anthropic-API", "OpenAI-API", "Google Gemini API") — der Leser muss erkennen, dass das Modell über eine Hersteller-Cloud betrieben wurde.
2. Erwähne unter keinen Umständen lokale Hardware. Verbotene Begriffe in diesem Review sind insbesondere:
   - "Apple Silicon", "M4", "M3", "M2", "M1"
   - "MacBook", "lokal", "Testsystem", "lokal betrieben"
   - "24 GB", "VRAM", "Unified Memory", "RAM"
   - "Swapping", "Offloading"
   - "Hardware-Ceiling", "GPU-Kapazität"
   Wenn dir einer dieser Begriffe in den Text rutscht, ist das ein Fehler — der Benchmark lief auf Cloud-Servern des Herstellers, nicht auf der Hardware des Reviewers.
3. Evaluiere die Geschwindigkeit (API-Latenz in t/s) primär in Relation zur Preis-Leistung (Preis pro 1M Token), der Latenz und der Stabilität der API. Nackte t/s-Werte sind hier Cloud-Cluster-Performance, keine Aussage über das Testsystem."""

        elif run_type == "cloud_open_weights":
            return """WICHTIGER KONTEXT ZUR PERFORMANCE (CLOUD OPEN-WEIGHTS / PROXY):
Dieses Modell ist ein auf offenen Gewichten basierendes Modell (Open-Weights), das über einen Cloud-Anbieter (z.B. Groq, OpenRouter) oder als API-Proxy läuft. Die Rechenlast wird vollständig in die Cloud des Anbieters ausgelagert.

REGELN FÜR DEIN REVIEW IN BEZUG AUF CLOUD-HARDWARE:
1. Mache unbedingt für den Leser klar, dass es sich hier um ein "Cloud Open-Weights"-Modell handelt und nenne den Cloud-Anbieter (z.B. "via Groq", "via OpenRouter") — nicht nur "über Cloud-Provider", sondern konkret.
2. Erwähne unter keinen Umständen lokale Hardware. Verbotene Begriffe in diesem Review sind insbesondere:
   - "Apple Silicon", "M4", "M3", "M2", "M1"
   - "MacBook", "lokal", "Testsystem", "lokal betrieben", "lokal evaluiert", "lokales Referenzsystem"
   - "24 GB", "VRAM", "Unified Memory", "RAM"
   - "Swapping", "Offloading"
   - "Hardware-Ceiling", "GPU-Kapazität"
   Wenn dir einer dieser Begriffe in den Text rutscht, ist das ein Fehler — der Benchmark lief auf Cloud-Cluster-Hardware (z.B. Groq LPU) plus Netzwerk-Latenz, nicht auf dem Rechner des Reviewers.
3. Behandle die ermittelte Geschwindigkeit (t/s) als Benchmark für den jeweiligen Cloud-Infrastruktur-Anbieter. Bei Groq sind das z.B. LPU-Werte, die in dieser Größenordnung mit Consumer-Hardware nicht reproduzierbar wären. Diese Einordnung ist Pflicht."""

        return ""
