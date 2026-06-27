# CrucibleMark — Agent Context

> **Single Source of Truth** für Cline, Hermes und Copilot.
> Dynamischer Projektstatus → `memory-bank/` (activeContext.md, progress.md)

---

## Project Overview

CrucibleMark ist ein LLM-Benchmark-Framework (Python 3.12).
Es führt strukturierte Tests gegen verschiedene AI-Modelle durch, bewertet sie
mit einem unabhängigen LLM-Judge (Blind-Evaluierung) und generiert Leaderboards.

- **Konfig-Hierarchie:** Global (`benchmark_config.yaml`) → Modul (`config.yaml`) → Runtime
- **Module** erben von `BaseTest`, `execute()` verarbeitet einzelne Aufgaben — keine modul-internen Batch-Schleifen
- **Memory Bank:** `memory-bank/` lesen vor jeder neuen Task (activeContext.md, progress.md, techContext.md, systemPatterns.md)

---

## Code Style

- **Python 3.12**, venv (nie global), Type hints in ALLEN neuen Funktionen (mypy-kompatibel)
- **Verbote:** Kein `print()` für Debugging → `logging.debug()`, kein bare `except:`, keine Provider-Namen hardcoden → aus `benchmark_config.yaml` lesen
- Bestehende Pytest-Fixtures wiederverwenden, keine Duplikate
- Keine neuen Dependencies ohne Rückfrage — `requirements.txt` ist bewusst schlank
- Modulnamen konsistent mit bestehender Verzeichnisstruktur

---

## Architecture Rules

- Keine Änderungen am BaseTest-Erbschema ohne explizite Bestätigung
- Judge-Phase und Test-Phase strikt trennen — kein gemeinsamer State
- **LLM-Blind-Evaluierung beibehalten:** Judge kennt Modellnamen während Bewertung NICHT
- Scoring-Logik nie stillschweigend verändern — das verfälscht historische Benchmarks
- Konfiguration ausschließlich über Config-Files, nie hardcodiert
- **Sequenzielle Modell-Abarbeitung (Design-Constraint):** Modelle werden einzeln nacheinander getestet, Server wird zwischen Modellen neu gestartet, Cooldown via `AdaptivePauseCalculator`. Das ist KEIN Performance-Bug — es garantiert gleichwertige Testumgebungen. NICHT parallelisieren.
- **Judge-Reset zwischen Tasks (Design-Constraint):** Jede Judge-Bewertung ist ein frischer API-Call ohne Kontext aus vorherigen Bewertungen. KEIN Judge-Caching einführen — verhindert Kontextmix.
- **Token-Budget SSoT:** `resolve_token_budget()` in `utils/model_utils.py` — nie inline duplizieren
- **Anthropic `max_tokens` Provider-Cap (v4.10.6):** Der Provider-Default in `provider_config.yaml` ist 32768 (seit v4.10.6, vorher 8192). `fallback_max_tokens` wurde entfernt (Dead Config). Per-Model Override für `claude-haiku-4-5-20251001: 8192` (Desktop-Klasse). Bei neuen Claude-Modellen prüfen, ob der Default ausreicht — Claude 4.x unterstützt bis 128K Output, aber 32768 deckt alle Reasoning-Budgets ab (max. 20000 bei code_quality).
- **CI@500-Artefakt (bereinigt v4.10.6):** Cultural Intelligence lief bis April/Mai 2026 mit `token_limit_used=500` (altes Budget). 130 Zeilen (26 Modelle) entfernt. Aktuelles Budget: 3000 (Standard) / 4000 (Reasoning). Achtung: Wenn `token_limit_used` in alten Audit-Logs 500 zeigt, sind diese Runs veraltet.
- **`token_param_name` per Provider:** aus `benchmark_config.yaml` lesen, nie hardcoden
- **Dead-Model-Handling (Workflow):** Wenn ein Modell bei einem Benchmark-Lauf `Model not found` / HTTP 400 (invalid-argument) zurückgibt: (1) Alle Modelle des Providers gegen die API prüfen (`/v1/models` o.ä.), (2) User fragen, ob die toten Modelle in `provider_config.yaml` auskommentiert werden sollen, (3) Einträge in `config/web_export_blacklist.yaml` ergänzen (Blacklist = Web-Export-Sperre), (4) Bestehende CSV-Einträge für 0.0-Scores aufräumen. NIEMALS eigenständig auskommentieren — immer den User bestätigen lassen.

---

## Build & Test

```bash
pytest -v --tb=short       # Tests
make validate              # Lint
make test                  # Full test suite
make benchmark             # Benchmark run
```

Referenzdocs: `docs/DEVELOPER_GUIDE.md`, `docs/ARCHITECTURE.md`, `docs/SETUP_GUIDE.md`

---

## AI & API Rules

### Security (absolut)
- API Keys **NIEMALS** in Code, Logs, Kommentaren oder Git — ausschließlich `.env`
- `.env` in `.gitignore` — vor jedem Commit prüfen
- Keine API-Calls in Tests gegen Live-Endpoints — Mocks verwenden

### Datenschutz
- Datenschutzsensible Tasks: europäische oder lokale Modelle bevorzugen
- OpenAI/Anthropic nur für nicht-sensible Daten
- Lokale Modelle via Ollama für alle internen/vertraulichen Inhalte

### Modell-Routing
| Aufgabe | Modell |
|---|---|
| Reasoning, Architektur, neue Features | Claude Sonnet 4.5+ |
| Datei-Lesevorgänge, einfache Änderungen < 30 Zeilen | Claude Haiku 3.5 |
| Code-Review ganzer Dateien | Claude Haiku 3.5 |
| Lokale Tasks / Datenschutz | Ministral 8B via Ollama |
| Benchmark-Judge | separates Modell vom zu testenden Modell |

### API-Effizienz
- Prompt Caching nutzen wo möglich (`cache_control` bei Anthropic)
- Fehlerbehandlung + Retry mit Backoff bei allen API-Calls standardmäßig
- Token-Zählung bei neuen Prompts schätzen und dokumentieren

---

## Context & Cost Management (Cline/Hermes)

- Kontextauslastung > 40%: Nutzer darauf hinweisen
- Kontextauslastung > 60%: aktuellen Schritt abschließen, `new_task` starten mit diesem Format:
```
KONTEXT-ÜBERGABE:
- Projekt: [Pfad und Beschreibung]
- Erledigte Schritte: [abgeschlossene Aktionen]
- Aktueller Datei-Status: [veränderte Dateien]
- Nächste Aktion: [konkreter nächster Schritt]
- Offene Probleme: [nur wenn relevant]
```
- NIEMALS neue komplexe Subtask beginnen wenn Kontext > 50%

---

## Communication Style

- Code > Prosa — Erklärungen kompakt halten
- Kein Wiederholen der Aufgabenstellung am Anfang
- Keine redundanten Bestätigungen ("Ich werde jetzt X tun..." → einfach X tun)
- Bearbeite genau den beschriebenen Auftrag — kein unrequested Refactoring
- Wenn Problem außerhalb Scope: kurz erwähnen, nicht eigenständig beheben
- Kein Gold-Plating: keine zusätzlichen Features ohne explizite Anfrage

---

## Critical Pitfalls (Known Issues)

- **CSV Write-Through (ab v4.10.2):** `_handle_single_asset()` in `unified_runner.py` schreibt jedes Ergebnis SOFORT per `save_results([result])` in die CSV. Vorher: Batch-Write erst am Ende des Runs — bei Crash/Kill/Timeout waren ALLE Ergebnisse des Runs verloren (Audit-Logs blieben, CSV aber leer). Der Caller (`benchmark_auto.py:498`, `run_score_benchmark.py:180`) behält den finalen `save_results(results)` als Safety-Netz (Upsert ist idempotent).
- **Namespace-Kollision:** Bei `importlib` mit gleichnamigen Plugin-Dateien `{parent.name}_{stem}` verwenden
- **Asset Schema:** Jede YAML-Aufgabe braucht zwingend `prompt`/`prompts`-Feld
- **Judge Parser:** Bei Parse-Fehler `parse_success=False` (niemals Exception schlucken)
- **CSV-Felder:** Neue dynamische Spalten in `result_manager.py` → `_get_updated_fieldnames` eintragen
- **CSV-Korruption:** Audit-Logs niemals direkt in CSV schreiben — immer separate Dateien verwenden. Bei Korruption: `load_csv_robust()` mit `on_bad_lines="skip"` verwenden
- **CSV-Write-Through atomar (v4.10.4):** `_write_to_csv()` nutzt `tempfile.mkstemp()` + `os.replace()` — Originaldatei bleibt intakt bei Kill/Crash. NIEMALS `"w"` (truncate) zum Überschreiben verwenden. Bestehende Zeilen werden beim Full-Rewrite NICHT re-validiert — nur neue Zeilen gehen durch Hard-Fail-Guard. `make backup` → tar (Snapshot) → `consolidate-csv` (Dedup latest-per-key) → bereinigte Live-CSV.
- **CSV-Daten-Pipeline:** `save_results()` = Upsert (gleiche `(model, asset_id)` wird ersetzt). `data_loader.py` dedupliziert via `drop_duplicates(keep="last")` nach Timestamp. `consolidate_csv.py` reduziert physisch auf 1 Zeile pro Key. Alle drei Schichten sind idempotent.
- **Token-Budget SSoT:** `resolve_token_budget()` in `utils/model_utils.py` — nie inline duplizieren
- **Anthropic `max_tokens` Provider-Cap (v4.10.6):** Der Provider-Default in `provider_config.yaml` ist 32768 (seit v4.10.6, vorher 8192). `fallback_max_tokens` wurde entfernt (Dead Config). Per-Model Override für `claude-haiku-4-5-20251001: 8192` (Desktop-Klasse). Bei neuen Claude-Modellen prüfen, ob der Default ausreicht — Claude 4.x unterstützt bis 128K Output, aber 32768 deckt alle Reasoning-Budgets ab (max. 20000 bei code_quality).
- **CI@500-Artefakt (bereinigt v4.10.6):** Cultural Intelligence lief bis April/Mai 2026 mit `token_limit_used=500` (altes Budget). 130 Zeilen (26 Modelle) entfernt. Aktuelles Budget: 3000 (Standard) / 4000 (Reasoning). Achtung: Wenn `token_limit_used` in alten Audit-Logs 500 zeigt, sind diese Runs veraltet.
- **`token_param_name` per Provider:** aus `benchmark_config.yaml` lesen, nie hardcoden
- **ThinkingProbe Signal-C-Verbot:** Response-Länge ist kein CoT-Signal — nur Signal A (`<think>`-Tags) und Signal B (`reasoning_tokens > 0`) verwenden
- **`_infer_provider()` — `/`-Präsenz-Heuristik:** Nie `"deepseek" in model_id` — lokale Ollama-IDs können Provider-Namen enthalten
- **`resolve_provider()` — `:free`-Suffix:** OpenRouter-Free-Tier-IDs haben das Format `vendor/model:free`. Die `:` Ollama-Erkennung greift nur wenn **kein** `/` im Namen ist. Fallback: `"/" in model_id` → `openrouter` (nicht mehr Groq).
- **Card-Naming SSoT:** `_card_path()` und `_find_card()` aus `utils/model_utils.py` — nie inline `Path(...) / f"{re.sub(...)}".json`. `-latest`-Aliases mit bekannter Version werden unter `{base}-{version}.json` abgelegt (`mistral-large-latest` → `mistral-large-3.json`). Die `model_id` *in der Card* bleibt immer der API-Alias.
- **`_find_card()` Dot→Hyphen-Fallback (ab v4.10.7):** `_safe_name()` konvertiert Punkte→Unterstriche, aber Cards, die aus provider_config-IDs mit Bindestrichen erstellt wurden, haben Bindestriche im Dateinamen (z.B. `grok-4-1-fast-reasoning.json` statt `grok-4_1-fast-reasoning.json`). Der Dot→Hyphen-Fallback in `_find_card()` schließt diese Lücke. XAI-Modelle mit Punkten in der API-ID (z.B. `grok-4.1-fast-reasoning`) werden über `internal_id_to_config_form()` automatisch aufgelöst (kein manueller Alias mehr nötig).
- **Review-Dir SSoT — `_safe_name()` zwingend:** Jedes Schreiben in `docs/reviews/{slug}/` muss `_safe_name(model_id)` nutzen — nie `subdir.name` oder rohe Audit-Log-Ordnernamen. Audit-Logs können `.` enthalten (z.B. `qwen_qwen3.6-plus`), `_safe_name` normalisiert zu `_` → ohne Normalisierung entstehen parallele Verzeichnisse, die im Web-Export Key-Kollisionen auslösen.
- **`audit_logger.py` `safe_model` — Punkte ersetzen:** `AuditLogWriter.write_audit_log()` und `PoliticalCompassTest.execute()` in `benchmark_modules/political_compass/` nutzen `str(model).replace(":", "_").replace("/", "_")` — **muss `.replace(".", "_")` enthalten**, sonst entstehen `xiaomi_mimo-v2.5/`-DOT-Dirs parallel zu den korrekten `xiaomi_mimo-v2_5/`-Underscore-Dirs. Fix: `.replace(":", "_").replace("/", "_").replace(".", "_")`.
- **Provider-Connector Thinking/Reasoning-Extraktion (ab v4.10.5 SSoT in `base.py`):** Jeder Provider-Connector MUSS drei Felder in `last_response_metadata` speichern:
  1. `reasoning_tokens` — via `self._extract_reasoning_tokens(usage)` (SSoT in `base.py`). Prüft automatisch: `completion_tokens_details` (OpenAI-kompatibel) → `output_tokens_details` (Anthropic) → `usage.reasoning_tokens` (Mistral). Google: inline `thoughts_token_count`. Ollama: inline `eval_count`.
  2. `think_content` — Non-Streaming via `self._extract_think_from_message(msg)` (SSoT). Streaming via `ThinkAccumulator` (SSoT in `base.py`). Anthropic/Google/Ollama: provider-spezifische Extraktion.
  3. `usage` — das vollständige `response.usage`-Objekt für `LLMParser.extract_usage_tokens()` (`llm_client.py:244`). OHNE `usage` fällt die Pipeline auf `estimate_tokens()` zurück (Zeichen-basierte Schätzung). NIEMALS `usage` weglassen.
  NIEMALS eigene Inline-Extraction schreiben — immer die Base-Utilities verwenden. Konsumenten: `base_runner.py:159` (Reasoning-Budget), `judge_evaluator.py:272` (Thinking-Aufwand), `benchmark_utils.py:382` (Audit-Log).
- **Model-ID-Namenskonvention (zwei Formen):** Interne `model_id`-Felder (Cards, CSVs, Leaderboard) nutzen die Underscore-Form — keine Punkte, nur Bindestriche und Unterstriche (`gpt-5_5-pro`, `xiaomi/mimo-v2_5-pro`). Provider_config-Einträge (`id`-Feld) und API-Calls nutzen die originale Schreibweise mit Punkten (`gpt-5.5-pro`, `xiaomi/mimo-v2.5-pro`). Die SSoT-Konvertierung intern→config/API übernimmt `internal_id_to_config_form()` in `utils/model_utils.py` — konvertiert Versions-Underscores zurück zu Punkten. **NIEMALS eigene Alias-Dicts pro Provider führen** — die generische Funktion deckt 95% der Fälle ab. Ausnahme: OpenRouter `z-ai/glm_*`-Modelle, wo `_safe_name()` Bindestriche und Punkte gleichermaßen zu `_` konvertiert (ambiguität). Editor-Prompt: `config/editor_prompts.yaml → model_onboarding`.
- **`is_accessible()` — 404 ≠ kein Zugriff:** `NotFoundError`/404 und `RateLimitError`/429 → `True` zurückgeben
- **Refusal-Flag statt Re-Run:** Antwort < 15 Zeichen → `refusal_flag=True`, kein Re-Run, kein Asset-Fix
- **OpenAI o-Series ThinkingProbe:** o1/o3-mini/o4-mini liefern keine `reasoning_tokens` → Card manuell mit `thinking_probe_manual_override: true` setzen
- **llama.cpp Native Thinking (`reasoning_content`):** Modelle wie Gemma-4 E4B geben Reasoning im Feld `reasoning_content` zurück (nicht im Standard-`content`). `llamacpp.py` extrahiert dieses Feld und setzt `reasoning_tokens = completion_tokens`. Probe erkennt das nicht → Card manuell: `thinking_probe_detected: true` + `thinking_probe_manual_override: true`
- **PC Skip-Logic Gap:** `execute_batch_module()` prüft nur 3 Standard-CSVs — nach Leaderboard-Reset explizit `political_compass_leaderboard.csv` als Fallback prüfen
- **Modellnamen-Normalisierung:** `save_leaderboard_csv()` in `io_manager.py` schneidet Datumssuffixe (`-YYYYMMDD` und `-MMDD` OpenRouter-Stil) automatisch ab — Modellnamen in der PC-Leaderboard-CSV sind immer suffix-frei
- **`reviews-auto` Skip-Logik:** mtime-basiert — nach jedem Benchmark-Run nur betroffene Modelle neu reviewt; `--force` deaktiviert Skip
- **Pricing SSoT:** Neue Preise gehören als `input_price_per_1m` / `output_price_per_1m` (USD/1M Tokens) ausschließlich in die Model Card JSON (`benchmark_scores/model_cards/*.json`).
- **Modell-Kategorisierung SSOT — nur `get_model_category()` aufrufen:** Niemals `"Open Weights (Cloud)"`, `"Open Weights (Local)"` oder `"Commercial"` als neue Kategorie-Strings verwenden. Die drei gültigen Display-Strings sind `"Proprietär"` / `"Restricted Weights"` / `"Open Weights"` — ausschließlich abgeleitet aus `weights_license_tier` in der Model Card via `get_model_category()` in `utils/model_utils.py`. Web-Export überschreibt den CSV-`Type`-Wert zur Laufzeit aus der Card — kein CSV-Rebuild nötig um Kategorien zu aktualisieren.
- **OpenRouter Alibaba Cloud / Qwen — `data_collection: allow`:** Qwen-Modelle (und andere Alibaba-Cloud-Endpoints) via OpenRouter liefern HTTP 404 ohne explizite Policy-Zustimmung. Fix: `extra_body={"data_collection": "allow"}` bei jedem OR-Request in `utils/providers/openrouter.py` (globaler Override, kein per-Modell-Schalter nötig).
- **Thinking-Erkennung SSoT — `resolve_effective_thinking()` aufrufen:** NIEMALS eigene Override/Probe-Logik inline schreiben. Die SSoT-Auflösung (Override > Card-Probe > None) liegt in `utils/model_utils.resolve_effective_thinking(model_card, provider_model_cfg, *, model_id, now)`. Für Token-Budget: `resolve_token_budget()` mit `provider=provider`-kwarg aufrufen (SSoT-Auflösung greift automatisch). Card-First-Property: Probe-Ergebnisse aus `thinking_probe_detected` sind robuster als String-Trigger im Modellnamen. Override-Schema in `config/card_template_provider.yaml` (Optionalfeld, `since v4.7.1`): `value` bool-Pflicht, `reason` Pflicht (Whitespace-only zählt als leer), `active_until` optional (ISO-8601, naive wird UTC). Drift-Schutz durch Auto-Expiry. Methodik: `docs/THINKING_PROBE.md`.
- **Card-Research `_commit_card` — `report.findings` statt `parsed["findings"]`:** `_commit_card()` iteriert über `report.findings` (enthält Pre-Findings + LLM-Findings), NICHT über `parsed["findings"]` (nur LLM). Pre-Findings mit `suggested`-Werten (z.B. Lizenz-Korrektur) gehen sonst verloren.
- **Card-Research Textfeld-Cascade — Pre-Finding + Post-Merge:** Lizenz-Wechsel erfordert Text-Rewrites in summary/strengths/known_limitations/judge_context_hint/weights_provenance_risk_rationale. Pre-Finding `_check_license_text_fields()` (auf ORIGINAL-Card) + Post-Merge `_check_license_cascade()` (auf gemergter Card). System-Prompt Regel 5 zwingt LLM zu kompletten Text-Rewrites.
- **GGUF-Konventionen SSoT — `_ensure_gguf_conventions()` aufrufen:** NIEMALS `deployment_type`, `params_active_b` oder Preise inline für GGUF-Modelle setzen. Die Post-Apply-Korrektur liegt in `manage_model_cards.py._ensure_gguf_conventions(card)`. GGUF-Erkennung via `_is_gguf_model(model_id)` (Regex: `q[2-8]_[k0-9]`, `gguf`, `-ud-`/`_ud_`). Läuft in `_commit_card` NACH `_ensure_license_consistency`.
- **Card-Template optional vs required:** Felder mit Beschreibung "null wenn X" müssen `required: false` sein — `is_unknown_sentinel(None)` returned `True`, also wird `null` bei `required: true` als Fehler gewertet. Betroffene Felder (Session 25): `params_total_b`, `params_active_b`, `knowledge_cutoff`, `license_url`, `input_price_per_1m`, `output_price_per_1m`.
- **`probe_thinking.py` Path-Handling:** `card_path` kann relativ sein (`benchmark_scores/model_cards/...`), `ROOT_DIR` ist absolut. Immer `card_path.resolve().relative_to(ROOT_DIR)` mit Fallback verwenden.
- **Card-Research `MODEL=all`:** `--card all` wird als Spezialwert erkannt (gleichbedeutend mit kein `--card`). Early-Validation in `main()` muss ebenfalls `all` erkennen.
- **Card-Research `MAX_CARDS=N`:** Limitiert Targets pro Run. Bei `FORCE=1` werden immer die ersten N alphabetischen Cards verarbeitet (kein Skip bereits verifizierter). Ohne `FORCE` werden nur unverifizierte Cards verarbeitet — dann funktioniert Batch-Processing korrekt (10 pro Run, nächster Run nächste 10).
- **`Apache-2.0` vs `Apache 2.0`:** Lizenz-String-Varianten werden vom LLM als Lizenz-Wechsel interpretiert → alle 5 Textfelder neu geschrieben. Ergebnis korrekt, aber viele rote Findings. `_check_license_consistency()` matched auf exakte Strings — Varianten sollten in `_KNOWN_LICENSE_MAPPINGS` ergänzt werden.
- **`profile_verified`-Validierung — finale Karte statt Findings-Historie:** `_commit_card` prüft `has_remaining_errors` durch Re-Validierung der FINALLEN Karte (`_check_license_consistency` + `_check_license_text_fields` + `_check_community` + Pflichtfelder), nicht durch Zählen der Findings. Findings können Fehler aus dem Originalzustand enthalten, die längst korrigiert wurden.
- **MCP Auto-Lifecycle:** `_ensure_mcp_running(mcp_url)` startet MCP automatisch wenn nicht bereits aktiv. `_stop_mcp_server()` stoppt am Ende (nur wenn gestartet). `_reset_llama_context(base_url)` resettet KV-Cache via `POST /slots/{id}?action=reset` nach jeder Karte (Best-Effort — die OpenAI-compatible API ist stateless, der Reset ist nur beim nativen Endpoint relevant). `_check_health(url)` vor jeder Karte.
- **Web-Export None-Stripping:** `_strip_none()` in `web_export.py` entfernt `None`-Werte rekursiv aus allen exportierten Dicts. Neue Felder zum Export hinzufügen: `card.get("feld")` reicht — `None` wird automatisch entfernt. Test `test_web_export_card_field_coverage.py` prüft Required-Felder gegen Sample-Card — wenn ein Required-Feld `None` sein kann, muss es in der Sample-Card einen Wert haben.
- **llamacpp `think_content` Key-Mismatch (Session 26):** `_extract_response_content()` in `llamacpp_base.py` speicherte `"thinking_content"` statt `"think_content"` — `base_runner.py:163` liest aber `"think_content"`. Ergebnis: `think_content` blieb immer leer in CSV. Fix: Key einheitlich auf `"think_content"` gesetzt. **Zusätzlich:** `reasoning_tokens` wurde nur bei leerem Content gesetzt — jetzt bevorzugt aus `usage.completion_tokens_details.reasoning_tokens` gelesen (llama.cpp-native), Fallback auf `completion_tokens` nur wenn Content leer.
- **`clean-results` Variant-Handling (v4.10.7):** `clean_results.py` muss ALLE Schreibweisen einer Model-ID bereinigen (Underscore `_`, Hyphen `-`, Punkt `.`). Die SSoT-Funktion `_collect_model_id_variants()` sammelt Varianten über `_safe_name()` + Card-Inhalt-Scan. **Reihenfolge kritisch:** CSVs werden VOR Cards bereinigt — `resolve_canonical_model_id()` braucht die Card für die Variant-Auflösung. `clean_cost_log()` ist separat von `clean_csv()` (cost_log ist keine Benchmark-CSV). `--dry-run` muss explizit in `clean.py` argparse ergänzt werden (Makefile erwartet es).
- **`_rebuild_index()` entfernt (v4.10.7):** `generate_model_cards.py` hatte `_rebuild_index()` — wurde zu `rebuild_card_index()` in `utils/card_template` migriert. `generate_review.py:200` ruf noch die alte Funktion auf → `AttributeError`-Crash bei `reviews-auto` (Modell 54/118). Fix: verwaisten Aufruf + unbenutzten `mc_gen`-Import entfernt.
- **Spark Token-Management (Session 26):** `llamacpp_spark` ist ein eigenständiger Server mit eigenem Kontextfenster. Drei Config-Ebenen pro Modell: (1) `context_length` → `--ctx-size` beim Serverstart (KV-Cache-Größe), (2) `max_tokens` → HTTP-Request-Limit pro Anfrage, (3) `parallel` → gleichzeitige Request-Slots (KV-Cache-Multiplikator). **Kardinalregel:** `max_tokens` muss kleiner sein als `context_length`, und `read_timeout` muss groß genug sein für `max_tokens / t/s`. Ohne `max_tokens`-Cap generiert das Modell bis zum Kontextfenster → Timeout-Loop. Per-Model-Cap wird in `llamacpp_base.py:query()` NACH `resolve_token_budget()` angewendet: `min(initial_tokens, model_cfg_max_tokens)`.
- **Cohere Native ToolUse (v4.10.8):** Prompt-basierte JSON-Tool-Schemas im System-Prompt kollidieren mit Cohere's Reasoning-Modellen (HTTP 422/500). ToolUse-Modul nutzt Cohere-native `tools`-API (`_extract_tool_schema()`, `_schema_to_cohere_tools()`, `_format_tool_calls_as_text()`). Andere Module bleiben prompt-basiert. Reasoning-Modelle: `thinking: {"type": "disabled"}` bei Native Tools verhindert 422. **Wichtig:** NIEMALS prompt-basierte Tool-Schemas für Cohere-Reasoning-Modelle verwenden — immer den nativen Pfad nutzen.
- **Cohere `command-a-plus` MoE-Instabilität:** `command-a-plus-05-2026` (Cohere's erstes MoE-Modell, 218B/25B aktiv) zeigt persistente HTTP 500 bei Benchmark-System-Prompts + nativen Tools. Einfache Prompts funktionieren. `thinking: disabled` hilft nicht. Serverseitiger Bug — `supports_tool_use=false` bis Cohere den Bug behebt (Stand 2026-06).
- **Card-Editor-Wrapper-Schicht (ab v4.10.11):** Der Card-Editor (`manage_model_cards.py`) kann bei Listen-Feldern wie `strengths` und `known_limitations` eine zusätzliche Wrapper-Schicht `[["a", "b"]]` statt `["a", "b"]` einführen. Symptom: `TypeError: sequence item 0: expected str instance, list found` in `get_model_card_context()`. **Defense-in-Depth:** Modul-Level-Helper `_flatten_strings()` in `scripts/analysis/review/metrics.py` akzeptiert beide Formen (flach + 1 Wrapper-Schicht) und filtert Nicht-Strings. Konsumenten MÜSSEN den Helper nutzen statt direkt `", ".join(card["strengths"])`. Bei Auftreten: alle betroffenen Cards per Backup-Recovery + Flatten-Script bereinigen (`grep -l '"strengths": \[\[' benchmark_scores/model_cards/*.json`).
- **WebExport Vendor-Dedup Defense-in-Depth (ab v4.10.11):** `_collect_vendor_cards()` in `scripts/web_export.py` filtert **immer** Placeholder-Karten (`unknown=true` ODER `vendor_id in _PLACEHOLDER_VENDOR_IDS = {"todo", "unknown"}`). Community-Karten gehen über `exclude_community=True` ausschließlich in `community_cards.json`. JS-Loader kann sich darauf verlassen, aber Python-Export macht den Filter bereits. Symptom: Wenn `vendor_cards.json` Placeholder oder Community enthält, ist die SSoT-Filter-Pipeline gebrochen — entweder Caller nutzt `exclude_community=False` falsch, oder neue Card-Generierung umgeht die Validierung. Workflow beim Anlegen neuer Vendor-Cards: (1) `vendor_id` MUSS kanonisch sein (siehe `classification_taxonomy.json → manufacturers.values[*].vendor_card_id`), (2) Fine-Tune/Quant-Varianten MÜSSEN `card_subtype: "community"` haben, (3) niemals `vendor_id: "todo"` oder `"unknown"` als Platzhalter — das löst Filter aus und Card verschwindet still.
- **WebExport Vendor-Card-Drift (ab v4.10.11):** Wenn die Taxonomie (`classification_taxonomy.json → manufacturers.values[*].vendor_card_id`) auf IDs verweist, die nicht als Vendor-Card-Datei in `benchmark_scores/vendor_cards/` existieren, zeigen die `vendor_card_ref`-Felder in `data.json` ins Leere. Symptom: Modell-Templates haben keinen Vendor-Namen/Vendor-Beschreibung (z.B. 13 Qwen-Modelle nach Cleanup von `alibaba_cloud.json`). **Defense-in-Depth:** `_init_export_context()` in `web_export.py` sammelt `existing_vendor_card_ids` einmalig und loggt WARN wenn Taxonomie-IDs fehlen; `_process_leaderboard()` loggt pro Modell WARN bei `vendor_card_ref`-Drift. Web-Loader-Fix (out of scope Python-Repo): bidirektionale Alias-Map in `vendorCards.11tydata.js` — `aliasToCanonical` muss in beide Richtungen aufgelöst werden (alias UND kanonisch zeigen auf dieselbe Card).
- **WebExport Provider-Cards Schema (ab v4.10.11):** Der Python-Export schreibt seit v4.10.11 zwei separate Files: `vendor_cards.json` (vollstaendige Vendor-Cards mit allen Feldern, inkl. Stats/Profile-Metadaten) und `provider_cards.json` (gefiltertes Sub-Set fuer Web-Display). Das Provider-Schema enthaelt nur display-relevante Felder: `vendor_id, display_name, company, headquarters, founding_year, description, deployment (Dict mit GDPR/Cloud-Act/Sovereign-Risk-Metadaten), pricing_model, api_base_url, api_documentation_url, notable_models, profile_verified, last_verified_at`. KEIN `stats, profile_verified_by, profile_verified_at, generated_at, last_modified_at, verification_source, unknown` — die sind interne Profile-Metadaten, die NICHT ins Web exportiert werden. Web-Loader: `CrucibleMark-Web/src/_data/providerCards.11tydata.js` liest `provider_cards.json`, filtert Placeholder (`todo`/`unknown`) und `unknown=true`, mergt `provider_stats.json`. `.eleventy.js` registriert `providerCards` UND `vendorCards` als Global-Data + passthrough zu `_site/data/`.
- **WebExport Blacklist-ID-Normalisierung (ab v4.10.11):** Die Blacklist (`config/web_export_blacklist.yaml`) enthaelt Eintraege in der kanonischen Underscore-Form (`deepseek_deepseek-chat-v3_1`), waehrend die `raw_model_id` aus dem Leaderboard Provider-Prefix und Punkte enthaelt (`deepseek/deepseek-chat-v3.1`). Symptom: 12/34 Blacklist-Eintraege (~35%) matchten NICHT und Modelle wurden trotz Blacklist-Eintrag exportiert (z.B. DeepSeek V3.1 wurde 4 Tool-Use-Monate lang ungewollt im Web-Export angezeigt). **Fix:** `_is_blacklist()` in `web_export.py` normalisiert BEIDE Seiten via `_safe_name()` und prueft Wildcard-Patterns in beiden Formen (roh + normalisiert). Tests in `tests/test_web_export_blacklist_normalization.py` (11 Tests). **Caveat:** 100% Effektivitaet nicht erreichbar, weil einige Blacklist-Eintraege Tippfehler enthalten (`gpt-5_5-pro-2026-04-23` statt `gpt-5_5-2026-04-23`) oder auf nicht-existierende Modelle zeigen.
- **Tool-Use-Cleanup-Atomaritaet (ab v4.10.11):** Das Sanitize-Skript `scripts/maintenance/sanitize_8_models_tooluse.py` muss ALLE Tool-Use-Datenquellen ATOMAR bereinigen, sonst entsteht Drift zwischen LB, Audit-Logs und narrativen Reviews. Symptom (User-Beobachtung 2026-06-26): DeepSeek V3.1 hatte Tool-Use-Scores im Leaderboard und narrative Reviews, aber keine Audit-Files im `outputs/audit_logs/<dir>/` — der Web-Export zeigte Tool-Use-Daten ohne nachvollziehbaren Audit-Trail. **Pflicht-Reihenfolge:** (1) Card-Reset auf `supports_tool_use: untested`, (2) Audit-Files loeschen, (3) Leaderboard-Rows loeschen (mit Backup), (4) narrative Reviews loeschen (mit Backup in `.bak_pre8_narrative/`), (5) **Konsistenz-Check** der alle Review-Dirs gegen Leaderboard-Eintraege verifiziert (auch ueber versionierte IDs wie `gpt-5_5-2026-04-23` ↔ `gpt-5_5/`). Niemals nur Teile ausfuehren.
- **Cleanup-Architektur-Vollstaendigkeit `clean_results.py --model` (ab v4.10.11):** Wenn ein Modell via `make clean-model MODEL=X` entfernt wird, muessen ALLE Datenquellen bereinigt werden — nicht nur die offensichtlichen. Die folgenden Pfade werden variant-aware in `clean_model_output_directories()` und `clean_csv()` integriert: (1) `outputs/audit_logs/<dir>/`, (2) `docs/reviews/<dir>/`, (3) `outputs/runs/results_<model>_<date>.json`, (4) `outputs/runs/dispatch_summaries/{political_compass,tooluse,score_<module>}_<model>.json`. Die Sub-Family-Leaderboards `gemma_leaderboard.csv`, `qwen_leaderboard.csv`, `provider_leaderboard.csv` sind in `SUB_FAMILY_LEADERBOARD_CSVS` integriert. Nach Card-Loeschung wird `rebuild_card_index("model")` + `rebuild_provider_index()` getriggert, sonst verweisen stale Index-Eintraege auf geloeschte Cards. **Vergessene Pfade fuehren zu Web-Export-Drift** (Sub-LBs sichtbar nach Rebuild, dispatch_summaries von `_build_benchmark_run_dates` und `_build_tooluse_entry` gelesen). Test-Suite: `tests/test_clean_results_arch_coverage.py` (13 Tests fuer alle Datei-Formate + Listen-Coverage + Dry-Run-Integration).
- **WebExport Score-Spalten-Vollstaendigkeit (ab v4.10.11):** `LdbCols` in `scripts/web_export.py` (Z. 35-70) MUSS eine Konstante fuer JEDE CSV-Modul-Spalte in `benchmark_scores/benchmark_leaderboard_detailed.csv` haben, sonst wird die Spalte stillschweigend ignoriert und landet nicht in `data.json.leaderboard.scores`. Stand v4.10.11: 10 Spalten (Code Quality, CLI Badge, UX Writing, Documentation Quality, Content Transformation, Cultural Intelligence, Logical Reasoning, Synthesis Quality, Tool Execution, Political Bias). Symptom bei Drift: Radar-Charts auf Webseite zeigen "Tool Execution" nicht an. Defense-in-Depth: `tests/test_web_export_field_coverage.py::TestLeaderboardScoreMapping::test_no_silent_csv_column_loss` prueft, dass jede CSV-Spalte einem LdbCols-Eintrag zugeordnet ist und im Export landet.

---

## Memory Bank

| Datei | Inhalt |
|---|---|
| `memory-bank/projectbrief.md` | Projektziele, Scope, Non-Goals |
| `memory-bank/productContext.md` | Warum CrucibleMark, Design-Philosophie |
| `memory-bank/systemPatterns.md` | Architektur-Patterns, Entscheidungen |
| `memory-bank/techContext.md` | Tech-Stack, Dependencies, Setup |
| `memory-bank/activeContext.md` | **Aktueller Sprint, offene Issues** |
| `memory-bank/progress.md` | **Was läuft, was in Arbeit, Blocker** |

> `activeContext.md` und `progress.md` werden nach jeder Session aktualisiert.
> Vor größeren Änderungen lesen — Konflikte mit laufender Arbeit vermeiden.
