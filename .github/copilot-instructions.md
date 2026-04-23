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
  - *OpenRouter Reasoning-Token-Budget:* OpenRouter verrechnet interne Reasoning-/Thinking-Tokens (z.B. MiniMax M2, DeepSeek R1) direkt gegen `max_tokens`. Ist das Budget erschöpft, liefert die API `message.content = null` + `finish_reason: length`. Fix: Modell-Name-Trigger in `is_reasoning_model()` (`utils/model_utils.py`) eintragen → OpenRouter-Provider erhöht Budget automatisch. Bei neuen Reasoning-Modellen via OpenRouter **immer** prüfen, ob der Name einen bestehenden Trigger trifft.

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
