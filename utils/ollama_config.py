"""
Zentrale Ollama-Konfiguration.
Lädt Hardware-Limits aus der `benchmark_config.yaml` (SSOT).
"""
from pathlib import Path
import yaml

# Lade Konfiguration zentral aus der YAML-Datei
# Das verhindert, dass User in utils-Dateien editieren müssen.
ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "benchmark_config.yaml"

def _load_context_window():
    """Liest context_window sicher aus benchmark_config.yaml."""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return int(data.get("providers", {}).get("local", {}).get("config", {}).get("context_window", 8192))
    except Exception:
        pass  # Silent fallback
    
    return 8192  # Absoluter Fallback

def get_generation_defaults() -> dict:
    """Lädt globale Generation-Defaults aus benchmark_config.yaml."""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("defaults", {}).get("generation", {})
    except Exception:
        pass
    
    # Hardcoded Fallback if config breaks
    return {
        "temperature": 0.1,
        "repeat_penalty": 1.1,
        "top_k": 40,
        "top_p": 0.9,
    }

# ==============================================================================
# OLLAMA DYNAMIC CONFIGURATION
# ==============================================================================
OLLAMA_NUM_CTX = _load_context_window()
GLOBAL_GEN_DEFAULTS = get_generation_defaults()

# Benchmark-Options für Coding & Logik (temperature=0.1)
CODING_BENCHMARK_OPTIONS = {
    "temperature": 0.1,  # Deterministisch für Code
    "num_predict": 8192,  # Fixierte Max-Tokens für Output
    "num_ctx": OLLAMA_NUM_CTX,  # Dynamische Context Size aus YAML
    "top_k": 10,  # Reduzierte Sampling-Varianz
    "repeat_penalty": 1.1,  # Leichte Penalty gegen Loops (erforderlich für Cogito/Qwen)
    "seed": 42,  # Reproduzierbarer Seed
}

# Benchmark-Options für UX Writing & Kreatives (temperature=0.3)
# Etwas mehr Spielraum als Coding, aber immer noch stabil genug für Vergleiche
CREATIVE_BENCHMARK_OPTIONS = {
    "temperature": 0.3,  # Leichte Varianz erlaubt
    "num_predict": 8192,
    "num_ctx": OLLAMA_NUM_CTX,  # Dynamische Context Size aus YAML
    "top_k": 20,  # Etwas mehr Auswahl bei Tokens
    "repeat_penalty": 1.1,  # Leichte Penalty gegen Loops (wichtig für UX!)
    "seed": 42,
}

# Legacy Alias für Rückwärtskompatibilität
BENCHMARK_OPTIONS = CODING_BENCHMARK_OPTIONS

# Kreative Options für Content-Generierung (NICHT für Benchmarks!)
CREATIVE_OPTIONS = {
    "temperature": 0.7,
    "num_predict": 4000,
    "top_k": 40,
    "top_p": 0.9,
    "repeat_penalty": 1.1,
}

# Erklärung der Parameter
PARAMETER_DOCS = """
temperature (0.0-2.0):
    - 0.1: Deterministisch, für Benchmarks
    - 0.7: Ausgewogen, für kreative Aufgaben
    - 1.5: Sehr kreativ, für Brainstorming

num_predict (int):
    Maximale Anzahl generierter Tokens
    
top_k (int):
    Anzahl der Top-Token-Kandidaten beim Sampling
    - Niedriger = konsistenter
    - Höher = diverser

repeat_penalty (float):
    Bestraft Wiederholungen
    - 1.0 = keine Penalty
    - >1.0 = weniger Wiederholungen
    
seed (int):
    Reproduzierbarer Seed für identische Outputs
"""
