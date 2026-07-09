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
- **vLLM-Thinking-Profile-Expansion nur für `api_type == "vllm"`:** `_expand_thinking_profiles()` darf NUR vLLM-Provider expandieren. llama.cpp's `enable_thinking` ist ein Server-Start-Flag (per-Server, nicht per-Request) — Expansion würde zwei Profile mit unterschiedlichem Server-Flag erzeugen, die dennoch neu starten müssen. Nur vLLM's `enable_thinking` ist ein Chat-Template-Kwarg, der per-Request via `chat_template_kwargs` gesteuert wird.

## Single Sources of Truth (SSoT)

| Thema | SSoT-Aufruf |
|---|---|
| Token-Budget pro Modell | `resolve_token_budget()` in `utils/model_utils.py` — nie inline duplizieren |
| Card-Pfad & -Lookup | `build_card_id()` = alleinige SSoT für Schreibpfad (SUFFIX `{base}--{shortcode}.json`). `_card_path(for_write=True)` und `ensure_card(provider=X)` rufen `build_card_id()` auf — erzeugen KEINE PREFIX-Form. `_find_card()` Read-Reihenfolge: SUFFIX → legacy PREFIX (`{shortcode}_{base}`) → unprefixed. Direkte `_card_path()`-Aufrufer müssen `provider=X` übergeben, sonst entsteht unprefixed Pfad → Duplikate. |
| Card-Felder-Separierung (`model_version`/`model_variant`/`quantization_format`) | `model_version` = **reine Versionsnummer** ("3.5", "4", "1.0", "4.0") — ist Leaderboard-Groupby-Key, Split bei Inkonsistenz. Quant/Format-Tokens (`Q8_0 GGUF`, `FP8`, `NVFP4`) → `quantization_format`. Interne Fein-Tune-/Variant-Namen (MTP, Coder-MTP, Ortenzya Wordsmith, E4B, QAT, Abliterated) → `model_variant`. Hardware bleibt in `hardware_profile` (CSV-Spalte + Provider-Config), NICHT in `model_version`. Bei Card-First-Override in `get_model_version()` müssen Card + CSV `model_version`-Spalte atomar zusammen migriert werden. |
| Model-ID intern ↔ config/API | `internal_id_to_config_form()` in `utils/model_utils.py` |
| Modell-Kategorisierung (Display) | `get_model_category()` in `utils/model_utils.py` |
| Thinking-Erkennung (Override > Probe > None) | `resolve_effective_thinking()` in `utils/model_utils.py` |
| `_safe_name()` für Datei-/Verzeichnis-Namen | `utils/model_utils.py` — Pflicht für `outputs/audit_logs/<slug>/` und `docs/reviews/<slug>/` |
| vLLM Dual-Thinking-Profile Expansion | `utils/config_validator.py:_expand_thinking_profiles()` — aufgerufen in `_load_config` nach Merge, vor `_check_duplicate_model_ids`. Nur für `api_type == "vllm"`. Generiert aus `enable_thinking: true` zwei Profile: Standard (`{id}`, `chat_template_kwargs: {enable_thinking: false}`) + Thinking (`{id}-thinking`, `card_model_id: {id}`, `chat_template_kwargs: {enable_thinking: true}`, `max_tokens: thinking_max_tokens}`). `thinking_max_tokens`-Quelle: model_cfg > provider > Fehler (kein Hardcoding). |
| vLLM Swap-Entkopplung (Profile-Wechsel ohne Neustart) | `utils/providers/vllm_base.py:_active_config` — trackt TOML-Config des aktiven Modells. `_ensure_model_ready` vergleicht `config:` statt `model_id`: gleiche `config:` → kein `swap_model`, nur per-Request-Param-Wechsel. Backward-compat: `_active_config is None` → bisheriges Verhalten. |
| `card_model_id`-Redirect (Card-Lookup für Thinking-Profile) | `utils/model_utils.py:_find_card()` + `resolve_canonical_model_id()` — akzeptieren optional `model_cfg`. Wenn `card_model_id` vorhanden → Card-Lookup über dieses Feld. `resolve_canonical_model_id` gibt Profile-eigene `_safe_name(base)` zurück (nicht Card's `model_id`) — CSV `model_id` bleibt `{id}-thinking`. `enforce_card_first()` + `ResultManager._find_model_cfg()` threaden `model_cfg` durch. |
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
