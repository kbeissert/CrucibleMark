# AGENTS.md

## Stack
- Python 3.12, venv (nie global)
- pytest mit `-v --tb=short`
- Typen immer annotieren (mypy-kompatibel)

---

## Verbote
- Kein `print()` für Debugging → `logging.debug()`
- Kein bare `except:` → immer spezifischer Exception-Typ
- Keine Provider-Namen hardcoden → immer aus `benchmark_config.yaml` lesen

---

## Architektur-Regeln

**Konfig-Hierarchie:** Global (`benchmark_config.yaml`) → Modul (`config.yaml`) → Runtime.

**Module:** Müssen von `BaseTest` erben, `execute()` verarbeitet einzelne Aufgaben –
keine modul-internen Batch-Schleifen (zerstört Leaderboard-Reporting).

**LLM Judge:**
- Provider erbt von `LLMJudgeProvider` (ABC), implementiert `complete()` + `health_check()`
- Globale Einstellungen in `benchmark_config.yaml` unter `llm_judge:` (Provider, Fallback,
  Scale, applicable_modules) – nie in `config.example.yaml`
- `is_complete()` prüft `judge_parse_success is not None`, NICHT `judge_score`
- Phase-Trennung: Benchmark-Zeitmessung einfrieren → Ollama-Unload → 500ms → Judge laden
- Batch-Mode (Phase 3.5): Tasks sammeln, einmalig laden, batch-judgen, entladen

**Neue Provider:** Erst in `benchmark_config.yaml` eintragen, dann Klasse in
`llm_judge/providers/` anlegen. Nie einen Provider referenzieren, der nicht in
`benchmark_config.yaml` definiert ist.

---

## Bekannte Fallstricke

- **Namespace-Kollision:** Bei `importlib` mit gleichnamigen Plugin-Dateien eindeutigen
  Modul-Namen verwenden: `{parent.name}_{stem}` – verhindert `sys.modules` Singleton-Fehler.
- **Leaderboard Missing Tests:** Fehlendes `prefix: "<name>"` in `metadata` der
  `config.yaml` → Tests werden als "Other" herausgefiltert.
- **Asset Schema:** Jede YAML-Aufgabe braucht zwingend ein `prompt`/`prompts`-Feld,
  sonst bricht `AssetValidator` ab.
- **Parser-Fallback:** `_strip_thinking_tags` darf nur explizite XML-Tags entfernen –
  niemals an `implicit_separator` abschneiden (nullt Tier 1/2 Reasoning-Scores).
- **Judge Parser:** Muss Score-Varianten abfangen (`[4]`, `"four"`, Markdown-Headers mit
  `#`/`**`). Bei Parse-Fehler: `JudgeResult(score=None, parse_success=False)` –
  niemals Exception schlucken.
- **CSV-Felder:** Neue dynamische Spalten (z.B. `scoring_method`) müssen in
  `result_manager.py` bei `_get_updated_fieldnames` explizit eingetragen werden.
- **DTO-Konsistenz:** Lokale Modul-Variablen, die exportiert werden sollen
  (z.B. `evaluated_prompt`), müssen in `schemas/result.py` ergänzt werden.
- **Modul-Config Propagation:** Neue Top-Level-Properties in `config.yaml` (z.B.
  `scoring`) müssen in `run_benchmark.py` manuell ins `benchmark_info`-Dict übernommen
  werden – sonst greifen Defaults.
- **Optional-Import Type-Hint:** Vor dem `try/except`-Block mit
  `Variable: Optional[Any] = None` deklarieren – verhindert MyPy-Fehler.
- **Golden Standards:** `asset.yaml` ist die Single Source of Truth (SSOT). Validierung von manuell verdichteten Standards ("Design by Intention") gegen rohe LLM-Outputs erzeugt durch fehlenden "Fluff" oft False Positives.
- **Code-Modelle & Tabellen-Loops:** `repeat_penalty` auf 1.15 erhöhen.
- **Doppelte kwargs:** Parameter vor Client-Übergabe explizit mit `.pop()` entfernen.
- **PendingJudgeResult:** Bei Overnight-Runs immer auf Disk persistieren –
  ermöglicht nachträgliche Score-Vergabe ohne Re-Run.
- **Audit-Log Extraction:** Der Meta-Reviewer (`generate_review.py`) greift via Regex auf Audit-Logs zu. Bei neuen Metadaten-Blöcken (z.B. `> [!WARNING]`) muss der Parser in `generate_review.py` entsprechend erweitert werden.
- **Silent Parser Fails:** Beim Regex-Parsing (z.B. Log-Extraktion) müssen lokale Container-Variablen als Default deklariert werden, bevor try/except-Blöcke starten, um lautlose "Variable Not Bound"-Aufhänger beim Datei-Skip zu vermeiden.
- **Lazy-Imports nach God-Script-Splitting:** Werden große Provider-Dateien mit optionalen Dependencies (wie `import openai` innerhalb eines `try/except ImportError`) in mehrere kleine Module gesplittet, muss zwingend ein `pass` (oder gültiger Code) im `try`-Block verbleiben, wenn der eigentliche Import entfällt. Sonst kommt es zu fatalen `IndentationError` beim Initialisieren der Pipeline.
- **Terminal Execution Limits:** Über das API/VS Code Terminal ausgelöste mehrzeilige Skriptinjektionen (z.B. `cat << 'EOF'`) oder komplexe `sed`-Befehle werden bei großen Textblöcken häufig abgeschnitten oder fehlerhaft interpretiert; für sichere Ersetzungen native VS Code File-Edit-Tools oder dedizierte Python-Dateien verwenden.
- **Versions-Wirrwarr durch Fingerprinting:** Dynamische Modell-Hashes (z.B. zuvor via `ModelFingerprinter`) erzwingen fehlerhafte Leaderboard-Duplikate; Modell-Versionen stets über deterministisches Regex-Mapping oder feste CLI-ID-Abfragen in `get_model_version()` auflösen.
