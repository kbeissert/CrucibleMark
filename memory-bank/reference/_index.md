# Reference Index

Cold files. **Nur laden, wenn der aktuelle Task es explizit erfordert.**
Hot files (`activeContext.md`, `progress.md`, `systemPatterns.md`) reichen für 95 % der Sessions.

| Datei | Zweck | Wann lesen |
|---|---|---|
| `decisions-log.md` | v3.x–v4.6.x Meilensteine, Reasoning-Aware-Backlog mit Re-Aktivierungs-Bedingung | Bei Architektur-Diskussionen, „warum haben wir X?"-Fragen |
| `data-schema.md` | Model-Card-Schema, Provider-Card-Schema, Benchmark-CSV-Spalten | Bei Card-Erstellung, CSV-Sanitizer, Leaderboard-Debugging |
| `feedback_schema.md` | Tool Use Schema Architektur v3.11.0 — Separation of Concerns, SSoT-Integrität, Null-Toleranz für Halluzinationen (tooluse003) | Bei Tool Use Asset-Erstellung, Scoring-Drift, Schema-Änderungen |
| `tooluse_module.md` | Tool Use Modul v3.11.0 — Architektur, Pitfalls, Golden Standard v1.3.0, AUTHORIZED_TOOLS-Aliases, MCP-Config, P1-Scoring-Stufen | Bei Tool Use Benchmark-Arbeit, MCP-Änderungen, bekannten Modul-Bugs |
| `social-media-archive.md` | Social-Media-Plan (separates Projekt, inaktiv) | Nur bei Social-Media-Fragen |
| `pitfall-diagnoses.md` | Detaillierte Bug-Diagnosen (Qwen 3.6 Hang, Hermes-Retries, ToolUse-Sanierung 8 Modelle, llama.cpp Timeouts) | Bei konkretem Fehlerbild mit Similarity zu dokumentierten Fällen |
| `architecture.md` | Architektur-Invariants, SSoT-Tabelle (Token-Budget, Card-Lookup, Thinking-Profile-Expansion), Dead-Model-Handling-Workflow | Bei Architektur-Änderungen an Runner, Card-Lookup oder Thinking-Profilen |
| `code-style.md` | Python-3.12-Konventionen, Verbote (print, bare except, hardcodierte Provider), Plugin-Laden | Bei Code-Reviews und neuen Modulen |
| `data-pipeline.md` | CSV-Upsert-Semantik, atomare Writes, Write-Through, Recovery-Sequenz, Judge-Parser | Bei CSV-IO, Konsolidierung, Korruptions-Recovery |
| `provider-models.md` | Provider-Connector-Verträge (reasoning_tokens, think_content, usage), Model-ID-Konventionen, Thinking-Probe, Pricing | Bei Provider-Änderungen, Model-Card-Workflow, Thinking-Integration |
| `web-export-cleanup.md` | WebExport-Pipeline, Cleanup- und Migrations-Regeln | Bei Web-Export-Änderungen und Bereinigungen |
| `heartbeat-v474-detail.md` | v4.7.4 Heartbeat-Configurable Implementation (Code, Config, Tests) | Bei Heartbeat-Tuning oder Wiederherstellung des Original-Verhaltens |

**Letzte Aktualisierung:** 2026-08-15
