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

## Token-Limit Fallback / Kopfnoten
- Alle Provider nutzen den `_execute_with_token_fallback`-Wrapper in `utils/provider_clients.py`.
- Harte Exceptions (wie Quota/Budget) provozieren einen sofortigen Test-Abbruch (Fast-Fail), Token-Limit Fehler lösen die Fallback-Kaskade (aus `benchmark_config.yaml`) abwärts aus.
- Ergebnisse iterieren nicht die Score-Punkte, sondern notieren rein kontextuelle "Kopfnoten" (`token_limit_used`) im Metric-Tracker. Diese flossen später über `generate_review.py` via Regex-Extraktion in die Meta-Reviewer Berichte ein.

## Neue Provider hinzufügen
1. In `benchmark_config.yaml` unter `providers.commercial` oder `providers.local` eintragen
2. Klasse in `llm_judge/providers/` anlegen (erbt von `LLMJudgeProvider`)

## Hardware Context & Prompt-as-Config
- Die Laufzeitumgebung (Hardware) wird unter `runner_environment:` in `benchmark_config.yaml` deklariert (t/s limits, Unified Memory vs VRAM).
- `SystemContextManager` injiziert dieses Profil automatisch als Kontext in Prompts (z.B. den Meta-Reviewer in `scripts/analysis/generate_review.py`).
- Zentrale System-Prompts (wie der Meta-Reviewer) werden in `config/*.yaml` externalisiert, um "Prompt-as-Config" zu etablieren und Code von Inhalt zu trennen.

