# AGENTS.md

## Stack

- Python 3.12, venv (nie global)
- pytest mit `-v --tb=short`
- Typen immer annotieren (mypy-kompatibel)

---

## Verbotenes

- Keine `print()` für Debugging → `logging.debug()`
- Keine bare `except:` → immer spezifischer Exception-Typ

---

## Bekannte Fallstricke

- Code-Modelle (z.B. Hermes) neigen bei Tabellen zu Loops → `repeat_penalty` erhöhen (1.15).
- Doppelte Argumente in `kwargs`: Parameter explizit mit `.pop()` entfernen, bevor sie an den Client weitergereicht werden.
- Parser-Fallback (`_strip_thinking_tags`): Darf auf keinen Fall an `implicit_separator` (z.B. `**Answer:**`) abschneiden – korrekte Modellantworten der Tier 1/2 Reasoning-Tests werden sonst fälschlicherweise genullt. Nur explizite XML-Tags entfernen.
- **Leaderboard Missing Tests (`*` Bug):** Wenn Tests eines Moduls nicht gezählt werden, fehlt `prefix: "<name>"` im Feld `metadata` der `config.yaml`. Ohne dies filtert der `score_calculator` die Tests als "Other" heraus.
- **Asset Schema Violation:** Jede YAML-Aufgabe muss zwingend ein `prompt` (oder `prompts`) Feld haben, selbst wenn es vom Modul ignoriert wird – sonst bricht der Basis-`AssetValidator` ab.
- **LLM Judge Provider:** Jeder Provider muss von `LLMJudgeProvider` (ABC) erben und `complete()` + `health_check()` implementieren. Kein Code-Branching im Runner.
- **LLM Judge Parsing:** `judge_parser.py` muss Score-Varianten abfangen: `[4]`, `"four"`, Score auf verschiedenen Zeilen. Bei Parse-Fehler: `JudgeResult(score=None, parse_success=False)` zurückgeben – niemals Exception schlucken.
- **LLM Judge is_complete():** Prüft `judge_parse_success is not None`, NICHT `judge_score is not None`. Ein fehlgeschlagener Parse (score=None, parse_success=False) ist ein abgeschlossener Phase-3-Run. Die alte Logik behandelte ihn fälschlicherweise als "noch offen" → Deadlock-Risiko bei Overnight-Runs.
- **LLM Judge Parser – Markdown-Ausreißer:** Manche Modelle (z.B. lfm2.5-thinking:1.2b) schreiben `### **REASONING:**` und `### **SCORE: 3**` statt Plain Text. `judge_parser.py` muss Markdown-Headers (#, ##, ###) und Bold-Marker (**) vor REASONING/SCORE strippen. Fix: Regex case-insensitive mit optionalen #* Präfixen.
- **LLM Judge Latency – per-task Loading:** Jeder Judge-Aufruf lädt das Judge-Modell neu (9GB bei ministral-3:14b = ~40s Overhead pro Task). Lösung: Batch-Mode (Phase 3.5) – alle Tasks eines Moduls sammeln, einmalig laden, batch-judgen, entladen.
- **judge_health.py Hardcoding:** Modellnamen niemals hardcoden. Skript liest provider.name/model und provider.fallback.name/model aus `benchmark_config.yaml`. Bei fehlendem llm_judge-Block: sys.exit(1), kein Silent-Fallback.
- **Pipeline-Integration fehlt nach Modul-Implementierung:** JudgeRunner wird nicht automatisch in den Benchmark-Ablauf eingebunden. Nach jeder neuen Modul-Implementierung prüfen ob base_runner.py den Judge aufruft. Symptom: 60+ grep-Befehle ohne Treffer.

---

## Patterns (gelernt)

- **Dynamische Modul-Ladung / Namespace-Kollision (sys.modules):** Wenn `importlib` verwendet wird, und sich viele Plugins eine Datei auf Dateisystem-Ebene den gleichen Namen teilen (z.B. `test.py`), müssen sie programmatisch zwingend einen eindeutigen Namen erhalten (z.B. `{module_path.parent.name}_{module_path.stem}`), um Singleton-Kollisionen im globalen `sys.modules` Cache zu vermeiden. Andernfalls führt das Skript-Routing immer nur das als Erstes in den Cache geladene Modul aus.

- **LLM Judge Config SSOT:** Globale Judge-Einstellungen (Provider, Fallback, Modell,
  scale, unload_delay_ms, applicable_modules) gehören in `benchmark_config.yaml`
  unter dem Top-Level-Block `llm_judge:` – analog zu `golden_standard:`.
  Die `utils/scoring/llm_judge/config.example.yaml` ist NUR für modul-spezifische
  Overrides (auskommentiert). Globale Felder dort eintragen = Fehler. Fallback unter `provider.fallback`, NICHT auf gleicher Ebene wie `provider`. Modul-Override: `llm_judge_model:` per Modul-Eintrag im `modules:`-Block.
- **LLM Judge Attributnamen:** JudgeResult verwendet `judge_latency_ms` und
  `judge_provider_used` (mit Präfix). Nicht latency_ms oder provider_used.
  Pipeline-Integration: `judge_res.judge_latency_ms`, `judge_res.judge_provider_used`.
- **Neue Provider hinzufügen:** Erst in `benchmark_config.yaml` unter
  `providers.commercial` oder `providers.local` eintragen, dann in
  `llm_judge/providers/` eine neue Klasse anlegen, die von `LLMJudgeProvider` erbt.
  Nie einen Provider nur in der llm_judge-Config referenzieren, der nicht in
  benchmark_config.yaml definiert ist.

- **Konfig-Hierarchie:** Global (`benchmark_config`) → Modul (`config.yaml`) → Runtime. Modul-Config überschreibt Global.
- **Test-Architektur:** Neue Module müssen in Python zwingend von `BaseTest` erben und in `execute()` stets einzelne Aufgaben verarbeiten. Modul-interne Batch-Schleifen zerstören das allgemeine Leaderboard-Reporting.
- **Optional-Import Type-Hint:** Bei optional importierten Modulen (z.B. `try/except ImportError`) vor dem try-Block `Variable: Optional[Any] = None` deklarieren, nicht im except-Block → verhindert MyPy-Fehler "Cannot assign to a type".
- **LLM Judge Config:** Folgt der bestehenden Konfig-Hierarchie. `applicable_modules` in `llm_judge/config.example.yaml` definiert, welche Module den Judge nutzen. `code_quality` absichtlich ausgeschlossen (regelbasiertes Scoring zuverlässiger).
- **Optional Provider Import:** Provider-Imports in `__init__.py` mit `Optional[Any] = None` Guard absichern (bekanntes MyPy-Pattern aus `run_commercial_benchmark.py`).
- **LLM Judge Phase-Trennung:** Benchmark-Zeitmessung muss eingefroren sein, bevor der Judge lädt. VRAM-Überschneidung auf M4 Unified Memory verfälscht Messungen. Ollama-Unload (keep_alive: 0) abwarten, dann 500ms Delay, dann Judge laden.
- **PendingJudgeResult als Safety-Net:** Bei Overnight-Runs immer auf Disk persistieren. Bei Judge-Absturz kann der Score nachträglich ohne Re-Run des Benchmarks vergeben werden.
- **CSV Output Felder (ResultManager):** Alle neuen dynamischen Spalten wie `scoring_method` müssen in `utils/result_manager.py` bei `_get_updated_fieldnames` explizit zu den garantierten Feldern hinzugefügt werden, da sonst DictWriter fehlschlägt oder Felder verloren gehen.
- **Audit Mode (Logging):** Wenn neue Metriken oder Category-Scores durch Sub-Module erzeugt werden (z.B. Regex-Details), müssen diese explizit im Markdown-Logger in `save_audit_log` oder den Runners (`run_commercial_benchmark.py`, `run_local_benchmark.py`) abgebildet werden, da sie nicht automatisch aus dem DTO in den Text gerendert werden.
- **DTO Payload Konstistenz:** Wenn ein Modul lokale Variablen hat, die im Kern gemessen oder exportiert werden sollen (z.B. der interpolierte `evaluated_prompt`), muss das `BenchmarkResult` Schema (`schemas/result.py`) zwingend erweitert werden, um diese Properties ans Orchestrierungs-Level durchreichen zu können.
- **Hybrid Score Separation:** Die Gewichte für Hybrid-Scoring (Regex + Judge) liegen ausschließlich in der Modul-Spezifikation (`config.yaml`), nicht im Framework. Bei inaktivem Judge (Formel B) greift als Safety-Check immer unverfälscht der Regex-Score, um Breaking Changes zu verhindern.
- **Module Config Dictionary Propagation:** Wenn neue Top-Level-Properties in einer Modul `config.yaml` hinzugefügt werden (wie `scoring`), müssen diese manuell in `run_benchmark.py` dem internen `benchmark_info` Dictionary hinzugefügt werden (z.B. `"scoring": internal_config.get("scoring", {})`). Andernfalls werden die Werte auf dem Weg vom Registry-Loader zu den Output-Runners (`run_local_benchmark.py`) verschluckt und Defaults greifen fälschlicherweise.
