# Tech Context

## Configuration Architecture

- **Global Defaults**: Defined in `benchmark_config.yaml` under `defaults.generation` (e.g., `temperature: 0.1`, `repeat_penalty: 1.1`).
- **Module Overrides**: Defined in `benchmark_modules/*/config.yaml` under `generation` block.
- **Runtime Merge**: `test.py` loads global defaults, updates with module config, and passes to LLM client.

## Critical Fixes

- **Parameter Handling**: `kwargs.pop()` utilized in `test.py` to prevent `multiple values for keyword argument` errors when merging configs.


## LLM Judge – Implemented Architecture

- **Audit Logging**: Runner-Scripts extahieren DTO-Daten, verknüpfen rule-basierte `category_scores` und deduktive `details` Logs und überführen den finalen `evaluated_prompt` samt LLM-Reasoning in formatierte Markdown-Dateien zur manuellen Inspektion.
- **Location**: `scoring/llm_judge/`
- **Mode**: `complement` (runs alongside Hybrid Scorer) or `replace`
- **Provider Abstraction**: Abstract base class `LLMJudgeProvider` in `base_provider.py`
  - Implementations: `anthropic_provider.py`, `mistral_provider.py`, `ollama_provider.py`, `openai_provider.py`
  - Auth via env vars: `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`, `OPENAI_API_KEY`
  - Ollama: no auth, configurable `base_url`
- **Scoring Scale**: Configurable (3 / 5 / 10 points), default 5
- **Prompt Strategy**: Chain-of-Thought mandatory – REASONING: block before SCORE: integer
- **Config Key**: `llm_judge:` in module-level `config.yaml`, follows existing config hierarchy:
  Global (`benchmark_config`) → Module (`config.yaml`) → Runtime
- **Integration Point**: `judge_runner.py` exposes `score(task_prompt, model_response, golden_standard, module_id)`
- **Output**: Adds `llm_judge_score` and `llm_judge_reasoning` fields to existing result JSON

### Config-Hierarchie (SSOT)

Zwei-Ebenen-System – analog zur bestehenden Global→Modul-Hierarchie:

**Ebene 1 – Global (SSOT): `benchmark_config.yaml`**
Zuständig für: Provider-Auswahl, Fallback-Provider, Modell-IDs, Scoring-Defaults,
applicable_modules, mode, unload_delay_ms.
Alle projektweiten Defaults des LLM Judge stehen hier – direkt unterhalb von
`golden_standard:` als Top-Level-Block `llm_judge:`.
Provider-Referenzen zeigen auf `providers.commercial.*` bzw. `providers.local.ollama`.

**Ebene 2 – Modul-Override (optional): `utils/scoring/llm_judge/config.example.yaml`**
Zuständig für: Modul-spezifische Abweichungen (z.B. scale: 10 für ux_writing,
anderer Fallback für ein einzelnes Modul).
Alle Einträge sind auskommentiert – nur aktiv setzen, wenn Abweichung vom Global-Default nötig.
Globale Felder gehören NICHT in diese Datei – sie wurden bewusst entfernt.

Priorität bei Konflikt: Modul-Override > Global (benchmark_config.yaml) > Code-Defaults
