# Project Guidelines

## Code Style
- **Python 3.12**, venv (nie global)
- Typen immer annotieren (mypy-kompatibel)
- **Verbote**: Kein `print()` für Debugging (nutze `logging.debug()`), kein bare `except:` (immer spezifischer Exception-Typ), keine Provider-Namen hardcoden (aus `benchmark_config.yaml` lesen).
- Siehe [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) für ausführliche Entwicklerrichtlinien.

## Architecture
- **Konfig-Hierarchie:** Global (`benchmark_config.yaml`) → Modul (`config.yaml`) → Runtime.
- **Module:** Müssen von `BaseTest` erben, `execute()` verarbeitet einzelne Aufgaben. Keine modul-internen Batch-Schleifen.
- Globale Konzepte und Architektur-Entscheidungen im Detail: [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Build and Test
- **Tests**: `pytest -v --tb=short`
- **Build/Lint**: `make validate`, `make test`
- Siehe Befehlsreferenzen in der [Makefile](Makefile) (z.B. `make benchmark`, `make validate`) und Setup-Details im [SETUP_GUIDE.md](docs/SETUP_GUIDE.md).

## Conventions
- **LLM Judge**: Provider erben von `LLMJudgeProvider`, Globale Einstellungen in `benchmark_config.yaml`. Siehe [SCORING_METHODOLOGY.md](docs/SCORING_METHODOLOGY.md) für Bewertungsdetails.
- **Golden Standards:** `asset.yaml` ist die Single Source of Truth. Siehe [GOLDEN_STANDARDS.md](docs/GOLDEN_STANDARDS.md).
- **Fallstricke und spezifische Patterns**:
  - *Namespace-Kollision:* Bei `importlib` mit gleichnamigen Plugin-Dateien `{parent.name}_{stem}` verwenden.
  - *Asset Schema:* Jede YAML-Aufgabe braucht zwingend ein `prompt`/`prompts`-Feld.
  - *Judge Parser:* Muss Score-Varianten abfangen. Bei Parse-Fehler `parse_success=False` verwenden (niemals Exception schlucken).
  - *CSV-Felder:* Neue dynamische Spalten müssen in `result_manager.py` bei `_get_updated_fieldnames` explizit eingetragen werden.
  - *Modul-Config Propagation:* Neue Top-Level-Properties in `config.yaml` müssen manuell ins `benchmark_info`-Dict (in `run_benchmark.py`) übernommen werden.
  - *Model Tags / Evaluation Context:* Neue Modell-Tags (in `model_utils.py`) müssen synchron in `meta_reviewer_prompt.yaml` und `judge_prompt_builder.py` dokumentiert werden, damit Judge und Meta-Reviewer die richtige Bewertungstoleranz anwenden.
  - *architecture_tags Override:* `generate_review.py` priorisiert das `architecture_tags`-Feld aus der JSON-Model-Card (`benchmark_scores/model_cards/*.json`) gegenüber dem String-Matching in `get_model_identity()`. Bei Tag-Korrekturen immer die Card aktualisieren — `model_utils.py` allein reicht nicht.
  - *Audit-Log Extraction:* Regex-Parser in `generate_review.py` muss bei neuen Metadaten-Blöcken (z.B. `> [!WARNING]`) erweitert werden. Siehe [AUDIT_AND_METAREVIEW.md](docs/AUDIT_AND_METAREVIEW.md).
  - *Terminal Execution Limits:* Für sichere Datei-Ersetzungen File-Edit-Tools oder Python-Dateien statt Terminal-Befehle nutzen.
  - *Google SDK Typing:* Bei Pylance/Pyright False-Positives (z.B. `reportPrivateImportUsage`) im `google.generativeai` SDK `# pyright: reportPrivateImportUsage=false` am Header nutzen.
  - *PC Skip-Logic Gap:* `execute_batch_module()` in `base_runner.py` prüft nur die 3 Standard-CSVs auf bereits vorhandene Ergebnisse — nach einem Leaderboard-Reset sind diese leer, die `political_compass_leaderboard.csv` aber nicht. Ohne expliziten Fallback auf `political_compass_leaderboard.csv` werden alle PC-Modelle fälschlich erneut gerunnt.
  - *max_expected_words gilt nur für Gesamtantworten:* Bei Assets wo das Limit nur einen Abschnitt der Antwort betrifft (z.B. Email-Body ≤300W, während Analyse-Teil zusätzlich erwartet wird), darf `max_expected_words` NICHT gesetzt werden — die Gesamtantwort überschreitet das Limit zwingend. Stattdessen `keyword_presence`-Check oder LLM-Judge verwenden.
  - *OpenRouter Reasoning-Token-Budget:* OpenRouter verrechnet interne Reasoning-/Thinking-Tokens (z.B. MiniMax M2, DeepSeek R1) direkt gegen `max_tokens`. Ist das Budget erschöpft, liefert die API `message.content = null` + `finish_reason: length`. Fix: Modell-Name-Trigger in `is_reasoning_model()` (`utils/model_utils.py`) eintragen → `resolve_token_budget()` erhöht Budget automatisch für alle Provider. Bei neuen Reasoning-Modellen **immer** prüfen, ob der Name einen bestehenden Trigger trifft.
  - *Token-Budget SSoT — nie inline duplizieren:* Die Funktion `resolve_token_budget(model, requested_max_tokens, config, module_key)` in `utils/model_utils.py` ist die einzige Stelle für Token-Budget-Logik. Kein Provider darf inline `is_reasoning_model()`-Checks mit eigenem Budget-Multiplizierlogik implementieren — immer `resolve_token_budget()` delegieren.
  - *`token_param_name` per Provider — nie hardcoden:* Der API-Parametername für Token-Limits (`max_tokens` vs. `max_completion_tokens`) ist in `benchmark_config.yaml → providers.commercial.<provider>.token_param_name` definiert. Providers lesen ihn via `_provider_cfg.get("token_param_name", "<fallback>")`. Nie als String-Literal in Provider-Code hardcoden.
  - *Refusal-Flag statt Re-Run:* Wenn ein Modell auf einen Asset mit < 15 Zeichen antwortet, ist das ein `refusal_flag=True`-Ergebnis, kein Testfehler. Kein Re-Run, kein Asset-Fix — sofern andere Modelle denselben Asset lösen. Das Refusal ist die Qualitätsaussage.
  - *ThinkingProbe Signal-C-Verbot:* Response-Länge ist **kein** zuverlässiges CoT-Signal. Instruction-Following-Modelle antworten auf Reasoning-Prompts ebenfalls ausführlich (False-Positive). Nur Signal A (`<think>`-Tags) und Signal B (`reasoning_tokens > 0`) verwenden. Signal C **nie wieder einführen**.
  - *Card-Lookup `_safe_name()`-Konsistenz:* Alle Pfadauflösungen für Model-Cards müssen `re.sub(r'[:/.\ ]', '_', model_id)` verwenden — nicht nur `replace('/', '_')`. Beispiel: `gemini-2.5-flash` → Datei `gemini-2_5-flash.json`. Wird die Transformation inkonsistent angewendet, findet `is_reasoning_model_from_card()` keine Card und fällt ohne Fehlermeldung auf Trigger-Heuristik zurück.
  - *Card-Pfad SSoT — `_card_path()` und `_find_card()`:* Alle Card-Pfadoperationen in `model_utils.py` und `generate_model_cards.py` müssen `_card_path(model_id, provider, for_write)` bzw. `_find_card(model_id)` aus `utils/model_utils.py` verwenden — nie inline `Path(...) / f"{re.sub(...)}.json"`. `CARD_DIR` ist ebenfalls aus `model_utils` zu importieren.
  - *Card-Naming-Regel (Provider-Qualifier):* Dateiname = `_safe_name(model_id).json` für (a) namespaced IDs (enthalten `/`) und (b) direkte API-Provider (`API`-Shortcode: Anthropic, OpenAI, Google, xAI, Mistral). Für nicht-namespaced IDs von Inference-Proxies und lokalen Runtimes (`LCL`, `GR`) gilt: `{SHORTCODE}_safe_name.json` — verhindert Card-Kollisionen wenn dasselbe Modell über mehrere Provider getestet wird (z.B. `llama3.3:70b` via Ollama *und* Groq). Bestehende unpräfixierte Legacy-Cards werden beim Read-Lookup als Fallback gefunden (`_find_card` und `_card_path` mit `for_write=False`).
  - *size_class Card-Slug-Mismatch:* Der Card-Pfad für `get_model_size_class()` wird aus dem **tatsächlichen Modell-Namen in der CSV** berechnet — nicht aus dem Display-Namen. `CognitiveComputations/dolphin-mistral-nemo:latest` → Card `CognitiveComputations_dolphin-mistral-nemo_latest.json`, nicht `dolphin-mistral-nemo_latest.json`. Bei Klassifikations-Fixes immer den CSV-Namen als Basis nehmen.
  - *`_infer_provider()` — `/`-Präsenz-Heuristik, kein Substring-Matching:* Lokale Ollama-Modell-IDs wie `deepseek-r1:8b` können Provider-Namen als Teilstring enthalten. Provider-Inferenz muss `/` im model_id als OpenRouter-Signal nutzen — nie `"deepseek" in model_id` o.ä. Sonst werden lokale Modelle fälschlicherweise via OpenRouter geprobt.
  - *OpenAI o-Series: ThinkingProbe kann Reasoning nicht erkennen:* o1/o3-mini/o4-mini liefern keine `reasoning_tokens` in der API-Antwort und keine `<think>`-Tags. `probe_thinking_model()` gibt `detected=False` zurück. Für diese Modelle muss die Card **manuell** mit `thinking_probe_detected: true` + `thinking_probe_manual_override: true` gesetzt werden.
  - *Kein reaktiver Retry bei Token-Cutoff:* Bei `token_limit_cutoff=True` für ein nicht erkanntes Reasoning-Modell **keinen automatischen Retry** mit erhöhtem Budget implementieren — das erzeugt unter abweichenden Bedingungen gemessene Daten, die nicht mit dem Leaderboard vergleichbar sind. Stattdessen wird ein actionable `[!WARNING]`-Block mit `make probe-thinking`-Befehl ins Audit-Log geschrieben (`benchmark_utils.py`). Der Maintainer führt den Re-Run nach Card-Korrektur manuell durch.
  - *Thinking-Optional Budget — `is_thinking_optional_from_card()` als SSoT:* Modelle mit `architecture_tags: ["Thinking-Optional"]` in der Model-Card erhalten in `resolve_token_budget()` automatisch das erhöhte Reasoning-Budget aus `token_budgets_reasoning_models` (z.B. 12.000 statt 6.000 für `code_quality`). Die Hilfsfunktion `is_thinking_optional_from_card()` in `model_utils.py` ist die einzige Stelle für diesen Check — nie inline prüfen. Gilt nur bei `explicit_budget=True` (d.h. Module mit Budget-Cap); Module ohne Limit (z.B. `reasoning_logic`) sind nicht betroffen. Fallback-Multiplizier: 2× Standard-Budget wenn kein Reasoning-Eintrag existiert.

## Memory Bank (Dynamic Project Context)

This project uses a **Cline Memory Bank** at `memory-bank/` as the single source of
truth for current project state. Before making architectural decisions or touching
unfamiliar modules, consult these files:

| File | Contains |
|---|---|
| `projectbrief.md` | Core project goals, scope, non-goals |
| `productContext.md` | Why CrucibleMark exists, target users, design philosophy |
| `systemPatterns.md` | Recurring architecture patterns, design decisions, rationale |
| `techContext.md` | Full tech stack, dependencies, environment setup |
| `activeContext.md` | **Current sprint focus**, open issues, recent decisions |
| `progress.md` | **What works, what's in progress, known blockers** |

> **Wichtig:** `activeContext.md` und `progress.md` werden von Cline nach jeder
> Session aktualisiert. Lies sie vor größeren Änderungen, um Konflikte mit laufender
> Arbeit zu vermeiden.

The static rules in this file (Code Style, Architecture, Conventions) define *how*
to work. The Memory Bank defines *where* the project currently stands.
