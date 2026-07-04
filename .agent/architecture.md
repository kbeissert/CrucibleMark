# Architecture & SSoTs

Detail-Referenz für CrucibleMark-Architektur-Constraints. Die Top-Constraints stehen in [`CLAUDE.md`](../CLAUDE.md); hier nur, was darüber hinausgeht.

## Architektur-Invariants

- **Keine Änderungen am BaseTest-Erbschema** ohne explizite Bestätigung.
- **Judge-Phase und Test-Phase strikt trennen** — kein gemeinsamer State.
- **LLM-Blind-Evaluierung beibehalten:** Judge kennt Modellnamen während Bewertung NICHT.
- **Scoring-Logik nie stillschweigend verändern** — das verfälscht historische Benchmarks.
- **Konfiguration ausschließlich über Config-Files**, nie hardcodiert.
- **Sequenzielle Modell-Abarbeitung (Design-Constraint):** Modelle werden einzeln nacheinander getestet, Server wird zwischen Modellen neu gestartet, Cooldown via `AdaptivePauseCalculator`. Das ist KEIN Performance-Bug — es garantiert gleichwertige Testumgebungen. **NICHT parallelisieren.**
- **Judge-Reset zwischen Tasks:** jede Judge-Bewertung ist ein frischer API-Call ohne Kontext aus vorherigen Bewertungen. KEIN Judge-Caching einführen — verhindert Kontextmix.

## Single Sources of Truth (SSoT)

| Thema | SSoT-Aufruf |
|---|---|
| Token-Budget pro Modell | `resolve_token_budget()` in `utils/model_utils.py` — nie inline duplizieren |
| Card-Pfad & -Lookup | `_card_path()` und `_find_card()` in `utils/model_utils.py` |
| Model-ID intern ↔ config/API | `internal_id_to_config_form()` in `utils/model_utils.py` |
| Modell-Kategorisierung (Display) | `get_model_category()` in `utils/model_utils.py` |
| Thinking-Erkennung (Override > Probe > None) | `resolve_effective_thinking()` in `utils/model_utils.py` |
| `_safe_name()` für Datei-/Verzeichnis-Namen | `utils/model_utils.py` — Pflicht für `outputs/audit_logs/<slug>/` und `docs/reviews/<slug>/` |
| GGUF Post-Apply-Korrekturen | `_ensure_gguf_conventions()` in `manage_model_cards.py` |

## Anthropic `max_tokens` (aktuell)

- Provider-Default (`provider_config.yaml`): **32768**.
- Per-Model Override für `claude-haiku-4-5-20251001`: **8192** (Desktop-Klasse).
- Bei neuen Claude-Modellen prüfen, ob der Default ausreicht — Claude 4.x unterstützt bis 128K Output, aber 32768 deckt alle Reasoning-Budgets ab (max. 20000 bei `code_quality`).

Versions-Historie und Audit-Trail (v4.10.6: 8192→32768, `fallback_max_tokens` entfernt) siehe [`.agent/provider-models.md`](provider-models.md).

## CI@500-Artefakt (Memory)

Aktuelles Cultural-Intelligence-Budget: **3000 (Standard) / 4000 (Reasoning)**.
- Achtung: Wenn `token_limit_used` in alten Audit-Logs **500** zeigt, sind diese Runs veraltet (vor v4.10.6).

Historische Bereinigung (130 Zeilen / 26 Modelle) siehe [`.agent/provider-models.md`](provider-models.md).

## `token_param_name` per Provider

Aus `benchmark_config.yaml` lesen, nie hardcoden.

## Dead-Model-Handling (Workflow)

Wenn ein Modell bei einem Benchmark-Lauf `Model not found` / HTTP 400 (invalid-argument) zurückgibt:

1. Alle Modelle des Providers gegen die API prüfen (`/v1/models` o.ä.).
2. **User fragen**, ob die toten Modelle in `provider_config.yaml` auskommentiert werden sollen.
3. Einträge in `config/web_export_blacklist.yaml` ergänzen (Blacklist = Web-Export-Sperre).
4. Bestehende CSV-Einträge für 0.0-Scores aufräumen.

**NIEMALS eigenständig auskommentieren** — immer den User bestätigen lassen.
