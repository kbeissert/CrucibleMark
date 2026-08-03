# AGENTS.md

> Projektweite Anweisungen für Kilo und andere AI-Agenten. Diese Datei ist die generische SSoT für Arbeitsweise, Architektur und Sicherheitsregeln.
> Dynamischer Projektstatus steht in `memory-bank/`.

## Projekt

CrucibleMark ist ein modulares LLM-Benchmark-Framework für Python 3.12. Es testet AI-Modelle gegen praxisnahe Aufgaben, bewertet Antworten blind über einen unabhängigen LLM-Judge und generiert Leaderboards.

**Stand:** v5.1.2 · 2026-08-03 · Production-Ready

## Session-Start

Vor jeder neuen Task diese Dateien lesen:

1. `memory-bank/activeContext.md` — aktueller Fokus und offene Punkte
2. `memory-bank/progress.md` — Release-Historie
3. `memory-bank/systemPatterns.md` — Architektur-Regeln, SSoT-Brücken und Pitfalls

Regel: Nur aktive, ungelöste Themen als Baustelle melden. Abgeschlossene Integrationen, akzeptierte Known Limitations und BACKLOG-Items sind keine Baustellen.

## Quick Commands

```bash
make benchmark-auto            # Vollautomatischer Batch-Run
make validate                  # Lint (Ruff und Pylint)
make validate-naming           # Naming-Validator (Publication-Gate)
make validate-csv              # CSV-Sanitizer
make test                      # Full Test Suite (pytest)
make leaderboard               # Leaderboard regenerieren
make tooluse-leaderboard       # ToolUse-Leaderboard aggregieren
make web-export                # Web-Export-Pipeline (Hard-Gate)
make web-export-dev            # Export ins Dev-Frontend (Warn-only)
make model-cards MODEL=<id>    # Neues Model-Card-Template
make probe-thinking MODEL=<id> # Thinking-Probe für ein Modell
make clean-model MODEL=<id>    # Modell vollständig entfernen
make mcp-start / mcp-stop      # Benchmark-MCP-Server starten oder stoppen
make docs-version-check        # Doku-Stempel-Drift prüfen
make docs-version-sync YES=1   # Doku-Stempel angleichen
```

## Architektur-Regeln (unverhandelbar)

1. **Separation of Concerns:** Measurement arbeitet autonom und ausfallsicher. Publishing arbeitet strikt offline.
2. **SSoT, DRY und SRP:** Eine Funktionalität gehört in ein Modul. Fail-Fast ohne versteckte Fallbacks. Import statt Duplikation.
3. **Config-Driven, No Magic Numbers:** Regeln, Zahlen und Limits stehen in YAML. Die zyklomatische Komplexität bleibt bei höchstens 12 (`ruff.toml`, C901).
4. **Anti-God-Script:** Logische Submodule auslagern. Hauptskripte bleiben schlank.

## Design-Constraints (nicht optimierbar)

- **Sequenzielle Modell-Abarbeitung:** Modelle einzeln nacheinander testen, Server zwischen Modellen neu starten und Cooldown einhalten. Nicht parallelisieren.
- **Judge-Reset zwischen Tasks:** Jede Bewertung ist ein frischer API-Call. Kein Judge-Caching.
- **Blind-Evaluierung:** Der Judge kennt die Modellnamen nicht.
- **Kein Judge-Fallback:** Anthropic-Overloads nur mit Exponential-Backoff-Retry behandeln. Nie ein anderes LLM als Ersatz-Judge verwenden.
- **Judge-Prompts unveränderlich halten:** Änderungen während laufender Tests brechen die Vergleichbarkeit.
- **Scoring-Logik nicht stillschweigend ändern:** Das verfälscht historische Benchmarks.
- **`vllm-start` nicht als idempotent behandeln:** Vor einem Modellwechsel den Server über `vllm-stop` stoppen. Die Details stehen in `.agent/architecture.md`.
- **vLLM-Server nicht unnötig neu starten:** Der Start kann mehrere Minuten dauern. Während Diagnose und Tests gegen den laufenden Server arbeiten.
- **Reports als flüchtig behandeln:** Benchmark-Reports werden pro Lauf überschrieben. Verbindlich sind die versionierten Ergebnisdateien in `outputs/runs/`.
- **ToolUse-Leaderboard bereinigen:** `tooluse_leaderboard.csv` ist ein Upsert-File. Bei Modell-ID-Renames alte IDs vor der Aggregation entfernen.
- **Selektives Reasoning beachten:** Modelle, die selbst entscheiden, wann sie denken, dürfen keine Always-Thinking-Konfiguration erhalten. `enable_thinking: true` kann sonst eine falsche Dual-Profile-Expansion auslösen.
- **`# noqa: C901` nicht verwenden:** Die CC-≤-12-Regel bleibt verbindlich. Stattdessen Methoden nach Pfaden aufteilen.

## Security

- API-Keys niemals in Code, Logs, Kommentaren oder Git speichern. Ausschließlich `.env` verwenden.
- `.env` muss in `.gitignore` stehen. Vor jedem Commit prüfen.
- Tests dürfen keine Live-Endpoints aufrufen. Mocks verwenden.

## Datenschutz und API-Nutzung

- Datenschutzsensible Tasks bevorzugt mit europäischen oder lokalen Modellen ausführen.
- Öffentliche Cloud-Provider nur für nicht sensible Daten verwenden.
- Bei API-Fehlern standardmäßig Retry mit Exponential-Backoff einsetzen.
- Neue Prompts auf Token-Verbrauch prüfen und das Budget dokumentieren.

## Konfig-Hierarchie

1. `benchmark_config.yaml` — Token-Budgets, Module und Runner-Environment (SSoT für Modul-Aktivierung)
2. `config/provider_config.yaml` — Modelle, Provider, Hardware-Profile und Sampling
3. Modul-`config.yaml` — modulspezifische Einstellungen
4. `.env` — API-Keys außerhalb von Git
5. `config/web_export_blacklist.yaml` — Web-Export-Sperren

## Arbeitsweise für Agenten

- Bestehende Fixtures und SSoT-Funktionen wiederverwenden. Keine parallelen Sonderlösungen einführen.
- Den beschriebenen Auftrag bearbeiten. Kein unangefordertes Refactoring und kein Gold-Plating.
- Erklärungen kompakt halten und technische Entscheidungen direkt dokumentieren.
- Bei Problemen außerhalb des Scopes nur den Befund nennen. Nicht eigenständig den Scope erweitern.
- Vor Änderungen an laufenden Benchmarks die Race-Condition-Regel beachten: Core-Module während eines Runs nicht verändern.

## Memory-Bank vs. Kilo-Local-Memory

`memory-bank/` ist die **einzige Content-SSoT** für dauerhaftes Projektwissen und für alle Agenten sichtbar. Kilo-Local-Memory ist nur Index und Zeiger.

- Durable Inhalte wie Facts, Decisions, Corrections und Patterns → `memory-bank/systemPatterns.md` bzw. `memory-bank/progress.md`
- Kilo-Local-Memory → Session-Digests, dünne Zeiger sowie operative Pfade und Commands

## Referenzen

- [.agent/architecture.md](.agent/architecture.md) — SSoT-Brücken, BaseTest und Token-Budget
- [.agent/code-style.md](.agent/code-style.md) — Python 3.12, Type Hints, Verbote und Pytest-Fixtures
- [.agent/data-pipeline.md](.agent/data-pipeline.md) — CSV-Atomic-Writes, `save_results()` und Konsolidierung
- [.agent/provider-models.md](.agent/provider-models.md) — Provider-Konnektoren, Thinking und Model-Card-Workflow
- [.agent/web-export-cleanup.md](.agent/web-export-cleanup.md) — WebExport, Cleanup und Migration
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Layer-Architektur und Provider-Abstraktion
- [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) — Entwicklerhandbuch
- [CHANGELOG.md](CHANGELOG.md) — Vollständige Versionshistorie
