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
- Alle Provider nutzen den `_execute_with_token_fallback`-Wrapper in `utils/providers/base.py`.
- Harte Exceptions (wie Quota/Budget) provozieren einen sofortigen Test-Abbruch (Fast-Fail), Token-Limit Fehler lösen die Fallback-Kaskade (aus `benchmark_config.yaml`) abwärts aus.
- Gegen Token-Loop-Halluzinationen (z.B. endlose Leerzeichen-Repeats von Gemini 2.5 Flash) ist eine Regex-basierte Character-Sequence Validation im BaseClient implementiert, die den Test sofort markiert und abbricht.
- Ergebnisse iterieren nicht die Score-Punkte, sondern notieren rein kontextuelle "Kopfnoten" (`token_limit_used` oder `⚠️ OUTPUT TRUNCATED/LOOP`) im Metric-Tracker. Diese fließen später über `generate_review.py` via Regex-Extraktion in die Meta-Reviewer Berichte ein.

## Neue Provider hinzufügen
1. In `benchmark_config.yaml` unter `providers.commercial` oder `providers.local` eintragen
2. Falls es ein API Provider ist: Neues Modul in `utils/providers/` anlegen (erbt von `BaseProviderClient`) und in `utils/providers/__init__.py` exportieren.
3. Falls es ein LLM Judge ist: Klasse in `llm_judge/providers/` anlegen (erbt von `LLMJudgeProvider`).

## Hardware Context & Prompt-as-Config
- Die Laufzeitumgebung (Hardware) wird unter `runner_environment:` in `benchmark_config.yaml` deklariert (t/s limits, Unified Memory vs VRAM).
- `SystemContextManager` injiziert dieses Profil automatisch als Kontext in Prompts (z.B. den Meta-Reviewer in `scripts/analysis/generate_review.py`).
- **Prompt-as-Config / Tier-System:** Logik-Regeln (wie Leaderboard Scoring-Tiers und deren Prompt-Repräsentanz für den Meta-Reviewer) werden zentral in `benchmark_config.yaml` (`scoring_tiers`) gepflegt. Präsentationsschicht (`formatter.py`) und AI-Anweisungen (`generate_review.py`) lesen diese Werte dynamisch zur Laufzeit, um Hardcoding und Inkonsistenzen (Noteninflation) zu vermeiden.

## Model Versioning (Deterministisch)
- Keine zufälligen oder hash-basierten Generierungen von Modell-Verisonen für identische API-Aufrufe (wie zuvor im `ModelFingerprinter`).
- Versionen werden zentral in `utils/model_utils.py` innerhalb der `get_model_version()`-Methode über Regex und statische Mappings (z.B. Regex für Datums-Stamps wie `2024-05-13`) verarbeitet.
- Ollama-Modellversionen werden direkt als ID-Hash über den `ollama list` Shell-Call zur Laufzeit ermittelt und nativ an das Leaderboard durchgereicht.
