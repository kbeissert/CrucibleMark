# System Patterns

## 🛑 OBERSTE ARCHITEKTUR-REGEL: Strict Separation of Concerns (Measurement vs. Publishing)
- **Measurement:** Autonom, ausfallsicher, isoliert. Keine Blockaden.
- **Publishing:** Laufen strikt offline.

## 🛑 ZWEITE ARCHITEKTUR-REGEL: Single Source of Truth (SSOT), DRY & SRP
- **Logische Exklusivität:** Jede spezifische Funktionalität hat genau **ein** zuständiges Modul.
- **Fail-Fast ohne Fallback:** Versteckte "Convenience Fallbacks" in internen Libraries oder API-Wrappern (z.B. ein leeres `"claude"` Model einfach auf `claude-3-5-sonnet` leiten) sind **strikt verboten**. Wenn Config-Parameter fehlen oder falsch sind, bricht das System hart ab (`ValueError`).
- **Wiederverwendung vor Neuerfindung:** Wird eine Funktion anderswo gebraucht, wird das Modul importiert – niemals dupliziert.
- **Erweiterung (Open/Closed):** Fehlt dem Modul eine Facette, wird es selbst intelligent erweitert.

## 🛑 DRITTE ARCHITEKTUR-REGEL: Configuration-Driven & No Magic Numbers
- **Keine Hardcodes:** Regeln, Zahlen, Limits oder Formeln dürfen **niemals** direkt im Code stehen ("Magic Numbers").
- **Auslagerung:** Das Projekt ist konfigurationsgetrieben. Alle Variablen werden in Config-Dateien (YAML) ausgelagert und importiert.

## 🛑 VIERTE ARCHITEKTUR-REGEL: Anti-God-Script & Modularisierung
- **Aktives Monitoring:** Bei der Weiterentwicklung wird strengstens auf die Länge und Komplexität der Skripte geachtet.
- **Kapselung:** Erkennst du, dass ein Skript zum monolithischen "God-Script" mutiert, musst du umgehend logische Submodule auslagern. Funktionalitäten werden in kleine Module gekapselt und sauber in das Hauptskript eingebunden.

## Runner-Konsolidierung
- **Unified Runner:** Alle Benchmarks (Lokal & Kommerziell) laufen zentral über den `UnifiedBenchmarkRunner` (`scripts/core/unified_runner.py`). Keine getrennten Runner-Skripte mehr!

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

## Model Card `architecture_tags` als manueller Tag-Override
- JSON-Cards in `benchmark_scores/model_cards/*.json` können ein `architecture_tags`-Feld führen (Array mit 1–n Tags aus dem definierten 9er-Set).
- `generate_review.py` priorisiert diese Card-Tags gegenüber dem automatischen String-Matching in `get_model_identity()` — damit können Tags für Modelle gesetzt werden, die im Namen keinen Hinweis tragen (z.B. `o4-mini→Thinking`, `codestral→Coder`).
- `model_utils.py` bleibt die SSOT für dynamisches Runtime-Matching (Judge, Runner); Cards sind nur für Review-Generierung relevant.
- `generate_model_cards.py` füllt `architecture_tags` per LLM-Klassifikation; manuelle Nachkontrolle ist erwünscht.

## Token-Budget-System (Output-Cap, ab v3.4.0)
- **Orthogonal zum Fallback-System:** `benchmark_config.yaml → token_budgets[module_key]` definiert einen direkten `max_tokens`-API-Parameter pro Modul — kein Fehler-Handling, sondern ein proaktiver Cap für faire Vergleichbarkeit.
- `base_runner.py → execute_test_module()` liest den Wert und übergibt ihn **nur wenn nicht `None`** — kein `None`-Wert darf an Provider-Clients weitergegeben werden.
- Reasoning-Module (`reasoning_logic`, `cli_benchmark`) sind bewusst ausgenommen. Budgetierte Module: `cultural_intelligence: 500`, `ux_writing: 3500`, `content_transformation: 3500`, `documentation_quality: 6000`, `code_quality: 6000`.
- `token_limit_cutoff=True` im BenchmarkResult → `[!NOTE]`-Block in Audit-Log (`benchmark_utils.py`). Trigger: `cutoff is True AND _budget is not None`.

## ThinkingProbe & Card-First Workflow (ab v3.5.8)
- **Empirische Erkennung:** `probe_thinking_model()` testet per API-Call, ob ein Modell Chain-of-Thought produziert. Signal A = `<think>`/`<thinking>`/`<thought>`-Tags (confidence=high), Signal B = `reasoning_tokens > 0` in API-Metadaten (confidence=medium). Signal C (Response-Länge) ist **nicht** implementiert — zu viele False-Positives bei Instruction-Following-Modellen.
- **`is_reasoning_model()` Hierarchie:** 1. `is_reasoning_model_from_card(model_id)` (Card-Lookup, immer Vorrang) → 2. String-Trigger als Fallback. Gibt `None` zurück wenn kein Card-Eintrag — kein False-Positive.
- **`_safe_name()` Konsistenz:** Alle Card-Pfad-Auflösungen müssen `re.sub(r'[:/.\ ]', '_', model_id)` verwenden. `replace('/', '_')` allein reicht nicht (z.B. `gemini-2.5-flash` → `gemini-2_5-flash.json`).
- **`_ensure_model_card()` Hook:** Wird in `unified_runner.py` vor dem ersten Run eines Modells aufgerufen. Prüft ob `thinking_probe_detected` in der Card vorhanden — falls nicht, führt Probe durch und schreibt Ergebnis. Fehlende Card → Minimal-Card erstellen. Probe-Fehler → RuntimeError (kein stilles Überspringen).
- **Manual Override:** OpenAI o-Series (o1, o3-mini, o4-mini) verbergen Reasoning-Tokens intern. Card manuell mit `thinking_probe_detected: true, thinking_probe_manual_override: true` setzen.
- **Retroaktiver Probe:** `make probe-all-thinking` → `scripts/tools/probe_thinking.py --missing`. Provider-Inference: Config-Lookup → `/` im model_id → `openrouter` → sonst `ollama`. Kein Substring-Matching (führt zu False-Routing bei lokalen Modell-Namen wie `deepseek-r1:8b`).

## OpenRouter: Reasoning-Token-Budget-Konflikt
- OpenRouter verrechnet interne Reasoning-/Thinking-Tokens bei Reasoning-Modellen gegen `max_tokens`. Bei erschöpftem Budget ist `message.content = null`, `finish_reason = length`.
- **Erkennung:** `is_reasoning_model()` in `utils/model_utils.py` — ab v3.5.8 Card-First + Trigger-Strings: `deepseek-r1`, `reasoning`, `phi4`, `qwq`, `o1`, `o3`, `magistral`, `glm-5`, `minimax-m2`, `gemini-2.5`, `kimi-k2`.
- **Fix:** `utils/providers/openrouter.py` multipliziert das Budget für erkannte Reasoning-Modelle automatisch (5× oder `token_budgets_reasoning_models` aus Config).
- **Tracking:** `completion_tokens_details.reasoning_tokens` wird aus der API-Response extrahiert → `BenchmarkResult.reasoning_tokens` → neue CSV-Spalte.
- **Audit-Log:** Bei `reasoning_tokens > 0 AND token_limit_cutoff=True` → `[!WARNING]`-Block mit Erklärung in `benchmark_utils.py`.
- **Neue Modelle prüfen:** Bei Ergänzung von Reasoning-Modellen via OpenRouter immer kontrollieren, ob der Modellname einen Trigger in `is_reasoning_model()` trifft. Falls nicht → Trigger ergänzen.

## Neue Provider hinzufügen
1. In `benchmark_config.yaml` unter `providers.commercial` oder `providers.local` eintragen
2. Falls es ein API Provider ist: Neues Modul in `utils/providers/` anlegen (erbt von `BaseProviderClient`) und in `utils/providers/__init__.py` exportieren.
3. Falls es ein LLM Judge ist: Klasse in `llm_judge/providers/` anlegen (erbt von `LLMJudgeProvider`).

## Hardware Context & Prompt-as-Config
- Die Laufzeitumgebung (Hardware) wird unter `runner_environment:` in `benchmark_config.yaml` deklariert (t/s limits, Unified Memory vs VRAM).
- `SystemContextManager` injiziert dieses Profil automatisch als Kontext in Prompts (z.B. den Meta-Reviewer in `scripts/analysis/generate_review.py`).
- **Prompt-as-Config / Tier-System:** Logik-Regeln (wie Leaderboard Scoring-Tiers und deren Prompt-Repräsentanz für den Meta-Reviewer) werden zentral in `benchmark_config.yaml` (`scoring_tiers`) gepflegt. Die Prompts großer analytischer Agenten (wie dem Meta-Reviewer) greifen nicht auf im Python-Script eingebetteten Text, sondern auf dynamische, austauschbare YAML-Konfigurationen (`config/meta_reviewer_prompt.yaml`) zurück. Dies verhindert Hardcoding und unterstützt die Iterierbarkeit.

## Model Versioning (Deterministisch)
- Keine zufälligen oder hash-basierten Generierungen von Modell-Verisonen für identische API-Aufrufe (wie zuvor im `ModelFingerprinter`).
- Versionen werden zentral in `utils/model_utils.py` innerhalb der `get_model_version()`-Methode über Regex und statische Mappings (z.B. Regex für Datums-Stamps wie `2024-05-13`) verarbeitet.
- Ollama-Modellversionen werden direkt als ID-Hash über den `ollama list` Shell-Call zur Laufzeit ermittelt und nativ an das Leaderboard durchgereicht.

## Model Environment & Architecture Tags
- Um spezialisierte Modelle (z.B. Thinking, Coder, Uncensored) fair und im passenden Kontext bewerten zu können, wird über `utils/model_utils.py` dynamisch ein Satz an Architektur-Tags (`Instruct`, `Thinking`, `Uncensored-Abliterated`, etc.) generiert.
- Diese Spezialisierungen müssen strikt "End-to-End" an alle Bewerter weitergereicht werden. Das bedeutet:
  1. Der CLI-Runner listet sie.
  2. Der `LLM-Judge` erhält sie als `tested_model_id` in seinen System-Prompt (via `judge_prompt_builder.py`), um z.B. bei Thinking-Modellen nicht wegen übermäßiger Erklärung ("Verbosity") Punktabzüge zu geben.
  3. Der `Meta-Reviewer` erhält sie in seinen System-Prompt (`meta_reviewer_prompt.yaml`), um z.B. bei abliterated Modellen Kohärenz-Abbrüche auf die zerstörten Weights statt mangelnde Intelligenz zurückzuführen.

## Data Management & CSV Retesting Behavior (Consolidation)
- **Logbestand & Überschreiben:** Die Datei `local_models_benchmark.csv` (und andere Benchmark-CSVs) fungieren zunächst als Append-Only-Log. Jeder Testdurchlauf hängt neue Zeilen an.
- **Maintenance (Consolidate):** Am Ende eines `make benchmark` (oder beim Backup) läuft das Skript `scripts/maintenance/consolidate_csv.py`. Dieses Skript sortiert nach Zeitstempel und führt ein `drop_duplicates(subset=["model", "asset_id"], keep="first")` durch. **Konsequenz:** Alle älteren Testläufe für ein Modell+Asset werden restlos gelöscht. Ein "Retest" überschreibt somit permanent die alten Ergebnisse. Wenn Werte nach einem Lauf plötzlich abweichen, ist dies keine Systemfehlfunktion, sondern das korrekte Greifen der Konsolidierung.

## Non-Determinism of Local Models
- Auch bei niedrigen Temperatureinstellungen (z.B. `0.1` in der `benchmark_config.yaml`) verhalten sich lokale Open-Weight Modelle (wie via Ollama / `llama.cpp`) aufgrund von Floating-Point-Berechnungen und Multithreading nicht zu 100% deterministisch.
- Leichte Abweichungen in der Formatierung einer Modell-Antwort (z. B. das Aufbrechen einer großen Tabelle in mehrere kleine) verändern den Textfluss derart, dass der LLM-Judge (z.B. Claude Haiku) zu abweichenden Bewertungen (z.B. bei der Fehlergewichtung / "Severity") gelangen kann. Dies erklärt Score-Schwankungen bei wiederholten Tests desselben Moduls und untermauert die Notwendigkeit der Durchschnittsbildung über 5 Assets.

## Python Subprocesses & Virtual Environments
- **Ausführung von Python-Skripten via `subprocess`**: Wenn innerhalb eines Python-Skripts (z. B. in Wartungs- oder CLI-Skripten) weitere Python-Prozesse aufgerufen werden, darf niemals hartkodiertes `"python"` als Befehl verwendet werden. Dies bricht oft aus dem aktiven Virtual Environment (`.venv`) aus.
- Stattdessen immer `sys.executable` verwenden, um sicherzustellen, dass der neue Prozess denselben Interpreter und dieselbe Umgebung nutzt wie der aufrufende Prozess (z.B. `cmd = [sys.executable, "update_guide.py"]`).
