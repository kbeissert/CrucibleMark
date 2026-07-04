# Provider & Models

Provider-Konnektoren, Model-Card-Workflow, Model-ID-Konventionen, Provider-spezifische Quirks. Versions-Audit-Trail zu SSoTs aus `architecture.md`.

## Provider-Connector Thinking/Reasoning-Extraktion (SSoT in `base.py`)

Jeder Provider-Connector MUSS drei Felder in `last_response_metadata` speichern:

1. **`reasoning_tokens`** — via `self._extract_reasoning_tokens(usage)` (SSoT in `base.py`). Auto-Routing:
   - `completion_tokens_details` (OpenAI-kompatibel)
   - `output_tokens_details` (Anthropic)
   - `usage.reasoning_tokens` (Mistral)
   - Google: inline `thoughts_token_count`
   - Ollama: inline `eval_count`
2. **`think_content`** — Non-Streaming via `self._extract_think_from_message(msg)`. Streaming via `ThinkAccumulator` (SSoT in `base.py`). Anthropic/Google/Ollama: provider-spezifisch.
3. **`usage`** — vollständiges `response.usage`-Objekt für `LLMParser.extract_usage_tokens()` (`llm_client.py:244`). OHNE `usage` fällt die Pipeline auf `estimate_tokens()` zurück. **NIEMALS weglassen.**

**NIEMALS eigene Inline-Extraction schreiben** — immer die Base-Utilities verwenden.

Konsumenten:
- `base_runner.py:159` (Reasoning-Budget)
- `judge_evaluator.py:272` (Thinking-Aufwand)
- `benchmark_utils.py:382` (Audit-Log)

## Versions-Audit zu SSoTs (historischer Kontext)

Versions-Notizen, die in `architecture.md` nur als aktive Regel stehen.

### Anthropic `max_tokens` v4.10.6

Default von 8192 → 32768 angehoben. `fallback_max_tokens` als Dead Config entfernt. Per-Model Override `claude-haiku-4-5-20251001: 8192` (Desktop-Klasse). Begründung: Claude 4.x deckt mit 32768 alle Reasoning-Budgets ab (max. 20000 bei `code_quality`).

### CI@500-Artefakt v4.10.6 (bereinigt)

Cultural Intelligence lief bis April/Mai 2026 mit `token_limit_used=500`. 130 Zeilen / 26 Modelle entfernt. Aktuelles Budget siehe `architecture.md`. Audit-Logs älter als v4.10.6 mit `token_limit_used=500` sind veraltet.

## Model-ID-Namenskonvention (zwei Formen)

- **Intern** (`model_id` in Cards, CSVs, Leaderboard): Underscore-Form — keine Punkte, nur Bindestriche und Unterstriche (`gpt-5_5-pro`, `xiaomi/mimo-v2_5-pro`).
- **Provider-Config (`id`-Feld) und API-Calls**: Originale Schreibweise mit Punkten (`gpt-5.5-pro`, `xiaomi/mimo-v2.5-pro`).
- SSoT-Konvertierung intern→config/API: `internal_id_to_config_form()` in `utils/model_utils.py`.
- **NIEMALS eigene Alias-Dicts pro Provider führen** — die generische Funktion deckt 95% der Fälle ab.
- Ausnahme: OpenRouter `z-ai/glm_*`-Modelle, wo `_safe_name()` Bindestriche und Punkte gleichermaßen zu `_` konvertiert (Ambiguität).
- Editor-Prompt: `config/editor_prompts.yaml → model_onboarding`.

## `_find_card()` Dot→Hyphen-Fallback (ab v4.10.7)

`_safe_name()` konvertiert Punkte→Unterstriche, aber Cards aus provider_config-IDs mit Bindestrichen behalten Bindestriche im Dateinamen (z.B. `grok-4-1-fast-reasoning.json` statt `grok-4_1-fast-reasoning.json`). Der Dot→Hyphen-Fallback in `_find_card()` schließt diese Lücke.

## Card-Naming SSoT

`_card_path()` und `_find_card()` aus `utils/model_utils.py` — nie inline `Path(...) / f"{re.sub(...)}".json`.

- `-latest`-Aliases mit bekannter Version werden unter `{base}-{version}.json` abgelegt (`mistral-large-latest` → `mistral-large-3.json`).
- Die `model_id` *in der Card* bleibt immer der API-Alias.

## `_safe_name()` zwingend (Audit-Log + Review Dirs)

- Jedes Schreiben in `docs/reviews/{slug}/` und `outputs/audit_logs/{slug}/` MUSS `_safe_name(model_id)` nutzen — nie `subdir.name` oder rohe Audit-Log-Ordnernamen.
- Ohne Normalisierung entstehen parallele Verzeichnisse (z.B. `xiaomi_mimo-v2.5/`-DOT-Dirs parallel zu `xiaomi_mimo-v2_5/`-Underscore-Dirs), die im Web-Export Key-Kollisionen auslösen.
- `audit_logger.py` (`AuditLogWriter.write_audit_log()`) und `PoliticalCompassTest.execute()` in `benchmark_modules/political_compass/` müssen `.replace(":", "_").replace("/", "_").replace(".", "_")` enthalten.

## Pricing SSoT

Neue Preise gehören als `input_price_per_1m` / `output_price_per_1m` (USD/1M Tokens) ausschließlich in die Model Card JSON (`benchmark_scores/model_cards/*.json`).

## Modell-Kategorisierung SSoT

NIEMALS `"Open Weights (Cloud)"`, `"Open Weights (Local)"` oder `"Commercial"` als neue Kategorie-Strings verwenden. Die drei gültigen Display-Strings sind `"Proprietär"` / `"Restricted Weights"` / `"Open Weights"` — ausschließlich abgeleitet aus `weights_license_tier` in der Model Card via `get_model_category()` in `utils/model_utils.py`.

Web-Export überschreibt den CSV-`Type`-Wert zur Laufzeit aus der Card — kein CSV-Rebuild nötig um Kategorien zu aktualisieren.

## Thinking-Erkennung SSoT

NIEMALS eigene Override/Probe-Logik inline schreiben. Die SSoT-Auflösung (Override > Card-Probe > None) liegt in `utils/model_utils.resolve_effective_thinking(model_card, provider_model_cfg, *, model_id, now)`.

- Für Token-Budget: `resolve_token_budget()` mit `provider=provider`-kwarg aufrufen (SSoT-Auflösung greift automatisch).
- Card-First-Property: Probe-Ergebnisse aus `thinking_probe_detected` sind robuster als String-Trigger im Modellnamen.
- Override-Schema in `config/card_template_provider.yaml` (Optionalfeld, `since v4.7.1`): `value` bool-Pflicht, `reason` Pflicht (Whitespace-only zählt als leer), `active_until` optional (ISO-8601, naive wird UTC). Drift-Schutz durch Auto-Expiry.
- Methodik: `docs/THINKING_PROBE.md`.

### ThinkingProbe Signal-C-Verbot

Response-Länge ist kein CoT-Signal — nur Signal A (`<</think>>`-Tags) und Signal B (`reasoning_tokens > 0`) verwenden.

### OpenAI o-Series ThinkingProbe

o1/o3-mini/o4-mini liefern keine `reasoning_tokens` → Card manuell mit `thinking_probe_manual_override: true` setzen.

### llama.cpp Native Thinking (`reasoning_content`)

Modelle wie Gemma-4 E4B geben Reasoning im Feld `reasoning_content` zurück (nicht im Standard-`content`). `llamacpp.py` extrahiert dieses Feld und setzt `reasoning_tokens = completion_tokens`. Probe erkennt das nicht → Card manuell: `thinking_probe_detected: true` + `thinking_probe_manual_override: true`.

### llamacpp `think_content` Key-Mismatch (Session 26)

`_extract_response_content()` in `llamacpp_base.py` speicherte `"thinking_content"` statt `"think_content"` — `base_runner.py:163` liest aber `"think_content"`. Fix: Key einheitlich auf `"think_content"`.

Zusätzlich: `reasoning_tokens` wird bevorzugt aus `usage.completion_tokens_details.reasoning_tokens` gelesen (llama.cpp-native), Fallback auf `completion_tokens` nur wenn Content leer.

## Spark Token-Management (Session 26)

`llamacpp_spark` ist ein eigenständiger Server mit eigenem Kontextfenster. Drei Config-Ebenen pro Modell:

1. `context_length` → `--ctx-size` beim Serverstart (KV-Cache-Größe).
2. `max_tokens` → HTTP-Request-Limit pro Anfrage.
3. `parallel` → gleichzeitige Request-Slots (KV-Cache-Multiplikator).

**Kardinalregel:** `max_tokens` muss kleiner sein als `context_length`, und `read_timeout` muss groß genug sein für `max_tokens / t/s`. Ohne `max_tokens`-Cap generiert das Modell bis zum Kontextfenster → Timeout-Loop.

Per-Model-Cap wird in `llamacpp_base.py:query()` NACH `resolve_token_budget()` angewendet: `min(initial_tokens, model_cfg_max_tokens)`.

## Provider-ID-Heuristiken

### `_infer_provider()` — `/`-Präsenz-Heuristik

Nie `"deepseek" in model_id` — lokale Ollama-IDs können Provider-Namen enthalten.

### `resolve_provider()` — `:free`-Suffix

OpenRouter-Free-Tier-IDs haben das Format `vendor/model:free`. Die `:` Ollama-Erkennung greift nur wenn **kein** `/` im Namen ist. Fallback: `"/" in model_id` → `openrouter` (nicht mehr Groq).

## Cohere Quirks

### Cohere Native ToolUse (v4.10.8)

Prompt-basierte JSON-Tool-Schemas im System-Prompt kollidieren mit Cohere's Reasoning-Modellen (HTTP 422/500). ToolUse-Modul nutzt Cohere-native `tools`-API (`_extract_tool_schema()`, `_schema_to_cohere_tools()`, `_format_tool_calls_as_text()`). Andere Module bleiben prompt-basiert. Reasoning-Modelle: `thinking: {"type": "disabled"}` bei Native Tools verhindert 422.

**Wichtig:** NIEMALS prompt-basierte Tool-Schemas für Cohere-Reasoning-Modelle verwenden — immer den nativen Pfad nutzen.

### Cohere `command-a-plus` MoE-Instabilität

`command-a-plus-05-2026` (Cohere's erstes MoE-Modell, 218B/25B aktiv) zeigt persistente HTTP 500 bei Benchmark-System-Prompts + nativen Tools. Einfache Prompts funktionieren. `thinking: disabled` hilft nicht. Serverseitiger Bug — `supports_tool_use=false` bis Cohere den Bug behebt (Stand 2026-06).

## OpenRouter Quirks

### Alibaba Cloud / Qwen — `data_collection: allow`

Qwen-Modelle (und andere Alibaba-Cloud-Endpoints) via OpenRouter liefern HTTP 404 ohne explizite Policy-Zustimmung. Fix: `extra_body={"data_collection": "allow"}` bei jedem OR-Request in `utils/providers/openrouter.py` (globaler Override, kein per-Modell-Schalter nötig).

## Accessibility-Pitfalls

### `is_accessible()` — 404 ≠ kein Zugriff

`NotFoundError`/404 und `RateLimitError`/429 → `True` zurückgeben.

### Refusal-Flag statt Re-Run

Antwort < 15 Zeichen → `refusal_flag=True`, kein Re-Run, kein Asset-Fix.

## Card-Workflow

### `manage_model_cards.py` — GGUF-Konventionen SSoT

NIEMALS `deployment_type`, `params_active_b` oder Preise inline für GGUF-Modelle setzen. Post-Apply-Korrektur in `manage_model_cards.py._ensure_gguf_conventions(card)`. GGUF-Erkennung via `_is_gguf_model(model_id)` (Regex: `q[2-8]_[k0-9]`, `gguf`, `-ud-`/`_ud_`). Läuft in `_commit_card` NACH `_ensure_license_consistency`.

### Card-Research `_commit_card` — `report.findings` statt `parsed["findings"]`

`_commit_card()` iteriert über `report.findings` (enthält Pre-Findings + LLM-Findings), NICHT über `parsed["findings"]` (nur LLM). Pre-Findings mit `suggested`-Werten (z.B. Lizenz-Korrektur) gehen sonst verloren.

### Card-Research Textfeld-Cascade — Pre-Finding + Post-Merge

Lizenz-Wechsel erfordert Text-Rewrites in `summary/strengths/known_limitations/judge_context_hint/weights_provenance_risk_rationale`. Pre-Finding `_check_license_text_fields()` (auf ORIGINAL-Card) + Post-Merge `_check_license_cascade()` (auf gemergter Card). System-Prompt Regel 5 zwingt LLM zu kompletten Text-Rewrites.

### `Apache-2.0` vs `Apache 2.0`

Lizenz-String-Varianten werden vom LLM als Lizenz-Wechsel interpretiert → alle 5 Textfelder neu geschrieben. Ergebnis korrekt, aber viele rote Findings. `_check_license_consistency()` matched auf exakte Strings — Varianten sollten in `_KNOWN_LICENSE_MAPPINGS` ergänzt werden.

### `profile_verified`-Validierung — finale Karte statt Findings-Historie

`_commit_card` prüft `has_remaining_errors` durch Re-Validierung der FINALLEN Karte (`_check_license_consistency` + `_check_license_text_fields` + `_check_community` + Pflichtfelder), nicht durch Zählen der Findings. Findings können Fehler aus dem Originalzustand enthalten, die längst korrigiert wurden.

### Card-Editor-Wrapper-Schicht (ab v4.10.11)

Der Card-Editor (`manage_model_cards.py`) kann bei Listen-Feldern wie `strengths` und `known_limitations` eine zusätzliche Wrapper-Schicht `[["a", "b"]]` statt `["a", "b"]` einführen. Symptom: `TypeError: sequence item 0: expected str instance, list found` in `get_model_card_context()`.

**Defense-in-Depth:** Modul-Level-Helper `_flatten_strings()` in `scripts/analysis/review/metrics.py` akzeptiert beide Formen (flach + 1 Wrapper-Schicht) und filtert Nicht-Strings. Konsumenten MÜSSEN den Helper nutzen statt direkt `", ".join(card["strengths"])`.

Recovery: alle betroffenen Cards per Backup-Recovery + Flatten-Script bereinigen (`grep -l '"strengths": \[\[' benchmark_scores/model_cards/*.json`).

### Card-Template optional vs required

Felder mit Beschreibung "null wenn X" müssen `required: false` sein — `is_unknown_sentinel(None)` returned `True`, also wird `null` bei `required: true` als Fehler gewertet. Betroffene Felder (Session 25): `params_total_b`, `params_active_b`, `knowledge_cutoff`, `license_url`, `input_price_per_1m`, `output_price_per_1m`.

### `--card all`

`--card all` wird als Spezialwert erkannt (gleichbedeutend mit kein `--card`). Early-Validation in `main()` muss ebenfalls `all` erkennen.

### Card-Research `MAX_CARDS=N`

Limitiert Targets pro Run. Bei `FORCE=1` werden immer die ersten N alphabetischen Cards verarbeitet (kein Skip bereits verifizierter). Ohne `FORCE` werden nur unverifizierte Cards verarbeitet — dann funktioniert Batch-Processing korrekt (10 pro Run, nächster Run nächste 10).

### `_rebuild_index()` entfernt (v4.10.7)

`generate_model_cards.py` hatte `_rebuild_index()` — wurde zu `rebuild_card_index()` in `utils/card_template` migriert. Falls noch alte Aufrufe existieren (Beispiel: `generate_review.py:200` rief die alte Funktion auf → `AttributeError`-Crash bei `reviews-auto` Modell 54/118): verwaisten Aufruf + unbenutzten `mc_gen`-Import entfernen.

## MCP Auto-Lifecycle

`_ensure_mcp_running(mcp_url)` startet MCP automatisch wenn nicht bereits aktiv. `_stop_mcp_server()` stoppt am Ende (nur wenn gestartet). `_reset_llama_context(base_url)` resettet KV-Cache via `POST /slots/{id}?action=reset` nach jeder Karte (Best-Effort — die OpenAI-compatible API ist stateless, der Reset ist nur beim nativen Endpoint relevant). `_check_health(url)` vor jeder Karte.

## `probe_thinking.py` Path-Handling

`card_path` kann relativ sein (`benchmark_scores/model_cards/...`), `ROOT_DIR` ist absolut. Immer `card_path.resolve().relative_to(ROOT_DIR)` mit Fallback verwenden.

## `reviews-auto` Skip-Logik

mtime-basiert — nach jedem Benchmark-Run nur betroffene Modelle neu reviewt; `--force` deaktiviert Skip.
