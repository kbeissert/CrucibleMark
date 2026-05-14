# CrucibleMark — Agent Context

> **Single Source of Truth** für Cline, Hermes und Copilot.
> Dynamischer Projektstatus → `memory-bank/` (activeContext.md, progress.md)

---

## Project Overview

CrucibleMark ist ein LLM-Benchmark-Framework (Python 3.12).
Es führt strukturierte Tests gegen verschiedene AI-Modelle durch, bewertet sie
mit einem unabhängigen LLM-Judge (Blind-Evaluierung) und generiert Leaderboards.

- **Konfig-Hierarchie:** Global (`benchmark_config.yaml`) → Modul (`config.yaml`) → Runtime
- **Module** erben von `BaseTest`, `execute()` verarbeitet einzelne Aufgaben — keine modul-internen Batch-Schleifen
- **Memory Bank:** `memory-bank/` lesen vor jeder neuen Task (activeContext.md, progress.md, techContext.md, systemPatterns.md)

---

## Code Style

- **Python 3.12**, venv (nie global), Type hints in ALLEN neuen Funktionen (mypy-kompatibel)
- **Verbote:** Kein `print()` für Debugging → `logging.debug()`, kein bare `except:`, keine Provider-Namen hardcoden → aus `benchmark_config.yaml` lesen
- Bestehende Pytest-Fixtures wiederverwenden, keine Duplikate
- Keine neuen Dependencies ohne Rückfrage — `requirements.txt` ist bewusst schlank
- Modulnamen konsistent mit bestehender Verzeichnisstruktur

---

## Architecture Rules

- Keine Änderungen am BaseTest-Erbschema ohne explizite Bestätigung
- Judge-Phase und Test-Phase strikt trennen — kein gemeinsamer State
- **LLM-Blind-Evaluierung beibehalten:** Judge kennt Modellnamen während Bewertung NICHT
- Scoring-Logik nie stillschweigend verändern — das verfälscht historische Benchmarks
- Konfiguration ausschließlich über Config-Files, nie hardcodiert

---

## Build & Test

```bash
pytest -v --tb=short       # Tests
make validate              # Lint
make test                  # Full test suite
make benchmark             # Benchmark run
```

Referenzdocs: `docs/DEVELOPER_GUIDE.md`, `docs/ARCHITECTURE.md`, `docs/SETUP_GUIDE.md`

---

## AI & API Rules

### Security (absolut)
- API Keys **NIEMALS** in Code, Logs, Kommentaren oder Git — ausschließlich `.env`
- `.env` in `.gitignore` — vor jedem Commit prüfen
- Keine API-Calls in Tests gegen Live-Endpoints — Mocks verwenden

### Datenschutz
- Datenschutzsensible Tasks: europäische oder lokale Modelle bevorzugen
- OpenAI/Anthropic nur für nicht-sensible Daten
- Lokale Modelle via Ollama für alle internen/vertraulichen Inhalte

### Modell-Routing
| Aufgabe | Modell |
|---|---|
| Reasoning, Architektur, neue Features | Claude Sonnet 4.5+ |
| Datei-Lesevorgänge, einfache Änderungen < 30 Zeilen | Claude Haiku 3.5 |
| Code-Review ganzer Dateien | Claude Haiku 3.5 |
| Lokale Tasks / Datenschutz | Ministral 8B via Ollama |
| Benchmark-Judge | separates Modell vom zu testenden Modell |

### API-Effizienz
- Prompt Caching nutzen wo möglich (`cache_control` bei Anthropic)
- Fehlerbehandlung + Retry mit Backoff bei allen API-Calls standardmäßig
- Token-Zählung bei neuen Prompts schätzen und dokumentieren

---

## Context & Cost Management (Cline/Hermes)

- Kontextauslastung > 40%: Nutzer darauf hinweisen
- Kontextauslastung > 60%: aktuellen Schritt abschließen, `new_task` starten mit diesem Format:
```
KONTEXT-ÜBERGABE:
- Projekt: [Pfad und Beschreibung]
- Erledigte Schritte: [abgeschlossene Aktionen]
- Aktueller Datei-Status: [veränderte Dateien]
- Nächste Aktion: [konkreter nächster Schritt]
- Offene Probleme: [nur wenn relevant]
```
- NIEMALS neue komplexe Subtask beginnen wenn Kontext > 50%

---

## Communication Style

- Code > Prosa — Erklärungen kompakt halten
- Kein Wiederholen der Aufgabenstellung am Anfang
- Keine redundanten Bestätigungen ("Ich werde jetzt X tun..." → einfach X tun)
- Bearbeite genau den beschriebenen Auftrag — kein unrequested Refactoring
- Wenn Problem außerhalb Scope: kurz erwähnen, nicht eigenständig beheben
- Kein Gold-Plating: keine zusätzlichen Features ohne explizite Anfrage

---

## Critical Pitfalls (Known Issues)

- **Namespace-Kollision:** Bei `importlib` mit gleichnamigen Plugin-Dateien `{parent.name}_{stem}` verwenden
- **Asset Schema:** Jede YAML-Aufgabe braucht zwingend `prompt`/`prompts`-Feld
- **Judge Parser:** Bei Parse-Fehler `parse_success=False` (niemals Exception schlucken)
- **CSV-Felder:** Neue dynamische Spalten in `result_manager.py` → `_get_updated_fieldnames` eintragen
- **Token-Budget SSoT:** `resolve_token_budget()` in `utils/model_utils.py` — nie inline duplizieren
- **`token_param_name` per Provider:** aus `benchmark_config.yaml` lesen, nie hardcoden
- **ThinkingProbe Signal-C-Verbot:** Response-Länge ist kein CoT-Signal — nur Signal A (`<think>`-Tags) und Signal B (`reasoning_tokens > 0`) verwenden
- **`_infer_provider()` — `/`-Präsenz-Heuristik:** Nie `"deepseek" in model_id` — lokale Ollama-IDs können Provider-Namen enthalten
- **Card-Naming SSoT:** `_card_path()` und `_find_card()` aus `utils/model_utils.py` — nie inline `Path(...) / f"{re.sub(...)}".json`
- **`is_accessible()` — 404 ≠ kein Zugriff:** `NotFoundError`/404 und `RateLimitError`/429 → `True` zurückgeben
- **Refusal-Flag statt Re-Run:** Antwort < 15 Zeichen → `refusal_flag=True`, kein Re-Run, kein Asset-Fix
- **OpenAI o-Series ThinkingProbe:** o1/o3-mini/o4-mini liefern keine `reasoning_tokens` → Card manuell mit `thinking_probe_manual_override: true` setzen
- **PC Skip-Logic Gap:** `execute_batch_module()` prüft nur 3 Standard-CSVs — nach Leaderboard-Reset explizit `political_compass_leaderboard.csv` als Fallback prüfen
- **Modellnamen-Normalisierung:** `save_leaderboard_csv()` in `io_manager.py` schneidet Datumssuffixe (`-YYYYMMDD` und `-MMDD` OpenRouter-Stil) automatisch ab — Modellnamen in der PC-Leaderboard-CSV sind immer suffix-frei
- **`reviews-auto` Skip-Logik:** mtime-basiert — nach jedem Benchmark-Run nur betroffene Modelle neu reviewt; `--force` deaktiviert Skip
- **Modell-Kategorisierung SSOT — nur `get_model_category()` aufrufen:** Niemals `"Open Weights (Cloud)"`, `"Open Weights (Local)"` oder `"Commercial"` als neue Kategorie-Strings verwenden. Die drei gültigen Display-Strings sind `"Proprietär"` / `"Restricted Weights"` / `"Open Weights"` — ausschließlich abgeleitet aus `weights_license_tier` in der Model Card via `get_model_category()` in `utils/model_utils.py`. Web-Export überschreibt den CSV-`Type`-Wert zur Laufzeit aus der Card — kein CSV-Rebuild nötig um Kategorien zu aktualisieren.

---

## Memory Bank

| Datei | Inhalt |
|---|---|
| `memory-bank/projectbrief.md` | Projektziele, Scope, Non-Goals |
| `memory-bank/productContext.md` | Warum CrucibleMark, Design-Philosophie |
| `memory-bank/systemPatterns.md` | Architektur-Patterns, Entscheidungen |
| `memory-bank/techContext.md` | Tech-Stack, Dependencies, Setup |
| `memory-bank/activeContext.md` | **Aktueller Sprint, offene Issues** |
| `memory-bank/progress.md` | **Was läuft, was in Arbeit, Blocker** |

> `activeContext.md` und `progress.md` werden nach jeder Session aktualisiert.
> Vor größeren Änderungen lesen — Konflikte mit laufender Arbeit vermeiden.
