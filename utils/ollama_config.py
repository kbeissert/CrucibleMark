"""
Zentrale Ollama-Konfiguration für alle Benchmark-Systeme.

Verwendet deterministische Settings für reproduzierbare Ergebnisse.
"""

# Benchmark-Options für Coding & Logik (temperature=0.1)
CODING_BENCHMARK_OPTIONS = {
    "temperature": 0.1,  # Deterministisch für Code
    "num_predict": 8192,  # Fixierte Max-Tokens für Konsistenz
    "top_k": 10,  # Reduzierte Sampling-Varianz
    "repeat_penalty": 1.1,  # Leichte Penalty gegen Loops (erforderlich für Cogito/Qwen)
    "seed": 42,  # Reproduzierbarer Seed
}

# Benchmark-Options für UX Writing & Kreatives (temperature=0.3)
# Etwas mehr Spielraum als Coding, aber immer noch stabil genug für Vergleiche
CREATIVE_BENCHMARK_OPTIONS = {
    "temperature": 0.3,  # Leichte Varianz erlaubt
    "num_predict": 8192,
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
