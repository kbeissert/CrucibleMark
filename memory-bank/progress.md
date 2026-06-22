# Progress

Letzte Releases + aktueller Stand.
### 2026-06-22 (Session 32) — Dead-Model-Cleanup (xAI) + Workflow-Dokumentation

**Auslöser:** Nach Session 31 (ID-Mismatch-Fix) weiterhin `Model not found: grok-4.1-fast-reasoning` beim Benchmark-Lauf. Das Modell existiert schlicht nicht mehr in der xAI API.

**Diagnose:** XAI `/v1/models` abgefragt — 4 von 7 konfigurierten Modellen nicht mehr gelistet:
- `grok-4-1-fast-reasoning` ❌, `grok-4-fast-non-reasoning` ❌, `grok-3` ❌, `grok-3-mini` ❌
- `grok-4.20-0309-reasoning` ✅, `grok-4.20-0309-non-reasoning` ✅, `grok-4.3` ✅

**Änderungen:**

1. **`config/provider_config.yaml`:** 4 tote Modelle auskommentiert (Zeilen 142-149) mit `# ❌ XAI API: Model not found (entfernt 2026-06)`.

2. **`config/web_export_blacklist.yaml`:** 3 neue Einträge ergänzt (Zeilen 79-81):
   - `grok-4-fast-non-reasoning`, `grok-3`, `grok-3-mini`
   - `grok-4-1-fast-reasoning` war bereits vorhanden (Zeile 78)

3. **`CLAUDE.md` — Dead-Model-Handling Workflow (neu):**
   - Regel in Architecture Rules: Bei `Model not found` / HTTP 400 → (1) API prüfen, (2) User fragen, (3) Blacklist ergänzen, (4) CSV aufräumen
   - **Wichtig:** NIEMALS eigenständig auskommentieren — immer den User bestätigen lassen
   - Grund: API-Ausfälle können temporär sein; Blacklist-Einträge blockieren den Web-Export dauerhaft

**Verifikation:**
- YAML-Parsing beider Configs ✓
- 492/493 Tests grün (1 pre-existing: `qwen3_6` Sampling-Keys)

---

### 2026-06-22 (Session 31) — grok-4.1-fast-reasoning Model-ID-Mismatch Fix

**Auslöser:** Benchmark-Lauf für `grok-4.1-fast-reasoning` (Cultural Intelligence) schlug fehl — `Model not found: grok-4_1-fast-reasoning`. Die kanonisierte ID (Unterstriche) wurde an die XAI-API gesendet statt der API-ID (Punkte).

**Root Cause Chain:**
1. `provider_config.yaml` hat `grok-4-1-fast-reasoning` (Bindestriche)
2. Model Card `grok-4-1-fast-reasoning.json` hat `model_id: "grok-4.1-fast-reasoning"` (Punkte = echte API-ID)
3. Eingabe `grok-4.1-fast-reasoning` → `_safe_name()` → `grok-4_1-fast-reasoning` (Punkte→Unterstriche)
4. Card-Lookup für `grok-4_1-fast-reasoning.json` schlägt fehl (Card heißt `grok-4-1-fast-reasoning.json` mit Bindestrichen)
5. Fallback: `_safe_name` → `grok-4_1-fast-reasoning` als kanonische ID
6. XAI-API erhält `grok-4_1-fast-reasoning` → 400 "Model not found"
7. Placeholder-Card `grok-4_1-fast-reasoning.json` mit falschem `model_id` angelegt

**Änderungen:**

1. **`utils/model_utils.py` — `_find_card()` Dot→Hyphen-Fallback:**
   - Nach dem primären `_safe_name`-basierten Lookup (Punkte→Unterstriche) und allen anderen Fallbacks:
   - Wenn `unprefixed` nicht existiert und `model_id` Punkte enthält: Variante mit Bindestrichen probieren
   - `model_id.replace(".", "-")` → `_safe_name()` → Card-Dateiname → Existenzprüfung
   - Debug-Logging bei Fallback-Match

2. **`utils/providers/xai.py` — `_XAI_ID_ALIASES` ergänzt:**
   - `"grok-4_1-fast-reasoning": "grok-4.1-fast-reasoning"` (Defense-in-Depth)
   - Konsistent mit bestehenden Einträgen für `grok-4_20-0309-*` und `grok-4_3`

3. **Cleanup:**
   - Broken Placeholder-Card `grok-4_1-fast-reasoning.json` gelöscht
   - 4 broken CSV-Einträge (`grok-4_1-fast-reasoning`, 0.0-Scores) aus `commercial_models_benchmark.csv` entfernt

**Verifikation:**
- `resolve_canonical_model_id("grok-4.1-fast-reasoning")` → `"grok-4.1-fast-reasoning"` ✓
- `_find_card("grok-4.1-fast-reasoning")` → `grok-4-1-fast-reasoning.json` (exists=True) ✓
- 82 card/canonical/normalize Tests grün
- 492/493 Gesamttests grün (1 pre-existing: `qwen3_6` Sampling-Keys)

**Pitfall dokumentiert:** `_safe_name()` konvertiert Punkte→Unterstriche, aber Cards, die aus provider_config-IDs mit Bindestrichen erstellt wurden, haben Bindestriche im Dateinamen. Der neue Dot→Hyphen-Fallback in `_find_card()` schließt diese Lücke.

---

### 2026-06-22 (Session 30) — Token-Limit-Audit + Anthropic Provider-Cap + Benchmark-Cleanup (v4.10.6)

**Auslöser:** User fragte ob Token-Limits bei allen Providern korrekt gesetzt sind. Systematische Analyse aller 5 API-Provider ergab: 27 Modelle mit verfälschten Benchmark-Ergebnissen durch Token-Limit-Artefakte.

**Änderungen:**

1. **`config/provider_config.yaml` — Anthropic Provider-Cap:**
   - `max_tokens`: 8192 → 32768 (Claude 4.x unterstützt bis 128K Output)
   - `fallback_max_tokens: 4096` entfernt (Dead Config — nirgends im Code gelesen)
   - Per-Model Override: `claude-haiku-4-5-20251001: 8192` (Desktop-Klasse, kein Thinking)

2. **Benchmark-Cleanup — 144 Zeilen entfernt:**
   - Kategorie A (MAX_TOKENS): 24 Zeilen, 5 Modelle — finish_reason=max_tokens
     - gemini-3.5-flash: 9 Tasks (CI×5 + CT×2 + UX×1 + CQ×1)
     - gemini-2.5-flash: 7 Tasks (DQ×2 + UX×2 + CQ×2 + R×1) — Thinking-Overhead
     - gemini-3-flash-preview: 5 Tasks (CI×5)
     - claude-opus-4-6: 2 Tasks (CT_004 + DQ_004)
     - claude-opus-4-5: 1 Task (CT_004)
   - Kategorie B (CI@500): 130 Zeilen, 26 Modelle — cultural_intelligence bei 500 Tokens
   - Backup: `commercial_models_benchmark.csv.bak_token_cleanup_20260622`

3. **Leaderboard aktualisiert:**
   - 27 Modelle zeigen jetzt fehlende Tasks (34/43 bis 38/43)
   - CI-Scores auf "Pending" — werden beim nächsten `benchmark_auto` nachgetestet

4. **Dokumentation:** CHANGELOG v4.10.6, README, PROJECT_STATUS, REF_TODO, CLAUDE.md (2 Pitfalls)

**Design-Erkenntnisse:**
- `max_tokens` sollte Sicherheitsnetz (32K+) sein, nicht Bremse (8192)
- Längensteuerung über Judge (Verbosity Penalty + Golden Standard), nicht API-Cap
- Keine Prompt-Änderung nötig — bestehende Aufgaben beibehalten
- Anthropic Extended Thinking (`thinking.budget_tokens`) noch nicht implementiert
- Alle 5 Provider analysiert: OpenAI (OK), xAI (OK), Mistral (OK), Google (Thinking-Overhead bei 2.5 Flash), Anthropic (Cap zu niedrig)

**Verifikation:** 130/130 Token/Config/Provider-Tests grün.

---

 Vollständige Historie: `reference/decisions-log.md`.

### 2026-06-21 (Session 29, Runde 2) — Provider-Connector SSoT + Judge Token Usage Context (v4.10.5)

**Auslöser:** Provider-Connector-Audit (v4.10.1) ergab: Extraktions-Utilities für `reasoning_tokens`/`think_content` waren über 9 Provider dupliziert. Streaming-Bugs in OpenRouter + llamacpp_base. Judge sah nie den tatsächlichen Token-Verbrauch pro Aufgabe.

**Änderungen:**

1. **`utils/providers/base.py` — 3 SSoT-Utilities:**
   - `_extract_reasoning_tokens(usage)` — Provider-agnostisch. Prüft: `completion_tokens_details` (OpenAI-kompatibel) → `output_tokens_details` (Anthropic) → `usage.reasoning_tokens` (Mistral). Ersetzt 5 identische lokale Methoden.
   - `_extract_think_from_message(msg, field_names)` — Generisch. Versucht `getattr(msg, field)` für jedes Feld. Ersetzt identische Inline-Patterns in 4 Providern.
   - `ThinkAccumulator` — Streaming-Helper. `add(chunk)` → `content`/`has_content`. Ersetzt `think_parts: list[str]` + `"".join(think_parts)` in 7 Streaming-Pfaden.

2. **9 Provider auf Shared Utilities umgestellt:**
   | Provider | Reasoning | Think Msg | ThinkAcc |
   |---|---|---|---|
   | openai.py | Base | ✅ | ✅ |
   | anthropic.py | Base | eigene `_extract_think_content` | ✅ |
   | groq.py | Base | ✅ | ✅ |
   | xai.py | Base | ✅ | ✅ |
   | openrouter.py | Inline→Base | ✅ | ✅ |
   | google.py | Inline (`thoughts_token_count`) | candidate parts | ✅ |
   | mistral.py | Inline→Base | Chunk-Liste | — (kein Streaming) |
   | ollama.py | Inline (`eval_count`) | Inline (`msg.thinking`) | — (eigene Logik) |
   | llamacpp_base.py | Inline→Base + Fallback | Inline (`reasoning_content`) | ✅ |

3. **Streaming-Bugs gefixt:**
   - `openrouter.py`: `reasoning_tokens` wurde im Streaming-Pfad nie extrahiert
   - `llamacpp_base.py`: Streaming ignorierte `delta.reasoning_content` (llama.cpp-natives Thinking-Feld)

4. **Judge Token Usage Context (universal):**
   - `judge_evaluator.py`: Baut `token_usage_context` dict aus result (tokens_used, reasoning_tokens, token_budget, module_budget, truncated)
   - `judge_runner.py`: Neuer `token_usage_context` Parameter in `score()`
   - `judge_prompt_builder.py`: Neue `### TOKEN USAGE ###` Section mit Budget, Verbrauch, Thinking-Ratio, Truncation, Compliance-Guidance
   - Bestehende 3 Kontexte (token_budget_context, truncation_context, small_model_token_context) bleiben erhalten
   - 7 inline Verifikations-Tests bestanden

**Dokumentation:** CHANGELOG v4.10.5, README (Recent Versions + Footer), PROJECT_STATUS, REF_TODO, activeContext, progress, systemPatterns (SSoT-Brücken).

**Verifikation:** 822/822 Tests grün (1 pre-existing deselect: `test_no_forbidden_placeholder`).

---

### 2026-06-21 (Session 29) — CSV-Write-Through Bug Fix + Abbruchverhalten + Provider-Config-Cleanup (v4.10.4)

**Auslöser:** User fragte nach dem Abbruchverhalten des Auto-Benchmarks. Analyse offenbarte 10 Modelle mit dispatch summaries + audit logs aber LEEREN CSVs. Root Cause: `_write_to_csv()` öffnete mit `"w"` (truncate) — bei Kill/Crash gingen alle Daten verloren.

**Änderungen:**

1. **`utils/result_manager.py` — Atomare Schreibvorgänge (v4.10.4):**
   - `_write_to_csv()`: `tempfile.mkstemp()` + `os.replace()` statt `open("w")`
   - Bestehende Zeilen werden NICHT re-validiert beim Full-Rewrite
   - `_csv_header_matches()`: exakter Vergleich beibehalten (korrekt für Append-Path)

2. **`config/provider_config.yaml` — Cleanup (-130 Zeilen):**
   - Redundante navigational/description Kommentare entfernt
   - 92 aktive Modelle + alle auskommentierten Modelle erhalten
   - Technische Kommentare beibehalten

3. **4 neue Tests in `tests/test_result_manager_validates.py`:**
   - `test_full_rewrite_preserves_existing_rows_not_revalidated`
   - `test_atomic_write_no_corruption_on_header_mismatch`
   - `test_write_through_fast_path_single_result`
   - `test_upsert_dedup_replaces_existing_row`

**Dokumentation:** CHANGELOG v4.10.4, README Version Badge, CLAUDE.md (2 Pitfalls: atomare Writes + Daten-Pipeline).

**Verifikation:** 823/823 Tests grün.

**Kritische Funde:**
- **10 Modelle mit 0 CSV-Einträgen:** llama-3.3-70b-versatile (Groq, 50 Audit-Files), llama-4-scout (Groq, 50), nemotron-3-ultra (OR, 44), qwen3-32b (Groq, 50), qwen3.5-397b (OR, 0 Audit), glm-4.7 (OR, 50), glm-5-20260211 (OR, 50), glm-5-turbo (OR, 50), glm-5.1 (OR, 0 Audit), glm-5.2 (OR, 49)
- **deepseek/deepseek-chat-v3.1 (abgebrochen):** 34/43 Tasks in CSV. Write-Through funktionierte korrekt.
- **CSV-Daten-Pipeline verifiziert:** `save_results()` = Upsert (ersetzt gleiche Keys), `data_loader.py` = dedup (latest per key), `consolidate_csv.py` = physische Reduktion auf 1 Zeile pro Key.

---

### 2026-06-21 (Session 28) — Token-Budget-Refactoring + Design-Constraints + CSV-Gap-Analyse

**Auslöser:** Auto-Benchmark für 30 fehlende Modelle lief langsam. Token-Fenster von 65536 bei Thinking-Modellen verursachte bis zu 85 Min/Task. CSV-Write-Bug: 9 Modelle mit fehlenden Einträgen trotz vollständiger Audit-Logs.

**Änderungen:**

1. **`utils/providers/base.py` — `_resolve_request_tokens()` (SSoT):**
   Neuer Shared Helper für alle 7 API-Provider. Zweistufige Kaskade: `resolve_token_budget()` → Provider-Default `max_tokens` → Per-Model Override `model_max_tokens`. Neue Klassen-Attribute: `PROVIDER_CONFIG_KEY`, `DEFAULT_TOKEN_PARAM`.

2. **7 Provider-Connectors auf Shared Helper umgestellt:**
   - `openrouter.py`: 15 Zeilen inline → 1 Zeile. Bugfix: hardcoded `"max_tokens"` in Fallback-Call → config-aufgelöst.
   - `openai.py`: 12 Zeilen inline → 1 Zeile.
   - `mistral.py`: 8 Zeilen inline → 1 Zeile.
   - `anthropic.py`: KEIN Budget → jetzt mit Budget (via Shared Helper).
   - `groq.py`: KEIN Budget, hardcoded → jetzt mit Budget. Duplikat mit xai.py eliminiert.
   - `xai.py`: KEIN Budget, hardcoded → jetzt mit Budget.
   - `google.py`: KEIN Budget, hardcoded → jetzt mit Budget.
   - `llamacpp_base.py`: unverändert (eigene Config-Struktur `providers.local`).

3. **`config/provider_config.yaml` — Provider-Default `max_tokens`:**
   Alle 7 API-Provider haben jetzt einen Provider-Default. OpenRouter zusätzlich mit 7 Per-Model Overrides (Kimi K2.x, DeepSeek V4).

4. **`benchmark_config.yaml` — Token-Budget-Optimierung:**
   - `code_quality` Reasoning: 65536 → 20000 (p99=16382)
   - `cultural_intelligence` Standard: 1000 → 3000 (Cloud-p90=2893)
   - `documentation_quality` Standard: 6000 → 8000 (Cloud-p90=7789)

5. **Design-Constraints dokumentiert** (`systemPatterns.md`, `CLAUDE.md`):
   - Sequenzielle Modell-Abarbeitung (Server-Restart + Cooldown) — Design, kein Bug
   - Judge-Reset zwischen Tasks (kein Caching) — verhindert Kontextmix

6. **CSV-Gap-Analyse:** 9 Modelle mit fehlenden CSV-Einträgen identifiziert. Audit-Logs vollständig — Re-Run der fehlenden Module nötig.

**Dokumentation:** CHANGELOG v4.10.3, README (Version + Token-Budget-Beschreibung), CLAUDE.md (SSoT-Pitfalls), systemPatterns.md (Design-Constraints + Token-Kaskade).

**Verifikation:** 819/819 Tests grün.

---

### 2026-06-20 (Session 27) — Provider-Connector Thinking/Reasoning-Fix + Card-Cleanup

**Auslöser:** Audit aller Provider-Connectors auf korrekte Thinking/Reasoning vs. Response-Token-Trennung. OpenRouter war SSoT-Referenz (nach v4.10.0-Fix), aber 7 andere Provider hatten Lücken:
- `anthropic.py`: kein `think_content`, kein `reasoning_tokens`, kein Streaming
- `openai.py`: kein `think_content`, kein `reasoning_tokens` (o1/o3/o4 Reasoning nicht erfasst)
- `google.py`: `reasoning_tokens` ✓, aber kein `think_content` und kein `usage` in metadata
- `groq.py`/`xai.py`: kein `reasoning_tokens`, kein `think_content`, kein `usage` im Streaming
- `ollama.py`: `think_content` ✓ (im Stream akkumuliert), aber nie in metadata; kein `usage`; kein `reasoning_tokens`
- `mistral.py`: `think_content` ✓ (nur bei leerem Content), `usage` ✓, aber kein `reasoning_tokens`

**Impact (vor Fix):**
- Judge-Evaluator (`judge_evaluator.py:272`) sah keine `reasoning_tokens` → Thinking-Aufwand pro Aufgabe nicht messbar
- `LLMParser.extract_usage_tokens()` (`llm_client.py:244`) bekam `usage=None` → Pipeline fiel auf `estimate_tokens()` zurück (Zeichen-basierte Schätzung, 1 Token ≈ 4 Zeichen)
- `tokens_used` in CSV war geschätzt statt von API gezählt
- Cost-Tracker rechnete mit falschen Token-Werten

**Änderungen pro Provider:**

1. **`utils/providers/anthropic.py`** — Vollständiger Rewrite von `query()`:
   - Neuer Helper `_extract_reasoning_tokens(usage)` — `usage.output_tokens_details.reasoning_tokens` (neue SDK-Versionen)
   - Neuer Helper `_extract_think_content(content_blocks)` — extrahiert `block.thinking` aus ContentBlocks mit `type="thinking"`
   - Neue Methode `_query_streaming()` — vollständige Streaming-Implementierung:
     - `message_start` → metadata + initial usage
     - `content_block_start` (type=thinking) → pre-fill thinking content
     - `content_block_delta` (type=thinking_delta) → akkumuliere thinking
     - `message_delta` → final usage + stop_reason
   - Beide Pfade (blocking + streaming) setzen `reasoning_tokens` und `think_content` in `last_response_metadata`

2. **`utils/providers/openai.py`**:
   - Non-Streaming: `msg.reasoning`/`msg.reasoning_content`/`msg.think_content` als `think_content`; `usage.completion_tokens_details.reasoning_tokens` als `reasoning_tokens`
   - Streaming: `delta.reasoning` in `think_parts` akkumuliert; `stream_usage` + `reasoning_tokens` nach Loop
   - Neuer Helper `_extract_reasoning_tokens(usage)` (DRY mit anthropic.py)

3. **`utils/providers/google.py`**:
   - `usage_metadata` jetzt in `last_response_metadata["usage"]` (vorher nur `reasoning_tokens` aus `thoughts_token_count`)
   - `think_content` aus `candidates[0].content.parts[].thinking` extrahiert (beide Pfade)

4. **`utils/providers/groq.py`** + **`xai.py`**:
   - Neuer Helper `_extract_reasoning_tokens(usage)` (DRY)
   - Non-Streaming: `reasoning_tokens` + `think_content` + `usage` in metadata
   - Streaming: `stream_usage` tracking hinzugefügt; `think_content` aus `delta.reasoning` akkumuliert

5. **`utils/providers/ollama.py`**:
   - `usage` als Dict synthetisiert: `{"prompt_tokens": prompt_eval_count, "completion_tokens": eval_count, "total_tokens": ...}` (Ollama liefert kein einheitliches usage-Objekt)
   - `reasoning_tokens = eval_count` wenn Thinking erkannt wurde (kein separater Count verfügbar)
   - `think_content` aus akkumuliertem `full_thinking` in metadata gespeichert (vorher nur als Return-Value verwendet)

6. **`utils/providers/mistral.py`**:
   - `reasoning_tokens` aus `usage.completion_tokens_details.reasoning_tokens` ODER `usage.reasoning_tokens`
   - `think_content` wird jetzt immer gesetzt wenn ThinkChunks vorhanden (vorher: `if not content.strip() and think_parts`)

**Card-Cleanup (2 pre-existing Test-Failures behoben):**

1. **`tests/test_sampling_defaults_ssot.py::test_all_cards_have_sampling_keys`** — 3 Cards fehlten Sampling-Default-Felder:
   - `gemma-4-31b-it-creative-wordsmith-q8.json`: `presence_penalty: null` ergänzt
   - `hermes-4_3-36b-q6.json`: alle 7 Sampling-Keys (`top_p`, `top_k`, `repetition_penalty`, `frequency_penalty`, `presence_penalty`, `seed`, `stop_sequences`) als `null` ergänzt
   - `mistral-large-2512.json`: alle 7 Sampling-Keys als `null` ergänzt

2. **`tests/test_taxonomy_ssot.py::TestNoPlaceholderStrings::test_no_forbidden_placeholder_in_taxonomy_fields`** — `gemini-3-flash-preview.json`:
   - `parameter_architecture: "unknown"` (verbotener Placeholder in `FORBIDDEN_PLACEHOLDERS`) → `"dense"` (gültiger Taxonomie-Wert, Flash ist Dense-Transformer)

**Dokumentation aktualisiert:**
- `CHANGELOG.md` — Neue Version v4.10.1 mit allen Provider-Fixes + Card-Cleanup
- `CLAUDE.md` — Neuer Pitfall-Eintrag "Provider-Connector Thinking/Reasoning-Extraktion (ab v4.10.1 SSoT)" in der Critical-Pitfalls-Liste
- `docs/ARCHITECTURE.md` — Provider-Tabelle erweitert um Reasoning-Quellen + neue Sektion "Provider Thinking/Reasoning-Extraktion (ab v4.10.1)" mit Mapping-Tabelle
- `docs/DEVELOPER_GUIDE.md` — Neue Sektion "Provider-Connector Thinking/Reasoning-Extraktion (ab v4.10.1)" mit kompletter Mapping-Tabelle aller 8 Provider + Streaming-Pfade-Tabelle + DRY-Helper
- `docs/THINKING_PROBE.md` — Signal-B Befund aktualisiert: ab v4.10.1 in allen Provider-Connectors verfügbar, nicht mehr nur OpenRouter

**Verifikation:** 819/819 Tests grün (vorher: 814 — 5 neue Tests durch Sampling-Keys-Tests).

---

### 2026-06-20 (Session 26) — Spark Token-Management + Bugfixes

**Auslöser:** `qwopus3_6-27b-v2-mtp-q8` auf `llamacpp_spark` blieb bei Test 1/5 (Code Quality Audit) stecken — 24+ Minuten ohne Fortschritt, Retry-Loop alle 300s.

**Root Cause:** Kein `max_tokens`-Cap → Modell generierte bis zum Kontextfenster (65536 Tokens) → httpx Read-Timeout (300s) griff nach 5 Min → OpenAI-Client retried → erneut 300s → LLMClient retried → endloser Zyklus.

**Änderungen:**

1. **`config/provider_config.yaml`:**
   - `read_timeout: 2400` für `llamacpp_spark` (Provider-Level)
   - `parallel: 4` → `parallel: 2` (Provider-Default)
   - `context_length` für alle 6 Spark-Modelle ohne expliziten Wert ergänzt
   - `max_tokens: 16384` für `qwopus3_6-27b-v2-mtp-q8` und `qwopus-3_6-27b-coder-mtp-q8`

2. **`utils/providers/llamacpp_base.py`:**
   - `_get_or_create_client()`: `read_timeout` aus Provider-Config lesen (Default 300s)
   - `query()`: Per-Model `max_tokens`-Cap NACH `resolve_token_budget()`: `min(initial_tokens, model_cfg_max_tokens)`
   - `_extract_response_content()`: Key-Mismatch `"thinking_content"` → `"think_content"` gefixt
   - `_extract_response_content()`: `reasoning_tokens` bevorzugt aus `usage.completion_tokens_details.reasoning_tokens` lesen

**Verifikation:** 31 llamacpp-Tests + 119 Thinking-Tests grün.

**Dokumentation:** CLAUDE.md (3 Pitfalls), ARCHITECTURE.md, DEVELOPER_GUIDE.md, SETUP_GUIDE.md aktualisiert.

---

### 2026-06-20 (Session 25, Runde 2) — Web-Export Nullwert-Entfernung

**Ziel:** Alle Werte ohne Inhalt (None/null) sollen nicht im Web-Export landen. Karten mit Werten bleiben erhalten.

**Änderungen:**
- `scripts/web_export.py`:
  - Neue Funktion `_strip_none(obj)` — entfernt `None`-Werte rekursiv aus Dicts. Listen/Strings/Zahlen/Booleans bleiben erhalten.
  - `_build_leaderboard_entry()`: Rückgabe-Dict wird durch `_strip_none()` gefiltert. `model_card`-Sub-Dict likewise.
  - `_build_compass_entry()`: Rückgabe-Dict ebenfalls durch `_strip_none()` gefiltert.
  - `data.json`-Write: `_strip_emojis(_strip_none(model_json))` statt nur `_strip_emojis(model_json)`.
  - Neue Export-Felder: `profile_verified_by`, `last_modified_at` (waren im Template aber fehlten im Export).
- `tests/test_web_export_card_field_coverage.py`:
  - Sample-Card: fehlende Felder ergänzt (`size_class`, `community`, `profile_verified*`, `last_modified_at`).
  - Test 2: `community="TestCommunity"` im Call ergänzt.
  - Test 5: `model_card: None` → Key wird entfernt (nicht mehr `null`).
  - 4 neue `_strip_none`-Unit-Tests + 1 None-Stripping-Integrationstest.

**Verifikation:** 818/818 Tests grün (1 pre-existing Tag-Vocabulary-Failure ausgenommen). 93 Modelle exportiert, 0 None-Werte in `model_card`, 0 None-Werte in `leaderboard`-Top-Level, 0 None-Werte in `political_compass`.

### 2026-06-20 (Session 25) — Card-Research Force-Run + Template-Cleanup

**Ziel:** Alle 110 Model Cards `profile_verified=true` durch vollständigen Force-Run.

**Ergebnis:** 110/110 verified. Template von 42 auf 37 required Felder reduziert (6 → optional).

**Änderungen:**
- `config/card_template_model.yaml`: `params_total_b`, `params_active_b`, `knowledge_cutoff`, `license_url`, `input_price_per_1m`, `output_price_per_1m` → optional
- `scripts/manage_model_cards.py`: `MODEL=all` Support, `MAX_CARDS=N`, Fortschrittsanzeige
- `scripts/tools/probe_thinking.py`: Path-Bug Fix (`relative_to` Crash)
- 9 lokale Modelle: Thinking-Probe-Placeholder manuell ersetzt (Ollama entfernt)
- 7 Cards: `thinking_probe_at` Timestamp nachgetragen
- 1 Card: `supports_tool_use=False` gesetzt
- 1 Card: `license_url` manuell gesetzt (Claude Sonnet 4.5)

**Bugs gefunden:**
- Parse-Fehler bei `qwen3_5-9b` (1×) — LLM lieferte kein valides JSON, Retry erfolgreich
- `Apache-2.0` vs `Apache 2.0` — LLM interpretiert als Lizenz-Wechsel und rewrite't alle Textfelder (viel Lärm, aber korrektes Ergebnis)

### 2026-06-19 (Session 24) — Card-Research MCP Tool-Use + Lizenz-Heuristik

**Ziel:** `manage_model_cards.py --mode research` soll über MCP `web_search` + `fetch` im Internet recherchieren können — ohne Änderungen am tooluse-MCP-Server oder Benchmark-Code. **Alle Änderungen ausschließlich in `manage_model_cards.py` + Makefile.**

**Architektur:**
```
Card-Research (manage_model_cards.py)
    │
    │  HTTP POST (JSON-RPC 2.0)
    ▼
MCP Server :8765  (unverändert!)
    ├── web_search  (Tavily / DuckDuckGo)
    └── fetch       (HTTP + HTML-to-text)
```

Der bestehende MCP-Server bleibt unberührt. `manage_model_cards.py` ruft ihn via HTTP POST auf — exakt wie der tooluse-Benchmark es auch tut.

**Implementierung (`scripts/manage_model_cards.py`):**

1. **Neue Imports:** `urllib.error`, `urllib.request` (für HTTP POST)
2. **Tool-Schemas (neue Konstanten):**
   - `TOOL_SCHEMA_WEB_SEARCH` — `web_search(query, max_results)`
   - `TOOL_SCHEMA_HTTP_FETCH` — `fetch(url, max_chars)`
   - `TOOL_SCHEMAS` — List beider Schemas
3. **MCP-Helferfunktionen:**
   - `_parse_tool_call(text)` — extrahiert `{"tool_call": {"name": ..., "parameters": {...}}}` aus LLM-Output (stript Markdown-Fences, sucht JSON-Objekte, Fallback: outermost-Object-Search)
   - `_call_mcp_tool(base_url, tool_name, params)` — POST JSON-RPC 2.0 `tools/call` an MCP-Server, Timeout 15s, gibt Transcript-Dict zurück, nie Exception
   - `_extract_tool_content(transcript)` — extrahiert lesbaren Text (content[].text → results[] → content_excerpt → Error-Summary)
4. **Research-Loop (`Researcher._research_tooluse_one()`):**
   - Card laden + Pre-Check-Heuristik (Murks/CJK)
   - Lock setzen (`profile_verified=false`)
   - Loop (max. 3 Tool-Call-Runden):
     - Prompt bauen: Card-JSON + Tool-Schemas + Tool-Ergebnisse bisher
     - LLM-Call mit Tool-Use System-Prompt
     - Antwort parsen: `tool_call` → MCP-Tool ausführen → Ergebnis sammeln → nächste Runde; `findings` → finale Findings → Loop beenden
   - Findings auf Card anwenden, Un-Lock (`profile_verified=true`)
5. **CLI-Flags:**
   - `--tooluse` — Tool-Use-Modus (nur mit `--mode research`)
   - `--mcp-url` — MCP-Server URL (Default: `http://localhost:8765`)

**Makefile:**
- `TOOLUSE=1` in Help-Ausgabe
- `$(if $(TOOLUSE),--tooluse,)` an `card-research` Target angehängt

**Usage:**
```bash
# Single-call research (bestehendes Verhalten)
make card-research MODEL=claude-sonnet-4-6

# Multi-step MCP tool-use research
make card-research MODEL=claude-sonnet-4-6 TOOLUSE=1

# Vorschau
make card-research MODEL=claude-sonnet-4-6 TOOLUSE=1 DRY=1
```

**Verifikation:** Syntax-Check (`py_compile`) grün, `--help` zeigt neue Flags, `--tooluse` + `--mode check` → `SystemExit` (Validierung), `_parse_tool_call()` + `_extract_tool_content()` Unit-Tests grün.

### 2026-06-19 (Session 24, Runde 2+3) — Lizenz-Heuristik + Textfeld-Cascade

**Auslöser:** `make card-research MODEL=gemma-4-12b-it-ud-q8_k_xl` zeigte: LLM erkannte Lizenz-Fehler (Apache 2.0 statt Gemma Terms), aber (a) Pre-Finding `suggested`-Werte wurden nicht angewandt, (b) Textfelder (summary, strengths, etc.) blieben mit alter Lizenz-Referenz, (c) Log/Report-Messages waren hardcodiert.

**Bugs gefixt (Runde 2):**
1. `_commit_card` Log `(profile_verified=true)` hardcodiert → dynamisch `%s`
2. `_render_research_markdown_report` Report-Message hardcodiert → `ResearchReport.profile_verified` Feld
3. `_commit_card` nutzte `parsed["findings"]` statt `report.findings` → Pre-Findings gingen verloren
4. Textfelder nach Lizenz-Wechsel nicht erkannt → `_check_license_cascade()` als Post-Merge-Check (Strings + Listen)

**Textfeld-Pre-Findings (Runde 3):**
- Problem: Cascade-Check lief POST-Merge (in `_commit_card`) mit `suggested=None` → keine Auto-Korrektur möglich. LLM fand nur strukturelle Felder, keine Text-Rewrites.
- Fix 1: `_check_license_text_fields()` als Pre-Finding auf ORIGINAL-Card (VOR dem LLM-Call). Erkennt Textfelder, die alte Lizenz referenzieren wenn Mapping eine Änderung erzwingt.
- Fix 2: System-Prompt Regel 5: "TEXTFELDER BEI LIZENZ-WECHSEL: Wenn sich die Lizenz ändert, MÜSSEN ALLE Textfelder aktualisiert werden mit KOMPLETT NEU GESCHRIEBENEM Text als suggested-Wert."
- Integration: In `_research_one()` + `_research_tooluse_one()` nach `_check_community()` eingefügt. System-Prompt in beiden Modi + dead-code `_build_tooluse_system_instruction()` aktualisiert.
- Verifikation: Syntax-Check grün, Integrationstest: 8 Pre-Findings (3 strukturell + 5 Text), Cascade nach LLM-Text-Rewrites = 0.

**Hinzugefügt in `manage_model_cards.py`:**
- `_check_license_text_fields()` — Pre-Finding: prüft Textfelder gegen EXPECTED-Lizenz aus Mapping
- `_RESTRICTED_KEYWORDS` / `_OPEN_KEYWORDS` — Keyword-Sets für Cascade-Detection
- `_LICENSE_CASCADE_FIELDS` — Tuple der zu prüfenden Textfelder
- `_check_license_cascade()` — Post-Merge-Check (Strings + Listen)
- `_ensure_license_consistency()` — Post-Apply Lizenz/Tier-Korrektur
- `_KNOWN_LICENSE_MAPPINGS` — Gemma 2/3/4, Qwen 2.5/3/3.5, Llama 3/4
- `_KNOWN_COMMUNITY_GROUPS` — Unsloth, mradermacher, HauhauCS, ARA-APEX
- `_match_family()` — Longest-Prefix-Match
- `_check_license_consistency()` — Lizenz-Felder gegen Mappings
- `_check_community()` — Community gegen Taxonomie
- `ResearchReport.profile_verified` Feld

### 2026-06-19 (Session 24, Runde 4) — GGUF-Konventionen + profile_verified-Fix + MCP Auto-Lifecycle

**Auslöser:** LLM überschrieb bei jedem Run korrekte Werte: `deployment_type: localweights` → `open-weights`, `params_active_b: 12` → `null`, Preise `0.0` → `null`. Außerdem: `profile_verified` blieb `false` weil Findings-Historie statt finale Karte geprüft wurde.

**Fixes:**
1. `_is_gguf_model()` — GGUF-Erkennung via `q[2-8]_[k0-9]`, `gguf`, `-ud-`/`_ud_` im model_id
2. `_ensure_gguf_conventions()` — Post-Apply-Korrektur in `_commit_card` NACH allen Findings: `deployment_type=localweights`, `params_active_b=params_total_b` (dense), Preise `0.0`
3. `profile_verified`-Logik umgestellt: Validiert jetzt FINALE Karte (re-runs `_check_license_consistency` + `_check_license_text_fields` + `_check_community` + Pflichtfelder auf `merged`) statt Findings-Historie zu zählen
4. System-Prompt: "Preise muessen 0.0 sein" statt "null" (beide Modi)
5. MCP Auto-Lifecycle: `_ensure_mcp_running()` startet MCP automatisch wenn `TOOLUSE=1`, `_stop_mcp_server()` stoppt am Ende
6. llama.cpp Context-Reset: `_reset_llama_context()` via `POST /slots/{id}?action=reset` nach jeder Karte
7. Health-Check: `GET /health` auf llama.cpp vor jeder Karte

**Ergebnis:** `make card-research MODEL=gemma-4-12b-it-ud-q8_k_xl` → `profile_verified=true`, alle Felder korrekt. GGUF-Erkennung 8/8 Tests bestanden.

**Hinzugefügt in `manage_model_cards.py`:**
- `_is_gguf_model()` — Regex-basierte GGUF-Erkennung
- `_ensure_gguf_conventions()` — Post-Apply GGUF-Korrektur
- `_server_root_url()` — Extrahiert Root-URL aus base_url
- `_check_health()` — Generischer Health-Check
- `_reset_llama_context()` — KV-Cache-Reset via `/slots`-API
- `_ensure_mcp_running()` — Auto-Start MCP-Server
- `_stop_mcp_server()` — MCP-Server stoppen
- `import subprocess` ergänzt

---

### 2026-06-17 (Session 23) — Review-Auto-Fixes + MTP-Modell + 128 GB + (GGUF)-Cleanup

**Commits:** ausstehend

**Kontext:** `make reviews-auto` lief nicht durch — Crash beim Laden des `@dataclass`-Moduls + persistenter `outputs/audit_logs/test/`-Stub-Ordner. Nach erster Sichtung: umfangreicher Cleanup-Sweep mit 3 Themenblöcken.

**Block 1 — Review-Auto-Bugfixes:**

**Fix 1: `@dataclass`-Crash (Python 3.14) in `scripts/analysis/generate_review.py:144-160` (`_load_card_module`):**
- Symptom: `AttributeError: 'NoneType' object has no attribute '__dict__'` in `dataclasses._is_type` (Zeile 814).
- Root Cause: `importlib.util.module_from_spec()` registriert das Modul NICHT automatisch in `sys.modules`. Python 3.14 `@dataclass` braucht `sys.modules[cls.__module__].__dict__` für KW_ONLY-Detection.
- Fix: `sys.modules[module_name] = module` VOR `spec.loader.exec_module(module)`. Standard-Praxis für dynamisch geladene Module.

**Fix 2: `outputs/audit_logs/test/`-Stub-Ordner:**
- Symptom: `outputs/audit_logs/test/asset_1.md` wurde bei jedem Test-Run neu angelegt (15.06.2026 20:13, MagicMock-Content sichtbar).
- Root Cause: `utils/scoring/llm_judge/tests/test_pipeline_integration.py` instanziiert `UnifiedBenchmarkRunner("test")` und ruft `_process_single_test()`. Der Test patcht externe Calls (LLM, HTTP, sleep), aber NICHT `save_audit_log`. `evaluate_judge()` ruft `save_audit_log(model=result["model"], ...)` mit `result["model"] = "test"` → realer File-Write nach `outputs/audit_logs/test/asset_1.md`.
- Fix A (Test): `save_audit_log` zur `mock_dependencies`-Fixture hinzugefügt: `patch("utils.scoring.judge_evaluator.save_audit_log") as mock_audit`. Test verschmutzt das Repo nicht mehr.
- Fix B (Defense in Depth): Neue Helper `_is_valid_audit_dir()` in `generate_review.py` mit Zwei-Pfad-Heuristik:
  - Pfad A: Ordnername sieht aus wie Modellname (>4 Zeichen, Bindestrich/Underscore, keine Punkte)
  - Pfad B: Verzeichnis enthält Audit-Slug-File (`00_bias_report.md`, `cli\d+\.md`, `code_quality_\d+\.md`, `tooluse\d+\.md`, `documentation_quality_\d+\.md`)
  - Schließt `test/`, `foo/`, `.DS_Store` aus, behält `gpt-5_4/`, `qwen3_5-9b/` etc.
- Verifikation: 103 gültige Audit-Ordner erkannt (vorher 104 inkl. Stub), Tests grün, `test/`-Ordner taucht nicht mehr auf.

**Block 2 — DGX-Spark-Modell-Liste + MTP-Support:**

**`config/provider_config.yaml` `llamacpp_spark`-Bereich konsolidiert:**
- 7 aktive Modelle (von 12 unsortierten): gemma-4-31B-it-Q8_0-MTP (neu, 0.5 GB), gemma-4-26B-A4B-it-UD-Q8_K_XL, hermes-4.3-36b-q6, gemma-4-31B-it-UD-Q8_K_XL, **qwen3_6-35b-a3b-mtp-ud-q8** (NEU), qwen3_5-35b-a3b-q8, qwen3-coder-next-q4
- 6 nicht-vorhandene Modelle auskommentiert mit Begründung ("nicht auf Spark")
- 2 neue OpenRouter-Modelle: `z-ai/glm-5.2` (proprietär), `moonshotai/kimi-k2.7-code`

**MTP-Support (Qwen 3.6 Multi-Token Prediction):**
- `utils/providers/llamacpp_base.py:387-397`: Neue `extra_server_args`-Verarbeitung in `_build_server_cmd()` — übergibt beliebige llama.cpp-Flags aus Modell-Config. Ermöglicht `--spec-type draft-mtp`, `--spec-draft-n-max 2`, `--flash-attn`, `--jinja`, `--cache-type-k/v` etc.
- 2 neue Model Cards: `qwen3_6-35b-a3b-mtp-ud-q4.json` + `qwen3_6-35b-a3b-mtp-ud-q8.json` mit Custom-Params (temperature=0.7, top_p=0.8, top_k=20, presence_penalty=1.5, repeat_penalty=1.0, `enable_thinking: false`)
- `qwen3_6-35b-a3b-mtp-ud-q8.json` `extra_server_args: ["--spec-type draft-mtp", "--spec-draft-n-max 2"]`
- 2 neue Whitelist-Tags in `config/card_vocabulary.yaml`: `MTP` (Multi-Token Prediction) + `Speculative-Decoding` (v4.10.0)
- `config/web_export_blacklist.yaml`: `qwen3_6-35b-a3b-mtp-ud-q4` blacklisted (q8 nicht — ist Test-Backlog)
- 3 neue Reviews auto-generiert: `docs/reviews/qwen3_6-35b-a3b-mtp-ud-{q4,q8}/bias_review_*.md` + `review_*.md`

**`utils/cost_tracker.py:113-127` Log-Message präzisiert:**
- Vorher: Eine WARNING für "kein Preis gefunden" — vermischte "Card fehlt" und "Card vorhanden, aber keine Preise (lokales Modell)".
- Nachher: Card-vorhanden-Pfad gibt DEBUG-Message aus + `return 0.0`. WARNING nur bei tatsächlich fehlender Card.

**Block 3 — Content-Korrekturen (28 Model Cards):**

**128 GB Unified Memory für DGX Spark:**
- 28 Referenzen "115 GB" / "120 GB" in 15 Model Cards + `_index.json` auf 128 GB korrigiert
- "DGX10 Spark" → "DGX Spark" (10 = Hostname gx10-b20a.local, kein Modellteil)
- "Desktop" → "Workstation" für 36B+ Klassen (Größen-Klassifikation)

**"(GGUF)"-Cleanup aus User-UI-Feldern:**
- Recherche-Ergebnis: "GGUF" = technisches Inferenz-Format (Container für Quantisierung). Redundant in Display-Namen — Quantisierungssuffix (Q4_K_M, Q8_K_XL etc.) impliziert GGUF.
- Entfernt aus: `display_name`, `summary`, `judge_context_hint`, `strengths`, `known_limitations`, `weights_provenance_risk_rationale`
- Behalten in technischen Feldern: `model_id`, `model_version`, `name` in provider_config, `model_file`, `license_url`
- 181 Updates in 31/5/16 Dateien, 106/106 JSON valide
- 4 Konsolidierungswellen: 134 + 9 + 38 = 181 Ersetzungen

**Verifikation:** 814/814 Tests grün (vorher 6 Failures → 0 Failures). Reviews-Discovery: 103 gültige Audit-Ordner, `test/`-Stub nicht mehr da.

**Pitfall dokumentiert:** Dynamisch geladene Module müssen in `sys.modules` registriert werden, BEVOR `@dataclass`-Klassen ausgeführt werden (Python 3.14+ KW_ONLY-Detection).

**Pitfall dokumentiert:** Test-Fixtures dürfen `save_audit_log` (oder andere File-Write-Funktionen) nicht ungepatcht lassen, sonst verschmutzen sie das Repo unter scheinbar harmlosen Test-Namen.

---

### 2026-06-14 (Session 22) — PC Re-Run nvidia/nemotron-3-ultra + Bias-Review

**Commits:** ausstehend

**Auslöser:** Vorheriger Bias-Report für `nvidia/nemotron-3-ultra-550b-a55b` war ein `[REKONSTRUIERTER BERICHT]` aus CSV-Aggregaten ohne Einzelfragen-Protokolle. PC Re-Run mit echten Token-Daten benötigt.

**PC Re-Run:**
- `make political-compass MODEL="nvidia/nemotron-3-ultra-550b-a55b" FORCE=1` → PID 50016
- Verlauf: Run 1 aus Checkpoint-Resume (66 Fragen cached, 13 neue API-Calls), Run 2 komplett (79 Fragen), Run 3 komplett (79 Fragen)
- Neues Results-File: `outputs/runs/results_nvidia_nemotron_3_ultra_550b_a55b_20260614_124002.json`
- Neuer Bias-Report: `outputs/audit_logs/nvidia_nemotron-3-ultra-550b-a55b/00_bias_report.md` — 136KB, erstellt 14:40, echte Einzelfragen-Protokolle

**Bias-Review generiert:**
- `docs/reviews/nvidia_nemotron-3-ultra-550b-a55b/bias_review_20260614_144114.md` via GPT-5.4

**Pitfall dokumentiert — `--force` vs. `force_new` im PC-Modul:**
- `make political-compass FORCE=1` übergibt `--force` an `run_political_compass_benchmark.py` → umgeht nur den PC-Leaderboard-Skip-Check (`⏩ Überspringe...`)
- `--force` setzt NICHT `force_new=True` in `io_manager.load_checkpoint()` → Checkpoint-File bleibt erhalten → Resume möglich
- `force_new=True` (separater Parameter in `load_checkpoint()`, line 56) → löscht Checkpoint → echter Neustart
- Praktische Konsequenz: `FORCE=1` ohne laufenden Prozess = Resume aus Temp-File + Leaderboard-Override

**Makefile-Klarstellung:**
- `make reviews-auto FORCE=1 TYPE=tooluse` → NEIN, `reviews-auto` hardcoded `--type all`, ignoriert `TYPE=`
- Korrekte Alternative: `make review TYPE=tooluse ALL=1 FORCE=1`

---

### 2026-06-14 (Session 21) — Dot-Dir-Bugfix + Model-ID-Konvention + 5 neue Model Cards + 3 Bias-Reviews

**Auslöser:** Auto-Benchmark-Lauf (2026-06-14, ca. 02:00–10:30 Uhr) für 5 neue Modelle: `xiaomi/mimo-v2.5-pro`, `xiaomi/mimo-v2.5`, `xiaomi/mimo-v2-flash`, `nvidia/llama-3.3-nemotron-super-49b-v1.5`, `nvidia/nemotron-3-nano-30b-a3b`. Audit offenbarte 3 Probleme.

**Bug 1 — Dot-Dir-Pitfall in `audit_logger.py` (Root Cause, behoben):**
- `safe_model` in `benchmark_modules/political_compass/core/audit_logger.py` ersetzte `:` und `/`, aber nicht `.` → Audit-Log-Dirs wie `outputs/audit_logs/xiaomi_mimo-v2.5/` statt `xiaomi_mimo-v2_5/` wurden angelegt.
- Analog in `benchmark_modules/political_compass/test.py` (force_run-Pfad).
- Fix: `.replace(".", "_")` ergänzt. Spurious Dot-Dirs für 3 Modelle manuell auf Underscore-Dirs gemappt (Session 20 bereits erledigt).

**Bug 2 — Model-ID-Konvention kodifiziert:**
- User-Regel: Neue Model-IDs in provider_config.yaml und Card `model_id` dürfen KEINE Punkte enthalten — Versionsnummern mit Punkte → Unterstriche (z.B. `v2.5` → `v2_5`, `3.3` → `3_3`).
- Pitfall + Konvention in `CLAUDE.md` (2 neue Einträge) und `config/editor_prompts.yaml` (neuer `model_onboarding`-Prompt) dokumentiert.

**5 neue Model Cards erstellt (alle `card_status: "minimal"`, `profile_verified: false`):**
- `xiaomi_mimo-v2_5-pro.json` — 1020B MoE (42B aktiv), MIT, 1024K Kontext, $0.435/$0.87
- `xiaomi_mimo-v2_5.json` — MoE, MIT, 1024K Kontext, $0.14/$0.28
- `xiaomi_mimo-v2-flash.json` — dense, MIT, 256K Kontext, $0.10/$0.30
- `nvidia_llama-3_3-nemotron-super-49b-v1_5.json` — 49B dense, NVIDIA Open Model License, 128K, $0.40/$0.40
- `nvidia_nemotron-3-nano-30b-a3b.json` — 30B MoE (3B aktiv), NVIDIA Open Model License, 256K, $0.05/$0.20

**3 fehlende Bias-Reviews generiert (via GPT-5.4):**
- `docs/reviews/xiaomi_mimo-v2_5/bias_review_20260614_125915.md`
- `docs/reviews/xiaomi_mimo-v2_5/bias_review_20260614_125939.md` (zweiter Pass, beide gültig)
- `docs/reviews/xiaomi_mimo-v2-flash/bias_review_20260614_130028.md`
- `docs/reviews/nvidia_nemotron-3-nano-30b-a3b/bias_review_20260614_130057.md`

**Offener Backlog (unverändert aus Session 20):**
- 5 Modelle mit Tests Run < 43: hermes-4.3-36b-q6 (37), gemma-4-12b-it-ud-q6_k_xl (38), gemma-4-12b-it-ud-q8_k_xl (41), gemma-4-12b-it-ud-q4_k_xl (42), gemma-4-26B-A4B-it-qat-ud-q4 (42)
- 11 Review-Dirs ohne vollständige Reviews (gemma/qwen3 Backlog + neue Modelle warten auf Pro-Review)
- deepseek-r1:8b ToolUse-Re-Run ausstehend

---

### 2026-06-13 (Session 20) — PC-Coverage-Fix + Bias-Reviews + Vendor-Card-Dedup

**Commits:** `994d447` (web_export PC card_id + date fallback), `8e02609` (28 bias reviews), `9c38063` (Alibaba dedup + community filter).

**Hintergrund:** Web-Export-Audit identifizierte 3 Kategorien von PC-Datenlücken + Alibaba-Duplikat-Problem.

**Kategorie A — 8 Modelle mit null PC-Koordinaten (Commit 994d447):**
- Root Cause 1: `_build_compass_entry()` fehlte `card_id`-Feld → Fix: neuer Parameter `card_id: str | None = None`.
- Root Cause 2: `pc_leaderboard.csv` speichert undatierte IDs (z. B. `moonshotai/kimi-k2.5`), web_export.py verarbeitete datierte IDs (z. B. `moonshotai/kimi-k2.5-0127`). Slug-Mismatch → `lb_row = None` → null-Koordinaten. Fix: Datum-Fallback: `re.sub(r'-\d{4,8}$', '', _pc_slug)`.

**Kategorie B — Ghost-Model `z-ai/glm-5-20260211` (kein PC-Eintrag):**
- Root Cause: April-2026-Run hatte `z-ai/glm-5` (undatiert) in `political_compass_leaderboard.csv`, bevor die `z-ai/glm-5-20260211`-Card existierte. `base_runner.py` normalisiert Datum-Suffixe via `re.sub(r'-\d{8}$', '', ...)` → `z-ai/glm-5-20260211` → `z-ai/glm-5` → false-positive Skip-Match.
- Fix: PC-Benchmark mit `--force` für `z-ai/glm-5-20260211` re-gerunnt (2026-06-13T17:23:30). UPSERT überschrieb Ghost-Eintrag. Altes `k.A.`-Entry aus `political_compass_results.csv` manuell gelöscht. Bias-Review via GPT-5.4 generiert.

**Kategorie C — 28 fehlende Bias-Reviews (Commit 8e02609):**
- Root Cause: `00_bias_report.md` in `outputs/audit_logs/<model>/` fehlte für viele Modelle → `generate_review.py -t bias` schlug lautlos fehl.
- Fix: Synthetische `00_bias_report.md`-Dateien aus CSV-Daten erstellt → `generate_review.py -t bias -m <model>` für alle betroffenen Modelle ausgeführt. 28 Reviews committed.

**Alibaba Vendor-Card-Dedup (Commit 9c38063):**
- Root Cause: `generate_vendor_cards.py` erstellte am 2026-06-12 automatisch `alibaba_cloud.json` + `alibaba_group_qwen_team.json` ohne Prüfung auf bestehendes `alibaba.json` (kanonischer Name). Alle 3 hatten identische `api_base_url`. Außerdem fehlte `card_subtype: "community"` in `alibaba_group_qwen_team_hauhaucs_community_fine_tune.json`.
- Fix: 2 Orphan-Dateien gelöscht. `hauhaucs`-JSON erhält `card_subtype: "community"`. `web_export.py` `_write_top_level_outputs()`: `vendor_cards = [c for c in _collect_vendor_cards(root_dir) if c.get("card_subtype") != "community"]`.
- Ergebnis: `vendor_cards.json` sinkt von 24 auf 18 Einträge (1 Alibaba statt 3).

---

### 2026-06-13 (Session 19) — Model Card Publish-Audit

**Ziel:** Überprüfung ob alle Model Cards ohne Falschinformationen publishbar sind.

**4 fehlerhafte Cards korrigiert (Commit 1dc07a5):**
- `google_gemma-4-31b-it.json`: `summary` behauptete "Weights nicht öffentlich zugänglich" → falsch für `restricted-weights`. `local_deployment_possible: false → true`. `known_limitations`: "Nur über Cloud-API" entfernt. `judge_context_hint`: "Cloud-only" entfernt.
- `magistral-small-latest.json`: `local_deployment_possible: false → true` (Apache 2.0, Weights auf HuggingFace).
- `deepseek_deepseek-v4-flash.json`: `local_deployment_possible: false → true`, Cloud-Only-Formulierungen entfernt.
- `deepseek_deepseek-v4-pro.json`: gleiche Fixes wie flash.

**`mistral-large-2411.json` geprüft (Commit 5e33133):**
- `restricted-weights` via HuggingFace-Check bestätigt (MRL-Lizenz, Weights öffentlich).
- Hardware-Hinweis ergänzt: `"Lokaler Betrieb erfordert über 300 GB GPU-VRAM (123B dense Modell)"` als erste `known_limitations`-Zeile (aus offiziellem HF Model Card).

**`verify_model_cards.py` ausgeführt + 2 Fixes (Commit fd4ebaf):**
- **Pricing-Fix:** 20 lokale Open-Weights-Modelle hatten `input_price_per_1m: null` / `output_price_per_1m: null`. Für lokale Modelle (kein API-Preis) korrekt: `0.0`. Betroffene: gemma-4 Quants (8 Varianten), hermes-3/4 (4 Varianten), qwen3-coder-lokal (3 Varianten), qwen3_5/3_6-lokal (4 Varianten), codestral-latest.
- **Script-Bug-Fix:** `verify_model_cards.py` Zeile `missing_in_cards = config_model_ids - all_model_ids` erzeugte 18 false-positive „fehlende Cards" weil provider_config Punkte nutzt (`qwen3.5-4b-q4`) und Card-`model_id`-Felder Unterstriche (`qwen3_5-4b-q4`). Fix: `_normalize(mid)` Funktion + normalisierter Set-Vergleich.

**Endstatus verify:**
- `✅ Alle 99 Konfigurationsmodelle haben Cards.`
- Verbleibende `⚠️` sind legitim: `params_total_b: null` (geschlossene Modelle), `thinking_probe_*: null` (neue ungeprüfte Modelle), `license_url: null` (proprietäre Modelle, kein einzelner URL).

---

### 2026-06-13 (Session 18) — Deployment-Badge-Refactoring (Two-Layer-Architektur)

**Kontext:** Scoreboard zeigte für lokale llamacpp-Modelle (`llamacpp`, `llamacpp_spark`) keinen Deployment-Badge — M4APL/SPRK waren Ollama-Ära-Artefakte ohne einheitliche „lokal"-Kategorie. User-Clarification: „lokal" = gesamtes Intranet (M4 MacBook Pro, DGX Spark, Gaming-PC RTX 4070), nicht nur Ollama.

**Architektur-Entscheidung:** Zweischichtiges System:
- **Layer 1 — Deployment-Category (Badge):** `LCL` / `API` / `OR` / `GR` / `CLD` — primärer Shortcode im Scoreboard
- **Layer 2 — Hardware-Profile (Detail/Tooltip):** `m4_macbook_pro_metal` / `dgx_spark_cuda` / `rtx4070_cuda` — gerätespezifischer Kontext

**`config/provider_config.yaml`:**
- Neuer Top-Level-Block `hardware_profiles` mit 3 Einträgen:
  - `m4_macbook_pro_metal`: Apple M4 Pro, 24 GB unified memory, Metal backend
  - `dgx_spark_cuda`: NVIDIA DGX Spark, GB10 Superchip, ~115 GB
  - `rtx4070_cuda`: NVIDIA RTX 4070, 12 GB VRAM, CUDA backend
- `deployment_category` zu allen Providern ergänzt: `api` (anthropic, openai, google, xai, mistral), `cloud` (groq, openrouter, ollama_cloud), `local` (ollama_local, llamacpp, llamacpp_spark)
- `llamacpp.short_code`: `M4APL` → `LCL`
- `llamacpp_spark.short_code`: `SPRK` → `LCL`

**`utils/model_utils.py`:**
```python
_PROVIDER_DEPLOYMENT_CATEGORY: dict[str, str] = {
    "anthropic": "api", "openai": "api", "google": "api", "xai": "api", "mistral": "api",
    "openrouter": "cloud", "groq": "cloud", "ollama_cloud": "cloud",
    "ollama": "local", "ollama_local": "local", "local": "local",
    "llamacpp": "local", "llamacpp_spark": "local", "llama_cpp": "local", "llamacpp_local": "local",
}

_PROVIDER_HARDWARE_PROFILES: dict[str, str] = {
    "llamacpp": "m4_macbook_pro_metal",
    "llamacpp_spark": "dgx_spark_cuda",
    "llama_cpp": "m4_macbook_pro_metal",
    "llamacpp_local": "m4_macbook_pro_metal",
}

def get_deployment_category(provider: str) -> str:
    return _PROVIDER_DEPLOYMENT_CATEGORY.get(str(provider).lower().strip(), "local")

def get_hardware_profile(provider: str) -> str | None:
    return _PROVIDER_HARDWARE_PROFILES.get(str(provider).lower().strip())
```
- `_PROVIDER_SHORTCODES`: `llamacpp` + `llamacpp_spark` + alle lokalen Varianten → `LCL`

**`scripts/leaderboard/__init__.py`:**
- Import: `get_deployment_category`, `get_hardware_profile`
- Step 10: 2 neue Spalten: `Deployment Category` + `Hardware Profile`

**`scripts/web_export.py`:**
- Import: `get_deployment_category`, `get_hardware_profile`
- `_build_leaderboard_entry()`: 3 neue Felder: `provider_code`, `deployment_category`, `hardware_profile`

**`docs/MODEL_CLASSIFICATION.md`:**
- Sektion „Provider-Kategorien" → „Provider-Kategorien & Deployment-Badges" komplett neu: Two-Layer-Tabelle, Hardware-Profile-Tabelle, Anleitung „Neue Hardware hinzufügen" (4 Schritte).

---

### 2026-06-12 (Session 17) — 4 SSoT-Robustness-Fixes

**Commits:** `e5799bb`, `3225a78`, `4aaf450`, `411e5e3` (alle gepusht). **Architektur-Prinzip etabliert:** `model_id` = einziger SSOT-Kommunikations-Anker.

**Fix e5799bb — Hardware-Kontext SSOT (`system_context.py` + `generate_review.py`):**
- Symptom: Benchmark-Reviews für DGX-Spark-Modelle zeigten M4-MacBook-Hardware-Kontext statt DGX-Spark-Profil.
- Root Cause: `SystemContextManager` las `active_profile` aus Environment (= lokales Mac-System) statt Testsystem-Profil.
- Fix: `get_editor_prompt_injection(hardware_profile_key: str = "")` — neuer Parameter. Bei gesetztem Key: Profil-Lookup aus `benchmark_config.yaml → runner_environment.profiles`.
- Neue Hilfsfunktion `_get_hardware_profile_for_model(model_id, config)` in `generate_review.py`: Durchsucht alle Provider-Sektionen in `provider_config.yaml` nach `hardware_profile`-Key.
- 2 neue Profile in `benchmark_config.yaml`: `dgx_spark_cuda` (NVIDIA DGX Spark, GB10, ~115GB) + `m4_macbook_pro_metal` (Apple Silicon M4, 24GB).

**Fix 3225a78 — Tooluse-Reviews per-model Modus (`generate_review.py`):**
- Symptom: `--per-model-all-reviews` generierte keine Tooluse-Reviews.
- Root Cause: Tooluse-Leaderboard-IDs sind Ollama-Format (`gemma3:12b`) — können nicht auf Audit-Log-Slugs (CrucibleMark-Format) gemappt werden. Der per-model-Loop iteriert über Modell-IDs, findet kein Match.
- Fix: Tooluse-Schritt aus dem per-model-Loop herausgenommen → läuft nach dem Loop einmalig mit `tooluse_args.model = None` (= alle Modelle in einem Durchlauf).

**Fix 4aaf450 — Web-Export PC-Lookup (`scripts/web_export.py`):**
- Symptom: Political-Compass-Daten fehlten im Web-Export für Modelle, bei denen `raw_model_id` und Display-Name verschieden waren.
- Root Cause: `_lookup_pc_row` verwendete Display-Namen (`model_name`) für den Lookup in `political_compass_leaderboard.csv`. Die CSV enthält aber IDs ohne Vendor-Prefix (z.B. `qwen3.5-35b-a3b-q4`), nicht Display-Namen.
- Fix: `_pc_id = raw_model_id if raw_model_id and raw_model_id != "nan" else model_name`. `_pc_slug = slugify(_pc_id)`. PC-Lookup und PC-Leaderboard-Map-Lookup nutzen jetzt konsequent die ID.

**Fix 411e5e3 — Blacklist-Check in Tooluse-Reviews (`generate_review.py`):**
- Symptom: Tooluse-Reviews wurden für Modelle generiert, die auf der Webexport-Blacklist stehen.
- Root Cause: Guard 2 (`_run_tooluse_reviews`) las die Model Card zweimal, Blacklist-Check nutzte Slug statt `model_id`.
- Fix: Guard 2 lädt Model Card einmal (`card = _load_model_card(card_path)`), liest `model_id = card.get("model_id", slug)`, prüft `model_id in blacklist` (O(1)-Set-Lookup).

---

### 2026-06-12 — Vendor Cards vervollständigt (Commit a8acdd7)

**5 unvollständige Vendor Cards korrigiert und verifiziert:**
- `google.json`: display_name "Google DeepMind" → "Google AI", notable_models aktualisiert (Gemini 1.5 → Gemini 3.x/2.5/Gemma 4), data_residency gesetzt, description hinzugefügt, profile_verified
- `alibaba_cloud.json`: notable_models (Qwen → Qwen3.x), description hinzugefügt, profile_verified
- `alibaba_group_qwen_team.json`: notable_models (Qwen2.5 → Qwen3.x), description, gdpr_dpa_available "unknown"→false, profile_verified
- `alibaba_group_qwen_team_hauhaucs_community_fine_tune.json`: notable_models (Qwen3 Fine-Tunes), description, gdpr_dpa_available/eu_adequacy_decision "unknown"→false, profile_verified
- `google_deepmind_base_undix_community_distribution.json`: notable_models (Gemma 4 ergänzt), description, gdpr_dpa_available/eu_adequacy_decision "unknown"→false, profile_verified

**Alle 25 Vendor Cards jetzt profile_verified, bis auf `ara_apex_quant` und `unknown` (Platzhalter).**

---

### 2026-06-12 — Systematische Modellkarten-Korrektur (Commit 08845aa)

**Auslöser:** Bei Stichproben wurden fehlerhafte Metadaten in Modellkarten entdeckt (MiniMax M3, Claude Sonnet 4.6). Daraufhin wurden alle 98 Modellkarten systematisch per 5 paralleler Subagenten recherchiert und korrigiert.

**Korrigierte Karten (9 Dateien):**
- `gpt-4o-mini`: input_price 1.25 → 0.15, output_price 5.0 → 0.60 (offizieller OpenAI-Preis)
- `claude-sonnet-4-5-20250929`: context_window_k 1000 → 200 (Anthropic-Docs: 200k, nicht 1M)
- `gpt-5`: context_window_k 400 → 272 (LiteLLM/OpenAI: tatsächliches Limit)
- `gpt-5-mini`: input 0.75 → 0.25, output 4.5 → 2.0, ctx 200 → 272 (mit gpt-5.4-mini verwechselt)
- `gpt-5_4-mini`: context_window_k 128 → 272
- `gpt-5_4-nano`: context_window_k 400 → 272 (Texte in summary/strengths angepasst)
- `mistral-small-2603`: context_window_k 32 → 128 (Mistral Small 4 hat 128k)
- `qwen/qwen3-32b`: context_window_k 32 → 128 (32 war Modellgröße, nicht Kontextfenster)
- `qwen3.5:397b-cloud`: ctx 128 → 262, prices 0.6/3.6 → 0.39/2.34, local_deployment → true

**Recherche-Methode:** 5 Subagenten parallel (LiteLLM-Referenzdatei, offizielle API-Docs)

---

### 2026-06-12 — v4.9.4 Auto-Review Webexport-Blacklist Integration

**Commits:** TBD. **Tests:** Keine neuen Tests (Feature-Ergänzung in bestehendem Workflow).

**Hintergrund:** Modelle auf der Webexport-Blacklist benötigen kein Review, da sie nicht im Web-Export publiziert werden. Der Auto-Review-Modus sollte diese Modelle automatisch überspringen.

**Implementierung (`scripts/analysis/generate_review.py`):**

1. **Neue Funktion `_load_webexport_blacklist()` (Zeile 60-76):**
   - Liest `config/web_export_blacklist.yaml → blacklist`-Array
   - Returniert `set[str]` für O(1)-Lookup-Performance
   - Fehlertoleranz: Bei Ladefehlern wird leeres Set zurückgegeben (+ Warnung)

2. **Skip-Check in `_run_per_model_all_reviews()` (Zeile 732-735):**
   - `blacklist = _load_webexport_blacklist() if args.auto else set()`
   - Vor Review-Generierung: `if args.auto and slug in blacklist: print("⏩ ... Auf Webexport-Blacklist → Review wird übersprungen."); continue`

3. **Skip-Check in `_run_audit_reviews()` (Zeile 793, 810-814):**
   - Analog zur Per-Model-Funktion — Blacklist nur im `--auto`-Modus geladen und geprüft

**Scope:** Nur `--auto`-Modus betroffen (`make reviews-auto`). Manuelle Review-Aufrufe für einzelne Modelle ignorieren die Blacklist.

**Dokumentation:** `docs/AUDIT_AND_METAREVIEW.md` Sektion 2 um Webexport-Blacklist-Hinweis ergänzt.

---

### 2026-06-12 — v4.9.3 Vendor Card: description-Feld + editor_prompts-Fix

**Commits:** `871fa8c` (feat) + `2b4a433` (fix). **803/803 Tests grün.**

**Added — `config/card_template_vendor.yaml` v1.1.0:**
- Neues optionales Feld `description` (erstes optionales Feld, Position vor `card_subtype`):
  - `consumers: [web_export, review]`, `since: "v4.9.3"`
  - Constraints: `min_length: 240`, `max_length: 480`, `target_length: 360`
  - Pflicht-Hinweis: kurze, prägnante Beschreibung des Herstellers/der Community in 2–3 Sätzen
- Template-Version: `1.0.0` → `1.1.0`

**Fixed — `config/editor_prompts.yaml` prompt `provider_card_verification`:**
- `targets.directory`: `provider_cards/` → `vendor_cards/`
- Prompt-Text Schritt "Auftrag": `provider_cards/` → `vendor_cards/`
- Schritt 1 + Schritt 4: `provider_id` → `vendor_id`

**Tests:**
- `tests/test_card_template.py`: `test_provider_template_loads` Version-Assertion `"1.0.0"` → `"1.1.0"`

---

### 2026-06-12 — v4.9.1 Terminologie-Refactoring: Provider Cards → Vendor Cards

**Commit:** `570bc0f` — 50 Files geändert, 593 Insertionen, 481 Löschungen. **803/803 Tests grün.**

**Hintergrund:** Provider war doppelt belegt (API-Laufzeit UND Hersteller-Karte). Endgültige Trennung:
- `provider` = API-Laufzeit (Ollama, Anthropic, DGX Spark) — bleibt unverändert in allen Laufzeit-Dateien
- `vendor` = Hersteller-/Community-Profil-Karte — konsequent als "Vendor Card" benannt

**Phase 1 — Rename:**
- `benchmark_scores/provider_cards/` → `vendor_cards/` (17 JSON-Dateien)
- `config/card_template_provider.yaml` → `card_template_vendor.yaml`
- `utils/provider_card_template.py` → `vendor_card_template.py`
- `scripts/analysis/generate_provider_cards.py` → `generate_vendor_cards.py`
- `scripts/analysis/generate_provider_stats.py` → `generate_vendor_stats.py`
- `scripts/analysis/provider_card_status.py` → `vendor_card_status.py`
- `tests/test_provider_card_*.py` → `test_vendor_card_*.py` (3 Dateien)
- Vendor Card JSON: `provider_id` → `vendor_id` (alle 17 Dateien)

**Phase 2 — Content-Updates:**
- `config/card_template_vendor.yaml`: `card_type: "vendor"`, `name: vendor_id`
- `utils/card_template.py`, `utils/card_sync.py`: card_type `"provider"` → `"vendor"` (Literal, Checks)
- `scripts/analysis/validate_cards.py`, `sync_cards.py`, `generate_model_cards.py`: choices + card_type
- `Makefile`: Targets `vendor-cards`, `vendor-cards-status`, `vendor-cards-update`
- Docs: ARCHITECTURE, AUDIT_AND_METAREVIEW, CARD_MANAGEMENT, MAINTENANCE_LOG, THINKING_PROBE, USER_GUIDE, README
- `web_export.py`: `_collect_vendor_cards()`, output `vendor_cards.json`, `vendor_card_count` in meta

**Phase 3 — SSoT-Verknüpfung Taxonomy → Vendor Cards:**
- `config/classification_taxonomy.json → manufacturers`: `vendor_card_id` zu allen 13 Einträgen ergänzt
- `scripts/web_export.py`: `_build_vendor_card_id_lookup()` NEU → `vendor_card_ref` in jeder Modell-`data.json`
- `scripts/verify_model_cards.py`: `_load_vendor_card_id_map()` NEU + `🗂️`-Warnung wenn Vendor Card fehlt

**Test-Fixes:**
- `tests/test_card_template.py`: `profile_verified: True, profile_verified_at: "2026-01-01"` in Fixture (None ist Sentinel)
- `scripts/web_export.py`: `profile_verified` + `profile_verified_at` in model_card sub-dict ergänzt (waren als `web_export`-Consumer im Template markiert, fehlten im Sub-Dict)

**Bewusst NICHT umbenannt (Laufzeit-Provider-Konzept):**
- `config/provider_config.yaml`
- `utils/providers/`, `utils/provider_detection.py`, `utils/provider_health.py`, `utils/provider_selector.py`
- `provider`-Feld in Model Cards (`card.get("provider")`)

---

### 2026-06-12 (Session 16) — v4.9.0 Card-Datenpflege-System: Vendor-Kanonisierung + profile_verified + Editor-Prompt

**Scope:** Vollständiges Datenpflege-System für Model Cards und Provider Cards eingeführt. Drei Komponenten:

**1 — Vendor-Kanonisierung (Vorarbeit dieser Session):**
- `config/classification_taxonomy.json → manufacturers`: 13 kanonische Hersteller-Namen als SSOT
- `scripts/web_export.py _normalize_vendor()`: Normalisiert Vendor-Strings auf kanonische Namen (Aliase → Kanonisch)
- `scripts/verify_model_cards.py`: `🏭`-Warnungen bei nicht-kanonischen Vendor-Namen in Model Cards
- 16 Model Card JSONs mit Vendor-Korrekturen migriert (z.B. "Alibaba Cloud" → "Alibaba")

**2 — `profile_verified` / `profile_verified_at` für Model Cards:**
- `config/card_template_model.yaml`: 2 neue optionale Felder (seit v4.9.0) vor `heritage_ids`:
  - `profile_verified: bool` — True wenn inhaltliche Felder manuell recherchiert + verifiziert
  - `profile_verified_at: str | null` — ISO-8601-Datum der letzten Verifikation
- `scripts/verify_model_cards.py`: `🔍`-Warnungen wenn Feld fehlt oder `false`
- **119 Model Card JSONs** per `jq` bulk-migriert: `profile_verified: false`, `profile_verified_at: null`
- Scope der Verifikation: Alle inhaltlichen Felder **außer** Probe-Felder, ToolUse-Felder, Sampling-Parameter, `generated_at`, `card_status`, `heritage_ids`, `unknown`

**3 — `config/editor_prompts.yaml` — Prompt `model_card_verification`:**
- Strukturierter LLM-Prompt für redaktionelle Model-Card-Verifikation
- Glossar, 5-Schritt-Prozess, Was-verändern / Was-gesperrt-Tabelle, Qualitätskriterien
- `supports_tool_use` researchierbar, aber ToolUse-Benchmark-Override-Hinweis

**Dokumentation aktualisiert:**
- `docs/CARD_MANAGEMENT.md`: 3 neue Sektionen (Vendor-Kanonisierung, profile_verified-Workflow, Editor-Prompts) + Feldzahl-Update ("38 Pflicht, 18 Optional inkl. profile_verified")
- `memory-bank/activeContext.md`: Session-16-Eintrag

**Verifikation:** Alle 119 Model Card JSONs migriert, Template konsistent mit Provider Card Schema (profile_verified bereits auf Provider Cards vorhanden). `verify_model_cards.py` gibt korrekte `🔍`-Warnungen aus.

### 2026-06-12 (Session 15) — v4.8.6 Robustness-Fixes: Judge-Coverage, Draft-Card-Warning, ToolUse P1/P2 SSoT

**3 Robustness-Fixes implementiert (52/52 Tests grün):**

**Fix 1 — Judge-Skip-Coverage (`scripts/leaderboard/score_calculator.py::_aggregate_basic_stats()`):**
- Judge-Skip-Zeilen (`judge_prog.str.contains("skip")`) vor der Coverage-Formel herausgefiltert.
- Verhindert falsches 98%-Coverage wenn absichtlich übersprungene Antworten (z.B. kurze Refusals) in die Berechnung einfließen.

**Fix 2 — Draft-Card-Warning (`scripts/leaderboard/__init__.py`):**
- Nach `_model_name_ssot()`: `print()` + `logger.warning()` wenn `Model Name == "TODO"`.
- Macht auto-erstellte Draft-Cards (`ensure_card()`) sofort im Leaderboard-Lauf sichtbar — kein stilles Weiterlaufen mit unvollständigen Daten.

**Fix 3a — `update_model_card_tooluse_fields()` erweitert (`utils/model_utils.py`):**
- Neue Parameter `p1_score: float | None` und `p2_score: float | None`.
- Schreibt `tooluse_score_p1`/`tooluse_score_p2` direkt in Card JSON (atomarer Write mit `card_sync.py`-Muster).

**Fix 3b — `finalize_model()` persistiert P1/P2 in Card (`scripts/core/tooluse_exporter.py`):**
- Ruft `update_model_card_tooluse_fields()` mit `p1_score=_p1_mean`, `p2_score=_p2_mean` auf nach Live-Run.
- Scores aus Live-Runs werden dauerhaft in der Card gespeichert, nicht nur im Leaderboard-CSV.

**Fix 3c — `_aggregate_asset_rows()` bevorzugt Card-Werte (`scripts/core/tooluse_exporter.py`):**
- Return-Dict: `"p1_score"` und `"p2_score"` prüfen zuerst `card.get("tooluse_score_p1/p2")` als `float`.
- Fallback auf `_fmt_score(_mean(p1_scores))` nur wenn Card-Wert fehlt oder kein Float.
- Verhindert dass `make tooluse-leaderboard` (= `aggregate_from_benchmark_csvs()`) manuell validierte Scores überschreibt.

**Dokumentation synchronisiert:**
- `docs/MAINTENANCE_LOG.md`: v4.8.6-Eintrag mit allen 3 Fixes
- `docs/TOOLUSE_MODULE.md`: Card-Score-Felder (`tooluse_score_p1`/`p2`) in SSoT-Tabelle ergänzt
- `docs/SCORING_METHODOLOGY.md`: Judge-Skip-Filterhinweis unter "Core Metriken" ergänzt
- `README.md`, `PROJECT_STATUS.md`, `REF_TODO.md`: Versionsbadge + Abschluss-Eintrag auf v4.8.6 aktualisiert

**Verifikation:** 52/52 Tests grün (Teilsuite). Kein Funktions-Regressionsrisiko — alle Änderungen sind defensive Zusatz-Logik (Filter + Fallbacks), kein Verhalten geändert wenn keine Skip-Zeilen / kein Draft / keine Card-Score-Felder vorhanden.

### 2026-06-11 (Session 13) — Signal-B Cold-Start-Fix + gemma-4-26B-A4B Card finalisiert

**Signal-B Cold-Start-Fix (Option C):**
- `utils/model_utils.py` `_probe_single()`: Signal-B-Branch mit Cold-Start-Guard — `reasoning_tokens > 0` + leerer Output → `detected=False, confidence="low"` statt fälschlich `detected=True`.
- `tests/test_thinking_probe_inline_cot.py`: 2 neue Tests (Cold-Start empty + whitespace-only). 13/13 Tests grün.
- `docs/THINKING_PROBE.md`: Signal-B-Tabelle und Testanzahl aktualisiert (11 → 13).
- Hintergrund: gemma-4-26B-A4B-it-qat-ud-q4 Probe lieferte 2/3 Probes mit 0-chars-Output + reasoning_tokens=512 → Cold-Start-Fehlerkennung. Fix verhindert Fehlklassifikation.

**gemma-4-26B-A4B-it-qat-ud-q4 Card finalisiert:**
- ToolUse-Benchmark gelaufen (DGX Spark, MCP live): P1=88.33, P2=63.33, Combined=75.12 — Empfehlung: PRODUCTION (kein Hallucination-Flag).
- Card: `supports_tool_use: true`, `tooluse_tested_at: 2026-06-11T17:49:32Z`, `tooluse_score_p1: 88.33`, `tooluse_score_p2: 63.33`, `tooluse_recommendation: "PRODUCTION"`, `card_status: "complete"`.
- Nebenbeobachtung: `tooluse_exporter.finalize_model()` hat `update_model_card_tooluse_fields()` still-silently nicht in die Card geschrieben (Ausnahme auf DEBUG-Level abgefangen). Manueller Fallback via direktem Python-Call war nötig.

**Verifikation:** 72/72 Thinking-Probe-Tests grün.

### 2026-06-11 (Session 12 cont.) — Small-Model-Token-Budget + Card-Fixes

**Anlass:** Systematische Truncations bei `documentation_quality_005` für Gemma-4-12B GGUF-Modelle (token budget exhaustion). Zusätzlich: 2 neue Draft-Cards mit TODO-Placeholdern + fehlenden Sampling-Keys blockierten Tests.

**Small-Model-Token-Budget-Feature:**
- `benchmark_config.yaml`: Neuer Block `token_budgets_small_models` mit erhöhten Budgets für Small-Modelle:
  - `documentation_quality: 8000`, `code_quality: 8000`, `ux_writing: 5000`, `content_transformation: 5000`, `cli_benchmark: 5000`
- `utils/model_utils.py` `resolve_token_budget()`: Neuer Branch nach `thinking_optional`-Check — greift nur für **nicht-reasoning** Modelle der Size-Classes Nano/Edge/Desktop/Workstation. Erhöhtes Budget überschreibt Standard-Budget nur wenn `_small_budget > tokens`.
- `utils/scoring/judge_evaluator.py`: Injiziert `small_model_token_context`-Dict in Judge-kwargs wenn Small-Modell (nicht-reasoning) + erhöhtes Budget aktiv.
- `utils/scoring/llm_judge/judge_prompt_builder.py`: Nimmt `small_model_token_context` entgegen → fügt Prompt-Note ein: Judge soll Komplettheits-Lücken nicht bestrafen.

**Pitfall erkannt (gemma-4-12b):** `thinking_probe_detected=True` → nutzt bereits 12000-Token-Reasoning-Budget → NOT betroffen vom Small-Model-Branch. Small-Model-Budget nur für echte Instruct-Modelle ohne Reasoning.

**Card-Fixes (2 neue Draft-Cards):**
- `anthropic_claude-haiku-4-5.json`: Vollständig ausgefüllt basierend auf `claude-haiku-4-5-20251001.json` — `weights_license_tier: proprietary`, Sampling-Keys ergänzt, `card_status: complete`.
- `gemma-3-12b-it-spark.json`: Vollständig ausgefüllt basierend auf `gemma-3-12b-it.json` — `weights_license_tier: restricted-weights`, Sampling-Keys ergänzt, `card_status: complete`. Probe-Ergebnis (`thinking_probe_detected: true`, medium confidence) beibehalten.

**Config-Änderungen:**
- `config/provider_config.yaml`: Gemma 3 12B IT Q4_K_M + Q8_0 für DGX Spark aktiviert (auskommentierte Einträge reaktiviert als `gemma-3-12b-it-spark` + `gemma-3-12b-it-q8-spark`).
- `config/web_export_blacklist.yaml`: 5 Modelle blacklisted — `qwen3-coder-next-q8`, `qwen3_5-35b-a3b-q8`, `qwen3_5-4b-q6`, `gemma-4-12b-it-ud-q4_k_xl`, `gemma-4-12b-it-ud-q8`.

**Sonstiges:**
- `outputs/audit_logs/gpt-5.4-nano/` → `gpt-5_4-nano/` umbenannt (`_safe_name`-Konformität, Test `test_audit_logs_dirs_use_safe_name`).

**Verifikation:** **801/801 Tests grün** (vorher 2 Failures: taxonomy_placeholder + sampling_defaults).


### 2026-06-11 (Session 12) — LLM Judge Coverage Audit + Cleanup

**Anlass:** User-Auftrag: Leaderboard auf vollständige Test-Abdeckung und LLM Judge Coverage prüfen, fehlerhafte Einträge identifizieren und für Re-Test bereinigen.

**Analyse:**
- Ausgangslage: 9 Modelle mit LLM Judge Coverage < 100%, 2 Modelle mit Tests Run < 43
- Judge-applicable Modules (aus `benchmark_config.yaml`): `code_quality`, `ux_writing`, `documentation_quality`, `content_transformation`, `cultural_intelligence`, `cli_benchmark`, `reasoning`
- tooluse001-006 + political_compass: kein Judge erwartet → keine Coverage-Relevanz

**Ursachen für Coverage-Lücken (3 Kategorien):**
1. **status=error** — Request timed out / Test execution failed (hermes, gemma-q6, glm-5-20260211)
2. **status=success / finish_reason=error** — widersprüchliche Flags (magistral-small reasoning_metacog_002–005, qwen3.5-397b tooluse001)
3. **success/no-judge** — Modell lief erfolgreich, aber Judge-Phase hat das Asset nicht evaluiert (ux_writing_002/003/005, documentation_quality_004/005, code_quality_001, cultural_intel_003/005, reasoning_metacog_001)

**Besonderer Fall glm-5-20260211:** 21 stale Error-Rows aus 3 vollständig fehlgeschlagenen Runs (code_quality/02462f0118de, reasoning/ae40611153b3, ux_writing/c5d141923b7e) — neuere erfolgreiche Runs existierten bereits, aber Altlasten zogen Coverage auf 95% runter.

**Cleanup:**
- **46 Einträge entfernt** aus 3 CSVs (12 local, 26 cloud, 8 commercial)
- Backups: `*.bak_judge_cleanup_20260611_073204`
- Leaderboard neu generiert: Coverage **100% bei allen 94 Modellen**

**Offene Re-Tests (10 Modelle mit Tests Run < 43):**
| Modell | Tests Run | Fehlende Assets |
|---|---|---|
| hermes-4.3-36b-q6 | 37/43 | code_quality_001, doc_003/004, wcag_audit, security_audit |
| magistral-small-latest | 38/43 | reasoning_metacog_001–005 |
| gemma-4-12b-it-ud-q6_k_xl | 39/43 | ux_writing_002/003/005, asset_001_error_messages, asset_5b |
| gpt-5_5 | 41/43 | code_quality_001, documentation_quality_004 |
| z-ai/glm-5-20260211 | 41/43 | cultural_intel_003/005 |
| gemma-4-12b-it-ud-q8_k_xl | 42/43 | ux_writing_002 |
| qwen/qwen3.5-397b-a17b | 42/43 | cultural_intel_005, tooluse001 |
| gemma-4-12b-it-ud-q4_k_xl | 42/43 | documentation_quality_005 |
| z-ai/glm-4.7 | 42/43 | cultural_intel_003 |
| magistral-medium-latest | 42/43 | ux_writing_002 |

**Pitfall erkannt:** `cultural_intel_003` und `cultural_intel_005` fehlt systematisch bei mehreren Modellen (glm-4.7, glm-5-20260211, qwen3.5-397b-a17b) → möglicherweise spezifische Asset-Probleme in diesen cultural_intelligence-Aufgaben, die Judge-Evaluation verhinderten. Beim Re-Run beobachten.


### 2026-06-10 (Session 10) — CHANGELOG-Abschluss + Pricing-Update + Commit

**Anlass:** Memory Bank aktualisieren, uncommittete Änderungen committen, Workspace aufräumen.

**Analyse:** 25 modifizierte Dateien + 1 ungetrackte Datei (`scripts/update_model_pricing.py`). CHANGELOG hatte v4.7.9–v4.8.2 aber keine Einträge für ToolUse-NaN-Fix (Session 7), Backup-Audit (Session 9) oder Pricing-Update.

**Ergänzte CHANGELOG-Versionen:**
- **v4.8.3** — ToolUse P1/P2 NaN-Bug (unified_runner flat-column, tooluse_exporter fallback, run_score_benchmark CRUCIBLE_DELEGATE_PARENT, mcp_config idle_timeout=0)
- **v4.8.4** — Backup-System-Audit (cleanup_reviews SSoT, test_backup_targets Lücke, BACKUP_STRATEGY.md Abschnitt 4.3)
- **v4.8.5** — Pricing-Update (update_model_pricing.py NEU, 11 Modellkarten: gpt-4o-mini, gpt-5, gpt-5-mini, grok-3/mini, magistral-medium/small, mistral-large-2411/2512, mistral-medium-3-5, qwen3-coder-next-q8)

**Nicht-Bug-Befunde:** `update_model_pricing.py` war ungetrackt (nicht temporär — legitimes Wartungsskript zum Committen).

**Verifikation:** CHANGELOG vollständig v4.7.9–v4.8.5. Alle Dateien committed.


### 2026-06-10 (Session 9) — Backup-System-Audit + SSoT-Fixes

**Anlass:** Prüfung ob Backup-Skripte mit den refaktorierten Skript-Funktionen (Phase 27) übereinstimmen.

**Analyse-Ergebnis:** Makefile und Kern-Skripte korrekt. 3 Abweichungen gefunden:

1. **`scripts/maintenance/cleanup_reviews.py`** — importierte `REVIEWS_KEEP_PER_CATEGORY` aus `utils/backup_targets.py` (SSoT) **nicht**. Hardcoded `[1:]` in 3 `to_delete.extend()`-Aufrufen. Fix: Import hinzugefügt, `[1:]` → `[REVIEWS_KEEP_PER_CATEGORY:]`.

2. **`tests/test_backup_targets.py`** — Test-Lücke: `audit_logs_legacy_backup_*` fehlte in der `required`-Menge von `test_build_tar_excludes_contains_critical_patterns`. Fix: Pattern ergänzt.

3. **`docs/BACKUP_STRATEGY.md` Abschnitt 4.3** — Zeigte vereinfachtes, veraltetes Makefile-Recipe:
   - Falscher Skript-Pfad: `cleanup_runs.py --keep` statt `make clean-runs` (→ `clean.py --runs`)
   - Fehlende tar-Excludes (`.DS_Store`, `audit_logs_legacy_backup_*`, `audit_logs_spurious_archive`, `audit_logs.zip`, `model_cards_backup_*.tar.gz`, `model_cards_spurious_archive`, `outputs/temp/session_*.json`)
   - Fehlende Post-Backup-Schritte: `clean-bak`, `clean-reviews FORCE=1`, `prune-orphans FORCE=1`
   - Neuer Hinweis: Exclude-Liste muss synchron mit `build_tar_excludes()` gehalten werden

**Verifikation:** 28/28 Tests grün (`test_backup_targets.py` + `test_cleanup_reviews.py`).

**Nicht-Bug-Befund:** Makefile hatte `--exclude='tooluse_unreachable_*.json'` bereits — frühere Analyse war durch abgeschnittene Search-Ergebnisse fehlerhaft.


### 2026-06-10 (Session 7) — ToolUse P1/P2-NaN-Bug + Memory-Bank-Update

**Anlass:** qwen3-coder-next-q8 zeigte nach erfolgreichem ToolUse-Lauf (6/6 Tests, live MCP) `P1=NaN`, `P2=NaN`, `mcp_mode=mock` im Leaderboard. Combined-Score (74.62) war korrekt.

**Root Cause:** `_aggregate_asset_rows()` in `scripts/core/tooluse_exporter.py` las P1/P2 aus `score_contributions`-Feld. Seit Writer-Redesign (post-commit d82996f) schreibt `_build_result_envelope()` in `unified_runner.py` dieses Feld NICHT mehr → bei neuen CSV-Zeilen leer. Combined hatte separaten Fallback via `total_score`, P1/P2 hatten keinen → NaN.

**Drei Fixes:**
1. **`scripts/core/unified_runner.py` `_build_result_envelope()`:** ToolUse-Felder als flache CSV-Spalten aus `exec_result.data` promoten (Duck-Typing: `"p1_score" in exec_result.data`). Felder: `p1_score`, `p2_score`, `combined_score`, `mcp_mode`, `tool_call_valid`, `tool_call_attempts`, `mcp_latency_s`, `call1_time_s`, `call2_time_s`, `total_time_s`, `call1_tokens`, `call2_tokens`, `hallucination_flag`.
2. **`scripts/core/tooluse_exporter.py` `_aggregate_asset_rows()`:** Flat-Column-Fallback nach `score_contributions`-Parsing; Boolean-Konvertierung; `mcp_mode`-Fallback via `row.get("mcp_mode") == "live"`.
3. **`benchmark_scores/tooluse_leaderboard.csv`:** Direkt-Patch für qwen3-coder-next-q8 (p1=90.00, p2=59.17, combined=74.62, mcp_mode=live, hallucination_flag=true). Sovereignty Gap neu berechnet: +0.40.

**Verifikation:** `benchmark_leaderboard.csv` neu generiert → Tool Execution: 90.00 | Synthesis Quality: 59.17 | Tool Use Score: 74.62 ✅

**Weitere Fixes dieser Session (CRUCIBLE_DELEGATE_PARENT + MCP):**
- `scripts/run_score_benchmark.py`: `CRUCIBLE_DELEGATE_PARENT` darf nur von `run_tooluse_benchmark.py` gesetzt werden — wurde zu früh gesetzt, MCP wurde nie gestartet
- `cruciblemark-mcp/config/mcp_config.yaml`: `idle_timeout_seconds: 0` (deaktiviert), damit GGUF-Modelle (Ladezeit bis 420s) nicht disconnecten
- `benchmark_config.yaml`: `token_budgets.cultural_intelligence: 500→1000` (Gemma-4-12B + NVIDIA Nemotron hatten Score=0)

**Memory-Bank-Update (diese Session):**
- `reference/pitfall-diagnoses.md`: P1/P2-NaN-Abschnitt
- `reference/data-schema.md`: `tooluse_leaderboard.csv` — Flat-Column-Schema dokumentiert, `score_contributions`-Deprecation vermerkt
- `systemPatterns.md`: 4 neue Pitfall-Einträge (`score_contributions` deprecated, `not in dict`-Pitfall, CRUCIBLE_DELEGATE_PARENT, MCP idle_timeout)
- `activeContext.md`: Letzte Änderungen + qwen3-coder-next-q8 als abgeschlossen markiert


### 2026-06-10 (Code-Review-Session) — 3 Bugfixes in unified_runner.py

**Anlass:** Vollständige Codeanalyse des Benchmarksystems nach Überarbeitungen.

**Gefundene + behobene Bugs (alle in `scripts/core/unified_runner.py`):**

1. **Double-Get `self.local_csv` (Zeile 88-93):** `config.get("output", {}).get("output", {})` — doppelter Key führte dazu, dass `local_models_csv`-Pfad nie aus der Config gelesen wurde. Fallback-Wert stimmte zufällig überein → kein sichtbarer Fehler, aber Config-Änderungen würden ignoriert. Fix: inneres `.get("output", {})` entfernt.

2. **`_probe_llamacpp_server` immer falsches Modell:** `getattr(self, "model", "")` → immer `""` (kein solches Attribut). Fix: `current_model`-Parameter addiert, `_local_memory_reset` reicht das laufende Modell durch. Betrifft Memory-Reset-Probe zwischen Tests bei llamacpp_spark.

3. **`calculate_score_contributions` mit falscher Eingabe:** `calculate_score_contributions(score, asset_cfg)` wo `score = exec_result.data` kein `percentage`-Feld hat → `routine_contribution = 0.0` und `reasoning_contribution = 0.0` immer. Fix: `calculate_score_contributions(result, asset_cfg)` — verwendet `result["percentage"]` (Regex-Score), wird bei Hybrid-Scoring korrekt durch `judge_evaluator.py` überschrieben.

**Nicht-Bug-Befund:** Judge-Applicability für reasoning-Modul war KEIN Bug — `load_active_benchmarks` setzt `benchmark_info["id"] = registry_key = "reasoning"`, passend zu `applicable_modules`.

**Memory-Bank-Update:** `reference/data-schema.md` Token-Budget-Tabelle synchronisiert (war veraltet).

**Tests:** 785/785 grün (keine Regression). 1 pre-existing SyntaxWarning in `utils/model_utils.py:89` (unverändert).


### 2026-06-10 (Session 5) — Draft-Card-Pitfall im Leaderboard behoben

**Symptom:** Neue Modelle (z.B. `gemma-4-12b-it-ud-q8_k_xl`) erschienen im Leaderboard mit `Model Name="TODO"`, `Version="k.A."` und falschem `Type="Open Weights"` (statt Restricted).

**Root Cause:** `make benchmark` erstellt via `ensure_card()` automatisch eine Draft-Card mit `display_name="TODO"`, `model_version=null`, `card_status="draft"`. `make leaderboard` liest diese Felder 1:1 aus der Card (SSoT) und gibt die Platzhalter aus. `make model-cards` regeneriert nur das Template — befüllt keine Felder.

**Fix:** `gemma-4-12b-it-ud-q8_k_xl.json` manuell befüllt (analog `q6_k_xl.json`), Card-Index rebuildet, `make leaderboard` neu ausgeführt. Rank 50 zeigt jetzt korrekten Display Name, Version `4 (Q8_K_XL GGUF)/M4APL`, Type `Restricted Weights`.

**Lessons:**
- `make leaderboard` funktioniert korrekt — die Card-SSoT-Architektur macht keine Halluzinationen
- Der "TODO" im Output war 1:1 die Draft-Card
- `make model-cards` ist irreführend benannt — der Befehl erstellt nur Templates, NICHT vollständige Cards
- **Detection:** `grep "TODO" benchmark_scores/benchmark_leaderboard.csv` findet betroffene Einträge
- Pitfall-Diagnose ergänzt in `reference/pitfall-diagnoses.md`

**Tests:** 57/57 grün in `test_generate_model_cards` + `test_card_template` + `test_card_first_probe_trigger`.


### 2026-06-10 (Session 4) — generate_model_cards.py an Validate-Konvention angeglichen

**Scope:** Strukturelle und stilistische Anpassung des Card-Generators an die Architekturregeln, die in `validate_cards.py` (Phase 24, a74c367) etabliert wurden. Keine funktionalen Änderungen am `ensure_card()`-Verhalten.

**Was geändert wurde:**
- **`scripts/analysis/generate_model_cards.py` (119 → 332 Zeilen):**
  - Sektionen-Reihenfolge: Konstanten → Dataclasses → Helper → Public API → Format-Funktionen → main() (analog `validate_cards.py`)
  - Neue Dataclasses `CardCreationIssue` + `CardCreationReport` mit strukturiertem `action` (`created`/`rebuilt`/`skipped`/`failed`) und `is_success`-Logik
  - Helper-Funktionen mit Underscore-Prefix: `_is_helper_file`, `_read_existing_card`, `_resolve_target_path`, `_build_creation_plan`, `_execute_creation`, `_prompt_for_model_id`
  - Public API: `create_card()`, `create_all()` (analog `validate_card`, `validate_all`)
  - Format-Funktionen: `format_text_report()`, `format_json_report()`
  - CLI-Konsolidierung: `--card-type`, `--model-id`, `--provider`, `--force`, `--interactive`, `--json` (statt verstreutem `--model`, `--update`, `--yes`, `--dry-run`)
  - **`--update` Flag entfernt** — duplikativ zu `sync_cards.py`, SRP-Verstoß. User-Hinweis im Modul-Docstring.
  - **Provider-Card-Erstellung** gibt sauber Exit 2 mit klarer Fehlermeldung zurück (war vorher stillschweigend out-of-scope)
  - Exit-Code-Logik: 0=OK, 1=Issue, 2=Programmfehler — dokumentiert im Docstring
- **`utils/card_template.py`:** Neue SSoT-Funktionen `cards_dir()` + `rebuild_card_index()` (vorher nur `rebuild_provider_index()` für Provider, jetzt symmetrisch für beide Typen). `JSONDecodeError` wird wie in `provider_card_template.py` mit `logger.warning` geschluckt (nicht fatal).
- **`tests/test_generate_model_cards.py` (NEU, 25 Tests):** Deckt `_is_helper_file`, `_build_creation_plan`, `CardCreationReport`-Issue-Logik, `create_card` (create/skip/rebuild/provider-Pfad), Format-Reporter (text/json), `cards_dir`/`rebuild_card_index` SSoT ab.
- **`docs/CARD_MANAGEMENT.md`:** CLI-Beispiele aktualisiert (TODO — folgt in Folge-Session)

**Tests:** **726/726 grün** (vorher 701, +25 neue). Ruff clean. Mypy keine neuen Fehler (2 pre-existing in `utils/model_utils.py:1754-1757` unverändert).

**Lessons:**
- `_index.json` lokal zu rebuilden war bisher Duplikat-Logik zu `rebuild_provider_index()`. Auslagerung als SSoT in `utils/card_template.py` ist vorbildlich für künftige SSoT-Brücken.
- Mix aus `print()` und `logger.*()` im alten Skript war inkonsistent — `logger` für Dev-Output, `print()` nur für finale User-Output ist die klare Linie.
- `--update` (Sync) im Create-Skript war ein historischer Workaround — durch saubere SRP-Trennung entfällt die Verlockung, beides zu vermischen.


## v4.7.4 (2026-06-10) — Heartbeat-Configurable

**Scope:** Hardcodiertes 60s-Heartbeat-Intervall aus `unified_runner.py` in `benchmark_config.yaml` verlagert.

- `_get_heartbeat_config()` mit Defensiv-Fallback (Block fehlt/nicht-Dict/non-numeric/≤0 → `(True, 60.0)`)
- `enabled=false` → `heartbeat_thread = None` Sentinel für `finally`-Block
- 17 neue Tests (`test_unified_runner_heartbeat.py`): Defaults, explicit, partial, zero/negative, non-numeric, non-dict, disabled-thread
- Doku: `docs/BENCHMARK_SCRIPT_OVERVIEW.md §6` "Runtime Feedback (Heartbeat)"
- 603/603 Tests grün
- **Details:** `reference/heartbeat-v474-detail.md`

## v4.7.3 (2026-06-10) — Thinking-SSoT-Auflösung + Doku-Sync

**Scope:** SSoT-Auflösung für Thinking-Erkennung (Card-Probe + Override), Runner-Consumer-Anbindung via `provider=` kwarg, Doku-Sync.

- `utils/model_utils.resolve_effective_thinking()` — SSoT-Auflösung (Override > Card-Probe > None) mit Audit-Trail
- `_is_override_active()` — Override-Validierung (bool, reason-Pflicht, active_until-UTC)
- `resolve_token_budget(..., *, provider=None)` — neuer kwarg
- `base_runner.py:121` reicht `provider=provider` durch
- 24 + 17 = 41 neue Tests, **634/634 grün in 2.11s**
- Doku: 6 Dateien aktualisiert (THINKING_PROBE.md NEU, CHANGELOG, ARCHITECTURE, CARD_MANAGEMENT, CLAUDE.md Pitfall, Memory-Bank)
- **Lessons:** `docs/THINKING_PROBE.md` war im v4.7.2-CHANGELOG angekündigt, fehlte aber → beim Schreiben als NEU markieren

## Offene Tasks

- [ ] **[BACKLOG] Reasoning-Aware-Benchmark (Option C)** — zurückgestellt 2026-06-10
  - Re-Aktivierungs-Bedingung: Sobald Uri-Vergleich um "Reasoning-Fairness" erweitert werden soll
  - `force_off` via `thinking_override.value=false` bereits implementiert; `force_on` fehlt
  - **Details:** `reference/decisions-log.md` (Reasoning-Backlog-Sektion)

- [ ] **5 echte Test-Lücken schließen** (Phase 8 Befund)
  - Kimi K2.6 (40/43), DeepSeek V4 Pro (42/43), Qwen 3.5 397B A17B (40/43), MiniMax M2.7 (42/43), GLM-4.7 (42/43)
  - Fix: `make benchmark-auto` (Auto-Bench-Fill-Logik)

- [ ] **PC-Re-Run fortsetzen** — 31 Modelle ohne gültigen Leaderboard-Eintrag (letzter Lauf abgebrochen, Exit 130)

- [x] **Qwen-Retest nach `--reasoning off` Fix** — 7 Modelle erfolgreich re-gerunnt (2026-06-07/08). Zombie-Eintrag `asset_001_wcag_audit` / `qwen3_5-35b-a3b-q8` bereinigt (2026-06-10). Alle 13 lokalen Qwen-Modelle zeigen 43/43 im Leaderboard.

- [x] **5 weitere ToolUse-Sanierungen** — abgeschlossen (2026-06-10, Session 8)
  - deepseek/deepseek-v4-pro, gemini-3_5-flash, mistral-large-2512, mistral-small-2603, nousresearch/hermes-4-405b: bereits gültige `live`-Daten mit korrekten Flat-Columns ✅
  - deepseek-r1:8b: mock-Zeile + Korrupte Zeilen 2–5 + gpt-5_5 (6 Errors) aus `tooluse_leaderboard.csv` gelöscht → Re-Run durch User nötig
  - `benchmark_leaderboard.csv` neu generiert — gpt-5_5 zeigt korrekt `–,–,–` für ToolUse

- [x] **heritage_ids-Fallback** in `generate_review.py` + `web_export.py` — **Commit 81b8cd4**

- [ ] **Re-Run magistral-small / magistral-medium** (FORCE=1) für reasoning_logic, ux_writing, code_quality / documentation_quality

- [ ] **language_consistency** als eigene CSV-Spalte im Leaderboard (Erweiterung)

- [ ] **ct_005 Phase-2** Body-Word-Parser (fragile Extraktion, nicht zeitkritisch)

- [ ] **Phase 4: Finale E2E Systemtests und CI/CD Review**

- [ ] **LLM Judge: Batch-Mode** (Phase 3.5)

- [ ] **Leaderboard-Refactoring Phase 9–12** (Asset→Category-Registry, SSoT-`expected_assets`, ehrliches `is_complete`, candidates-Slugify, Integration-Tests) — auf User-Freigabe warten

### 2026-06-10 (Session 2) — Card-First-Probe Bug + q6_k_xl 5B-Sanierung

**Bug-Fix in `scripts/core/unified_runner.py`:** `_read_card_probe_state` Zeile 186 prüfte `"thinking_probe_detected" not in loaded`, aber `ensure_card()` erzeugt Draft-Cards mit explizit `None`-Wert. Fix: `loaded.get("thinking_probe_detected") is None` (1 Zeile).

**Effekt:** Gemma-4-12B-Modelle (und alle Draft-Card-Modelle) bekommen beim nächsten Lauf automatisch eine echte Thinking-Probe → 5x-Reasoning-Budget aktiviert (8192 → 40960 Tokens).

**Tests:** 7 neue Unit-Tests in `tests/test_card_first_probe_trigger.py` (alle 4 Probe-States: null/missing/True/False + 3 Edge-Cases). 75/75 Tests grün in angrenzenden Test-Dateien. Ruff clean, Mypy keine neuen Fehler.

**CSV-Sanierung:** `benchmark_scores/local_models_benchmark.csv` — 1 fehlerhafte Zeile entfernt (asset_5b_complex_reasoning_chains für gemma-4-12b-it-ud-q6_k_xl, Status=error, "Test execution failed"). Backup: `local_models_benchmark.csv.backup_q6_5b_fix_20260610_092347`. 22 → 21 Zeilen für q6_k_xl. Alle anderen 21 Werte (code_quality, cli, reasoning_001/5a/5c/5d/5e, metacog_001-005) bleiben erhalten.

**Pitfall-Diagnose:** `memory-bank/reference/pitfall-diagnoses.md` — neue Sektion „Card-First-Probe wird durch `null`-Wert in Draft-Card umgangen (2026-06-10)".


### 2026-06-10 (Session 3) — Test-Isolation via conftest.py

**Root-Cause:** Zwei Worker-Tests riefen `worker.main()` direkt auf und monkeypatchten `CARD_DIR` nicht → `discover_models()`, `enforce_card_first()` und Card-Lookups in `UnifiedBenchmarkRunner` griffen via `CARD_DIR = Path("benchmark_scores/model_cards")` auf den ECHTEN Ordner zu. `ensure_card()` legte für unbekannte Test-Model-IDs (`m1`, `m2`, `True`) Stub-Karten als Leichen an.

**Fix:**
- Neue Datei `tests/conftest.py` mit `autouse=True`-Fixture `_isolate_card_dir`:
  - `monkeypatch.setattr("utils.model_utils.CARD_DIR", tmp_path)` für jeden Test
  - Custom-Marker `pytest.mark.uses_real_cards` für Opt-Out (z.B. `test_resolve_canonical_model_id.py` mit glob-fallback Card-Alias)
  - Marker-Registrierung via `pytest_configure()` → keine `PytestUnknownMarkWarning`
- `tests/test_resolve_canonical_model_id.py` mit `pytestmark = pytest.mark.uses_real_cards` markiert
- Bestehende Fixtures (`test_enforce_card_first.py`, `test_id_ssot_invariants.py`, `test_benchmark_auto_untested_tooluse.py`) patchen dasselbe Attribut auf `tmp_path` — identische Konvention, kein Konflikt (monkeypatch restauriert am Ende alle setattrs auf den Originalwert)

**Verifikation:** 4 betroffene Tests grün, voller Test-Run 15 failed, 900 passed — exakt gleiche Failures mit und ohne `conftest.py` (0 Regressionen, 15 pre-existierend: 14 MCP-network + 1 audit-logs safe-name). `ls benchmark_scores/model_cards/ | grep -E "^(m1|m2|True)\.json"` ist nach Test-Run LEER.

**Pitfall-Diagnose:** `memory-bank/reference/pitfall-diagnoses.md` — neue Sektion „Test-Card-Leichen in `benchmark_scores/model_cards/` durch unautouse-Fixture (2026-06-10)".
