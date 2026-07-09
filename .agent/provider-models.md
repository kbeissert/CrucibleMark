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

## vLLM Dual-Thinking-Profile (Session 52)

vLLM-Modelle mit `enable_thinking: true` werden beim Config-Load automatisch in zwei Profile expandiert. Ein Container bedient beide per-Request — kein Server-Neustart beim Profil-Wechsel.

### Expansion-Mechanik

`_expand_thinking_profiles(providers)` in `utils/config_validator.py`, aufgerufen in `_load_config` nach Merge, vor `_check_duplicate_model_ids`:

- **Nur `api_type == "vllm"`** — llama.cpp's `enable_thinking` ist ein Server-Start-Flag (`--reasoning on`/`off`), kein per-Request-Parameter. Expansion für llama.cpp würde zwei Profile erzeugen, die trotzdem neu starten müssen.
- **Original-Eintrag (Standard-Profil):** konsumiert `enable_thinking`, setzt `chat_template_kwargs: {"enable_thinking": false}`.
- **Generierter Thinking-Eintrag:** `id: {original_id}-thinking`, `config:` identisch (→ kein Swap), `card_model_id: {original_id}` (→ teilt Card), `chat_template_kwargs: {"enable_thinking": true}`, `max_tokens: {thinking_max_tokens}`.
- **`thinking_max_tokens`-Quelle:** model_cfg > provider > Fehler (kein Hardcoding).

### Swap-Entkopplung

`_active_config: str | None` in `vllm_base.py` trackt die TOML-Config des aktiven Modells. `_ensure_model_ready` vergleicht `config:` statt `model_id`:

- Gleiche `config:` (z.B. Standard → Thinking desselben Modells) → **kein `swap_model`**, nur per-Request-Param-Wechsel via `_resolve_sampling`.
- Unterschiedliche `config:` → `swap_model` wie bisher.
- Backward-compat: `_active_config is None` → bisheriges Verhalten.

### Card-Lookup via `card_model_id`

`_find_card()` und `resolve_canonical_model_id()` akzeptieren optional `model_cfg`. Wenn `card_model_id` vorhanden → Card-Lookup über dieses Feld (deterministisch, kein Suffix-Stripping-Heuristik). `resolve_canonical_model_id` gibt die **Profile-eigene ID** zurück (`{id}-thinking`), NICHT die Card's `model_id` — CSV `model_id` bleibt eindeutig.

`enforce_card_first()` und `ResultManager._find_model_cfg()` threaden `model_cfg` durch → verhindern Platzhalter-Card-Erstellung für Thinking-Profile.

### `resolve_provider` muss expandierte Config sehen

`resolve_provider()` nutzt `ConfigValidator().config` als primäre Quelle (merge + expansion aware), nicht die Roh-YAML. Andernfalls sind generierte `{id}-thinking`-Profile unsichtbar → fälschlicher Fallback auf Ollama.

### `thinking_mode`-Spalte erfasst Runtime-Konfiguration (Session 54)

`utils/base_runner.py:_resolve_thinking_mode(model, provider)` leitet aus model_cfg ab:

| Config | `thinking_mode` |
|---|---|
| `card_model_id` vorhanden (vLLM Dual-Profile Thinking) | `Thinking` |
| `chat_template_kwargs.enable_thinking: false` (vLLM Dual-Profile Standard) | `Standard` |
| `chat_template_kwargs.enable_thinking: true` | `Thinking` |
| `enable_thinking: true` (llama.cpp) | `Thinking` |
| `enable_thinking: false` (llama.cpp) | `Standard` |
| Keine Thinking-Config (Cloud/Commercial) | `n/a` |

CSV-Spalte + Leaderboard-Spalte "Thinking Mode" zwischen `Speed Profile` und `Total Score`. **Trennung:** `thinking_mode` = Runtime-Config (pro-Run); `thinking_probe_detected` = Capability (stabil).

### `thinking_mode` dreifach sichtbar (Session 55)

Eine Datenquelle (`_resolve_thinking_mode()`), drei Ausgabeorte:

| Ebene | Code | Sichtbar für |
|---|---|---|
| **CSV-Spalte** | `utils/base_runner.py:build_base_result()` | Datenanalyse, Leaderboard |
| **Audit-Log-Header** | `utils/benchmark_utils.py:save_audit_log(thinking_mode=...)` | Mensch (Datei direkt) |
| **Review-Prompt** | `scripts/analysis/generate_review.py:_resolve_thinking_mode_for_review()` | LLM-Reviewer |

**Review-Prompt-Pitfall:** Externe Audit-Analyse zeigte, dass Reviewer beide Ornith-Läufe fälschlich als "Thinking-Lauf" deklarierten. Wurzel: `{model_tags}` enthält "Thinking" als Architektur-Tag (Capability, immer vorhanden), aber kein Runtime-Modus-Datenfeld. Reviewer riet aus Tags statt aus Daten. **Pflicht:** Jede Runtime-Config, die den Reviewer beeinflusst, MUSS als hartes Datenfeld im Prompt stehen.

**Pattern für Prompt-Variablen:** `model_metrics.get("<Spalte>") or _resolve_<x>_for_review(model_id)` — Leaderboard-Spalte als Primärquelle, Config-Lookup via `resolve_model_cfg_for()` als Fallback für alte Daten ohne Spalte.

### `{hardware_context}` pro-Modell korrekt auflösen (Session 56)

`SystemContextManager.get_editor_prompt_injection()` injiziert Hardware-Info in den Reviewer-Prompt. Der `hardware_profile`-Key pro Provider:

| Provider | `hardware_profile`-Key | Hardware | `ram_gb` |
|---|---|---|---|
| `llamacpp` | `m4_macbook_pro_metal` | Apple Silicon M4, 24 GB | 24 (constrained) |
| `llamacpp_spark` | `dgx_spark_cuda` | NVIDIA DGX Spark, 115 GB | 115 (ample) |
| `vllm_spark` | `asus_gx10_blackwell` | ASUS GX10 / DGX Spark, 115 GB | 115 (ample) |

**Lookup-Kette in `generate_review.py`:**
1. `_get_hardware_profile_for_model(model_id, validator.config)` — sucht in Provider-Config (SSoT)
2. `_get_hardware_profile_from_csv(model_id)` — Fallback: liest `hardware_profile`-Spalte aus roher CSV (für auskommentierte/umbenannte Modelle)
3. `SystemContextManager.get_editor_prompt_injection(run_type, hardware_profile_key=...)` — löst Key gegen `benchmark_config.yaml:runner_environment.profiles` auf;Fallback auf `active_profile`

**Pflicht:** Jeder `hardware_profile`-Key in `provider_config.yaml` MUSS in `benchmark_config.yaml:runner_environment.profiles` definiert sein. Sonst fällt der Lookup auf `active_profile` (M4) zurück → Reviewer zitiert falsche Hardware. Die Sperrklausel im Prompt verbietet Hardware-Spekulation, funktioniert aber NUR wenn `{hardware_context}` die korrekte Hardware liefert.

**Local-Template konditional (Session 56):** `system_context.py` verwendet zwei Templates je nach `ram_gb`:
- **`ram_gb < 64` (memory-constrained):** Template nennt "Speichergrenze" und "Swapping-Risiken" als legitimen Diskurspunkt. Korrekt für M4 (24 GB).
- **`ram_gb >= 64` (ample):** Template formuliert "Speicher ist hier kein Engpass" — keine Speicher-Spekulation. Verhindert, dass der Reviewer Timeouts auf 115-GB-Hardware fälschlich dem Speicher zuschreibt. Die Beschreibung enthält "kein praktisches Speicherlimit für getestete Modellgrößen".

**Audit-Befund (Session 56):** Externe Audit-Analyse zeigte, dass Reviews für Spark/GX10-Modelle "Apple Silicon M4, 24GB Unified Memory" zitierten. Ursache: `asus_gx10_blackwell`-Profil fehlte in `benchmark_config.yaml` → Fallback auf `active_profile` = M4. Die Sperrklausel im Prompt war korrekt, aber das Datenfeld `{hardware_context}` lieferte die falsche Hardware.

### `-thinking`-Suffix-Fallback für Card-Lookup ohne `model_cfg` (Session 54)

Viele Caller (`generate_review.py`, `review/risk_calculator.py`, `review/metrics.py`, `sync_cards.py`) rufen `_find_card()` ohne `model_cfg` auf. Der `card_model_id`-Redirect greift dort nicht.

**Lösung — `_find_card()`-Fallback:** wenn `model_cfg is None` UND `lookup_id.endswith("-thinking")` UND keine Card gefunden, streife `-thinking` deterministisch ab und rufe `_find_card(base_id, card_dir)` rekursiv. Greift nur als Last-Resort (nach SUFFIX/PREFIX/date-glob/dot→hyphen).

**Kritische Trennung:** `resolve_canonical_model_id` darf NICHT `card.model_id` zurückgeben wenn die Card via Suffix-Fallback gefunden wurde — sonst verschmelzen Basis- und Thinking-Profil im Leaderboard. Stattdessen `_safe_name(base)` zurückgeben (Profil-eigene ID).

### Display-Name-Sharing (Session 54)

`scripts/leaderboard/module_integration.py:_add_thinking_profile_names()` ergänzt `display_lookup` für Thinking-Profile aus der expandierten Config. Beide Profile zeigen denselben Display-Namen, Unterscheidung über `model_id` + `thinking_mode`-Spalte.

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

### `_index.json` entfernt (v4.10.12)

`_index.json` (denormalisiertes Array aller Card-JSONs) wurde vollständig entfernt — sowohl für `model_cards/` als auch `vendor_cards/`. Begründung: 50% der Card-Modifikations-Commits vergaßen den Rebuild, der Index driftete silently. Kein Production-Code las den Index (Web-Export, Leaderboard, Benchmark-Runner lesen direkt per `glob("*.json")`); einziger Konsument war `audit_model_cards_full.py` (Duplicate-Detection), das jetzt inline globt. Die Funktionen `rebuild_card_index()` und `rebuild_provider_index()` wurden entfernt; defensive `if p.name == "_index.json": continue`-Checks bleiben als harmloses Dead Code bestehen.

### `_rebuild_index()` entfernt (v4.10.7, historisch)

`generate_model_cards.py` hatte früher `_rebuild_index()` — wurde zwischenzeitlich zu `rebuild_card_index()` in `utils/card_template` migriert, dann mit dem Index vollständig entfernt (siehe oben).

## MCP Auto-Lifecycle

`_ensure_mcp_running(mcp_url)` startet MCP automatisch wenn nicht bereits aktiv. `_stop_mcp_server()` stoppt am Ende (nur wenn gestartet). `_reset_llama_context(base_url)` resettet KV-Cache via `POST /slots/{id}?action=reset` nach jeder Karte (Best-Effort — die OpenAI-compatible API ist stateless, der Reset ist nur beim nativen Endpoint relevant). `_check_health(url)` vor jeder Karte.

## `probe_thinking.py` Path-Handling

`card_path` kann relativ sein (`benchmark_scores/model_cards/...`), `ROOT_DIR` ist absolut. Immer `card_path.resolve().relative_to(ROOT_DIR)` mit Fallback verwenden.

## `reviews-auto` Skip-Logik

mtime-basiert — nach jedem Benchmark-Run nur betroffene Modelle neu reviewt; `--force` deaktiviert Skip.
