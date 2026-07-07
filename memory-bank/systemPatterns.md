# System Patterns

Architektur-Regeln + aktuelle SSoT-Brücken (One-Liner). Details: `reference/data-schema.md`, `reference/pitfall-diagnoses.md`.

---

## 🛑 4 Architektur-Regeln

1. **Separation of Concerns:** Measurement = autonom/ausfallsicher. Publishing = strikt offline.
2. **SSOT/DRY/SRP:** Eine Funktionalität = ein Modul. Fail-Fast ohne versteckte Fallbacks (`ValueError` bei falscher Config). Import statt Duplikation.
3. **Config-Driven, No Magic Numbers:** Alle Regeln/Zahlen/Limits in YAML. CC ≤ 12 (`ruff.toml` C901).
4. **Anti-God-Script:** Logische Submodule auslagern, Haupt-Skript bleibt schlank.

---

## 🛑 Design-Bedingungen: Benchmark-Ausführung (nicht optimierbar)

Diese Eigenschaften sind **bewusste Design-Entscheidungen** für faire, reproduzierbare Messungen. Sie dürfen NICHT zugunsten von Performance optimiert werden.

1. **Sequenzielle Modell-Abarbeitung:** Modelle werden einzeln nacheinander getestet. Zwischen Modellen wird der Server gestoppt und neu gestartet. `AdaptivePauseCalculator` sorgt für Cooldown zwischen Tasks. **Ziel:** Gleichwertige Testumgebung für jedes Modell — kein "warmes" Modell hat Vorteile durch gecachten KV-Cache.
2. **Judge-Reset zwischen Tasks:** Der LLM-Judge wird NICHT gecacht. Jede Bewertung ist ein frischer API-Call ohne vorherigen Kontext. **Ziel:** Kein Kontextmix durch gecachten Kontext aus vorherigen Bewertungen — jede Bewertung ist unabhängig.
3. **Keine Cross-Run-Pollution:** Jeder Benchmark-Run ist unabhängig (Stateless Runs). Ergebnisse aus vorherigen Runs beeinflussen den aktuellen Run nicht.

---

## SSoT-Brücken (One-Liner + Datei)

| Brücke | SSoT-Speicherort | Hot-Aufruf |
|---|---|---|
| **Token-Budget** | `benchmark_config.yaml → token_budgets` + `token_budgets_reasoning_models` | `resolve_token_budget()` → `min(budget, provider_num_predict)` |
| **Token-Kaskade (Provider)** | `provider_config.yaml → <provider>.max_tokens` + `<provider>.model_max_tokens` | `_resolve_request_tokens()` in `base.py` → Kaskade: `min(resolve_budget, model_override ?? provider_default)` |
| **Thinking** | Card `thinking_probe_detected` + optional `thinking_override` (Provider-Card) | `resolve_effective_thinking()` Priorität: Override > Probe > None |
| **Provider-Config SSOT-Chain** | Provider-Config → Card Name → Card `model_id` → Downstream SSOT | Provider-Config definiert die ID, Card wird daraus abgeleitet, Card `model_id` wird SSOT für alles Weitere. Card-Name/CARDFELD `model_id` NICHT ändern — ist an `provider_config.yaml` gebunden. |
| **Model-Identität** | Card `model_id` ist einziger Identifier | `resolve_canonical_model_id()` (5-Level-Lookup) |
| **Model-ID als Kommunikations-Anker** | Card `model_id` / `raw_model_id` | Alle CSV-/Leaderboard-Lookups via `model_id`. `raw_model_id` lesen, dann `slugify()` für Format-Matching. NIEMALS Display-Name für Lookups verwenden. |
| **Card-ID-Pipeline (SUFFIX SSoT, Session 49)** | `build_card_id()` in `utils/model_utils.py` | Schreibpfad-SSoT: `{base}--{shortcode}.json` (z.B. `ornith-1-0-35b--SPRK.json`). `_card_path(for_write=True)` + `ensure_card(provider=X)` rufen `build_card_id()` auf. `_find_card()` Read-Reihenfolge: SUFFIX → legacy PREFIX → unprefixed. Direkte `_card_path()`-Caller MÜSSEN `provider=X` übergeben. |
| **Card-First CSV-Senke** | `result_manager.save_results()` | `enforce_card_first()` (Draft wenn fehlt, KEIN Hard-Fail) |
| **Hardware-Profile (Review-Kontext)** | `provider_config.yaml → <provider>.hardware_profile` → `benchmark_config.yaml → runner_environment.profiles` | `_get_hardware_profile_for_model()` in `generate_review.py`; `get_editor_prompt_injection(hardware_profile_key=...)` |
| **Modell-Kategorie** | Card `weights_license_tier` | `get_model_category()` (3 Tiers: `proprietary`/`restricted-weights`/`open-weights`) |
| **Provider-Shortcodes** | `_PROVIDER_SHORTCODES` + `short_code` in Config | `API`/`OR`/`GR`/`LCL` — alle lokalen Provider (ollama, llamacpp, llamacpp_spark) → `LCL` |
| **Deployment-Category** | `_PROVIDER_DEPLOYMENT_CATEGORY` in `model_utils.py` + `deployment_category` in `provider_config.yaml` | `get_deployment_category(provider)` → `"api"` / `"cloud"` / `"local"` |
| **Hardware-Profile (Deployment-Badge)** | `_PROVIDER_HARDWARE_PROFILES` in `model_utils.py` + `hardware_profiles` in `provider_config.yaml` | `get_hardware_profile(provider)` → `"m4_macbook_pro_metal"` / `"dgx_spark_cuda"` / `"rtx4070_cuda"` / `None` |
| **Sampling-Defaults** | `providers.local.config.llama_cpp_defaults` | 7 Parameter, Pro-Modell-Override schlägt Default |
| **1-Klasse-pro-Hardware** | `LlamaCppBaseClient` + Subklassen | Auto-Registry via `__init_subclass__` mit `PROVIDER_NAMES` |
| **Tri-State Tool-Use** | Card `supports_tool_use`: `true`/`false`/`"untested"` | `normalize_supports_tool_use()` Helper |
| **Card-Research MCP Tool-Use** | `manage_model_cards.py` → MCP Server `:8765` (JSON-RPC 2.0 HTTP POST) | `--tooluse` + `--mcp-url`; `_call_mcp_tool()` POST `tools/call`; `_parse_tool_call()` extrahiert `{"tool_call": {...}}`; `_extract_tool_content()` liest Transcript |
| **CSV-Daten-Pipeline (v4.10.4)** | `result_manager.save_results()` = Upsert → `data_loader.py` dedup → `consolidate_csv.py` physische Reduktion | Atomare Writes via `tempfile.mkstemp()` + `os.replace()`. Existing Rows werden NICHT re-validiert. `make backup` → tar → consolidate → bereinigte CSV. Alle drei Schichten idempotent. |
| **Provider-Thinking-Extraktion (v4.10.5)** | `utils/providers/base.py`: `_extract_reasoning_tokens()`, `_extract_think_from_message()`, `ThinkAccumulator` | 9 Provider nutzen Shared Utilities statt Inline-Code. Streaming + Non-Streaming. Provider-spezifische Felder (Google `thoughts_token_count`, Ollama `eval_count`) bleiben inline. |
| **Judge Token Usage Context (v4.10.5)** | `judge_evaluator.py` baut `token_usage_context` → `judge_runner.py` → `judge_prompt_builder.py` | Universell für alle Modelle: `tokens_used`, `reasoning_tokens`, `token_budget`, `module_budget`, `truncated`. Neue `### TOKEN USAGE ###` Section im Judge-System-Prompt. |
| **Cohere Native ToolUse (v4.10.8)** | `utils/providers/cohere.py`: `_extract_tool_schema()` + `_schema_to_cohere_tools()` + `_format_tool_calls_as_text()` | ToolUse-Modul nutzt Cohere-native `tools`-API; andere Module bleiben prompt-basiert. Reasoning-Modelle: `thinking: disabled` bei Native Tools. 500-Retry (2× Backoff). |
| **ToolUse Tri-State Export (v4.10.12, revidiert v4.10.13)** | Card `supports_tool_use`: `true`/`false`/`null` → `web_export.py:_build_leaderboard_entry()` | **Scores datenbasiert (v4.10.13):** `synthesis_quality`/`tool_execution` werden exportiert sobald ein Leaderboard-Wert existiert — unabhängig vom `supports_tool_use`-Flag. Verhindert "8 Scores ohne synthesis_quality"-Befunde für 7 getestete Modelle mit stu=false. **Detail-Block bleibt gated:** der `tooluse`-Block in `data.json` (Per-Asset-Details) bleibt an `supports_tool_use=true` gebunden (Frontend-Nav, Session-44-Design). Frontend: `supports_tool_use_state` ("true"/"false"/null) bleibt separates Capability-Indikator; `scoreboard-table.js:toolsBadge()` überschreibt bei stu=false auf "n/a". |
| **Web-Export Provider-Entfernung (v4.10.12)** | `provider_leaderboard.csv` wird NICHT mehr von `_load_sources()` geladen | Provider/Speed-Messungs-Konzept dauerhaft aufgegeben. `provider_stats.json` + `provider_landscape_review.md` + `provider_cards.json` nicht mehr geschrieben. `vendor_cards.json` + `community_cards.json` bleiben (echte Herstellerkarten). `provider_leaderboard.csv` bleibt als Datenquelle fuer Vendor-Card-Stats via `generate_vendor_cards.py`. |
| **Web Linkify-Abschaffung (v4.10.12)** | `cruciblemark-web/.eleventy.js`: `inlineContent`-Filter mit `linkify: false` | Auto-Linkify von Plain-Text-Domains deaktiviert — nur explizite Markdown-Links `[Text](URL)` werden gerendert. Externe Links erhalten automatisch `target="_blank"`, `rel="noopener noreferrer"`, `aria-label` (WCAG 2.4.4). CSS `a[target="_blank"]::after` rendert `bi-box-arrow-up-right` als visuellen Indikator. Interne Links bleiben unverändert. |
| **Web-Export Typ-Konsistenz (v4.10.12)** | `scripts/web_export.py`: `parse_compact_number()`, `parse_percent()`, `parse_int()` | Zahlen als Zahlen im JSON-Export (Vertrags-Pflicht). `parse_compact_number()` löst "83.7K"→83700, "1.2M"→1200000 auf. `parse_percent()` löst "100%"→100.0 auf. `parse_int()` liefert int nie float. Angewendet auf `tokens_total`, `tokens_per_module.*`, `llm_judge_coverage`, `timeout_count`. Formatierung gehört in Darstellungsschicht, nicht JSON. Siehe `cruciblemark-web/memory-bank/reference/data-schema.md` (Export-Vertrag). |
| **Review-Prosa-Vertrag (v4.10.12)** | `config/meta_reviewer_prompt.yaml` + `scripts/analysis/generate_review.py: _strip_metric_lines()` | Narrative Reviews enthalten KEINE exakten numerischen Metrik-Werte (Tokens/s, P95, Timeout-Rate) im Fließtext. Speed wird qualitativ anhand Speed-Profile-Badge beschrieben. Exakte Zahlen ausschließlich als strukturierte Datenfelder. Zweischichtiger Fix: (1) Prompt-Anweisung entfernt Zahl-Zitat, (2) `_strip_metric_lines()` entfernt Per-Task-Metriken aus Audit-Log-Kontext bevor LLM-Prompt. `model_tokens_per_s` aus template_vars entfernt. Bestehende Reviews bei nächster Regenerierung (`make reviews-auto --force`) aktualisieren. |
| **audit_log_count Semantik (v4.10.12)** | `scripts/web_export.py: _write_top_level_outputs()` | `meta.audit_log_count` zählt NUR `.md`-Audit-Logs in Verzeichnissen von Modellen, die im aktuellen Export enthalten sind. Früher wurden alle Verzeichnisse gezählt (inkl. tote/blacklisted Modelle) → Delta zum Web-Export. Jetzt konsistent mit `leaderboard.json.total_models`. `exported_slugs` via `_safe_name()` gematcht. |
| **vllm_spark Provider (2026-07-07)** | `utils/providers/vllm_base.py` + `vllm_spark.py` + `config/provider_config.yaml` | SSH-Steuerung des vLLM-Servers auf asusGX10 via `vllm-start`/`vllm-stop`. OpenAI-kompatibles Backend auf **Port 3300** (direkt, kein Proxy). Models laden bis 600s. `_server_model_name` getrennt von normalized Card-ID (Server kennt nur Original-Namen mit Punkten, Benchmark normalisiert zu Underscores). `_probe_status()` 3-State: `healthy`/`loading`/`down`. Code-Pattern-Sharing mit `llamacpp_base.py` (Subklasse + PROVIDER_NAMES-Auto-Registry). |

**Code-Beispiele und Felder:** `reference/data-schema.md`. Pitfalls: `reference/pitfall-diagnoses.md`.

---

## Thinking-Override-Schema

```yaml
thinking_override:
  value: false                 # bool (Pflicht)
  reason: "Cost-Benchmark: CoT-Suppression"   # str (Pflicht)
  active_until: "2026-12-31"   # ISO-8601 (optional)
```

Aktivierung: `value` bool, `reason` nicht whitespace-only, `active_until` in der Zukunft.

---

## Konventionen

- **Naming:** BEM (CSS) / snake_case (Python) / kebab-case (YAML-Keys)
- **Commits:** Conventional Commits (feat/fix/chore/docs)
- **Doku:** Deutsch für Kommentare/Docs, Englisch für Code
- **Linter:** Pylance + Pylint + Ruff, ≥ 9.5/10 für Core-Module
- **Tests:** pytest `-v --tb=short`, Fixtures in `conftest.py`
- **Type-Hints:** immer, mypy-kompatibel
- **Errors:** Niemals bare `except:`, `logging.exception()`, Custom Exceptions

---

## Pitfalls (Goldene Regeln, Kurz-Liste)

- **Race-Condition:** NIEMALS während laufendem Benchmark Core-Module modifizieren
- **Python 3.14 `sys.path`:** `ROOT_DIR = Path(__file__).resolve().parent.parent.parent` vor Package-Imports
- **Provider-Inferenz:** `model_id` muss Slash-Form (z.B. `nvidia/nemotron-3-ultra`) für exakten Config-Lookup haben
- **Mypy `pandas.isna()`:** None-Check vor `str(val).strip()` — sonst `"nan"`-Strings
- **`assertIsNotNone()` reicht Pylance nicht:** expliziter Cast-Kommentar
- **Pylint W0611:** Jeder neu hinzugefügte Import muss sofort verwendet werden
- **`score_contributions` deprecated:** Seit Writer-Redesign (d82996f) leer in neuen CSV-Rows → NICHT als einzige Datenquelle für ToolUse-Metriken verwenden. Neue Pattern: Flat-Columns (`p1_score` etc.) direkt in Zeile.
- **`not in dict` ≠ Wert fehlt:** `ensure_card()` setzt alle Felder auf `None` → `key not in d` ist `False` trotz fehlendem Wert. Immer `d.get(key) is None` prüfen.
- **CRUCIBLE_DELEGATE_PARENT:** Darf nur von `run_tooluse_benchmark.py` gesetzt werden — nie von `run_score_benchmark.py`. Sonst wird MCP nie gestartet und alle ToolUse-Tests schlagen fehl.
- **MCP `idle_timeout_seconds: 0`** deaktiviert den Timeout — nötig für GGUF-Modelle (Ladezeit bis 420s).
- **Display-Name ≠ Model-ID für Lookups:** PC-Leaderboard, Tooluse-Leaderboard, Blacklist — immer `raw_model_id` aus der Card verwenden. `slugify(raw_model_id)` für Format-Anpassungen. Display-Namen sind UI-only.
- **Tooluse-Leaderboard-IDs sind Ollama-Format** (`gemma3:12b`, `qwen3:14b`) — nicht CrucibleMark-IDs. Im per-model-Review-Loop können sie nicht auf Audit-Log-Slugs gemappt werden → Tooluse-Schritt muss nach dem Loop mit `model=None` separat laufen.
- **Hardware-Profil-Lookup:** `provider_config.yaml → <provider>.hardware_profile` ist der SSoT-Key. Nie aus `active_profile` oder Environment ableiten — das ist das Test-System, nicht das Hardware-Profil des getesteten Modells.
- **PC-Ghost-Model durch Datum-Normalisierung (2026-06-13):** `base_runner.py` normalisiert Modell-IDs via `re.sub(r'-\d{8}$', '', model_id)` für den Leaderboard-Skip-Check. Wenn ein alter undatierter PC-Leaderboard-Eintrag (`z-ai/glm-5`) existiert, trifft `z-ai/glm-5-20260211` darauf → false-positive Skip, kein neuer PC-Run. Fix: `--force`-Flag beim PC-Benchmark-Re-Run. Danach alten `k.A.`-Entry aus `political_compass_results.csv` manuell löschen.
- **Vendor-Card-Generator erzeugt Duplikate (2026-06-13):** `generate_vendor_cards.py` prüft nicht auf bestehende Karten mit ähnlichem Namen. Auto-generierte Karten (`alibaba_cloud.json`, `alibaba_group_qwen_team.json`) kollidierten mit dem kanonischen `alibaba.json` — alle 3 mit identischer `api_base_url`. Symptom: mehrfache Vendor-Einträge im Web-Export. Fix: Orphan-Dateien löschen + `card_subtype: "community"` für Community-Cards setzen + Community-Filter in `web_export.py`.
- **Card-Research Tool-Use: max. 3 Runden (2026-06-19):** `Researcher._research_tooluse_one()` hat einen Hard-Cap von 3 Tool-Call-Runden. Verhindert Endlosschleifen bei kaputtem Modell (das nie mit `{"findings": ...}` antwortet). Wenn 3 Runden ohne finale Answer erreicht → Fehler, Lock bleibt offen, nächster Lauf nimmt Card im Resumption-Pfad.
- **Card-Template optional vs required (2026-06-20):** Felder mit Beschreibung "null wenn X" müssen `required: false` sein — `is_unknown_sentinel(None)` returned `True`, also wird `null` bei `required: true` als Fehler gewertet. Betroffene Felder: `params_total_b`, `params_active_b`, `knowledge_cutoff`, `license_url`, `input_price_per_1m`, `output_price_per_1m`.
- **Card-Research Batch-Processing (2026-06-20):** `MAX_CARDS=N` limitiert pro Run. Ohne `FORCE` werden nur unverifizierte Cards verarbeitet — Batch-Processing funktioniert (10 pro Run, nächster Run nächste 10). Mit `FORCE=1` werden immer die ersten N alphabetischen Cards verarbeitet (kein Skip). `MODEL=all` ist Spezialwert für "alle Cards".
- **Web-Export None-Stripping (2026-06-20):** `_strip_none()` in `web_export.py` entfernt `None`-Werte rekursiv vor JSON-Export. Verhindert `"field": null` im Web-Payload. Felder mit Wert (`0`, `False`, `""`, `[]`) bleiben erhalten. `model_card: null` wird komplett entfernt (Key fehlt statt null).
- **CSV-Write-Through atomar (v4.10.4, 2026-06-21):** `_write_to_csv()` nutzt `tempfile.mkstemp()` + `os.replace()` — Originaldatei bleibt intakt bei Kill/Crash. NIEMALS `"w"` (truncate) verwenden. Bestehende Zeilen beim Full-Rewrite NICHT re-validieren — nur neue Zeilen durch Hard-Fail-Guard. 10 Modelle mit 0 CSV-Einträgen waren Root Cause für diesen Fix.
- **Provider-Thinking-Extraktion SSoT (v4.10.5, 2026-06-21):** `_extract_reasoning_tokens()`, `_extract_think_from_message()`, `ThinkAccumulator` in `base.py`. NIEMALS eigene Inline-Extraction schreiben — immer die Base-Utilities verwenden. Provider-spezifische Felder (Google `thoughts_token_count`, Ollama `eval_count`) bleiben inline.
- **`clean-results` Variant-Handling (v4.10.7, 2026-06-22):** `_collect_model_id_variants()` sammelt ALLE Schreibweisen (Underscore, Hyphen, Punkt). **Reihenfolge kritisch:** CSVs VOR Cards — `resolve_canonical_model_id()` braucht die Card für die Variant-Auflösung. `clean_cost_log()` ist separat von `clean_csv()`. NIEMALS nur `_safe_name()` verwenden — Card-Inhalt-Scan + `_find_card` nötig für vollständige Abdeckung.
- **Cohere Native ToolUse (v4.10.8, 2026-06-23):** Prompt-basierte JSON-Tool-Schemas kollidieren mit Cohere's Reasoning-Logik (422/500). ToolUse-Modul nutzt Cohere-native `tools`-API; andere Module bleiben prompt-basiert. `command-a-plus-05-2026` hat persistente 500er bei Benchmark-Prompts — `supports_tool_use=false`. NIEMALS prompt-basierte Tool-Schemas für Cohere-Reasoning-Modelle verwenden.
- **Cohere `command-a-plus` MoE-Instabilität (v4.10.8, 2026-06-23):** Cohere's erstes MoE-Modell (218B/25B aktiv) zeigt persistente HTTP 500 mit komplexeren System-Prompts + nativen Tools. Einfache Prompts funktionieren. Serverseitiger Bug, nicht clientseitig behebbar. Status: `supports_tool_use=false` bis Cohere den Bug behebt.
- **ToolUse Tri-State Export (v4.10.12, revidiert v4.10.13, 2026-07-04):** ZWEI-STUFIGE Entscheidung: (1) **Scores datenbasiert** — `synthesis_quality` (ToolUse P1) und `tool_execution` (ToolUse P2) werden in `leaderboard.json.scores` exportiert sobald das Modell einen Wert im Leaderboard hat, unabhängig vom `supports_tool_use`-Flag. 7 Modelle mit stu=false haben aber echte ToolUse-Daten in `tooluse_leaderboard.csv` (command-a-plus, gpt-oss-20b, qwen3-4b/14b, qwen2_5-coder-7b, qwen3_5-4b-*/9b) — diese wurden vor v4.10.13 fälschlich ausgeblendet. (2) **Detail-Block bleibt gated** — der `tooluse`-Block in `data.json` (Per-Asset-Details, Radar, Reliability) bleibt an `supports_tool_use=true` gebunden, weil er Frontend-Navigationsauswirkungen hat (Session-44-Design: ToolCalling-Nav nur bei stu=true). Das `supports_tool_use_state`-Feld ("true"/"false"/null) bleibt separates Capability-Indikator und wird nicht aus den Scores abgeleitet. `_strip_none()` entfernt null-Werte, d.h. ungetestete Modelle (kein Leaderboard-Wert) bekommen keinen Score-Key.
- **Web Linkify-Abschaffung (v4.10.12, 2026-06-29):** Auto-Linkify von Plain-Text-Domains (`markdown-it` `linkify: true`) war ein Anti-Pattern fuer kuratierte Benchmark-Seite. Symptom: "Z.AI" im Sovereign-Risk-Warnungstext wurde zu `<a href="http://Z.AI">Z.AI</a>` — ungeprueftes Linkziel, schlechter Linktext (WCAG 2.4.4). Fix: `linkify: false` im `inlineContent`-Filter. Nur explizite Markdown-Links `[Text](URL)` werden gerendert, mit `target="_blank"` + `rel="noopener noreferrer"` + `aria-label` + CSS-Icon. **NIEMALS `linkify: true` wieder aktivieren** — Verlinkung ist stets eine bewusste, editoriale Entscheidung.
- **Review-Prosa-Drift (v4.10.12, 2026-06-29):** Der Review-Generator las pro-Task Metrik-Zeilen (`**Tokens/s:**`, `**Execution Time:**` etc.) aus Audit-Logs und speiste sie ungefiltert in den LLM-Prompt. Der LLM zitierte diese Per-Task-Werte — sie weichen vom Leaderboard-Aggregat ab (Faktor bis 2.8× bei gpt-5/gemini-2-5-pro). Fix ist zweischichtig: (1) Prompt-Anweisung entfernt — LLM soll Speed qualitativ beschreiben, keine exakten Zahlen zitieren. (2) `_strip_metric_lines()` in `generate_review.py` entfernt 4 Metrik-Zeilen-Typen aus dem Audit-Log-Kontext BEVOR der LLM sie sieht (19.912 Zeilen über 5.071 Logs). Die strukturierten Leaderboard-Felder (`tokens_per_s`, `p95_time_s` etc.) bleiben alleinige SSoT-Quelle. **NIEMALS Per-Task-Metriken unfiltered in den Review-Prompt geben** — sie sind nicht mit dem Leaderboard-Aggregat synchronisiert.
- **Web-Export Typ-Inkonsistenz (v4.10.12, 2026-06-29):** `normalize_pending()` lieferte bei "83.7K" einen String zurück, weil `float("83.7K")` fehlschlägt. `parse_compact_number()` löst K/M-Suffixe auf und liefert immer Zahlen. Gleiches für `parse_percent()` ("100%"→100.0) und `parse_int()` (nie float). **Vertrags-Pflicht:** Zahlen als Zahlen im JSON, Formatierung in der Darstellungsschicht. Wenn ein neues Feld mit kompakter Zahlen-Notation oder Prozent-String hinzukommt, IMMER die dedizierten Parser verwenden — nie `normalize_pending()` für numerische Felder.
- **audit_log_count Zaehl-Basis (v4.10.12, 2026-06-29):** `meta.audit_log_count` zählt NUR Audit-Logs für exportierte Modelle (via `exported_slugs` Match mit `_safe_name()`). Früher wurden alle Verzeichnisse in `outputs/audit_logs/` gezählt — inkl. tote/blacklisted Modelle, deren Audit-Logs veraltet sind. Das erzeugte ein Delta von bis zu 1245 zwischen `meta.audit_log_count` und der tatsächlichen Anzahl im Web-Export. **Bei neuen Sanity-Counts:** immer nur Daten für exportierte Modelle zählen — sonst entsteht Drift zwischen Meta und Web-Export.
- **Emoji-Variation-Selectors strippen (v4.10.13, 2026-07-04):** `_EMOJI_RE` in `web_export.py` erfasste zwar die Emoji-Basiszeichen (z.B. ⏱ U+23F1), aber NICHT die Variation Selectors U+FE0F (VS16, Emoji-Presentation) / U+FE0E (VS15, Text-Presentation) und die Zero Width Joiner U+200D. Nach `_strip_emojis("⏱\ufe0f Interactive")` blieb `"\ufe0f Interactive"` — ein unsichtbares Zeichen vor "Interactive" in `performance_tier`/`speed_profile`. Betraf ~20 Modelle, nicht nur sichtbare Symptome. Fix: VS16/VS15/ZWJ in die Zeichenklasse aufgenommen. **NIEMALS nur Basis-Emoji-Codepoints in eine Strip-Regex aufnehmen** — immer auch VS15/VS16/ZWJ, sonst bleiben unsichtbare Artefakte zurück.
- **Judge-Fallback verboten — Retry-only (2026-07-06):** Anthropic-Overloads (529/429/5xx) NIEMALS durch ein anderes LLM als Ersatz-Judge auffangen — Score-Drift zwischen Judge-Modellen verfälscht historische Vergleiche. Stattdessen Exponential-Backoff-Retry im `health_check()` (max 3 Versuche, 1s/2s Backoff). Permanent-Fehler (4xx) fail-fast ohne Retry. Tuning via `CRUCIBLE_JUDGE_HEALTH_MAX_ATTEMPTS` / `CRUCIBLE_JUDGE_HEALTH_BACKOFF`.
- **vllm Token-Capture-Proxy Auth (2026-07-07):** Reverse-Proxy vor vLLM (z.B. Token-Capture-Proxy auf Port 4300) authentifiziert JEDEN Request inkl. `/health` und `/v1/models` mit Bearer-Token. Wenn der Bearer-Token aus dem Config nicht matched → 401 → Connector stoppt irrtümlich den Server. **Lösung:** Direkt gegen vLLM-Backend auf **Port 3300** benchmarken (akzeptiert jeden Key, kein Auth-Layer). Port 4300 nur für Token-Capture-Analyse.
- **vLLM Probe muss 3-State sein (2026-07-07):** Binärer Health-Check (`/health` HTTP 200) reicht NICHT — während des Modell-Loads antwortet vLLM mit 200 + `{"status": "loading"}` und der Probe-Chat schlägt fehl. Connector muss `healthy`/`loading`/`down` unterscheiden: 502/503 = loading (warten), Connection refused = down (Container restart), 200 = healthy (adopt/start). Verhindert fatal restarts von bereits ladenden Containern.
- **vllm_spark Config-API-Key via Env-Var (2026-07-07):** `<provider>.api_key: "${VAR}"` in `provider_config.yaml` wird zur Laufzeit via `os.environ` aufgelöst. Verhindert API-Keys im Git-tracked Config-File (CLAUDE.md: „API Keys NIEMALS in Git"). Default-Fallback ist `sk-local`. Andere Provider können dieses Pattern übernehmen — einfach `${ENV_VAR_NAME}` als Config-Wert setzen.
- **Card-Pfad SUFFIX-SSoT Divergenz (Session 49, 2026-07-07):** `_card_path(for_write=True)` produzierte bis Session 49 PREFIX `{shortcode}_{base}.json`, während `build_card_id()` SUFFIX `{base}--{shortcode}.json` erzeugte. Diese Divergenz zwischen zwei SSoT-Funktionen erzeugte Duplikat-Karten (PREFIX-Version + unprefixed Auto-Generierung). **Fix:** `_card_path(for_write=True)` ruft jetzt `build_card_id()` auf → beide produzieren SUFFIX. `_find_card()` behält PREFIX als legacy Read-Fallback. **Pflicht:** Direkte `_card_path()`-Aufrufer (`generate_model_cards.py:132`, ehemals `generate_review.py:213`) MÜSSEN `provider=X` übergeben — sonst entsteht unprefixed Pfad und `enforce_card_first()` auto-generiert Duplikate. Besser: `ensure_card(model_id)` ohne expliziten Pfad aufrufen (delegiert an SSoT). 13 Karten per `git mv` von PREFIX/unprefixed → SUFFIX umbenannt, 2 Auto-Duplikate gelöscht. Regressionstests in `tests/test_card_path_suffix_ssot.py`.
- **`model_version`-Pollution — Felder-Separierung SSoT (Session 49, 2026-07-07):** Quant/Format-Tokens (`Q8_0 GGUF`, `FP8`, `NVFP4`) und interne Variant-Namen (MTP, Coder-MTP, Ortenzya Wordsmith, E4B, QAT, Abliterated) hatten sich in `model_version` angesammelt, weil das korrekte Feld `quantization_format` in allen Karten `null` war (nowhere to go). **Fix:** Neues Feld `model_variant` in `_CARD_TEMPLATE` (`utils/card_utils.py`) für interne Variant-Bezeichnung. SSoT-Trennung: `model_version`=reine Versionsnummer, `model_variant`=interne Variante, `quantization_format`=Quant/Format, `hardware_profile`=Hardware (CSV-Spalte, bleibt dort — NICHT in model_version). **Kritisch:** `model_version` ist Leaderboard-Groupby-Key (`score_calculator.py` ~10× `groupby(["model","model_version","type"])`). Card-First-Override in `get_model_version()` (Z.796-830) liest neue Runs aus Card — alte CSV-Zeilen behalten stale Wert → Split. Daher Migration atomar: Card-Felder + CSV `model_version`-Spalte ZUSAMMEN aktualisieren. Migration via `scripts/maintenance/migrate_model_versions_pollution.py` (explizite Mapping-Tabelle, idempotent, Backup). 33 Karten + 1498 CSV-Zeilen migriert. Audit via `scripts/maintenance/audit_model_versions.py` (vorher 31 flagged, nachher 0).

Whenever a task involves refactoring, unexpected behavior, or
architecture changes: automatically load reference/pitfall-diagnosis.md before proposing any solution.


## Context Loading Rules
Before starting any task, check the task type and load accordingly:
- Refactoring / debugging / architecture review
  → load reference/pitfall-diagnosis.md
- Template or frontend work
  → load reference/data-schema.md
- New feature from roadmap
  → load reference/feature-specs.md
- "Why did we..." questions
  → load reference/decisions-log.md
Default: load nothing from reference/ unless task matches above.
