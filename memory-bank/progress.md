# Progress

## Completed
- [DONE] Leaderboard TypeError `None` Bug in `__init__.py` und Pydantic Validierungs-Bug (ValidationError in Config) behoben.
- [DONE] Hardcoded Models in `judge_health.py` entfernt, Konfiguration erfolgt über `benchmark_config.yaml`.
- [DONE] LLM Judge Timeout für Ollama von 30s auf 120s hochgesetzt.
- [DONE] LLM Judge Markdown-Ausreißer geparsed (`judge_parser.py` Regex robuster gegen Headings und Bold-Tags).
- [DONE] LLM Judge Config-Architektur finalisiert:
  benchmark_config.yaml als SSOT (llm_judge:-Block),
  config.example.yaml auf Modul-Override-Rolle verschlankt.
- [DONE] LLM Judge Modul implementiert (utils/scoring/llm_judge/)
  - Phase 1: Provider-Abstraktion (4 Provider), judge_config, judge_prompt_builder,
    judge_parser, judge_runner, 35 Tests
  - Phase 2: judge_handoff.py, Ollama-Lifecycle (unload_model), Fallback-Chain,
    unload_delay_ms, response_time_ms-Übergabe, 38 weitere Tests
  - Selbstkorrektur: is_complete()-Bug eigenständig durch Claude identifiziert und gefixt

- [DONE] Konfigurations-Hierarchie und Laufzeitparameter vereinheitlicht
- [DONE] Fix infinite loops in Hermes3 (Code Quality Module)
- [DONE] Integration von Google Gemini (2.5 / 3.0 Serie) und xAI Grok (3 / 4) in Config und Pricing-Pipeline
- [DONE] Bugfix im `reasoning_logic` Evaluator: Parsing-Cutoffs bei `implicit_separator` ("**Answer:**") für Standard Logic-Tests verhindert
- [DONE] Refaktorierung von `cli_benchmark` für korrekte `BaseTest`-Integration und Einzel-Test Ausführung.
- [DONE] Fix Leaderboard-Asterisk Bug (`*`) durch Ergänzung des Modul-Präfix in der `cli_benchmark/config.yaml`.
- [DONE] MyPy-Fehler Zeile 35 in `run_commercial_benchmark.py` behoben (Optional-Import Type-Hint). Pylint: 10/10.
- [DONE] **LLM Judge Modul – Phase 1**: Provider-Abstraktion (Anthropic, Mistral, OpenAI, Ollama), Pydantic-Config, CoT-Prompt Builder, Response Parser, `JudgeRunner`, Leaderboard-Integration, `make judge-health`, Tests (35), README, `config.example.yaml`.
- [DONE] **LLM Judge Modul – Phase 2**: `judge_handoff.py` (PendingJudgeResult + frozen response_time_ms + JSON-Persistenz), `unload_model()` in OllamaProvider, `FallbackProviderConfig` + `unload_delay_ms` in Config, Fallback-Chain + Lifecycle in `JudgeRunner`, 38 neue Tests (73 gesamt grün).
- [DONE] **LLM Judge Modul – Phase 2.5 (Pipeline Integration)**: `run_local_benchmark.py`, `run_commercial_benchmark.py`. Strikte Phase-Run Sequenz eingebaut (Execute -> Zeitmesser -> Unload -> Judge -> Result Merge). Unit-Tests implementiert & erfolgreich.
- [DONE] **LLM Judge Modul – Phase 3 (ResultManager Schema)**: Abwärtskompatible Schema-Erweiterung für 5 neue `llm_judge_*`-Spalten. Leaderboard-Aggregation (`scripts/leaderboard/score_calculator.py`) um `llm_judge_avg` und `judge_coverage` ergänzt. Unit-Tests für Legacy-Laden und Partial-Data etabliert.

## Ongoing
- [ ] First real benchmark run (single module, single model)
- [ ] Re-run des `reasoning_logic` Benchmarks für (lokale) Modelle, um verfälschte 0-Punkte Resultate auszugleichen
- [ ] Analyse der Stabilität von `gpt-oss` (vorheriger Absturz-Kandidat)
- [ ] Monitor full benchmark suite execution
- [ ] Volldurchlauf des Benchmarks für alle lokalen Modelle starten, um das finale Leaderboard (43/43 Tests) zu befüllen.
