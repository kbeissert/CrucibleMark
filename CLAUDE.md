# CrucibleMark — Agent Context

> **Single Source of Truth** für KiLo, Cline, Hermes und Copilot.
> Dynamischer Projektstatus → `memory-bank/`.

## Project Overview

CrucibleMark ist ein LLM-Benchmark-Framework (Python 3.12). Strukturiertes Testen
von AI-Modellen, Bewertung mit unabhängigem LLM-Judge (Blind-Evaluierung),
Generierung von Leaderboards.

- **Sprache:** Python 3.12, venv (nie global)
- **Konfig-Hierarchie:** Global (`benchmark_config.yaml`) → Modul (`config.yaml`) → Runtime
- **Module** erben von `BaseTest`, `execute()` verarbeitet einzelne Aufgaben — keine modul-internen Batch-Schleifen
- **Memory Bank:** `memory-bank/` vor jeder neuen Task lesen (activeContext.md, progress.md, techContext.md, systemPatterns.md)

## Quick Reference

```bash
pytest -v --tb=short       # Tests
make validate              # Lint
make test                  # Full test suite
make benchmark             # Benchmark run
```

Referenzdocs: `docs/DEVELOPER_GUIDE.md`, `docs/ARCHITECTURE.md`, `docs/SETUP_GUIDE.md`

## Architecture Top Constraints

Hartcodiert, nicht verhandelbar. Detail-Referenz → [architecture.md](.agent/architecture.md):

- Judge- und Test-Phase strikt trennen — kein gemeinsamer State.
- Judge kennt Modellnamen während Bewertung NICHT (Blind-Evaluierung).
- **Sequenzielle Modell-Abarbeitung:** Modelle einzeln nacheinander, Server-Neustart zwischen Modellen, Cooldown via `AdaptivePauseCalculator`. NICHT parallelisieren (Design-Constraint, kein Performance-Bug).
- **Judge-Reset zwischen Tasks:** jede Judge-Bewertung ist ein frischer API-Call. KEIN Judge-Caching.
- **Kein Judge-Fallback auf anderes LLM:** Anthropic-Overloads (529/429/5xx) nur mit Exponential-Backoff-Retry im `health_check()` auffangen — Score-Drift zwischen Judge-Modellen verfälscht historische Benchmarks.
- Konfiguration ausschließlich über Config-Files, nie hardcodiert.
- Scoring-Logik nie stillschweigend verändern — verfälscht historische Benchmarks.
- **`vllm-start` ist NICHT idempotent für Model-Swap:** Wenn der Container bereits mit einem anderen Modell läuft, weigert sich das Script zu starten und stoppt den laufenden Container nicht automatisch. Vor jedem Modell-Wechsel via Connector immer `vllm-stop` aufrufen (siehe `swap_model()` in `utils/providers/vllm_base.py`).

## AI & API Basics

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

## Communication Style

- Code > Prosa — Erklärungen kompakt halten
- Kein Wiederholen der Aufgabenstellung am Anfang
- Keine redundanten Bestätigungen ("Ich werde jetzt X tun..." → einfach X tun)
- Bearbeite genau den beschriebenen Auftrag — kein unrequested Refactoring
- Wenn Problem außerhalb Scope: kurz erwähnen, nicht eigenständig beheben
- Kein Gold-Plating: keine zusätzlichen Features ohne explizite Anfrage

## Detailed Guidelines

- [Architecture & SSoTs](.agent/architecture.md) — BaseTest, Judge/Trennung, Token-Budget, Anthropic-Cap, Card-Naming
- [Code Style](.agent/code-style.md) — Python 3.12, Type hints, Verbote, Pytest-Fixtures
- [Data Pipeline](.agent/data-pipeline.md) — CSV atomic writes, save_results, consolidate
- [Provider & Models](.agent/provider-models.md) — Provider-Konnektoren, llama.cpp, Cohere, OpenRouter, Card-Workflow
- [Web Export & Cleanup](.agent/web-export-cleanup.md) — WebExport (vendor/provider/blacklist), Cleanup-Atomarität, Migration

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
