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
- **`token_param_name` per Provider:** aus `benchmark_config.yaml` lesen, nie hardcoden

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
- **Token-Budget SSoT:** `resolve_token_budget()` in `utils/model_utils.py` — nie inline duplizieren
- **`token_param_name` per Provider:** aus `benchmark_config.yaml` lesen, nie hardcoden
- **ThinkingProbe Signal-C-Verbot:** Response-Länge ist kein CoT-Signal — nur Signal A (`<think>`-Tags) und Signal B (`reasoning_tokens > 0`) verwenden
- **`_infer_provider()` — `/`-Präsenz-Heuristik:** Nie `"deepseek" in model_id` — lokale Ollama-IDs können Provider-Namen enthalten
- **`resolve_provider()` — `:free`-Suffix:** OpenRouter-Free-Tier-IDs haben das Format `vendor/model:free`. Die `:` Ollama-Erkennung greift nur wenn **kein** `/` im Namen ist. Fallback: `"/" in model_id` → `openrouter` (nicht mehr Groq).
- **Card-Naming SSoT:** `_card_path()` und `_find_card()` aus `utils/model_utils.py` — nie inline `Path(...) / f"{re.sub(...)}".json`. `-latest`-Aliases mit bekannter Version werden unter `{base}-{version}.json` abgelegt (`mistral-large-latest` → `mistral-large-3.json`). Die `model_id` *in der Card* bleibt immer der API-Alias.
- **Review-Dir SSoT — `_safe_name()` zwingend:** Jedes Schreiben in `docs/reviews/{slug}/` muss `_safe_name(model_id)` nutzen — nie `subdir.name` oder rohe Audit-Log-Ordnernamen. Audit-Logs können `.` enthalten (z.B. `qwen_qwen3.6-plus`), `_safe_name` normalisiert zu `_` → ohne Normalisierung entstehen parallele Verzeichnisse, die im Web-Export Key-Kollisionen auslösen.
- **`audit_logger.py` `safe_model` — Punkte ersetzen:** `AuditLogWriter.write_audit_log()` und `PoliticalCompassTest.execute()` in `benchmark_modules/political_compass/` nutzen `str(model).replace(":", "_").replace("/", "_")` — **muss `.replace(".", "_")` enthalten**, sonst entstehen `xiaomi_mimo-v2.5/`-DOT-Dirs parallel zu den korrekten `xiaomi_mimo-v2_5/`-Underscore-Dirs. Fix: `.replace(":", "_").replace("/", "_").replace(".", "_")`.
- **Provider-Connector Thinking/Reasoning-Extraktion (ab v4.10.1 SSoT):** Jeder Provider-Connector MUSS drei Felder in `last_response_metadata` speichern:
  1. `reasoning_tokens` — aus `usage.completion_tokens_details.reasoning_tokens` (OpenAI/Mistral/OpenRouter/Groq/xAI), `usage.output_tokens_details.reasoning_tokens` (Anthropic), `usage_metadata.thoughts_token_count` (Google), `eval_count` (Ollama bei Thinking-Modellen)
  2. `think_content` — der vollständige Thinking-Text (OpenAI: `msg.reasoning`, Anthropic: `block.thinking`, Google: `part.thinking`, Mistral: `chunk.thinking`, Ollama: `msg.thinking`)
  3. `usage` — das vollständige `response.usage`-Objekt für `LLMParser.extract_usage_tokens()` (`llm_client.py:244`). OHNE `usage` fällt die Pipeline auf `estimate_tokens()` zurück (Zeichen-basierte Schätzung). NIEMALS `usage` weglassen.
  Helper: `_extract_reasoning_tokens(usage)` (DRY-Pattern) in anthropic.py, openai.py, groq.py, xai.py. Streaming-Pfade: Reasoning-Chunks akkumulieren (`delta.reasoning`, `thinking_delta`, `part.thinking`, `msg.thinking`). Konsumenten: `base_runner.py:159` (Reasoning-Budget), `judge_evaluator.py:272` (Thinking-Aufwand), `benchmark_utils.py:382` (Audit-Log).
- **Model-ID-Namenskonvention (keine Punkte in IDs):** Interne `model_id`-Felder und provider_config-Einträge dürfen **keine Punkte** enthalten — nur Bindestriche und Unterstriche. Versionspunkte werden zu Unterstrichen: `v2.5` → `v2_5`, `3.3` → `3_3`. Beispiele: `xiaomi/mimo-v2_5-pro` ✓, `nvidia/llama-3_3-nemotron-super-49b-v1_5` ✓. Die OpenRouter/API-ID (mit Punkt) wird als `api_model_id` oder via Provider-Alias getrennt gespeichert. Editor-Prompt: `config/editor_prompts.yaml → model_onboarding`.
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
- **Spark Token-Management (Session 26):** `llamacpp_spark` ist ein eigenständiger Server mit eigenem Kontextfenster. Drei Config-Ebenen pro Modell: (1) `context_length` → `--ctx-size` beim Serverstart (KV-Cache-Größe), (2) `max_tokens` → HTTP-Request-Limit pro Anfrage, (3) `parallel` → gleichzeitige Request-Slots (KV-Cache-Multiplikator). **Kardinalregel:** `max_tokens` muss kleiner sein als `context_length`, und `read_timeout` muss groß genug sein für `max_tokens / t/s`. Ohne `max_tokens`-Cap generiert das Modell bis zum Kontextfenster → Timeout-Loop. Per-Model-Cap wird in `llamacpp_base.py:query()` NACH `resolve_token_budget()` angewendet: `min(initial_tokens, model_cfg_max_tokens)`.

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
