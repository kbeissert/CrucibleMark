# AGENTS.md

> Projektanweisungen für Kilo und andere AI-Agenten. Vollständiger Kontext: [CLAUDE.md](CLAUDE.md). Dynamischer Status: `memory-bank/`.

## Projekt

CrucibleMark — modulares LLM-Benchmark-Framework (Python 3.12). Testet AI-Modelle gegen praxisnahe Aufgaben (Code-Reviews, UX-Texte, Reasoning, Tool-Use, Political Compass), bewertet blind über einen unabhängigen LLM-Judge und generiert Leaderboards.

**Stand:** v5.1.0 · 2026-08-02 · Production-Ready

## Session-Start

Vor jeder neuen Task diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus, offene Punkte
2. `memory-bank/progress.md` — Release-Historie
3. `memory-bank/systemPatterns.md` — Architektur-Regeln, SSoT-Brücken, Pitfalls

Regel: Nur aktive, ungelöste Themen als Baustelle melden. Abgeschlossene Integrationen, akzeptierte Known Limitations und BACKLOG-Items sind KEINE Baustellen.

## Quick Commands

```bash
make benchmark-auto          # Vollautomatischer Batch-Run
make validate                # Lint (ruff + pylint)
make validate-naming         # Naming-Validator (Publication-Gate, Session 76)
make validate-csv            # CSV-Sanitizer
make test                    # Full test suite (pytest)
make leaderboard             # Leaderboard regenerieren
make tooluse-leaderboard     # ToolUse-Leaderboard aggregieren
make web-export              # Web-Export-Pipeline (hard gate: Naming-Validator)
make web-export-dev          # Export ins Dev-Frontend (warn-only)
make model-cards MODEL=<id>  # Neues Model Card Template
make probe-thinking MODEL=<id>  # Thinking-Probe für ein Modell
make clean-model MODEL=<id>  # Modell vollständig entfernen
make mcp-start / mcp-stop    # Benchmark-MCP-Server starten/stoppen
make docs-version-check      # Doku-Stempel-Drift prüfen
make docs-version-sync YES=1 # Doku-Stempel auf aktuelle Version angleichen
```

## Architektur-Regeln (unverhandelbar)

1. **Separation of Concerns:** Measurement = autonom/ausfallsicher. Publishing = strikt offline.
2. **SSoT/DRY/SRP:** Eine Funktionalität = ein Modul. Fail-Fast ohne versteckte Fallbacks. Import statt Duplikation.
3. **Config-Driven, No Magic Numbers:** Alle Regeln/Zahlen/Limits in YAML. CC ≤ 12 (`ruff.toml` C901).
4. **Anti-God-Script:** Logische Submodule auslagern, Haupt-Skript bleibt schlank.

## Design-Constraints (nicht optimierbar)

- **Sequenzielle Modell-Abarbeitung:** Modelle einzeln nacheinander, Server-Neustart zwischen Modellen, Cooldown. NICHT parallelisieren.
- **Judge-Reset zwischen Tasks:** Jede Bewertung ist ein frischer API-Call. KEIN Judge-Caching.
- **Blind-Evaluierung:** Judge kennt Modellnamen NICHT.
- **Kein Judge-Fallback:** Anthropic-Overloads nur mit Backoff-Retry — niemals anderes LLM als Ersatz-Judge.
- **Judge-Prompts unveränderlich während laufender Tests:** Änderungen brechen Vergleichbarkeit.
- **Scoring-Logik nie stillschweigend verändern:** Verfälscht historische Benchmarks.

## Security

- API Keys **NIEMALS** in Code, Logs, Kommentaren oder Git — ausschließlich `.env`.
- `.env` in `.gitignore` — vor jedem Commit prüfen.
- Keine API-Calls in Tests gegen Live-Endpoints — Mocks verwenden.

## Konfig-Hierarchie

1. `benchmark_config.yaml` — Token-Budgets, Module, Runner-Environment (SSoT für Modul-Aktivierung)
2. `config/provider_config.yaml` — Modelle, Provider, Hardware-Profile, Sampling
3. Modul-`config.yaml` — Modul-spezifisch
4. `.env` — API-Keys (außerhalb von Git)
5. `config/web_export_blacklist.yaml` — Web-Export-Sperren

## Memory-Bank vs. Kilo-Local-Memory

`memory-bank/` ist die **einzige Content-SSoT** für dauerhaftes Projektwissen — sichtbar für alle Agenten. Kilo-Local-Memory ist Index/Zeiger nur.

- Durable Inhalte (Facts, Decisions, Patterns) → `memory-bank/systemPatterns.md` bzw. `progress.md`
- Kilo-Local: Session-Digests, dünne Zeiger, operative Pfade/Commands

## Referenzen

- [CLAUDE.md](CLAUDE.md) — Vollständiger Agent-Kontext (Constraints, Pitfalls, Modell-Routing)
- [.agent/architecture.md](.agent/architecture.md) — SSoT-Brücken, BaseTest, Token-Budget
- [.agent/code-style.md](.agent/code-style.md) — Python 3.12, Type hints, Verbote
- [.agent/data-pipeline.md](.agent/data-pipeline.md) — CSV atomic writes, save_results
- [.agent/provider-models.md](.agent/provider-models.md) — Provider-Konnektoren, Card-Workflow
- [.agent/web-export-cleanup.md](.agent/web-export-cleanup.md) — WebExport, Cleanup, Migration
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Layer-Architektur, Provider-Abstraktion
- [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) — Entwicklerhandbuch
- [CHANGELOG.md](CHANGELOG.md) — Vollständige Versionshistorie
