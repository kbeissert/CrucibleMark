"""
Zentrale Ollama-Konfiguration für alle Benchmark-Systeme.

Verwendet deterministische Settings für reproduzierbare Ergebnisse.
"""

# Benchmark-Options für stabiles Scoring (temperature=0.1)
BENCHMARK_OPTIONS = {
    'temperature': 0.1,      # Deterministisch für Benchmarks (default: 0.8)
    'num_predict': 4000,     # Fixierte Max-Tokens für Konsistenz (erhöht für Qwen3)
    'top_k': 10,             # Reduzierte Sampling-Varianz (default: 40)
    'repeat_penalty': 1.0,   # Keine Wiederholungs-Penalty (default: 1.1)
    'seed': 42               # Reproduzierbarer Seed (optional)
}

# Kreative Options für Content-Generierung (NICHT für Benchmarks!)
CREATIVE_OPTIONS = {
    'temperature': 0.7,
    'num_predict': 4000,
    'top_k': 40,
    'top_p': 0.9,
    'repeat_penalty': 1.1
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
