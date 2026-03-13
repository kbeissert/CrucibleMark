# System Patterns

## Konfig-Hierarchie (SSOT)
Global (`benchmark_config.yaml`) → Modul (`config.yaml`) → Runtime.
Gilt für Generation-Parameter UND LLM Judge. Modul-Override gewinnt immer.

## LLM Judge – Architektur
- Provider-Abstraktion: ABC `LLMJudgeProvider` → `complete()` + `health_check()`
- Globale Judge-Einstellungen in `benchmark_config.yaml` unter `llm_judge:`
- `config.example.yaml` ausschließlich für Modul-spezifische Overrides (alles auskommentiert)
- Prompt-Strategie: Chain-of-Thought zwingend – REASONING: vor SCORE:
- Phase-Trennung: Benchmark einfrieren → Ollama-Unload → 500ms → Judge laden
- `is_complete()` prüft `judge_parse_success is not None` (nicht `judge_score`)

## Module
- Alle Module erben von `BaseTest`, `execute()` verarbeitet einzelne Aufgaben
- Neue Top-Level-Properties in `config.yaml` müssen in `run_benchmark.py` manuell
  ins `benchmark_info`-Dict übernommen werden

## Neue Provider hinzufügen
1. In `benchmark_config.yaml` unter `providers.commercial` oder `providers.local` eintragen
2. Klasse in `llm_judge/providers/` anlegen (erbt von `LLMJudgeProvider`)
