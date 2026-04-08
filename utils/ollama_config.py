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

# Hardcoded safety overrides for models with known native context limits.
# YAML values can still override these defaults if needed.
DEFAULT_MODEL_CONTEXT_OVERRIDES = {
    "dolphin-mistral-nemo": 4096,
}


def _load_context_window():
    """Liest context_window sicher aus benchmark_config.yaml."""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return int(
                    data.get("providers", {})
                    .get("local", {})
                    .get("config", {})
                    .get("context_window", 8192)
                )
    except Exception:
        pass  # Silent fallback

    return 8192  # Absoluter Fallback


def _load_context_overrides() -> dict:
    """Liest model_context_overrides aus benchmark_config.yaml."""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                yaml_overrides = (
                    data.get("providers", {})
                    .get("local", {})
                    .get("config", {})
                    .get("model_context_overrides", {})
                )
                merged_overrides = DEFAULT_MODEL_CONTEXT_OVERRIDES.copy()
                merged_overrides.update(yaml_overrides)
                return merged_overrides
    except Exception:
        pass
    return DEFAULT_MODEL_CONTEXT_OVERRIDES.copy()


def get_num_ctx_for_model(model: str) -> int:
    """Gibt den effektiven num_ctx für ein Modell zurück.

    Prüft zuerst modellspezifische Overrides (für Modelle mit eingeschränktem
    nativem Kontext), fällt sonst auf den globalen OLLAMA_NUM_CTX zurück.
    """
    model_lower = model.lower()
    for pattern, ctx in MODEL_CONTEXT_OVERRIDES.items():
        if pattern.lower() in model_lower:
            return int(ctx)
    return OLLAMA_NUM_CTX


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
MODEL_CONTEXT_OVERRIDES = _load_context_overrides()
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
