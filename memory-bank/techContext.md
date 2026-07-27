# Tech Context

## Tech-Stack

- **Sprache:** Python 3.12
- **Runzeit:** venv (nie global installiert)
- **Testing:** pytest (`pytest -v --tb=short`)
- **Linting:** ruff + Pylint
- **Typisierung:** mypy-kompatibel, Type-Hints in ALLEN neuen Funktionen
- **Build/Make:** Makefile als SSoT für Commands

## Konfig-Hierarchie

1. **Global:** `benchmark_config.yaml` (Token-Budgets, Module-Konfiguration)
2. **Modul:** `config.yaml` (Modul-spezifisch)
3. **Runtime:** `.env` (API-Keys — ausserhalb von Git)
4. **Provider:** `provider_config.yaml` (Modelle, Provider, Hardware-Profile)
5. **Blacklist:** `config/web_export_blacklist.yaml` (Web-Export-Sperren)

## Provider-Unterstützung

| Provider | Connector | Notes |
|---|---|---|
| OpenAI | `utils/providers/openai.py` | native + Groq-Proxy |
| Anthropic | `utils/providers/anthropic.py` | Extended Thinking supported |
| Google | `utils/providers/google.py` | `thoughts_token_count` |
| Mistral | `utils/providers/mistral.py` | kein Streaming |
| xAI | `utils/providers/xai.py` | Gemma-Modelle |
| OpenRouter | `utils/providers/openrouter.py` | `data_collection: allow` fuer Qwen |
| Cohere | `utils/providers/cohere.py` | Native ToolUse (v4.10.8) |
| Ollama | `utils/providers/ollama.py` | Local, `eval_count` |
| Llama.cpp | `utils/providers/llamacpp_base.py` | Local, `reasoning_content` + GGUF |
| Spark (llamacpp) | `llamacpp_spark.py` | Eigenstaendiger Server mit Kontextfenster |
| vLLM (Spark) | `vllm_base.py` + `vllm_spark.py` | SSH-gesteuert (asusGX10), OpenAI-kompatibel Port 3300, MoE-kompatibel |

## Architektur-Module

| Modul | Pfade |
|---|---|
| Core-Runner | `utils/base_runner.py` |
| Result-Manager | `utils/result_manager.py` |
| Benchmark-Runner | `run_benchmark.py`, `benchmark_auto.py` |
| Web-Export | `scripts/web_export.py` |
| Card-Management | `manage_model_cards.py` |
| Review-Generator | `scripts/analysis/generate_review.py` |
| ToolUse-Exporter | `scripts/core/tooluse_exporter.py` |
| Provider-Basis | `utils/providers/base.py` |
| Utility-Funktionen | `utils/model_utils.py` |

## Daten-Persists (Dateisystem)

| Datenquelle | Path | Format |
|---|---|---|
| Benchmark-CSV | `benchmark_scores/benchmark_leaderboard_*.csv` | CSV |
| Modell-Cards | `benchmark_scores/model_cards/*.json` | JSON |
| Vendor-Cards | `benchmark_scores/vendor_cards/*.json` | JSON |
| Audit-Logs | `outputs/audit_logs/<model>/` | Markdown |
| Reviews | `docs/reviews/<model>/` | Markdown |
| Leaderboards | `benchmark_scores/benchmark_leaderboard_compact.csv` | CSV |
| Cost-Log | `outputs/cost_log.csv` | CSV |
| Web-Export | `CrucibleMark-Web/src/_data/raw/` | JSON |

## Key-Patterns

- **SSoT/DRY:** Ein Feature = ein Modul. Fail-Fast ohne versteckte Fallbacks.
- **Card-First CSV-Senke:** `result_manager.save_results()` — `enforce_card_first()` erstellt Draft-Cards wenn keine vorhanden.
- **Atomic Writes:** `tempfile.mkstemp()` + `os.replace()` — kein Datenverlust bei Crash.
- **Memory-Bank:** Lese vor jeder Session `activeContext.md`, `progress.md`, `systemPatterns.md`.
