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
- **Trennung Card-Lookup vs. Modell-Identität (ab Session 54):** `_find_card()` darf `-thinking`-Suffix-Strip nutzen (deterministischer Last-Resort-Fallback für Card-Datei-Suche). `resolve_canonical_model_id()` darf NICHT — muss `_safe_name(base)` bei Thinking-Suffix zurückgeben, damit CSV `model_id` als `{id}-thinking` erhalten bleibt. Würde `resolve_canonical_model_id` `card.model_id` zurückgeben, verschmelzen Basis- und Thinking-Profil im Leaderboard zu einer ID (CSV-Zeile wird überschrieben).
- **`thinking_mode` ist dreifach sichtbar (ab Session 55):** Eine Datenquelle (`_resolve_thinking_mode()` aus model_cfg), drei Sichtbarkeitsebenen: (1) CSV-Spalte `thinking_mode` pro Task, (2) Audit-Log-Header `**Thinking Mode:** Thinking/Standard` pro `.md`-Datei (sichtbar für Mensch), (3) Review-Prompt `{model_thinking_mode}` als hartes Datenfeld (LLM-Reviewer sieht Runtime-Modus, rät nicht aus Architektur-Tags). Pflicht: jede Runtime-Config, die den Reviewer beeinflusst, MUSS als hartes Datenfeld im Prompt stehen — nicht aus Modellnamen oder Architektur-Tags ableiten lassen.
- **`{hardware_context}` muss pro-Modell korrekt sein (ab Session 56):** `SystemContextManager.get_editor_prompt_injection()` injiziert Hardware-Info in den Reviewer-Prompt. Der `hardware_profile`-Key kommt aus `provider_config.yaml` (SSoT), aufgelöst gegen `benchmark_config.yaml:runner_environment.profiles`. **Jeder in `provider_config.yaml` genutzte `hardware_profile`-Key MUSS in `benchmark_config.yaml` definiert sein** — sonst fällt der Lookup auf `active_profile` (M4) zurück und der Reviewer zitiert die falsche Hardware. Fallback-Kette: (1) Provider-Config-Lookup → (2) rohe CSV `hardware_profile`-Spalte → (3) `active_profile`. Die Sperrklausel im Prompt verbietet Hardware-Spekulation, funktioniert aber NUR wenn `{hardware_context}` die korrekte Hardware liefert.
- **Local-Template konditional auf Speichergröße (ab Session 56):** `system_context.py` verwendet zwei Local-Templates: bei `ram_gb < 64` (memory-constrained, z.B. M4 mit 24 GB) wird "Swapping-Risiken" als legitimer Diskurspunkt genannt; bei `ram_gb >= 64` (ample, z.B. Spark/GX10 mit 115 GB) wird "Speicher ist hier kein Engpass" formuliert — keine Speicher-Spekulation. Verhindert, dass der Reviewer Timeouts auf ample Hardware fälschlich dem Speicher zuschreibt.

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
| `-thinking`-Suffix-Fallback in Card-Lookup (ab Session 54) | `utils/model_utils.py:_find_card()` — Last-Resort-Fallback wenn `model_cfg is None` und `lookup_id.endswith("-thinking")`. Streift `-thinking` deterministisch ab und ruft `_find_card(base_id, card_dir)` rekursiv. Analog zu `strip_date_suffix`. **Trennung:** `_find_card` darf Suffix-Strip nutzen (Card-Datei-Suche); `resolve_canonical_model_id` darf NICHT (würde Profil-Identität im Leaderboard verschmelzen). |
| `thinking_mode`-Spalte erfasst Runtime-Konfiguration (ab Session 54) | `utils/base_runner.py:_resolve_thinking_mode()` + `scripts/leaderboard/exporter.py` | Neue Methode `_resolve_thinking_mode(model, provider)` leitet aus model_cfg ab: `card_model_id` → `"Thinking"`; `chat_template_kwargs.enable_thinking` → `"Thinking"`/`"Standard"`; `enable_thinking` (llama.cpp) → `"Thinking"`/`"Standard"`; sonst `"n/a"`. CSV-Spalte + Leaderboard-Spalte "Thinking Mode" zwischen `Speed Profile` und `Total Score`. Trennung: `thinking_mode` = Runtime-Config (pro-Run); `thinking_probe_detected` = Capability (stabil). |
| Display-Name-Sharing für Thinking-Profile (ab Session 54) | `scripts/leaderboard/module_integration.py:_add_thinking_profile_names()` | Ergänzt `display_lookup` für Thinking-Profile: iteriert `providers.local.<key>.models[]` (nested!), findet Modelle mit `card_model_id`, trägt `display_lookup[profile_id] = display_lookup[card_ref]` ein. Aufgerufen in `_get_lookups()` nach `_build_card_lookups()`. Beide Profile zeigen denselben Display-Namen, Unterscheidung über `model_id` + `thinking_mode`. |
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
