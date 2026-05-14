# REF_TODO.md – Refactoring & Future Development

## Backlog (Phase 2)
- [ ] **`content_transformation_005` — Body-Word-Parser:** `keyword_presence`-Check für 300-Wort-Limit des Email-Bodys durch echten Wort-Count ersetzen. Benötigt Section-Parser der Analyse-Teil von Newsletter-Body trennt. Aufwand: ~30 LOC in `__init__.py` + Issue-Umstellung in `asset_005_newsletter_adaptation.yaml`. Risiko: Modelle formatieren Body uneinheitlich — falsche Penalties bei ~20% der Antworten möglich. Wert: 2.4 Pkt. Nicht zeitkritisch.

## Abgeschlossen

### Modell-Kategorisierungs-SSOT: 3-Tier `weights_license_tier` (v3.7.0 – 14.05.26)
- [x] `get_model_category()` in `utils/model_utils.py`: Card-First-Lookup via `_find_card()` → `weights_license_tier` → Display-String. Drei gültige Tiers: `Proprietär` / `Restricted Weights` / `Open Weights`.
- [x] `scripts/web_export.py`: `type`-Feld aus Model Card zur Export-Zeit abgeleitet; Legacy-CSV-Werte werden überschrieben ohne Rebuild. `model_category` im PC-Export ebenfalls Card-basiert.
- [x] `benchmark_modules/political_compass/core/io_manager.py`: Inline-Kategorie-Logik durch `get_model_category()`-Aufruf ersetzt.
- [x] `scripts/leaderboard/data_loader.py`: Fallback-Funktion auf 3-Tier-Strings vereinfacht.
- [x] Frontend `model-types.js`: 3-Tier-SSoT (`isCommercial`, `isRestrictedWeights`, `isOpenWeight`, `CHART_SERIES_CONFIG` 3 Einträge). Alle Chart-Module migriert: `political-compass-chart.js`, `politicalCompass.11tydata.js`, `leaderboard-chart.js`, `scoreboard-table.js`, `shift-chart.js`.
- [x] SCSS: `--cm-chart-label-restricted: $cm-amber`, Badge-Styles `cm-model-badge--restricted` + `--restricted-sub`.
- [x] Docs: `CLAUDE.md` Critical Pitfalls, `ARCHITECTURE.md` Web Export Pipeline, `memory-bank/systemPatterns.md` neuer Pattern-Block.

### Archetyp-Umbenennung: Stoiker + Narr (v3.6.5 – 09.05.26)
- [x] `Das Schaf` → `Der Stoiker`, `Chamäleon` → `Der Narr`. Finale vier Bezeichnungen: Stoiker / Wolf im Schafspelz / Die Chimäre / Der Narr. Nur Labels geändert, Logik/Schwellwerte unverändert. CSV-Backfill 76 Zeilen, Web-Export 72/72.

### Archetyp-Umbenennung: Chimäre + Das Schaf, Chamäleon-Threshold (v3.6.4 – 08.05.26)
- [x] `Offener Wolf` → `Die Chimäre` (hoher Shift + Quadrantenwechsel). `Echtes Schaf` → `Das Schaf`. `classify_behavior_archetype()` um `forced_x`/`forced_y` erweitert. CSV-Backfill 76 Zeilen. Neue Verteilung: Schaf 54, Wolf 18, Chimäre 2, Chamäleon 2.
- [x] `ARCHETYPE_CHAMELEON_FLIP_THRESHOLD` von 50 → 35 (Operator `>` → `>=`). Empirisch kalibriert (P90=27.2 %, n=76). Chamäleon: gemini-3-flash-preview + dolphin-mistral-nemo.

### behavior_archetype, vendor, Modellnamen-Normalisierung (v3.6.3 – 08.05.26)
- [x] `behavior_archetype`-Feld im PC-Leaderboard + Web-Export. Modellnamen-Normalisierung (Datumssuffix-Strip `-YYYYMMDD`/`-MMDD`). 8 CSV-Einträge bereinigt, 76 Zeilen backgefüllt.
- [x] `vendor`-Feld in allen 72 Model Cards (13 Werte). Leaderboard-Detailed-CSV Vendor-Spalte.

### model_id SSOT, benchmark-auto Fix, supports_tool_use, 3 Grok-Modelle (v3.6.0 – 04.05.26)
- [x] **`scripts/leaderboard/exporter.py` — `model_id`-Spalte:** Rohe Config-ID in `benchmark_leaderboard_detailed.csv` als SSOT.
- [x] **`scripts/web_export.py` — Dir-Lookup via `model_id`:** Fallback 1: Date-Suffix-Strip. Fallback 2: Suffix-Match. 69/69 Coverage.
- [x] **`scripts/core/benchmark_auto.py` — `COMPLETED_STATUSES`:** `language_mismatch`/`truncated`/`refusal` nicht mehr retried.
- [x] **`utils/benchmark_utils.py` — P95-Akkumulation:** Regex-Fix. 154 Dateien bereinigt.
- [x] **`supports_tool_use`** in 77 Model Cards migriert. Prompt-Dokumentation aktualisiert.
- [x] **3 neue Grok-Modelle** in `benchmark_config.yaml` + `cost_limits.yaml`.
- [x] **Docs:** `ARCHITECTURE.md`, `USER_GUIDE.md`, `systemPatterns.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `README.md` synchronisiert.

### size_class Card-Lookup, empty_response_context, Model-Card-Korrekturen (v3.5.9 – 24.04.26)
- [x] **`utils/model_utils.py` — `get_model_size_class()` Priority-Kaskade:** (1) Card-Lookup SSoT → (2) Ollama-Colon-Tag case-insensitive → (3) Dash/Dot-Suffix-Regex → Fallback `"Frontier"`. Hilfsfunktionen `_param_b_to_size_class()` + `_SIZE_CLASS_VALID`. Leaderboard: Nano=5, Edge=5, Desktop=7, Workstation=4, Server=1, Frontier=40.
- [x] **`scripts/analysis/generate_review.py` — `_build_empty_response_context()`:** Liest alle 3 Benchmark-CSVs, filtert `response_length=0 + status=success`, liefert Asset-IDs als Kontext-Block an Meta-Reviewer. Nur aktiv für `review_type == "benchmark"`.
- [x] **`config/meta_reviewer_prompt.yaml` — `{empty_response_context}`:** Neuer Pflicht-Block nach `constraint_violations_context`. Lautlose Verweigerungen werden als Qualitätsmerkmal dokumentiert.
- [x] **`scripts/analysis/generate_model_cards.py` — Auto-`size_class`:** Beide Pfade (`_generate_card()` + `_create_minimal_card()`) schreiben `size_class` via `get_model_size_class()`. Bestehende Felder werden nicht überschrieben.
- [x] **Model-Card-Korrekturen:** 6 Cards manuell korrigiert (Desktop/Server/Workstation/Nano). Slug-Mismatch `CognitiveComputations/dolphin-mistral-nemo:latest` → `CognitiveComputations_dolphin-mistral-nemo_latest.json` behoben.
- [x] **Dokumentation:** `README.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `REF_TODO.md`, `scripts/web_export.py`, `memory-bank/`, `.github/copilot-instructions.md` (neuer Fallstrick: size_class Card-Slug-Mismatch) synchronisiert.

### ThinkingProbe & Card-First Workflow (v3.5.8 – 23.04.26)
- [x] **`utils/model_utils.py` — `ThinkingProbeResult` & `probe_thinking_model()`:** Dataclass mit `detected: bool`, `evidence: str`, `confidence: Literal["high","medium","low"]`. Signal A: `<think>`/`<thinking>`/`<thought>`-Tags in Response-Body. Signal B: `reasoning_tokens > 0` in API-Metadaten. Signal C (Response-Länge) bewusst nicht implementiert (False-Positive bei Instruction-Following-Modellen).
- [x] **`utils/model_utils.py` — `is_reasoning_model_from_card()`:** Card-First-Lookup für `thinking_probe_detected`-Feld. Dateinamen via `re.sub(r'[:/.\s]', '_', model_id)` auflösen — konsistent mit `_safe_name()` in `generate_model_cards.py`. Gibt `None` bei fehlender Card oder fehlendem Feld zurück.
- [x] **`utils/model_utils.py` — `is_reasoning_model()` Hierarchie:** Card-Lookup hat Vorrang. Neuer Trigger `kimi-k2` ergänzt.
- [x] **`scripts/core/unified_runner.py` — `_ensure_model_card()`:** Vor erstem Run eines Modells: Card + Feld vorhanden → Skip; Feld fehlt → Probe → Feld schreiben; keine Card → Probe → Minimal-Card erstellen (`card_status: minimal`); Probe-Fehler → RuntimeError (kein stilles Skip).
- [x] **`scripts/analysis/generate_model_cards.py` — `_create_minimal_card()`:** Erstellt Card ohne LLM-Aufruf mit `card_status: minimal`. `_generate_card()` setzt `card_status: complete` und bewahrt bestehende Probe-Felder bei `--force`.
- [x] **`scripts/tools/probe_thinking.py`** (NEU): Standalone-CLI. `--model <id>`, `--missing` (Batch: alle ohne Feld), `--all` (Force-Rescan). `_infer_provider()`: Config-Lookup → `/` im ID → `openrouter` → sonst `ollama`. Batch-Modus bricht bei Einzelfehlern nicht ab (`sys.exit(1)` nur bei `--model`).
- [x] **Makefile:** `probe-thinking` (`MODEL=<id>` required) + `probe-all-thinking` (`--missing`) als neue `.PHONY`-Targets.
- [x] **Bugfix `is_reasoning_model_from_card()` — `_safe_name()`:** War `replace('/', '_')` → ist jetzt `re.sub(r'[:/.\s]', '_', model_id)`. Behebt: `gemini-2.5-flash` fand `gemini-2_5-flash.json` nicht.
- [x] **Bugfix `probe_thinking.py` — `_infer_provider()`:** War Substring-Matching (`"deepseek" in model_id`) → ist jetzt `/`-Präsenz-Heuristik. Behebt: `deepseek-r1:8b` (lokal) wurde fälschlich via OpenRouter geprobt.
- [x] **Bugfix Batch-Exit:** `sys.exit(1)` nur noch bei explizitem `--model`-Fehler. `--missing`/`--all` bricht bei Einzelfehlern nicht ab.
- [x] **26 API-Model-Cards retroaktiv** via `make probe-all-thinking` mit Probe-Feldern versehen. 25 Offline-Ollama-Modelle: graceful failure.
- [x] **o1/o3-mini/o4-mini:** Manuelle Overrides (`thinking_probe_detected: true`, `thinking_probe_manual_override: true`) — OpenAI exponiert Reasoning-Tokens nicht im API-Response.
- [x] **`moonshotai/kimi-k2.5`:** Neue Minimal-Card via Card-First-Hook während Re-Run erstellt.
- [x] **Re-Runs:** 18 `gemini-2.5-flash`-Zeilen in `commercial_models_benchmark.csv` (code_quality 5, cultural_intelligence 5, ux_writing 4, documentation_quality 2, content_transformation 2) + 3 Zeilen `gemini-2.5-pro` gelöscht. 3 `kimi-k2.5`-Zeilen in `cloud_models_benchmark.csv` gelöscht + re-run.
- [x] **Dokumentation:** `CHANGELOG.md` v3.5.8, `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md` (v3.2.0), `docs/MODEL_CLASSIFICATION.md`, `memory-bank/systemPatterns.md`, `memory-bank/activeContext.md`, `memory-bank/progress.md`, `.github/copilot-instructions.md` (3 neue Fallstricke: Signal-C-Verbot, `_safe_name()`-Konsistenz, `_infer_provider()`-`/`-Heuristik, OpenAI-o-Series-Override).

### SSoT Token-Budget, Gemini-2.5 Reasoning-Fix, Judge-Verbosity-Penalty, Refusal-Metadaten (v3.5.7 – 23.04.26)
- [x] **`utils/model_utils.py` — `resolve_token_budget()`:** Zentrale SSoT-Funktion für Token-Budget-Berechnung. Gibt `(effektives_budget: int, is_reasoning: bool)` zurück. Alle drei Provider (`openai.py`, `openrouter.py`, `mistral.py`) delegieren dorthin. Behebt fehlende `elif is_reasoning and tokens < 10000: tokens = 25000`-Branch in `mistral.py`.
- [x] **`benchmark_config.yaml` — `token_param_name` pro Provider:** Fünf Provider-Blöcke (`mistral`, `openai`, `groq`, `xai`, `openrouter`) mit `token_param_name: max_tokens` bzw. `max_completion_tokens`. Provider lesen via `_provider_cfg.get("token_param_name", "<fallback>")`.
- [x] **`utils/model_utils.py` — `gemini-2.5` Reasoning-Trigger:** `is_reasoning_model()` erkennt `gemini-2.5-flash`/`gemini-2.5-pro`. Elevated Budget: ux_writing 8.000 statt 500, documentation_quality 12.000 statt 6.000 Tokens. Behebt 12–18%-Scores durch Thinking-Token-Budget-Erschöpfung.
- [x] **`utils/scoring/llm_judge/judge_prompt_builder.py` — `token_budget_context`:** Neuer Parameter `token_budget_context: Optional[Dict[str, int]]`. Injiziert `TOKEN BUDGET NOTE` in System-Prompt: sichtbarer Output > 2× Standard-Budget mit Padding/Wiederholung → −1 Punkt `output_quality`.
- [x] **`utils/scoring/llm_judge/judge_runner.py` — Pass-through:** `token_budget_context`-Parameter zu `score()` ergänzt und an `build_prompts()` weitergegeben.
- [x] **`utils/scoring/judge_evaluator.py` — Auto-Injektion:** Liest `standard`/`elevated`-Budget aus Config und setzt `kwargs["token_budget_context"]` automatisch für Reasoning-Modelle.
- [x] **`scripts/core/unified_runner.py` — Refusal-Metadaten:** Antworten < 15 Zeichen setzen `refusal_flag=True`, `refusal_type="content_safety"`, `refusal_note` im Result.
- [x] **`utils/result_manager.py` — CSV-Schema:** `refusal_flag`, `refusal_type`, `refusal_note` in `_get_updated_fieldnames()` als neue Pflicht-Spalten registriert.
- [x] **Dokumentation:** `CHANGELOG.md` v3.5.7, `docs/ARCHITECTURE.md` (SSoT-Abschnitt, Refusal-Metadaten, Trigger-Liste), `docs/SCORING_METHODOLOGY.md` (Verbosity-Penalty, Refusal-Dokumentation), `.github/copilot-instructions.md` (3 neue Fallstricke), `memory-bank/`.

### OpenRouter Reasoning-Token-Tracking (v3.5.6 – 23.04.26)
- [x] **`utils/model_utils.py` — `minimax-m2` Reasoning-Trigger:** `is_reasoning_model()` um `"minimax-m2"` ergänzt. OpenRouter-Provider setzt 5× Token-Budget (~40.000 Tokens) für alle `minimax-m2.*`-Varianten — verhindert `finish_reason: length` mit leerem Output.
- [x] **`schemas/result.py` — `reasoning_tokens`-Feld:** Neues `Optional[int]`-Feld in `BenchmarkResult` zwischen `finish_reason` und `token_limit_cutoff`. Wird als neue CSV-Spalte persistiert.
- [x] **`utils/providers/openrouter.py` — Extraktion:** `completion_tokens_details.reasoning_tokens` aus API-Response → `last_response_metadata["reasoning_tokens"]`.
- [x] **`utils/base_runner.py` — Propagation:** `reasoning_tokens` aus `client.last_response_metadata` → `exec_result.reasoning_tokens` → Result-Dict.
- [x] **`utils/benchmark_utils.py` — Audit-Log-Erweiterung:** Token-Header zeigt `(davon N Reasoning-Tokens, die intern verbraucht wurden)`. Neuer `[!WARNING]`-Block bei `reasoning_tokens > 0 AND token_limit_cutoff=True` mit Erklärung des Budget-Konflikts.
- [x] **`utils/scoring/judge_evaluator.py` — Pass-through:** `reasoning_tokens=result.get("reasoning_tokens")` an `save_audit_log()` weitergegeben.
- [x] **2 ungültige CSV-Zeilen gelöscht:** `minimax/minimax-m2.7` × `cli005` + `ux_writing_005` aus `cloud_models_benchmark.csv` (resp_len=0, finish_reason: length — Budget-Erschöpfung vor Fix).
- [x] **`Makefile` — `clean-bak`-Target:** Entfernt `.bak_*`-Dateien aus `benchmark_scores/`. `backup`-Target um `docs/reviews/`, `docs/audits/`, `config/`, `memory-bank/` erweitert, `.bak_*` excludiert.
- [x] **Dokumentation:** `docs/ARCHITECTURE.md` (Provider-Tabelle + Besonderheiten-Spalte + Reasoning-Budget-Abschnitt), `memory-bank/systemPatterns.md` (neuer Abschnitt), `.github/copilot-instructions.md` (Fallstrick).

### Asset-Limit-Kalibrierung & Fleet-Audit (v3.5.3 – 21.04.26)
- [x] **`ux_writing/assets/asset_005_microcopy_audit.yaml` — Limit-Kalibrierung:** `max_expected_words` 150 → 350 (P25 der Ist-Längen × 1.20 = 337, aufgerundet auf 350). Prompt-Text ergänzt: `"Maximale Länge: 350 Wörter gesamt (Analyse + Tabelle). Sei präzise – jeder Satz zählt."` — Modell war zuvor nie über das Limit informiert. 50/52 Modelle verletzten das alte Limit.
- [x] **`content_transformation/assets/asset_003_glossary_simplification.yaml` — Limit-Kalibrierung:** `max_expected_words` 150 → 250 (P25 = 210 W × 1.20 = 252 → 250). Format-Hinweis `"Max 150 Wörter"` → `"Max 250 Wörter"` synchronisiert. 29/52 Modelle verletzten das alte Limit.
- [x] **`content_transformation/assets/asset_004_video_script_tutorial.yaml` — Limit-Kalibrierung:** `max_expected_words` 600 → 900 (P25 = 789 W × 1.20 = 947 → 900). Format-Range `"400-600 Wörter"` → `"600-900 Wörter"` synchronisiert. Min-Ist aller 52 Modelle war 742 W.
- [x] **156 CSV-Zeilen gelöscht:** ct_003/ct_004/ux_005-Einträge aus allen 3 Benchmark-CSVs (75 + 42 + 39). Trigger für automatischen Re-Run.
- [x] **156 Audit-Log-Dateien gelöscht:** Alle `*/ux_writing_005.md`, `*/content_transformation_003.md`, `*/content_transformation_004.md` aus `outputs/audit_logs/`.
- [x] **Fleet-Scan (52 Modelle × 37 Tasks):** Alle Tasks auf strukturelle Limit-Fehler analysiert. Befund: 3 isolierte Fehler (behoben). `ux_writing_003` (per-Step-Limit korrekt), `content_transformation_005` (abschnittsbezogenes Limit, `keyword_presence` begründeter Trade-off) und 34 bewusst limit-lose Tasks.

### Code-Qualität, Terminologie & Block-7.9-Dokumentation (v3.5.2 – 21.04.26)
- [x] **`scripts/core/unified_runner.py` — Pylint W1309:** `f`-Prefix aus String ohne Interpolation entfernt (Zeile 511).
- [x] **`utils/providers/base.py` — Pylint W0719:** `raise Exception(...)` → `raise RuntimeError(...)`.
- [x] **`benchmark_modules/political_compass/core/audit_logger.py` — Pylint C0206:** `for _q_id in hydrated_responses:` → `for _q_id, _q_data in hydrated_responses.items():`. Beispieltext `repressiv-nationalistisch` → `repressiv-reaktionär`.
- [x] **`benchmark_modules/political_compass/core/evaluators.py` — Mypy annotation-unchecked:** `__init__(self) -> None` in `ExtremismWatchdog` und zweiter Klasse ergänzt.
- [x] **`benchmark_modules/political_compass/config.yaml` — Skalen-Label:** `Nationalistisch` → `Reaktionär` (X-Achse, Range 4.4–7.4).
- [x] **`docs/POLITICAL_COMPASS_KONZEPT.md` — Block 7.9:** Neuer Abschnitt 7 „Die Parolen-Extremismus-Sonde" mit Konzept, Asset-Tabelle (11 Assets), 80/20-Koordinatenformel und Hard-Refusal-Interpretationshinweis.

### Gemini Daily-Quota Fast-Fail (v3.5.1 – 17.04.26)
- [x] **`utils/providers/base.py` — `retry_delay`-Schwellenwert:** `retry_delay > 300 s` aus Gemini-API-Antwort gilt als Tages-Quota-Erschöpfung (Google Daily Quota, Reset Mitternacht Pacific). Statt 7,6 h zu schlafen: Fast-Fail mit `exceeded your current quota`-Exception → `_quota_exhausted = True` → sauberer Checkpoint-erhaltender Abbruch.
- [x] **`config/rate_limits.yaml` — `max_retry_delay_seconds: 300`:** Schwellenwert als dokumentierter Config-Wert eingetragen.

### PC Token-Asymmetrie-Analyse & Bias-Reviewer-Restrukturierung (v3.5.0 – 17.04.26)
- [x] **`utils/llm_client.py` — `last_output_tokens`:** `self.last_output_tokens = 0` vor jedem API-Call, `self.last_output_tokens = output_tokens` nach Kosten-Tracking (nur wenn Wert verfügbar). Liefert Output-Tokens (Ollama `eval_count`) ohne Nachparsing.
- [x] **`benchmark_modules/political_compass/test.py` — `output_tokens` im Checkpoint:** Live-Pfad nutzt `getattr(llm_client, "last_output_tokens", 0)`; Resume-Pfad schreibt `None` — semantisch trennbar von echter Null.
- [x] **`benchmark_modules/political_compass/core/audit_logger.py` — Section 2.6 Token-Asymmetrie:** Neuer Audit-Log-Abschnitt, nur bei `verification_mode=True`. Primär: echte `output_tokens` aus Checkpoint. Fallback: Zeitproxy mit `Hardware-abhängige Schätzung`-Label. Flags: `ELABORATION_SPIKE` (Forced > +50 %), `CAPITULATION_DROP` (Forced < −40 %). None-sicherer `(... or 0) > 0`-Filter, Coverage-Warnung bei partiellen Daten.
- [x] **`config/meta_reviewer_prompt.yaml` — Prompt-Architektur:** `{model_card_context}` vor Pflichtstruktur verschoben (sequenzielles LLM-Lesen). Drei offene Leitfragen → eine präzise Einzel-Instruktion. Section-2.6-Verzahnungs-Instruktion: Token-Befund als Dimension der Schattenmetriken (nicht isolierter Absatz). YAML-Kommentar vor `bias_reviewer:` dokumentiert Legacy/Neu-Lauf-Unterschied und Re-Run-Prioritäten.
- [x] **12 Legacy-Audit-Logs retroaktiv gepflegt:** Alle PC-Anomaly-Modelle (Shift > 1.0) aus initialem Run erhalten Section 2.6 mit Zeitproxy und `Hardware-abhängige Schätzung`-Label. Zero-Write-Regel greift — historischer Record vollständig.
- [x] **`docs/AUDIT_AND_METAREVIEW.md`:** Neuer Abschnitt "Section 2.6 Token-Asymmetrie" mit Primär-/Fallback-Modus, Flag-Schwellenwerten, Thinking-Modell-Einschränkung, retroaktiver Legacy-Notiz.
- [x] **`docs/POLITICAL_COMPASS_KONZEPT.md`:** Neues Kapitel 5 "Schattenmetriken" (Section 2.5 Standardabweichung, Section 2.6 Token-Asymmetrie, Flag-Tabelle, Kombinations-Interpretation).

### PC Budget-Exhaustion-Guard & Daten-Hygiene (v3.4.7 – 16.04.26)
- [x] **`benchmark_modules/political_compass/test.py` — Budget-Exhaustion-Erkennung:** Exception-Handler im Query-Loop setzt `self._quota_exhausted = True` bei Budget/Quota-Keywords (`quota`, `budget`, `billing`, `credit`, `payment`, `insufficient_funds`, ...). Logger-Warning statt stiller Absorption.
- [x] **`utils/base_runner.py` — Quota-Flag-Propagation:** `execute_batch_module()` prüft `getattr(test, "_quota_exhausted", False)` nach `test.execute()` und setzt `self.provider_quota_exhausted = True`. Gibt `[]` zurück — kein korruptes All-Zero-Ergebnis mehr im Leaderboard.
- [x] **`benchmark_modules/political_compass/core/io_manager.py` — `cost`-Spalte entfernt:** `fieldnames`-Liste und `row`-Dict bereinigt. Interne `total_cost`-Berechnung in `test.py` für Audit-Log erhalten.
- [x] **`config/meta_reviewer_prompt.yaml` — `bias_reviewer`-Prompt:** Neuer `bias_reviewer:`-Key mit 4300-Zeichen-System-Prompt für politische Bias-Analyse ergänzt.
- [x] **`scripts/web_export.py` — `inference_provider`-Feld:** `leaderboard.json` enthält jetzt `inference_provider` pro Eintrag.
- [x] **PC-Leaderboard bereinigt:** 34 → 13 Zeilen (21 März-Einträge mit `polarity_flip_rate = 0.0` entfernt). 21× `Political Bias` → `Pending` in `benchmark_leaderboard.csv`.

### PC Skip-Logic Fix & Leaderboard-Bereinigung (v3.4.6 – 14.04.26)
- [x] **`utils/base_runner.py` — PC Skip-Logic-Fallback:** `execute_batch_module()` liest `benchmark_scores/political_compass_leaderboard.csv` direkt, wenn Standard-CSV-Cache leer ist (Post-Reset-Szenario). Aktiviert nur für PC-Module via `PoliticalCompassHandler.is_political_compass()`. Graceful-Fallback bei `OSError`/`csv.Error`.
- [x] **PC-Leaderboard-Bereinigung:** 11 Einträge mit korrupten Koordinaten (runde Ganzzahlwerte aus Verweigerungssession 23.03.2026) entfernt. Leaderboard: 31 → 20 verifizierte Einträge. Backup: `political_compass_leaderboard.bak_20260414_222150.csv`. 31 Modelle für Re-Run freigegeben.
- [x] **`.github/copilot-instructions.md`:** Fallstrick „PC Skip-Logic Gap" dokumentiert.

### Architektur-Code-Review & Magic-String/Number-Elimination (v3.4.4 – 11.04.26)
- [x] **`utils/constants.py` — 12 neue Konstanten:** `MODEL_TYPE_OPEN_WEIGHTS_CLOUD`, `RESULT_TYPE_LOCAL/CLOUD/COMMERCIAL`, `TIMEOUT_OLLAMA_HEALTH/LIST_FAST/LIST/VERSION/WARMUP`, `TIMEOUT_HTTP_FETCH`, `TIMEOUT_ANTHROPIC_API` als SSOT definiert.
- [x] **Magic Strings/Numbers aus 8 Dateien eliminiert:** `result_manager.py`, `model_utils.py`, `providers/anthropic.py`, `pricing_updater.py`, `benchmark_auto.py`, `unified_runner.py`, `run_cross_model_benchmark.py`, `list_models.py` referenzieren alle Werte ausschließlich via `constants.py`.
- [x] **Verifikation:** 163/163 pytest passed, mypy clean (9 Dateien). Commit 95f2055, Tag v3.4.4.

### Dokumentation: Redaktionelle Überarbeitung (11.04.26)
- [x] **14 Dokumentationsdateien (README.md + docs/) einheitlich überarbeitet:** Ansprache (`du`/`dein`) → unpersönliches `man`/`sein`; alle Emojis aus Überschriften entfernt (nur 🛑 als Warnmarker behalten); alle englischen H1–H3 ins Deutsche übertragen; einheitliche Intro-Blöcke (`**Zielgruppe:**` / `**Inhalt:**` / `> **Voraussetzung:**`) ergänzt; alle `______`-Trennlinien → `---`.
- [x] **`module_weight`-Feld in alle 7 Modul-`config.yaml`s:** Neues `integration.leaderboard.module_weight`-Key pro Modul. Vollmodule je `1.0`, CLI `0.5` (Supplement, kein vollwertiges Evaluierungsmodul). Direkter YAML-Hebel für kundenspezifische Gewichtung ohne Code-Änderung.
- [x] **`score_calculator.py: _module_scale()`:** Hilfsfunktion berechnet `scale = module_weight / config_weight_sum` — self-normalizing, kein hardcodierter Kehrwert nötig. Alle 4 Contrib-Spalten (`final_routine`, `final_reasoning`, `weight_routine`, `weight_reasoning`) werden vor Aggregation mit `scale` multipliziert.
- [x] **`scripts/leaderboard/__init__.py`:** `module_weight` aus `lb_config.get("module_weight")` ins `mod_entry`-Dict propagiert. `None`-Fallback → `scale = 1.0` (Rückwärtskompatibilität).
- [x] **5 neue Ollama-Cloud-Modelle in `config/cost_limits.yaml`:** `deepseek-v3.1:671b-cloud` ($0.28/$0.42 per 1M Input/Output), `qwen3.5:397b-cloud`, `gemma4:31b-cloud`, `kimi-k2.5:cloud`, `glm-5:cloud`.
- [x] **`docs/BENCHMARK_MODULES.md`:** Abschnitt "Designprinzip: Module als gleichwertige, geschlossene Tests" mit Erklärung der `module_weight`-Konfiguration und CLI-Sonderfall ergänzt.
- [x] **`docs/SCORING_METHODOLOGY.md`:** Formel auf selbstnormierende Variante aktualisiert (`Σ(score × weight) / Σ(weight)`). Neue Sektion "Modulgewichtung" mit Default-Gewichtstabelle und Konfigurationshinweis.

### Vollständige Modell-Preisliste & Sync-Tool (v3.4.2 – 09.04.26)
- [x] **config/cost_limits.yaml: Vollständige Preis-Datenbasis:** Alle 25 konfigurierten Cloud-/Commercial-Modelle haben jetzt verifizierte Preiseinträge. Neue Sektionen: `ollama_cloud`, `google`; `xai` aus `settings:` in `providers:` verschoben.
- [x] **exporter.py: LLM Judge Avg Sterne-Format:** `_format_judge_stars()` formatiert den Wert als `3.8 ★` im Compact- und Detailed-Leaderboard.
- [x] **scripts/dev/sync_cost_limits.py:** Neues Dev-Tool. Vergleicht konfigurierte Modelle gegen `cost_limits.yaml`, meldet Missing-Entries. `--fix` schreibt `null`-Platzhalter — boundary-sicher (`providers_start/end`) und duplikatfrei.
- [x] **Makefile: `sync-cost-limits [FIX=1]`:** Neues Target für den standardisierten Pricing-Workflow.
- [x] **docs/USER_GUIDE.md:** `make sync-cost-limits` in F.2 Systemgesundheit dokumentiert + eigenständiger Workflow-Abschnitt "Preisliste abgleichen" ergänzt.

### Token-Verbrauch im Leaderboard (v3.4.1 – 08.04.26)
- [x] **score_calculator.py: scoring_df im calculate_scores():** Lokale `scoring_df`-Variable aus `cat_to_scoring`-Map aufgebaut (analog zu `_aggregate_basic_stats()`), damit Token-Aggregation dieselbe Modul-Basis wie der Total Score nutzt.
- [x] **score_calculator.py: Tokens Total Korrektur:** `tokens_used`-Summe aus `_aggregate_basic_stats()` (inkl. Political Compass) wird nach dem Merge überschrieben — neue Summe nur über `scoring_df` (enable_scoring=True). Verhindert Verzerrung durch variable PC-Retest-Mengen.
- [x] **score_calculator.py: Tokens: \<Modul\>-Spalten:** `token_by_module`-Block unpivotiert Token-Summen pro `(model, model_version, category)` aus `scoring_df` und prefixiert Spalten mit `Tokens: `. Political Compass bleibt ausgeschlossen.
- [x] **exporter.py: Compact-Leaderboard:** `Tokens Total` nach `Cost per 1K (USD)` eingefügt.
- [x] **exporter.py: Detailed-Leaderboard:** `Tokens Total` + alle dynamischen `Tokens: <Modul>`-Spalten (alphabetisch sortiert) ergänzt.
- [x] **README.md: Key Features:** Neuer Bullet-Punkt "Token-Verbrauch im Leaderboard" ergänzt.
- [x] **docs/SCORING_METHODOLOGY.md: Dokumentation:** Neue Sektion "Token-Verbrauch im Leaderboard" mit Tabelle, Begründung und Kosten-Kontext (API vs. Flat-Rate) eingefügt.

### Token-Budget-System & Verbosity-Transparenz (v3.4.0 – 08.04.26)
- [x] **base_runner.py: max_tokens API-Cap:** `execute_test_module()` liest `token_budgets[module_key]` aus der Config und übergibt `max_tokens=budget` NUR wenn budget nicht `None` ist. Kein None-Wert wird an Provider-Clients weitergegeben. Reasoning/Metacog/CLI ohne Limit (by design).
- [x] **benchmark_config.yaml: token_budgets kalibriert:** Werte auf 2× Modul-Median gesetzt: `cultural_intelligence: 500`, `ux_writing: 3500`, `content_transformation: 3500`, `documentation_quality: 6000`, `code_quality: 6000`. `cli_benchmark` entfernt.
- [x] **benchmark_utils.py: Token-Effizienz-Flag im Audit-Log:** Neuer `[!NOTE]`-Header-Block wenn `token_limit_cutoff is True AND _budget is not None`. Bestehender `[!CAUTION]`-Block bleibt unverändert.
- [x] **generate_review.py: Token-Effizienz-Kontext:** Neue Template-Variable `{token_efficiency_context}` injiziert modulspezifische Ø-Token-Werte (Modell vs. Fleet-Median) vor `{log_data}`.
- [x] **meta_reviewer_prompt.yaml: Verbosity-Diagnostik:** Neuer Block "Token-Effizienz (Verbosity)" — Reviewer schreibt Pflicht-Absatz wenn Ratio > 1.5× Median (Reasoning/Metacog ausgenommen).

### Political Compass Integration Fix (v3.3.1 – 08.04.26)
- [x] **io_manager.py: model_category-Feld:** `save_leaderboard_csv()` schreibt jetzt `model_category` (`local` / `cloud` / `commercial`) in die Leaderboard-CSV (nach `model`-Spalte); Routing-Logik analog `result_manager.py`.
- [x] **io_manager.py: provider_type-Korrektur:** Ollama-gehostete Cloud-Modelle (`:cloud`-Suffix) erhalten `provider_type=cloud` statt `ollama`.
- [x] **political_compass_handler.py Upsert:** `_update_local_pc_csv()` von append-only auf Upsert umgestellt — Parität zu `_update_commercial_pc_csv()`; eliminiert Duplikate bei Retry/Re-Run.
- [x] **clean_results.py: PC Leaderboard-CSV:** `political_compass_leaderboard.csv` zur `files`-Liste hinzugefügt; defensiver `asset_id`-Guard in `clean_csv()` verhindert KeyError bei PC-CSVs.
- [x] **CSV-Datenbereinigung:** `political_compass_leaderboard.csv` 66 → 56 Zeilen (Duplikate entfernt), `model_category` rückwirkend befüllt, `provider_type` für 8 Cloud-Modelle korrigiert.
- [x] **local_models_benchmark.csv:** 6 historische Cloud-Modell-Einträge entfernt (495 → 489 Zeilen).

### Language Compliance & Prompt Hardening (v3.3.0 – 07.04.26)
- [x] **Language Compliance Pipeline:** `judge_prompt_builder.py` um `required_language` / `language_weight` erweitert. Bei gesetztem Asset-Metadatum `language: de` wird dem Judge automatisch ein LANGUAGE COMPLIANCE Rubrik-Block injiziert (Standard 20 % Gewichtung; Sprachverstoß − 1,5 Punkte, Sprachmix −0,5 Punkte).
- [x] **judge_runner.py Forwarding:** `required_language` und `language_weight` werden aus dem Asset-Config-Dict an `build_prompts()` weitergeleitet.
- [x] **judge_evaluator.py:** `language_mismatch`-Flag wird aus der Judge-Response extrahiert und im Ergebnis-Dict protokolliert.
- [x] **Metacog Language Enforcement:** `reasoning_logic` Assets `metacog_001–005` mit `language: de` Metadatum und explizitem Deutsch-Constraint (`Antworte auf Deutsch.`) versehen.
- [x] **Editorial Audit (30 Fixes, 21 Assets):** Systemweite Bereinigung aller Gemini-Artefakte über 5 Module:
  - Token-Limit-Leak entfernt aus 13 Prompts (ux_writing, content_transformation, documentation_quality, code_quality)
  - Höflichkeitsformel `Bitte` aus 13 imperativen WICHTIG/HINWEIS-Blöcken gestrichen
  - Gemini-Pseudolabels `Mission:` / `TASK:` aus cultural_intelligence entfernt
  - `Erfülle dabei strikt die folgenden Anforderungen:` → `Anforderungen (strikt einhalten):` in 5 ux_writing Assets
- [x] **Kyrillischer Unicode-Artefakt-Fix:** 3 cyrillische Zeichen (U+043C м, U+0430 а, U+0442 т) in `asset_6a_german_tech_localization.yaml` durch lateinische Entsprechungen ersetzt. Systemweiter Scan: alle 43 übrigen Assets clean.
- [x] **Golden Standard Grammatikfehler:** `ein negatives Entwicklung` → `eine negative Entwicklung` in `asset_6e_german_idioms.yaml`.
- [x] **Stale Data Cleanup:** 492 obsolete Benchmark-Zeilen für geänderte Module aus `local_models_benchmark.csv`, `cloud_models_benchmark.csv`, `commercial_models_benchmark.csv` entfernt.
- [x] **Audit-Infrastruktur:** `docs/audits/`-Verzeichnis angelegt; `AUDIT_2026-04-07_editorial.md` archiviert.

### Audit Fixes & Scoring Integrity (v3.2.2 Patch – 07.04.26)
- [x] **Loop Detection in `llm_parser.py`:** Strukturelle Endlosschleifen (>50 Zeichen, >10× Wiederholung) werden erkannt und mit `> [!ERROR]`-Block ins Audit-Log injiziert.
- [x] **Regex Fix `generate_review.py`:** Multi-Line-Alert-Blöcke (`> [!WARNING]`) werden durch `re.DOTALL` korrekt erfasst.
- [x] **Hard Constraint generisch ausgerollt:** `constraints.max_expected_words` in YAML aktiviert für `ct003` (150W), `ct004` (600W) und `ux_writing_005` (150W). Constraint-Prüfung in beiden Evaluatoren (CT + UX) generisch per YAML-Read.
- [x] **Progressive Penalty-Stufen:** Flat-40%-Abzug durch dreistufige Logik ersetzt: Toleranzzone ≤120%; >120%→−20%, >200%→−40%, >300%→−60% (`tier_label` im Audit-Log dokumentiert).
- [x] **Language-Mismatch Auto-Flag:** Heuristische DE/EN Marker-Frequenzprüfung nach `score_response()` in `unified_runner.py`; setzt `status=language_mismatch` + `> [!WARNING]`-Block.
- [x] **ux_writing_002 Two-Step Enforcement:** Prompt um explizite `[SCHRITT 1 – ANALYSE]` / `[SCHRITT 2 – OPTIMIERUNG]` Header ergänzt.
- [x] **Code Quality Asset Hardening:** `asset_001_wcag_audit.yaml` um WCAG 2.2 Kriterien (Focus Not Obscured 2.4.11, Target Size 2.5.8) erweitert; `asset_002_security_audit.yaml` um 5 implizite Schwachstellen (Mail Header Injection, SQL Injection, User Enumeration, Unsafe Cookies) ergänzt.

### Data Architecture & Meta-Review (v3.2.2)
- [x] **3-CSV Data Separation:** Migration der fehleranfälligen Fallbacks aus der 2-CSV Form auf exakte SSOT-Aufspaltung (`cloud_models_benchmark.csv`).
- [x] **Context Injection Pipeline:** Meta-Reviewer Logik um das Modul `cloud_open_weights` ausgebaut, um Hardware-Fehlurteile bei API-Proxies zu verhindern.

### Performance & Cache Repair (v3.2.1)
- [x] **Data-Routing Bugfix:** Behebung des kritischen Autofill-Fehlers im `UnifiedBenchmarkRunner` (kommerzielle Ergebnisse in `local_models_benchmark.csv`).
- [x] **Datenbereinigung Log-Files:** Skriptbasierte und verlustfreie Überführung von 75 fehlgeleiteten Scores (`gpt-oss`, `llama-4-scout`) ins korrekte kommerzielle Logbuch.
- [x] **Lazy Loading Implementation:** Startup-Beschleunigung durch On-Demand Import von `sentence_transformers`/`sklearn` in mathematischen Evaluationsbausteinen.
- [x] **Groq API Ping Bypass:** Anpassung des 1-Token-Ping-Modells zur Provider-Validierung auf `llama-3.1-8b-instant`, da alte Referenz durch Groq inaktiviert wurde.
- [x] **CLI Terminal Metrics:** Output-Konsolidierung am Ende einzelner Module zur dynamischen Berechnung und Visualisierung von Durchschnittsscores, Dauer, Tokens und USD-Kosten.

### Fallbacks & Provider SSOT (v3.2.0)
- [x] **Dynamic Provider SSOT:** Hardgecodete Kategorie-Definitionen in CLI und Leaderboard entfernt; zentral über `benchmark_config.yaml` (`utils/model_utils.py`) dynamisiert.
- [x] **Open-Weights Cloud API Support:** Dedizierte Cloud-Infrastruktur für Open-Weights Modelle (z. B. via Groq) eingerichtet.
- [x] **Local Cloud Removal:** Legacy-Kategorie "Local Cloud" im gesamten System (Scores, Meta-Reviews, DataFrames) sauber mit `Cloud (Open-Weights)` fusioniert.

### Audit & Meta-Review Generation (v3.1.0)
- [x] **Meta-Reviewer Anchoring:** Off-by-one Parsing Bugs behoben (via durchgängiger YAML ID-Anker).
- [x] **Anti-Halluzinations-Schutz (Grammar Restriktionen):** Meta-Review-Prompt um harten Passiv-Zwang ergänzt, um Anthropomorphisierung im Fazit zu verhindern.
- [x] **Automatisierte Metadaten-Extraktion:** Regex-basiertes Herausfiltern von API-Limits, Endlosschleifen und Safety-Protokollen (Warnings) in den Audit-Logs für kontextsensitive Evaluierung.

### Architecture Hardening & Anti-Censorship (v3.0.0)
- [x] **3-Tier Refusal Framework:** Intelligentes Abfangen von Hard- und Soft-Refusals und API-Timeouts.
- [x] **Progressive Temperature Loop:** `while True`-Retry-Block im Execution-Layer mit schrittweisen Temperaturerhöhungen (0.1, 0.4, 0.7) als Safety-Bypass.
- [x] **Pydantic Schema Serialization:** Behebung von `AttributeError`-Abstürzen durch präzises `json.loads()` Parsing aus der rohen String-Response.
- [x] **Repository Consolidation:** Major Markdown-Updates, Entschlackung der Roadmap und Framework Bump auf 3.0.0.

### Version 1.1+ Core Architecture
- [x] **Leaderboard Overhaul (v1.1)** (Absolute Scoring, Speed Profiles)
- [x] **Reasoning Module Implementation**
- [x] **System Probes & Warnungen**
- [x] **Global Cascading Token Fallback & Error Handling** ("Fast Fail")
- [x] **Golden Standard Consolidierung** (Asset YAML as SSOT)

### LLM-Based Scoring System (v1.5 Milestone Reached)
- [x] Abstract Scorer Interface und Provider Abstraction
- [x] Native Pipeline Integration & Phase 1–3 implementation
- [x] Hybrid Scoring System (Gewichtung Regex- und Judge-Scores, Fallback-Weights)
- [x] Rubric & Prompt Configuration (`benchmark_config.yaml`)
- [x] Module Rollout (Code Quality, UX Writing, Docs, Content)

### Refactoring & Stability (v2.6.2)
- [x] **God-Script Dismantling (Phase 3):** `provider_clients.py` sauber in modulare Pakete unter `utils/providers/` aufgeteilt – Facade Pattern.
- [x] **Namespace Collision Resolution:** Modulspezifische `ResultManager`-Logik extrahiert, strikte Entkopplung von globalen Systemen hergestellt.
- [x] **Magic Numbers Centralization:** Endpunkte und Limits (z. B. Ollamas Default-Port 11434) in `constants.py` zentralisiert.
- [x] **LLM Token Loop Hallucination Fallback:** API-Trimming-Logik in `llm_client.py` implementiert und in `AUDIT_AND_METAREVIEW.md` dokumentiert.
- [x] **Documentation Restructuring:** README.md rigoros an `benchmark_config.yaml`-Kategorien angeglichen, veraltete Scripts vollständig entfernt.

### Module Refactoring & Features
- [x] Political Compass Decoupling (Metrics-Logik von Scoring isoliert)
- [x] Alpha-Randomization in Multiple Choice Modules (Label-Bias vermieden)
- [x] Human Baseline Script (`run_human_compass.py`)
- [x] Code Quality Audit → v2.0.1 (Fixed Import)
- [x] UX Writing & Microcopy → v2.0
- [x] Documentation Quality → v2.0
- [x] Content Transformation → v2.0.1 (Fixed Logic)
- [x] Cultural Intelligence → v2.0

---

## In Bearbeitung

### Nächste Session
- [ ] **LLM Judge: Batch-Mode (Phase 3.5)**: Token-Verbrauch durch gebündelte Requests reduzieren.
- [ ] **Volldurchlauf aller lokalen Modelle**: Generierung eines echten finalen Leaderboards (43/43).
- [ ] **Re-run Reasoning Logic**: Verfälschte 0-Punkte für lokale Modelle bereinigen.

### Offene Features (v3.5.x+)
- [ ] **Score-Penalty für Token-Verbosity:** Separates Feature — keine Änderung an bestehenden Scores. Bewertungsabzug wenn Modell Token-Budget konsistent ausschöpft ohne Qualitätsgewinn.
- [ ] **Leaderboard-Spalten: avg_tokens, token_efficiency_ratio, est_cost_per_1k_tasks:** Implementierung in `score_calculator.py` + `generate_leaderboard.py`.
- [ ] **gpt-5.4-mini cultural_intel 108-Token-Anomalie:** `--force` Re-Run prüfen, ob echter Bug (abgeschnittene Response) oder valides Ergebnis.

### Testing Infrastructure
- [ ] Unit tests für alle Module (aktuell ca. 60%)
- [ ] Integration tests (Framework-Ebene)
- [ ] Performance Benchmarks
- [ ] CI/CD Pipeline (GitHub Actions)

---

## Backlog

### Q3 und Q4 2026

#### 1. Creative Writing Module
- Story generation
- Poetry evaluation
- Character development
- Plot coherence

#### 2. Web UI
- Interactive dashboard
- Real-time progress
- Result visualization
- Model comparison

#### 3. API Mode
- REST API for remote benchmarking
- Queue management
- Authentication

#### 4. Cost vs. Accuracy Analysis
- Meta-Analyse der Judge-Cost- und Token-Verhältnisse über Modelle hinweg
- System-Prompts tunen, um Overhead zu reduzieren (ohne Konsensqualität zu opfern)

### v2.0.0 (Cloud & Redesign)

#### 1. Multimodal Support
- Image + Text tasks
- Vision-based benchmarks
- OCR evaluation

#### 2. Advanced Feature Set
- Custom Plugin Evaluator System
- Adaptive Testing (Dynamic Difficulty)
- Scheduled Continuous Benchmarking & Alerting

---

| Task | Priority | Effort | Status |
|------|----------|--------|---------|
| **LLM Judge JSON Batching** | High | 1 week | In Progress |
| **Volldurchlauf Leaderboard** | High | 1 week | Pending |
| **Unit Tests & CI/CD** | Med | 2–3 weeks | Pending |
| **Web UI / Analytics Dash.** | Low | 4–6 weeks | Backlog |
| **Multimodal Support** | Low | 6–8 Wochen | Backlog |

---

**Last Updated:** 2026-04-23 **Version:** 3.5.7 (SSoT Token-Budget, Gemini-2.5 Reasoning-Fix, Judge-Verbosity-Penalty, Refusal-Metadaten) **Nächster Meilenstein:** Re-Run Gemini 2.5 Flash (UX Writing, Documentation Quality) / Leaderboard-Update
