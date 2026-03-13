# Tech Context

## Stack & Tools
- Python 3.12, venv, pytest (`-v --tb=short`)
- `pandas-stubs` als verbindliche Dependency für Typechecking
- VS Code: `files.trimTrailingWhitespace` und `files.insertFinalNewline` → `true`

## Build & Config
- Globale Defaults: `benchmark_config.yaml` unter `defaults.generation`
- Modul-Overrides: `benchmark_modules/*/config.yaml` unter `generation`
- Runtime-Merge: `test.py` lädt Global, updated mit Modul-Config, übergibt an Client

## LLM Judge – Stack
- Location: `utils/scoring/llm_judge/`
- Provider: Anthropic, Mistral, OpenAI (via API Key env vars), Ollama (no auth)
- Scoring Scale: Konfigurierbar (3 / 5 / 10), Default: 5
- Output-Felder: `llm_judge_score`, `llm_judge_reasoning` im Result-JSON
