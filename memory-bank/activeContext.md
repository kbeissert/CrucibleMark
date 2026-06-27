## SESSION START INSTRUCTIONS

On every new session, read these files in this order:
1. `memory-bank/activeContext.md`  — current focus and open questions
2. `memory-bank/progress.md`       — what is done, what is blocked
3. `memory-bank/systemPatterns.md` — architecture, stack, patterns

Do NOT auto-read reference files. Only load a reference file when the current
task explicitly requires it. Check `memory-bank/reference/_index.md`
to know what reference files exist.

---

# Active Context
## Aktueller Status (2026-06-26)

- **Session 38 abgeschlossen (2026-06-26) — Card-Wrapper-Fix + Vendor-Card-Cleanup + WebExport Defense-in-Depth (v4.10.11):**

1i. **Skeptischer Audit + Atomic-Writes-Fix (Folge-Audit 9, 2026-06-26 14:20):**
      - User-Anweisung: "schau dir mal den Webexport an unter skeptischen Gesichtspunkten? Decke Schwaechen auf."
      - Systematischer Audit in 10 Dimensionen: Architektur, Error Handling, Logging, Tests, Code-Duplikation, Atomic Writes, Type Hints, SSoT-Normalisierung.
      - **Befunde priorisiert:**
        - Hoch: Atomic Writes fehlten (8× `open(..., "w")` → korrupte Files bei Crash)
        - Hoch: provider_landscape_review.md Pfad: docs/reviews/ statt docs/comparisons/ + silent skip → 2,5-Monate-Drift
        - Mittel: Silent-Pass-Logging (4× `except ... pass` → Failures verschluckt)
        - Niedrig: Test-Coverage (0/16 Helper-Funktionen), Type-Hints unvollstaendig, `_BLACKLIST_PATH` hardcoded
      - **Fixes:**
        - `_atomic_write_json()` Helper eingefuehrt mit Temp-File + os.replace (POSIX-Atomic). 8/8 Schreibstellen ersetzt.
        - `_collect_vendor_cards()` mit Defense-in-Depth (Placeholder + unknown=true Filter + exclude_community Parameter).
        - `_PLACEHOLDER_VENDOR_IDS` Konstante wiederhergestellt (ging durch git checkout verloren).
        - `_is_blacklisted()` mit `_safe_name()`-Normalisierung wiederhergestellt (12/34 Blacklist-Eintraege matchten vorher nicht).
        - `LdbCols` + `scores`-Dict um 3 fehlende Score-Spalten ergaenzt (Synthesis Quality, Tool Execution, Political Bias).
        - 4× `except ... pass` durch `logging.warning/debug` ersetzt.
        - `provider_landscape_review.md` Fallback-Logik: erst docs/comparisons/, dann docs/reviews/, sonst Warning.
      - **Tests:** 9 neue in `tests/test_web_export_atomic_writes.py` (alle gruen).
      - **Verifikation:** 902/902 Python-Tests gruen, Hugo-Build 319 Files / 0 Errors / 0.83s.

  1h. **Detaillierter Export-Audit (Folge-Audit 8, 2026-06-26 14:03):**
  1h. **Detaillierter Export-Audit (Folge-Audit 8, 2026-06-26 14:03):**
      - User-Anweisung: "ganz detailliert ueberpruefen, ob WebExport wirklich alle Daten erfasst".
      - Systematische Inventur: 101 Model Cards (62 Felder), 29 Vendor Cards (24 Felder), 11 Leaderboard-CSVs, 5194 Audit-Logs, 113174 Cost-Log-Zeilen, 495 Dispatch Summaries.
      - **4 echte Luecken identifiziert und gefixt:**
        1. **LdbCols hatte nur 7/10 CSV-Modul-Spalten** — `Synthesis Quality`, `Tool Execution`, `Political Bias` fehlten komplett. Wurden stillschweigend ignoriert. Fix in `scripts/web_export.py:35-75`.
        2. **`provider_cards.json` wurde NICHT geschrieben** — die Liste wurde gebaut, aber das `with open()` Schreiben fehlte. **Fund: In Session 38 (vorhin) wurde die Liste ergaenzt, aber das Schreiben nicht implementiert.** Fix ergaenzt.
        3. **`inference_interfaces` und `privacy_note`** fehlten im Provider-Sub-Set. Wichtige Display-Felder (Hardware/Performance + Datenschutz). Fix ergaenzt in `provider_cards` Dict-Komposition.
        4. **`MODULE_KEYS` im Web-Repo** hatte `tooluse_execution` statt `tool_execution` — die neuen 10 Modul-Scores muessen hier mitfuehren. Fix in `CrucibleMark-Web/src/_data/lib/module-keys.js`.
      - **Tests:** 9 neue in `tests/test_web_export_field_coverage.py` (alle gruen). Tests sichern ab: keine stille CSV-Spalten-Drift, alle 15 Provider-Felder, llama.cpp inference_interfaces, chinese-providers privacy_note, data.json Top-Level-Sections, files.audit_logs gruppiert nach Modul, model_card self-contained.
      - **Verifikation:** 893/893 Python-Tests gruen, Hugo-Build 319 Files / 0 Errors / 0.85s.
      - **Pitfall in `CLAUDE.md` ergaenzt:** "WebExport Score-Spalten-Vollstaendigkeit" — Defense-in-Depth-Test, dass jede CSV-Spalte einen LdbCols-Eintrag hat.

  1g. **Web-Repo Modularisierung (Folge-Audit 7, 2026-06-26 13:53):**
      - User-Frage: Empfehlung zur Modularisierung der dichten `models.11tydata.js` (236 Zeilen).
      - **Analyse:** 4 DRY-Probleme identifiziert (ToolUse-Score-Injection in 3 Loadern, Fleet-Norm in 3 Loadern, Module-Keys in 2 Loadern, Markdown-Sanitizer inline).
      - **Loesung:** `src/_data/lib/` Verzeichnis mit 4 Modulen angelegt:
        - `lib/tooluse-scores.js` — `injectTooluseScores(scores, tuScores)` (SSoT fuer p1/p2/combined Mapping)
        - `lib/fleet-normalize.js` — `collectBounds()`, `computeFleetBounds()`, `parseCoverage()`, `normalizeModel()`, `normalizeAll()`
        - `lib/markdown-sanitizers.js` — `stripReviewHeader()`, `stripErstelltAm()`, `boldHeadingsToH3()`
        - `lib/module-keys.js` — `RADAR_INDICATOR`, `MODULE_KEYS`, Re-Exports von `TOKEN_MODULE_ORDER`/`TOKEN_LABELS`
      - **Loader refactored:** `models.11tydata.js` (236 → 130 Zeilen), `moduleStats.11tydata.js` (136 → 90 Zeilen), `leaderboard.11ty.js` (81 → 92 Zeilen mit extrahierter `loadTooluseForModel()`-Helper-Funktion).
      - **Tests:** 30 neue Lib-Tests in `tests/lib-*.test.js` (ToolUse 9, Fleet 11, Markdown 10). Pure Functions ermoeglichen jetzt isolierte Tests ohne Build-Context.
      - **Verifikation:** Hugo-Build 319 Files / 0 Errors / 0.70s. **Bit-identische _site/-Output** (`diff -r` ist leer) — Refactoring ohne semantische Aenderung.

  1f. **Provider-Display-Pipeline (Folge-Audit 6, 2026-06-26 13:42):**
      - User-Anweisung: Provider-Infos auf Webseite darstellbar machen. "Export-Definition uebernehmen, Import im Web-Repo anpassen."
      - **Loesung:** Python-Export schreibt `provider_cards.json` mit gefiltertem Provider-Sub-Set der Vendor-Cards (display-relevante Felder). Vendor-Cards bleiben separat fuer vollstaendige Daten.
      - **Schema-Felder** in `provider_cards.json`: vendor_id, display_name, company, headquarters, founding_year, description, deployment (Dict mit GDPR/Cloud-Act/Sovereign-Risk-Metadaten), pricing_model, api_base_url, api_documentation_url, notable_models, profile_verified, last_verified_at. **Kein** Stats/Profile-Metadaten-Leak (Defense-in-Depth: bekannte Felder explizit ausschliessen).
      - **Web-Repo:** `providerCards.11tydata.js` liest die neue Datei, filtert Placeholder (`todo`/`unknown`) + `unknown=true`, mergt `provider_stats.json` falls vorhanden. `vendorCards.11tydata.js` aktiviert. Beide Loader in `.eleventy.js` als Global-Data registriert, passthrough zu `_site/data/`.
      - **Tests:** 10 neue in `tests/test_web_export_provider_cards.py` (Schema, Pflichtfelder, Filter, Metadata-Leak-Check, Taxonomy-Cross-Check). Alle gruen.
      - **Build:** 319 Files, 0 Errors, 0.76s. `_site/data/` enthaelt jetzt 5 Files (leaderboard, political_compass, provider_cards, vendor_cards, community_cards).

  1e. **WebExport-Verifikation (Folge-Audit 5, 2026-06-26 13:38):**
      - User-Anweisung: Pruefen ob WebExport-Skip und Datenbefuellung der erneuerten Architektur entspricht.
      - Frischer `make web-export-dev` Lauf erzeugt 75 Modelle (vorher 76 — DeepSeek V3.1 jetzt korrekt geblacklistet nach Normalisierungs-Fix).
      - **meta.json: skipped_in_run=23 / total_entries=23** (100% Blacklist-Effektivitaet, vorher 12 stille Tote).
      - **Echte Probleme identifiziert:**
        1. `provider_cards.json` war 18 Tage alt (2026-06-08), vom Python-Export nie regeneriert. Enthielt tote/alte Eintraege (alibaba_cloud, nous_research, todo, unknown, Fine-Tune-Slugs). **Fix:** Datei aus raw/ geloescht (Backup in `.bak_web_export_20260626/`).
        2. `providerCards.11tydata.js` und `vendorCards.11tydata.js` sind Dead Code im Web-Repo — nicht in `.eleventy.js` registriert, nicht in Templates referenziert. 11ty laedt sie aber automatisch (alle `*.11tydata.js`), `providerCards` hat ohne `provider_cards.json` gecrasht. **Fix:** `providerCards.11tydata.js` mit `fs.existsSync()`-Check + leeres Result als Defense-in-Depth.
      - **Architektur-konform:** models.11tydata.js synthetisiert `synthesis_quality`/`tooluse_execution` aus `tooluse.scores.p1/p2` zur Laufzeit — kein WebExport-Bug. `LdbCols` enthaelt diese Spalten nicht im CSV-Mapping, aber der Loader fuegt sie korrekt hinzu.
      - **Hugo-Build:** 319 Files, 0 Errors, 0.77s. Alle Loader laufen sauber, kein Crash mehr.

  1d. **Cleanup-Architektur-Audit (Folge-Audit 4, 2026-06-26 13:02):**
      - User-Anweisung: "make clean-model" auf Vollstaendigkeit pruefen — alle Dateien/Datenbankeintraege beim Loeschen eines Modells erfasst?
      - **Architektur-Analyse ergab 6 Luecken:** (1) Sub-Family-LBs (gemma/qwen/provider) nicht in CLEAN_CSV_FILES, (2) `outputs/runs/dispatch_summaries/political_compass_<model>.json` nie bereinigt, (3) `outputs/runs/dispatch_summaries/tooluse_<model>.json` nie bereinigt, (4) `outputs/runs/dispatch_summaries/score_<module>_<model>.json` nie bereinigt, (5) `benchmark_scores/model_cards/_index.json` und `vendor_cards/_index.json` nicht rebuildet nach Card-Loeschung, (6) `outputs/web_export_check/` nirgendwo referenziert.
      - **Fixes:**
        - `SUB_FAMILY_LEADERBOARD_CSVS` Konstante in `clean_results.py` (3 neue Pfade)
        - `tooluse_leaderboard.csv` zu LEADERBOARD_CSVS hinzugefuegt (vorher nur bei `--module tooluse`)
        - `_extract_model_from_dispatch_summary()` Helper mit Module-Key + Provider-Key Whitelist (korrekte Behandlung von `score_cultural_intelligence_*`, `score_cli_benchmark_anthropic_*`, etc.)
        - `clean_model_output_directories()` erweitert: `outputs/runs/results_*.json` + `outputs/runs/dispatch_summaries/*`
        - Card-Index-Rebuild via `rebuild_card_index("model")` + `rebuild_provider_index()` nach Card-Loeschung
        - `outputs/web_export_check/` in `clean --cache` integriert
      - **Tests:** 13 neue in `tests/test_clean_results_arch_coverage.py` (alle gruen).
      - **Pitfall in `CLAUDE.md` ergaenzt:** "Cleanup-Architektur-Vollstaendigkeit `clean_results.py --model` (ab v4.10.11)" mit allen Pfaden.

  1c. **Historische-Überbleibsel-Cleanup (Folge-Audit 3, 2026-06-26 12:54):**
      - User-Anweisung: alle nicht-mehr-referenzierten Artefakte entfernen.
      - **Blacklist aufgeräumt:** 10 tote Eintraege entfernt (Tippfehler + nicht-existierende Modelle). **Blacklist-Effektivitaet jetzt 100%** (vorher 65%, dann 68%).
      - **Drift-Review bereinigt:** 2 narrative ToolUse-Reviews in `qwen3-coder-30b-a3b-q8/` (kein LB-Eintrag in `tooluse_leaderboard.csv`) geloescht. Backup in `.bak_pre8_narrative/`.
      - **Backup-Dirs entfernt:** `.bak_nested_lists_20260626/` (68 Cards, 312K) + `.bak_vendor_card_cleanup_20260626/` (7 Vendor-Cards, 28K).
      - **Alte web_export/-Datenstruktur entfernt:** v3.1.0 (Maerz 2026, 51 Modelle, 1.3M) — wird nicht mehr verwendet, aktueller Export laeuft nach `CrucibleMark-Web/src/_data/raw/`.
      - **73 PC-Run-Files entfernt:** `outputs/runs/results_*.json` fuer nicht-mehr-existierende Modelle (z.B. `codestral-2405`, `gemini-3.1-flash-lite-preview`, `gpt-5.4-nano`, `mock-test-model`, etc.).
      - **5 Pre-Cleanup-Backups entfernt:** `.bak_token_cleanup_20260622` (3x ~12M), `.bak_hermes_merge`, `.bak_pre_cleanup`.
      - **Konsistenz-Check:** 0 Drift (vorher 7 Review-Dirs).
      - **Tests:** 858/861 gruen (3 pre-existing Failures unveraendert). 39 neue Tests in dieser Session.

  1b. **DeepSeek-V3.1-Drift-Analyse + Architektur-Reparatur (Folge-Audit 2, 2026-06-26 12:44):**
      - User-Audit: DeepSeek V3.1 hat Tool-Use-Daten im Web-Export, aber keine Audit-Logs und steht in der Blacklist (matcht aber nicht) — drei zusammenhängende Architektur-Bugs.
      - **Bug 1: Blacklist-Normalisierung.** `_is_blacklist()` verglich rohe `raw_model_id` (z.B. `deepseek/deepseek-chat-v3.1`) gegen Blacklist-Einträge in Underscore-Form (`deepseek_deepseek-chat-v3_1`). 12/34 Einträge (~35%) matchten nicht. **Fix:** `_is_blacklist()` normalisiert BEIDE Seiten via `_safe_name()` und prüft Wildcards in beiden Formen.
      - **Bug 2: Tool-Use-Daten kommen aus 2 Quellen.** `_build_tooluse_entry()` nutzt `tooluse_leaderboard.csv` (aggregiert) + narrative Reviews (Per-Asset-Details) — Audit-Logs sind NICHT erforderlich. Das ist gute Resilience, aber schlechte Auditierbarkeit.
      - **Bug 3: Sanitize-Cleanup war unvollständig.** `sanitize_8_models_tooluse.py` hat nur Card + Audit-Files + Leaderboard-Rows bereinigt, NICHT die narrativen Reviews → Reviews zeigen auf entfernte LB-Werte. **Fix:** Schritt 4 (narrative Reviews mit Backup) + Schritt 5 (Konsistenz-Check) ergänzt. Check scannt ALLE Review-Dirs gegen LB-Einträge.
      - **Discovery durch Konsistenz-Check:** 7 echte Drifts identifiziert (1× `qwen3-coder-30b-a3b-q8/` ohne LB-Eintrag, 6× `gpt-5*` mit Version-Suffix-Mismatch). Diese müssen manuell vom User bereinigt werden.
      - **Tests:** 11 neue in `tests/test_web_export_blacklist_normalization.py`, 4 neue in `tests/test_sanitize_tooluse_consistency.py` (alle grün).
      - **Pitfalls:** 2 neue in `CLAUDE.md` (`WebExport Blacklist-ID-Normalisierung` + `Tool-Use-Cleanup-Atomaritaet`).

  1a. **Vendor-Card-Drift Detection (Folge-Audit, 2026-06-26 01:43):**
      - User-Audit fand: 13 Qwen-Modelle mit `vendor_card_ref: "alibaba"` zeigen im Web-Loader ins Leere, weil dort eine legacy `alibaba → alibaba_cloud` Alias-Map existiert und `alibaba_cloud.json` in dieser Session gelöscht wurde.
      - **Root Cause:** Python exportiert sauber `vendor_card_ref` aus der Taxonomie-SSoT; das Problem ist nur die veraltete Alias-Map im Web-Repo (`vendorCards.11tydata.js:24-29`).
      - **Fix (Python-Defense-in-Depth):** `_init_export_context()` in `scripts/web_export.py` sammelt `existing_vendor_card_ids` einmalig und loggt WARN wenn Taxonomie-IDs auf fehlende Vendor-Card-Dateien verweisen. `_process_leaderboard()` ergänzt Per-Modell-WARN bei Drift.
      - **Web-Loader-Fix:** Als dokumentierter Snippet in `progress.md` für Copy-Paste ins Web-Repo dokumentiert (out of scope Python-Repo).
      - **Tests:** 3/3 neue Tests in `tests/test_web_export_vendor_drift.py` grün.

  1. **Root-Cause `generate_review.py:545` Crash:**

  1. **Root-Cause `generate_review.py:545` Crash:**
     - `get_model_card_context()` (`scripts/analysis/review/metrics.py`) rief `", ".join(card["strengths"])` auf 68 Model Cards mit verschachtelten Listen `[["a", "b"]]` statt flacher Liste `["a", "b"]` → TypeError, Run crashte bei Modell 36/109 (`gpt-5-2025-08-07`).
     - **Fix 1 (Cards):** 68 Model Cards geflattet. Backup in `.bak_nested_lists_20260626/`.
     - **Fix 2 (Defense-in-Depth):** Neuer Modul-Level-Helper `_flatten_strings()` in `metrics.py` (akzeptiert flach + 1 Wrapper-Schicht, filtert Nicht-Strings). `get_model_card_context` nutzt ihn.
     - **Fix 3 (Vendor-Feld):** 2 Cards (`openai_gpt-oss-120b`, `openai_gpt-oss-20b`) hatten `vendor: "Groq"` → `"OpenAI"` (Groq ist Hosting, OpenAI ist Hersteller).
     - **Verifikation:** 11/11 neue Tests in `tests/test_review_metrics_flatten.py` grün.

  2. **Vendor-Card-Cleanup + WebExport Defense-in-Depth:**
     - **7 Files gelöscht** (Backup `.bak_vendor_card_cleanup_20260626/`): `todo.json`, `unknown.json`, `nous_research.json`, `z_ai_formerly_zhipu_ai.json`, `zhipu_ai_z_ai.json`, `alibaba_cloud.json`, `alibaba_group_qwen_team.json`.
     - **7 Fine-Tune-Cards** als `card_subtype: "community"` markiert (3× google_deepmind_* Fine-Tune/Quant + 1× alibaba HauhauCS + 2× alibaba jackrong/Kyle Hessling).
     - **`scripts/web_export.py` `_collect_vendor_cards`:** Neuer Parameter `exclude_community` (default False). Neue Konstante `_PLACEHOLDER_VENDOR_IDS = {"todo", "unknown"}` filtert Placeholder-Karten unabhängig vom `unknown`-Flag.
     - **`_write_top_level_outputs`:** Schreibt `vendor_cards.json` jetzt mit `exclude_community=True` → Community-Karten landen nur noch in `community_cards.json`.
     - **`_index.json` rebuilt** via `rebuild_provider_index()` → 29 Entries (vorher 35).
     - **10/10 neue Tests** in `tests/test_web_export_vendor_filter.py` grün.

  3. **Inventur nach Cleanup:**
     - Total Vendor-Cards: 35 → 29 (−6)
     - Hersteller-Karten: 17 (unverändert)
     - Community-Karten: 4 → 12 (+8)
     - Placeholder (`todo`/`unknown`): 2 → 0
     - `unknown=true`: 2 → 1 (verbleibend: `ara_apex_quant` — als Community markiert, daher explizit gewollt)

  4. **Pitfall in `CLAUDE.md` ergänzt:** "Card-Editor-Wrapper-Schicht" + "WebExport Vendor-Dedup Defense-in-Depth" als wiedererkennbare Failure-Modes dokumentiert.

  5. **Offene Backlog-Items (aus User-Audit-Bericht):**
     - **Pre-existing Test-Failures (nicht durch Session 38 verursacht):**
       - `test_card_vocabulary_ssot.py::test_all_model_cards_pass_tag_whitelist`
       - `test_sampling_defaults_ssot.py::test_all_cards_have_sampling_keys`
       - `test_taxonomy_ssot.py::test_no_forbidden_placeholder_in_taxonomy_fields` — `gpt-5_5-pro.json: weights_license_tier='TODO'`
     - **Vendor-Card-Taxonomie-Gap:** `cohere`, `google`, `llamacpp` haben Vendor-Cards ohne Eintrag in `classification_taxonomy.json → manufacturers.values`. Sollte ergänzt werden (z.B. `CLOUD` als Kategorie oder Erweiterung).
     - **Web-Repo-LB-ToolUse-Fallback:** User-Hinweis: Falls `leaderboard.11tydata.js` weiterhin `tooluse_score`/`tooluse_rating` exposed, muss es aus `data.json.tooluse.scores` ergänzt werden (anderes Repo, out of scope).

## Aktueller Status (2026-06-24)

- **Session 35 abgeschlossen (2026-06-24) — Benchmark-Maintenance + ToolUse Aggregator Fix:**

  1. **Standby-Einträge entfernt:** Computer ging in Standby während Benchmark-Lauf. 2 CSV-Einträge aus `commercial_models_benchmark.csv` entfernt:
     - `gpt-5-2025-08-07` / `content_transformation_003` (Connection error, 1107.9s, 0.0%)
     - `gemini-3.1-pro-preview` / `code_quality_002` (0.0%, 337 Tokens, Judge 0.0/5)
     - CSV-Validierung: 110 Spalten, 0 Spaltenfehler, Modellcounts konsistent

  2. **Model Card Updates:**
     - `openai_gpt-oss-20b.json`: `supports_tool_use: true → false` (Modell kann keine Tools nutzen)
     - `openai_gpt-oss-120b.json`: `supports_tool_use` bleibt `true` (51% ToolUse-Score, Grenzfall)

  3. **ToolUse Aggregator Bug (P1/P2 leer, Combined befüllt):**
     - **Root Cause:** `_aggregate_asset_rows()` in `tooluse_exporter.py` hatte `total_score`-Fallback nur für `combined_score` (Zeile 499), nicht für `p1_score`/`p2_score`. Lokale Modelle (llamacpp_spark) schreiben nur `total_score` in die CSV, keine separaten P1/P2-Spalten.
     - **Fix:** Per-Zeile `total_score`-Fallback für P1 und P2 ergänzt. Nutzt `_p1_found`/`_p2_found`-Flags statt globaler Listen-Leer-Prüfung.
     - 68/68 ToolUse-Tests grün.

  4. **GPT-OSS 20B Thinking-Modell-Analyse:** 17200 Tokens, 0.0%, Judge 0.0/5. Modell produzierte ausschließlich Reasoning-Tokens ohne sichtbaren Content-Output. Token-Budget-Erhöhung würde nichts ändern — Modellversagen auf Groq.

## Aktueller Status (2026-06-23)

- **Session 34 abgeschlossen (2026-06-23) — Cohere Native ToolUse Connector + command-a-plus-05-2026 supports_tool_use=false (v4.10.8):**

  1. **Auslöser:** Cohere ToolUse-Benchmark für alle 3 Cohere-Modelle (command-a-03-2025, command-a-plus-05-2026, command-a-reasoning-08-2025) lieferte keine live-Ergebnisse. Prompt-basierte JSON-Tool-Schemas kollidierten mit Cohere's Reasoning-Logik → HTTP 422/500.

  2. **Root Cause:** Prompt-basierte Tool-Schemas im System-Prompt verursachten bei Cohere-Reasoning-Modellen (command-a-plus, command-a-reasoning) einen 422-Fehler (`Thinking.type` fehlte). `command-a-plus` bekam zusätzlich persistente 500-Fehler bei nativen Tool-Calls mit komplexeren System-Prompts (Benchmark-Szenarien) — einfache Prompts funktionierten.

  3. **Lösung: Cohere-nativer `tools`-Parameter (v4.10.8):**
     - `utils/providers/cohere.py` komplett überarbeitet: Extrahiert Tool-Schema aus dem ToolUse-System-Prompt (`_extract_tool_schema()`), konvertiert zu Cohere-nativem `tools`-Format (`_schema_to_cohere_tools()`), extrahiert Tool-Calls aus der nativen Response (`_format_tool_calls_as_text()`).
     - `_module_key == "tooluse"` triggert den nativen Pfad; andere Module bleiben prompt-basiert.
     - Reasoning-Modelle: `thinking: {"type": "disabled"}` wird gesetzt wenn Native Tools + Reasoning-Modell → verhindert 422 durch auto-thinking.
     - 500-Retry: 2 Retries mit exponentiellem Backoff (2s, 4s).

  4. **Ergebnisse nach Fix:**
     - `command-a-03-2025`: **4/6 live**, P1=85.0, P2=50.0, Combined=43.3 (2× NO_TOOL_CALL 422 auf fetch-Assets — intermittierend)
     - `command-a-plus-05-2026`: **0/6 mock** (persistente 500 mit Benchmark-System-Prompt, nicht behebbar clientseitig)
     - `command-a-reasoning-08-2025`: **6/6 live**, P1=90.0, P2=51.7, Combined=70.5 (Halluzination=YES)

  5. **Model-Card-Änderung:** `command-a-plus-05-2026.json`: `supports_tool_use` auf `false` gesetzt + `known_limitations`-Eintrag ergänzt.

  6. **Systematische API-Tests:** Simple Prompts → alle 3 Modelle OK. Kompletter Benchmark-System-Prompt + Native Tools → nur `command-a-plus-05-2026` scheitert mit persistenten 500s. `thinking: disabled` half nicht. Cohere-Statuspage zeigt 100% Uptime (infra-level, nicht modell-spezifisch). `command-a-plus` ist Cohere's erstes MoE-Modell (218B/25B aktiv) — 500s deuten auf unreife serverseitige Tool-Use-Routing-Logik bei komplexen Prompts hin.

  7. **Dokumentation:** CHANGELOG v4.10.8, CLAUDE.md (Cohere Pitfalls), ARCHITECTURE.md (Cohere in Provider-Tabelle), DEVELOPER_GUIDE.md (Cohere-Connector-Sektion), Memory Bank.

## Aktueller Status (2026-06-22)

- **Session 33 abgeschlossen (2026-06-22) — clean-results Variant-Handling + _rebuild_index Fix + Dead-Model grok-4.1-fast-reasoning Cleanup (v4.10.7):**

  1. **Auslöser:** `make clean-model MODEL=grok-4.1-fast-reasoning` bereinigte nur EINE von 3 ID-Varianten. Orphan-Cards, CSV-Zeilen, cost_log-Einträge und Review/Audit-Dirs blieben übrig.

  2. **Root Cause:** `clean_results.py` nutzte nur `_safe_name()` (Punkte→Unterstriche) für die Variant-Auflösung. Drei Schreibweisen existierten parallel: `grok-4_1-fast-reasoning` (Underscore), `grok-4-1-fast-reasoning` (Hyphen, provider_config), `grok-4.1-fast-reasoning` (Dot, API-ID).

  3. **5 Fixes in `clean_results.py`:**
     - **Fix 1 (`clean_model_card`):** Findet und löscht ALLE Card-Varianten (Dateiname + `_find_card` + Glob + Inhalt-Scan)
     - **Fix 2 (`clean_csv`):** Matched alle ID-Varianten in CSV-Spalten (`model`, `Model ID`, `model_id_raw`)
     - **Fix 3 (Reihenfolge):** CSVs werden VOR Cards bereinigt (Card wird für `resolve_canonical_model_id()` gebraucht)
     - **Fix 4 (`clean_model_output_directories`):** Variant-aware für audit_logs, comparisons, runs, reviews
     - **Fix 5 (neue Funktionen):** `clean_cost_log()`, `_dead_model_info()`, `LEADERBOARD_CSVS`-Konstante

  4. **Neue SSoT-Funktion `_collect_model_id_variants()`:** Sammelt ALLE Schreibweisen einer Model-ID über `_safe_name()` + Card-Inhalt-Scan.

  5. **`clean.py`:** `--dry-run` Argument ergänzt (fehlte in argparse, wurde aber vom Makefile erwartet).

  6. **`generate_review.py`:** Verwaister `mc_gen._rebuild_index()`-Aufruf + unbenutzter Import entfernt (Zeile 197-200). Crash bei `reviews-auto` Lauf Modell 54/118.

  7. **Dead-Model grok-4.1-fast-reasoning bereinigt:** 49 CSV-Zeilen, 256 cost_log-Einträge, 6 Leaderboard-Einträge, 1 Card, 1 Audit-Log-Dir, 1 Review-Dir.

  8. **Verifikation:** 10/10 clean_results-Tests grün, keine False Positives bei anderen Modellen (Test mit `claude-sonnet-4-5`), Lint ohne neue Warnungen.

## Aktueller Status (2026-06-22)

- **Session 32 abgeschlossen (2026-06-22) — Dead-Model-Cleanup (xAI):**

  1. **Auslöser:** Nach dem ID-Mismatch-Fix (Session 31) weiterhin `Model not found` für `grok-4.1-fast-reasoning`. XAI-API-Check via `/v1/models` ergab: 4 von 7 xAI-Modellen nicht mehr erreichbar.

  2. **Betroffene Modelle:**
     - `grok-4-1-fast-reasoning` ❌ API: Model not found
     - `grok-4-fast-non-reasoning` ❌ API: Model not found
     - `grok-3` ❌ API: Model not found
     - `grok-3-mini` ❌ API: Model not found
     - `grok-4.20-0309-reasoning` ✅, `grok-4.20-0309-non-reasoning` ✅, `grok-4.3` ✅

  3. **Änderungen:**
     - `provider_config.yaml`: 4 tote Modelle auskommentiert (mit `# ❌ XAI API: Model not found (entfernt 2026-06)`)
     - `web_export_blacklist.yaml`: 3 neue Einträge (`grok-4-fast-non-reasoning`, `grok-3`, `grok-3-mini`) — `grok-4-1-fast-reasoning` war bereits vorhanden
     - Workflow-Regel in `CLAUDE.md` dokumentiert: Dead-Model-Handling — erst API prüfen, dann User fragen, dann auskommentieren + blacklisten

  4. **Neuer Workflow (in CLAUDE.md):** Bei `Model not found` / HTTP 400: (1) Alle Provider-Modelle gegen API prüfen, (2) User fragen ob auskommentieren, (3) Blacklist ergänzen, (4) CSV-Cleanup. NIEMALS eigenständig auskommentieren.

- **Session 31 abgeschlossen (2026-06-22) — grok-4.1-fast-reasoning Model-ID-Mismatch Fix:**

  1. **Root Cause:** `_find_card()` konnte die Card `grok-4-1-fast-reasoning.json` nicht finden, wenn die Eingabe `grok-4.1-fast-reasoning` (Punkte) war. `_safe_name()` konvertiert Punkte→Unterstriche (`grok-4_1-fast-reasoning`), aber die Card-Datei benutzt Bindestriche (`grok-4-1-fast-reasoning.json`). Dazu fehlte der Eintrag `grok-4_1-fast-reasoning` → `grok-4.1-fast-reasoning` in `_XAI_ID_ALIASES`.

  2. **3 Fixes implementiert:**
     - **Gelöscht:** Broken Placeholder-Card `grok-4_1-fast-reasoning.json` (falsches `model_id: "grok-4_1-fast-reasoning"`)
     - **`utils/model_utils.py` `_find_card()`:** Dot→Hyphen-Fallback hinzugefügt. Wenn die `_safe_name`-basierte Lookup fehlschlägt und die Eingabe Punkte enthält, wird die Variante mit Bindestrichen probiert.
     - **`utils/providers/xai.py` `_XAI_ID_ALIASES`:** `"grok-4_1-fast-reasoning": "grok-4.1-fast-reasoning"` als Defense-in-Depth ergänzt.

  3. **CSV-Cleanup:** 4 broken Einträge (`grok-4_1-fast-reasoning`, alle 0.0 Scores) aus `commercial_models_benchmark.csv` entfernt.

  4. **Verifikation:** `resolve_canonical_model_id("grok-4.1-fast-reasoning")` → `"grok-4.1-fast-reasoning"` (korrekte API-ID). 82 card/canonical/normalize Tests grün.

  5. **Hintergrund:** `provider_config.yaml` hat `grok-4-1-fast-reasoning` (Bindestriche), Card hat `model_id: "grok-4.1-fast-reasoning"` (Punkte = tatsächliche XAI-API-ID). Historisch funktionierte der Aufruf über den provider_config-Eintrag (Bindestriche), aber der direkte Aufruf mit API-ID (Punkte) schlug fehl.

## Aktueller Status (2026-06-22)

- **Session 30 abgeschlossen (2026-06-22) — Token-Limit-Audit + Anthropic Provider-Cap + Benchmark-Cleanup (v4.10.6):**

  1. **Token-Limit-Audit aller Provider:**
     - Systematische Analyse aller 5 API-Provider (OpenAI, Anthropic, Google, xAI, Mistral) auf Token-Limit-Probleme
     - 27 Modelle identifiziert mit verfälschten Benchmark-Ergebnissen
     - 2 Kategorien: MAX_TOKENS-Truncation (24 Zeilen, 5 Modelle) + CI@500-Artefakt (130 Zeilen, 26 Modelle)
     - Gemini 3.5 Flash: 9 MAX_TOKENS (schlimmster Fall) — CI×5 + CT×2 + UX×1 + CQ×1
     - Gemini 2.5 Flash: 7 MAX_TOKENS durch Thinking-Overhead (sichtbare Tokens 735–2436 bei Limit 8000–12000)
     - Alle 6 Claude-Modelle: CI bei 500 Tokens (nie nachgetestet, altes Budget)
     - Alle 7 Grok-Modelle: CI bei 500 Tokens

  2. **Config-Änderung (v4.10.6):**
     - `provider_config.yaml`: Anthropic `max_tokens` 8192 → 32768
     - Per-Model Override `claude-haiku-4-5-20251001: 8192` (Desktop-Klasse)
     - `fallback_max_tokens: 4096` entfernt (Dead Config — nirgends gelesen)

  3. **Benchmark-Cleanup:**
     - 144 Zeilen aus `commercial_models_benchmark.csv` entfernt
     - Backup: `.bak_token_cleanup_20260622`
     - Leaderboard aktualisiert: 27 Modelle mit fehlenden Tasks (34/43 bis 38/43)
     - CI-Scores auf "Pending" — werden beim nächsten `benchmark_auto` automatisch nachgetestet

  4. **Dokumentation:** CHANGELOG v4.10.6, README Version Badge + Recent Versions, PROJECT_STATUS, REF_TODO, CLAUDE.md (2 neue Pitfalls: Anthropic Cap + CI@500-Artefakt), Memory Bank

  5. **Design-Erkenntnisse (Session 30):**
     - `max_tokens` sollte Sicherheitsnetz sein (32K+), nicht Bremse
     - Längensteuerung über Judge (Verbosity Penalty + Golden Standard), nicht über API-Cap
     - Keine Prompt-Änderung nötig — bestehende Aufgaben beibehalten
     - Anthropic Extended Thinking (`thinking.budget_tokens`) noch nicht genutzt — separates Thinking-Budget möglich
     - `fallback_max_tokens` war Dead Config seit mindestens v4.10.3

## Aktueller Status (2026-06-21)

- **Session 29 abgeschlossen (2026-06-21) — CSV-Write-Through Bug + Provider-Connector SSoT + Judge Token Usage + Provider-Config-Cleanup:**

  1. **CSV-Write-Through Bug (v4.10.4) — 3 Root Causes behoben:**
     - `_write_to_csv()` öffnete mit `"w"` (truncate) → bei Kill/Crash gingen ALLE CSV-Daten verloren
     - Fix: Atomare Schreibvorgänge via `tempfile.mkstemp()` + `os.replace()`
     - Bestehende Zeilen werden beim Full-Rewrite NICHT re-validiert (nur neue Zeilen → Hard-Fail-Guard)
     - `_csv_header_matches()` exakter Vergleich beibehalten (korrekt für Append-Path)

  2. **10 Modelle mit 0 CSV-Einträgen identifiziert:**
     - llama-3.3-70b-versatile, llama-4-scout, nemotron-3-ultra, qwen3-32b, qwen3.5-397b, glm-4.7, glm-5-20260211, glm-5-turbo, glm-5.1, glm-5.2
     - Dispatch summaries + audit logs vorhanden, CSV aber leer → Root Cause war Full-Rewrite-Überschreibung
     - Re-Run oder `sanitize_benchmark_csvs.py`-Rekonstruktion möglich

  3. **Provider-Connector SSoT (v4.10.5):**
     - 3 Reasoning/Thinking-Extraktions-Utilities in `utils/providers/base.py`:
       - `_extract_reasoning_tokens(usage)` — provider-agnostisch (completion_tokens_details → output_tokens_details → reasoning_tokens)
       - `_extract_think_from_message(msg, field_names)` — generisch
       - `ThinkAccumulator` — Streaming-Helper (ersetzt `think_parts: list[str]`)
     - 9 Provider migriert (openai, anthropic, groq, xai, openrouter, google, mistral, ollama, llamacpp_base)
     - Streaming-Bugs gefixt: OpenRouter fehlte `reasoning_tokens`, llamacpp_base fehlte beides

  4. **Judge Token Usage Context (v4.10.5):**
     - LLM-Judge erhält universelle Token-Verbrauchsinformation für JEDE Aufgabe:
       `tokens_used`, `reasoning_tokens`, `token_budget`, `module_budget`, `truncated`
     - Neue `### TOKEN USAGE ###` Section im Judge-System-Prompt
     - Judge kann Budget-Compliance, Reasoning-Overhead, Resource Discipline bewerten

  5. **Abbruchverhalten analysiert:**
     - `deepseek/deepseek-chat-v3.1` bei 13:33 mid-`content_transformation` abgebrochen
     - Write-Through funktionierte korrekt: 34/43 Tasks in CSV

  6. **Provider-Config Cleanup:**
     - `provider_config.yaml`: 768→638 Zeilen (−17%), redundante Kommentare entfernt
     - 92 aktive Modelle + alle auskommentierten Modelle erhalten

  7. **Tests:** 822/822 grün (4 neue Tests für atomare Writes + Existing-Row-Schutz, 1 pre-existing deselect)

  8. **Dokumentation:** CHANGELOG v4.10.3/v4.10.4/v4.10.5, README Version Badge + Recent Versions, CLAUDE.md (Provider-Connector SSoT Pitfall + 2 CSV Pitfalls)

- **Session 28 abgeschlossen (2026-06-21) — Token-Budget-Refactoring + Design-Constraints + CSV-Gap-Analyse:**

  1. **Design-Constraints dokumentiert** (`systemPatterns.md`, `CLAUDE.md`):
     - Sequenzielle Modell-Abarbeitung (Server-Restart + Cooldown) — KEIN Performance-Bug
     - Judge-Reset zwischen Tasks (kein Caching) — verhindert Kontextmix
     - Keine Cross-Run-Pollution (Stateless Runs)

  2. **Token-Budget-Refactoring — SSoT `_resolve_request_tokens()` in `base.py`:**
     - **Alle 7 API-Provider** nutzen jetzt einen Shared Helper statt inline duplizierter Token-Logik
     - **Zweistufige Provider-Kaskade:** Provider-Default `max_tokens` → Per-Model Override `model_max_tokens`
     - **Provider ohne Budget (anthropic, groq, xai, google)** bekommen jetzt korrekte Reasoning-Budgets
     - **Duplikat-Code eliminiert:** ~30 Zeilen in groq.py + xai.py (Copy-Paste), ~60 Zeilen inline in 7 Providern
     - **Config:** `provider_config.yaml` — 7 Provider mit `max_tokens` Default, OpenRouter mit 7 Per-Model Overrides

  3. **Token-Budget-Optimierung** (`benchmark_config.yaml`):
     - `code_quality` Reasoning: **65536 → 20000** (p99=16382, Reduktion 85→26 Min/Task)
     - `cultural_intelligence` Standard: **1000 → 3000** (Cloud-p90=2893)
     - `documentation_quality` Standard: **6000 → 8000** (Cloud-p90=7789)

  4. **CSV-Gap-Analyse** (9 Modelle mit fehlenden Einträgen):
     - Hermes 4.3 36B: 37/43, Kimi K2.7 Code: 5/43, GLM 4.6: 32/43, Gemma-4 (5 Modelle): 38–42/43
     - DeepSeek V4 Pro: 43/43 ✅ (Analyse-Fehler korrigiert)
     - **Audit-Logs enthalten ALLE Daten** — Tasks wurden ausgeführt, CSV-Write-Through schlug fehl
     - **Aktion:** Re-Run der fehlenden Module (kein Code-Fix nötig)

  5. **Dokumentation:** CHANGELOG v4.10.3, README (Version Badge + Token-Budget-Beschreibung), CLAUDE.md (SSoT-Pitfalls), systemPatterns.md (Design-Constraints + Token-Kaskade-Brücke)

- **Offene Tasks:**
  - Re-Run fehlender Module für 9 Modelle (Hermes 4.3, Kimi K2.7, GLM 4.6, 5× Gemma-4)
  - Re-Run oder Rekonstruktion für 10 Modelle mit 0 CSV-Einträgen (llama-3.3-70b-versatile, llama-4-scout, nemotron-3-ultra, qwen3-32b, qwen3.5-397b, glm-4.7, glm-5-20260211, glm-5-turbo, glm-5.1, glm-5.2)
  - Political Compass für alle 30 Modelle nachholen (deaktiviert im Auto-Benchmark)

---

## Aktueller Status (2026-06-20)

- **Session 27 abgeschlossen (2026-06-20) — Provider-Connector Thinking/Reasoning-Fix + Card-Cleanup:**
  - **Auslöser:** OpenRouter war der einzige Provider, der `reasoning_tokens`/`think_content`/`usage` korrekt in `last_response_metadata` speicherte. Andere Provider (anthropic, openai, google, groq, xai, ollama, mistral) hatten Lücken, was zu:
    - fehlerhafter Judge-Evaluation (Thinking-Aufwand pro Aufgabe nicht messbar)
    - falscher Cost-Analyse (Pipeline fiel auf `estimate_tokens()`-Fallback zurück)
    - verfälschter Benchmark-Qualität (Tokens geschätzt statt gezählt) führte
  - **Alle 7 Provider-Connectors gefixt** (`utils/providers/anthropic.py`, `openai.py`, `google.py`, `groq.py`, `xai.py`, `ollama.py`, `mistral.py`):
    - `reasoning_tokens` extrahiert aus `usage.completion_tokens_details.reasoning_tokens` (OpenAI-kompatibel) / `usage.output_tokens_details.reasoning_tokens` (Anthropic) / `usage_metadata.thoughts_token_count` (Google) / `eval_count` (Ollama, wenn Thinking erkannt)
    - `think_content` extrahiert aus `msg.reasoning`/`delta.reasoning` (OpenAI), `block.thinking`/`thinking_delta` (Anthropic), `part.thinking` (Google), `msg.thinking` (Ollama), `chunk.thinking` (Mistral)
    - `usage` in `last_response_metadata["usage"]` gespeichert (vorher fehlte in google.py und groq.py/xai.py Streaming)
  - **Anthropic Streaming-Pfad komplett neu implementiert** (`_query_streaming()`): akkumuliert `content_block_delta`-Events mit `type="thinking_delta"`, trackt `usage` aus `message_start`/`message_delta` Events.
  - **DRY-Helper `_extract_reasoning_tokens(usage)`** in anthropic.py, openai.py, groq.py, xai.py (4x identisches Pattern).
  - **Mistral `think_content`-Fix:** wurde vorher nur bei leerem Content gesetzt — jetzt immer wenn ThinkChunks vorhanden.
  - **Ollama `usage`-Dict synthetisiert** aus `prompt_eval_count`/`eval_count` (Ollama liefert kein einheitliches `usage`-Objekt).
  - **2 pre-existing Test-Failures behoben:**
    - `test_sampling_defaults_ssot.py`: 3 Model-Cards fehlten Sampling-Keys (`gemma-4-31b-it-creative-wordsmith-q8`, `hermes-4_3-36b-q6`, `mistral-large-2512`) — alle 7 Sampling-Default-Felder als `null` ergänzt.
    - `test_taxonomy_ssot.py`: `gemini-3-flash-preview.json` hatte `parameter_architecture: "unknown"` (verbotener Placeholder) → `"dense"` (gültiger Taxonomie-Wert).
  - **Dokumentation aktualisiert:** `CLAUDE.md` (neuer Pitfall-Eintrag "Provider-Connector Thinking/Reasoning-Extraktion"), `CHANGELOG.md` (neue v4.10.1), `docs/ARCHITECTURE.md` (Provider-Tabelle + "Provider Thinking/Reasoning-Extraktion" Sektion), `docs/DEVELOPER_GUIDE.md` (neue Sektion "Provider-Connector Thinking/Reasoning-Extraktion"), `docs/THINKING_PROBE.md` (Signal-B-Update mit v4.10.1-Verweis).
  - **Verifikation:** 819/819 Tests grün.

- **Session 26 abgeschlossen (2026-06-20) — Spark Token-Management + Bugfixes:**
  - **Root Cause Timeout-Loop:** `qwopus3_6-27b-v2-mtp-q8` auf `llamacpp_spark` produzierte endlose Generierungen weil kein `max_tokens`-Cap gesetzt war. Das Modell generierte bis zum Kontextfenster (65536 Tokens), httpx Read-Timeout (300s) griff nach 5 Min → Retry-Loop.
  - **Per-Model `max_tokens`-Cap implementiert:** `max_tokens: 16384` für beide Qwopus-Modelle in `provider_config.yaml`. Cap-Logik in `llamacpp_base.py:query()` NACH `resolve_token_budget()`: `min(initial_tokens, model_cfg_max_tokens)`.
  - **`read_timeout` konfigurierbar gemacht:** `llamacpp_spark` Provider-Level `read_timeout: 2400` (40 Min statt 5 Min Default). `llamacpp_base.py` liest jetzt `prov_cfg.get("read_timeout", 300.0)`.
  - **`context_length` für alle Spark-Modelle explizit gesetzt:** Qwopus=32768, Qwen3.6/3.5=65536, Gemma-4=65536, Qwen3-Coder=65536. Vorher: nur Hermes und Gemma-4-MTP hatten explizite Werte.
  - **`parallel` 4→2:** Provider-Default von `parallel=4` auf `parallel=2` gesetzt (Benchmark ist sequentiell, spare Slot für Health-Checks reicht). Hermes behält `parallel=1`.
  - **Bugfix `think_content` Key-Mismatch:** `_extract_response_content()` speicherte `"thinking_content"` statt `"think_content"` — `base_runner.py` las aber `"think_content"`. Key einheitlich auf `"think_content"` gesetzt.
  - **Bugfix `reasoning_tokens`-Extraktion:** Wurde nur bei leerem Content gesetzt. Jetzt bevorzugt aus `usage.completion_tokens_details.reasoning_tokens` gelesen (llama.cpp-native), Fallback auf `completion_tokens` nur wenn Content leer.
  - **Dokumentation aktualisiert:** `CLAUDE.md` (3 neue Pitfalls), `docs/ARCHITECTURE.md` (Spark Token-Management), `docs/DEVELOPER_GUIDE.md` (Spark Connector + reasoning_content), `docs/SETUP_GUIDE.md` (Per-Model Token-Management).

- **Session 25 abgeschlossen (2026-06-20) — Card-Research Force-Run + Template-Cleanup:**
  - **110/110 Cards `profile_verified=true`** — vollständiger Force-Run aller Model Cards.
  - **Template-Änderungen (required → optional):** `params_total_b`, `params_active_b`, `knowledge_cutoff`, `license_url`, `input_price_per_1m`, `output_price_per_1m`. Grund: Beschreibungen sagten "null wenn X" aber `required: true` — Widerspruch.
  - **`MAX_CARDS=N`** implementiert: `make card-research MODEL=all MAX_CARDS=10` für Batch-Verarbeitung. Fortschrittsanzeige am Ende.
  - **`MODEL=all`** gefixt: Early-Validation und `_discover_research_targets()` erkennen jetzt `all` als "alle Cards".
  - **`probe_thinking.py`** Path-Bug gefixt: `card_path.relative_to(ROOT_DIR)` Crash bei relativen Pfaden.
  - **Thinking-Probe Platzhalter:** 9 lokale Modelle (Ollama entfernt) → manuell sinnvolle Werte gesetzt basierend auf Modellfamilie (Qwen3 = thinking detected, Gemma 4 = not detected).
  - **Lizenz-String-Konsistenz:** `Apache-2.0` vs `Apache 2.0` — LLM erkennt das als Lizenz-Wechsel und rewrite't alle Textfelder. Führt zu vielen roten Findings aber korrektem Ergebnis.
  - **Parse-Fehler:** 1× `qwen3_5-9b` (LLM lieferte kein valides JSON) → Retry erfolgreich.
  - **Claude `license_url`:** Manuell auf `https://www.anthropic.com/legal/terms` gesetzt für `claude-sonnet-4-5-20250929`.
  - **`thinking_probe_at` Timestamp:** 7 Cards hatten Probe-Ergebnisse aber keinen Timestamp → nachgetragen.
  - **`supports_tool_use`:** `gemma-4-26B-A4B-it-UD-Q8_K_XL` hatte kein `supports_tool_use` → `False` gesetzt.
  - **Dokumentation aktualisiert:** `docs/DEVELOPER_GUIDE.md` (optional-Felder markiert), `docs/ARCHITECTURE.md` (Card-Research Flow + optionale Template-Felder), `CLAUDE.md` (6 neue Pitfalls), `Makefile` (probe-thinking Hilfe).

- **Session 24 abgeschlossen (2026-06-19) — Card-Research MCP Tool-Use + Lizenz-Heuristik + GGUF-Fixes:**
  - `manage_model_cards.py --mode research` kann jetzt über MCP `web_search` + `fetch` im Internet recherchieren.
  - Architektur: JSON-RPC 2.0 HTTP POST zum bestehenden MCP-Server (`:8765`), keine Änderungen am MCP-Server nötig.
  - Neue Funktionen: `_parse_tool_call()`, `_call_mcp_tool()`, `_extract_tool_content()`
  - Neue Methode: `Researcher._research_tooluse_one()` — Multi-Step-Loop (max. 3 Runden)
  - Neue CLI-Flags: `--tooluse` (nur mit `--mode research`), `--mcp-url` (Default: `http://localhost:8765`)
  - Makefile: `TOOLUSE=1` Flag an `card-research` Target
  - Lizenz-Heuristik: `_KNOWN_LICENSE_MAPPINGS` (Gemma/Qwen/Llama), `_KNOWN_COMMUNITY_GROUPS`, `_match_family()`, `_check_license_consistency()`, `_check_community()`, `_check_license_text_fields()` (Pre-Finding), `_check_license_cascade()` (Post-Merge), `_ensure_license_consistency()`
  - GGUF-Fixes: `_is_gguf_model()`, `_ensure_gguf_conventions()` (Post-Apply: deployment_type, params_active_b, Preise)
  - `profile_verified`-Fix: Validiert finale Karte statt Findings-Historie
  - MCP Auto-Lifecycle: `_ensure_mcp_running()` + `_stop_mcp_server()` + `_reset_llama_context()` + `_check_health()`
  - Usage: `make card-research MODEL=gemma-4-12b-it-ud-q8_k_xl TOOLUSE=1` (MCP auto-start/stop)

- **Session 23 abgeschlossen (2026-06-17) — Review-Auto-Fixes + MTP-Modell + 128 GB-Korrektur + (GGUF)-Cleanup:**
  - **Bug 1 (Python 3.14 @dataclass-Crash):** `scripts/analysis/generate_review.py` `_load_card_module()` lud Modul via `module_from_spec` ohne `sys.modules`-Registrierung. Fix: `sys.modules[module_name] = module` VOR `exec_module`. Hintergrund: Python 3.14 `@dataclass` ruft `sys.modules[cls.__module__].__dict__` für KW_ONLY-Detection → NoneType-AttributeError ohne Registrierung.
  - **Bug 2 (`outputs/audit_logs/test/`-Stub):** `test_pipeline_integration.py` instanziiert `UnifiedBenchmarkRunner("test")` und ruft `_process_single_test()` auf. `save_audit_log(model="test", ...)` schreibt real nach `outputs/audit_logs/test/asset_1.md` (mit MagicMock-Content). Fix 1: Test patched jetzt `utils.scoring.judge_evaluator.save_audit_log` in `mock_dependencies`-Fixture. Fix 2 (Defense in Depth): Neue Helper `_is_valid_audit_dir()` in `generate_review.py` mit Zwei-Pfad-Heuristik — entweder (a) Slug-File vorhanden ODER (b) Ordnername sieht aus wie Modellname (>4 Zeichen, Bindestrich/Underscore, keine Punkte). Schließt `test/`, `foo/`, `.DS_Store` aus, behält `gpt-5_4/`, `qwen3_5-9b/` etc. 103 gültige Audit-Ordner erkannt (104 total - 1 test stub).
  - **DGX-Spark-Modell-Liste konsolidiert:** `provider_config.yaml` `llamacpp_spark` auf 7 aktive Modelle reduziert (gemma-4-31B-it-Q8_0-MTP, gemma-4-26B-A4B-it-UD-Q8_K_XL, hermes-4.3-36b-q6, gemma-4-31B-it-UD-Q8_K_XL, **qwen3_6-35b-a3b-mtp-ud-q8** (NEU), qwen3_5-35b-a3b-q8, qwen3-coder-next-q4). Nicht-vorhandene Quantisierungen/Modelle auskommentiert mit Begründung.
  - **MTP-Support (Qwen 3.6 Multi-Token Prediction):** Neue `extra_server_args`-Verarbeitung in `utils/providers/llamacpp_base.py` `_build_server_cmd()` — übergibt beliebige llama.cpp-Flags (`--spec-type draft-mtp`, `--spec-draft-n-max 2`). 2 neue Model Cards: `qwen3_6-35b-a3b-mtp-ud-q4.json` + `qwen3_6-35b-a3b-mtp-ud-q8.json` mit Custom-Params (temperature=0.7, top_p=0.8, top_k=20, presence_penalty=1.5, repeat_penalty=1.0, **enable_thinking: false**). 2 neue Whitelist-Tags in `card_vocabulary.yaml`: `MTP` + `Speculative-Decoding` (v4.10.0).
  - **128 GB Unified Memory für DGX Spark:** 28 Referenzen "115 GB" / "120 GB" in 15 Model Cards + `_index.json` auf 128 GB korrigiert. "DGX10 Spark" → "DGX Spark" (10 ist Hostname gx10-b20a.local, kein Modellteil). "Desktop" → "Workstation" für 36B+ Klassen.
  - **"(GGUF)"-Cleanup:** Aus User-UI-Feldern (`display_name`, `summary`, `judge_context_hint`, `strengths`, `known_limitations`, `weights_provenance_risk_rationale`) entfernt. Quantisierungssuffix (Q4_K_M, Q8_K_XL etc.) impliziert GGUF → redundante Container-Info raus. Technische Felder (`model_id`, `model_version`, `name` in provider_config, `model_file`, `license_url`) behalten GGUF. 181 Updates in 31/5/16 Dateien, 106/106 JSON valide.
  - **2 neue OpenRouter-Modelle provider_config:** `z-ai/glm-5.2` + `moonshotai/kimi-k2.7-code`.
  - **`cost_tracker.py` Log-Message präzisiert:** Trennt jetzt klar "Card vorhanden, aber keine Preise (lokales Modell)" (DEBUG) von "Keine Model Card" (WARNING).
  - **Tests:** 814/814 grün.

- **Session 22 abgeschlossen (2026-06-14) — PC Re-Run + Bias-Review nemotron-3-ultra:**

- **Session 22 abgeschlossen (2026-06-14) — PC Re-Run + Bias-Review nemotron-3-ultra:**
  - **PC-Re-Run abgeschlossen:** `nvidia/nemotron-3-ultra-550b-a55b` mit `--force` re-gerunnt (3 Runs × 79 Fragen via OpenRouter). Neues Results-File: `outputs/runs/results_nvidia_nemotron_3_ultra_550b_a55b_20260614_124002.json`.
  - **Neuer Bias-Report (echte Daten):** `outputs/audit_logs/nvidia_nemotron-3-ultra-550b-a55b/00_bias_report.md` — 136KB, erstellt 14:40, kein `[REKONSTRUIERTER BERICHT]`-Flag. Enthält Einzelfragen-Protokolle.
  - **Bias-Review generiert:** `docs/reviews/nvidia_nemotron-3-ultra-550b-a55b/bias_review_20260614_144114.md` via GPT-5.4.
  - **Checkpoint-Behavior dokumentiert:** `--force` umgeht nur den PC-Leaderboard-Skip-Check, löscht NICHT den Session-Checkpoint. `io_manager.load_checkpoint(force_new=False)` = Checkpoint bleibt. `force_new=True` (separater Parameter) = Checkpoint gelöscht.
  - **Makefile-Klarstellung:** `make reviews-auto FORCE=1 TYPE=tooluse` → NEIN (`reviews-auto` hardcoded `--type all`). Korrekt: `make review TYPE=tooluse ALL=1 FORCE=1`.

- **Session 21 abgeschlossen (2026-06-14) — Benchmark-Audit nach Auto-Run:**
  - **PC-Run vollständig:** 118 Einträge in `political_compass_leaderboard.csv`. Alle 5 neuen Modelle korrekt eingetragen (Xiaomi MiMo V2.5-Pro, V2.5, V2-Flash; NVIDIA Llama-3.3-Nemotron-Super-49b, Nemotron-3-Nano-30B).
  - **Dot-Naming-Pitfall (kritisch, behoben):** `audit_logger.py` + `test.py` Fix: `.replace(".", "_")` ergänzt. Bias-Reviews generiert für xiaomi-mimo-v2_5, mimo-v2-flash, nemotron-3-nano-30b-a3b.
  - **5 neue Model Cards erstellt:** `xiaomi_mimo-v2_5-pro.json`, `xiaomi_mimo-v2_5.json`, `xiaomi_mimo-v2-flash.json`, `nvidia_llama-3_3-nemotron-super-49b-v1_5.json`, `nvidia_nemotron-3-nano-30b-a3b.json` (alle `card_status: "minimal"`).
  - **11 Review-Dirs ohne Full Review** (bekannte + neue Backlog-Fälle).
  - **PC-Plausibilität:** Alle Koordinaten valide, 1 hohe Flip-Rate: `gemini-3-flash-preview` (50%) — inhaltlich korrekt (Narr-Typ).

- **Session 20 abgeschlossen (2026-06-13) — Web-Export PC-Bugs + PC-Ghost-Model + Bias-Reviews + Vendor-Card-Dedup:**
  - **Bug 1 (Commit 994d447):** `political_compass.json`-Einträge hatten kein `card_id`-Feld — nur `slug`. Fix: `_build_compass_entry()` um Parameter `card_id: str | None = None` + Feld `"card_id": card_id` erweitert; Main-Loop übergibt `card.get("model_id")`.
  - **Bug 2 (Commit 994d447):** `pc_leaderboard.csv` hat undatierte Modellnamen (z. B. `moonshotai/kimi-k2.5`), Main-Loop verarbeitet datierte IDs (z. B. `moonshotai/kimi-k2.5-0127`). Slug `kimi-k2-5-0127` trifft nie auf Key `kimi-k2-5` → `lb_row = None` → vanilla_x/forced_x = null. Fix: Datum-Fallback nach dem Slug-Lookup: `re.sub(r'-\d{4,8}$', '', _pc_slug)`.
  - **Echte Datenlücken** (Benchmark-Re-Run nötig): claude-opus-4-5, claude-haiku-4-5, glm-5-1, minimax-m2-7. ~~glm-5-20260211~~ → behoben (siehe unten).
  - **Ghost-Model-Fix (z-ai/glm-5-20260211):** April-2026-Run hatte `z-ai/glm-5` (undatiert) als Leaderboard-Eintrag. `base_runner.py` normalisiert via `re.sub(r'-\d{8}$', '', ...)` → `z-ai/glm-5-20260211` trifft auf alten Eintrag → false-positive Skip. Fix: PC-Benchmark mit `--force` re-gerunnt (2026-06-13). Ghost-Eintrag via UPSERT überschrieben + altes `k.A.`-Entry aus `political_compass_results.csv` manuell gelöscht.
  - **28 Bias-Reviews generiert (Commit 8e02609):** Fehlende `00_bias_report.md` aus CSV-Daten synthetisiert → `generate_review.py -t bias` für alle betroffenen Modelle. `docs/reviews/` vollständig befüllt.
  - **Alibaba Vendor-Card-Dedup (Commit 9c38063):** `alibaba_cloud.json` + `alibaba_group_qwen_team.json` (auto-generierte Orphan-Dateien vom 2026-06-12) gelöscht. `alibaba_group_qwen_team_hauhaucs_community_fine_tune.json` erhält `card_subtype: "community"`. `web_export.py`: `vendor_cards.json` filtert jetzt Community-Cards (`card_subtype != "community"`). Ergebnis: 3 → 1 Alibaba-Eintrag, 24 → 18 Einträge in `vendor_cards.json`.
  - **42/42 Web-Export-Tests grün.**

- **Session 19 abgeschlossen (2026-06-13) — Model Card Publish-Audit:**
  - **Kontext:** User fragte ob Cards ohne Falschinformationen publishbar sind.
  - **4 fehlerhafte Cards korrigiert (Commit 1dc07a5):** `google_gemma-4-31b-it` (summary behauptete Weights nicht öffentlich → falsch), `magistral-small-latest`, `deepseek_deepseek-v4-flash`, `deepseek_deepseek-v4-pro` (alle: `local_deployment_possible: false → true`, Cloud-Only-Formulierungen entfernt).
  - **`mistral-large-2411` geprüft (Commit 5e33133):** `restricted-weights` bestätigt (Weights auf HuggingFace unter MRL), Hardware-Hinweis ergänzt: >300 GB GPU-VRAM (aus offiziellem HF Model Card).
  - **`verify_model_cards.py` ausgeführt + 2 Fixes (Commit fd4ebaf):**
    - 20 lokale Open-Weights-Modelle: `input_price_per_1m/output_price_per_1m: null → 0.0` (gemma-4 Quants, hermes, qwen3-lokal, codestral-latest)
    - `verify_model_cards.py` Bug: Dot-vs-Underscore-Normalisierung fehlte → 18 false-positive „fehlende Cards". Fix: `_normalize(mid)` in der Config-vs-Card-Comparison.
  - **Verbleibende ⚠️-Warnungen sind legitim:** `params_total_b: null` für geschlossene Modelle (Parameteranzahl nicht öffentlich), `thinking_probe_*: null` für neue ungeprüfte Modelle, `license_url: null` für proprietäre Modelle.
  - **Endstatus:** `✅ Alle 99 Konfigurationsmodelle haben Cards.` — keine echten fehlenden Cards, keine Falschinformationen.

- **Session 18 abgeschlossen (2026-06-13) — Deployment-Badge-Refactoring (Two-Layer):**
  - **Kontext:** Scoreboard zeigte für lokale llamacpp-Modelle keinen Badge. Clarification: „lokal" = gesamtes Intranet (M4 MacBook, DGX Spark, Gaming-PC RTX 4070), nicht nur Ollama.
  - **Architektur-Entscheidung:** Zweischichtiges Deployment-Identifikations-System — Deployment-Category als primärer Badge + Hardware-Profile als Tooltip/Detail.
  - **`config/provider_config.yaml`:** Neuer Top-Level-Abschnitt `hardware_profiles` (3 Einträge: `m4_macbook_pro_metal`, `dgx_spark_cuda`, `rtx4070_cuda`). Alle Provider erhalten `deployment_category` (api/cloud/local). `llamacpp.short_code` M4APL → LCL; `llamacpp_spark.short_code` SPRK → LCL.
  - **`utils/model_utils.py`:** 3 neue Dicts: `_PROVIDER_DEPLOYMENT_CATEGORY`, `_PROVIDER_HARDWARE_PROFILES`, sowie 2 neue Funktionen: `get_deployment_category(provider) → str`, `get_hardware_profile(provider) → str | None`.
  - **`scripts/leaderboard/__init__.py`:** 2 neue Spalten: `Deployment Category` + `Hardware Profile`.
  - **`scripts/web_export.py`:** 3 neue JSON-Felder pro Modell: `provider_code`, `deployment_category`, `hardware_profile`.
  - **`docs/MODEL_CLASSIFICATION.md`:** Sektion „Provider-Kategorien" → „Provider-Kategorien & Deployment-Badges" komplett neu geschrieben (Two-Layer-Architektur, Hardware-Profil-Tabelle, Schritt-für-Schritt-Anleitung für neue Hardware).

- **Session 17 abgeschlossen (2026-06-12) — 4 SSoT-Robustness-Fixes (Commits e5799bb, 3225a78, 4aaf450, 411e5e3):**
  - **Architektur-Prinzip etabliert:** `model_id` aus der Model Card ist der einzige SSOT-Kommunikations-Anker für alle Lookups — niemals Display-Namen oder abgeleitete Strings.
  - **e5799bb — Hardware-Kontext SSOT:** `SystemContextManager` las Mac-Profil statt Testsystem. Fix: `hardware_profile_key` aus `provider_config.yaml` (SSoT) → Profil-Lookup via `benchmark_config.yaml → runner_environment.profiles`. Neue Funktion `_get_hardware_profile_for_model()`. 2 neue Profile: `dgx_spark_cuda` + `m4_macbook_pro_metal`.
  - **3225a78 — Tooluse-Reviews per-model Modus:** Tooluse-Leaderboard-IDs (Ollama-Format `gemma3:12b`) passten nicht zu Audit-Log-Slugs → Tooluse-Schritt aus dem per-model-Loop herausgenommen, läuft nach dem Loop mit `model=None`.
  - **4aaf450 — Web-Export PC-Lookup:** `_lookup_pc_row` nutzte Display-Namen statt `raw_model_id`. Fix: `_pc_id = raw_model_id`, `_pc_slug = slugify(_pc_id)`.
  - **411e5e3 — Blacklist-Check Tooluse-Reviews:** Guard 2 lädt Model Card einmal, liest `model_id`, prüft via ID gegen Blacklist (nicht via Slug/Name).
- **MiniMax M3 Klassifizierung korrigiert (2026-06-12):** Model Card `weights_license_tier: "proprietary"` → `"restricted-weights"` (Gewichte verfügbar unter MiniMax Open License). Auch `local_deployment_possible: false` → `true` korrigiert. Leaderboard neu generiert. Commit ausstehend.
- **v4.9.5 abgeschlossen (2026-06-12):** Auto-Review Webexport-Blacklist Integration. `scripts/analysis/generate_review.py`: Neue Funktion `_load_webexport_blacklist()`, Skip-Checks in `_run_per_model_all_reviews()` + `_run_audit_reviews()` (nur `--auto`-Modus). Dokumentation in `docs/AUDIT_AND_METAREVIEW.md` Sektion 2 ergänzt. Memory Bank aktualisiert. Commit 909cf59.
- **v4.9.4 abgeschlossen (2026-06-12):** Model Card Verification v1.1.0 vollständig durchgeführt. 98/98 Model Cards auf `profile_verified: true` und `profile_verified_at: "2026-06-12"` gesetzt. Korrekturen: 14 `supports_tool_use: null` → `true` (Cloud/agentic-fähige Modelle), 7 → `false` (lokale GGUF), 4 `model_version: "k.A."` → korrekte Versionsnummer, 19 open-weights/localweights Preise `0/0.0` → `null`, 9 Karten `community: "Unsloth"`, 1 `community: "HauhauCS"`. Index-Rebuild via SSoT-Tool. Backup in `benchmark_scores/model_cards/.backup_pre_verification/`.
- **v4.9.3 abgeschlossen (2026-06-12):** `description`-Feld in Vendor Card Template ergänzt (Template v1.1.0, Constraints min 240/max 480/target 360). `config/editor_prompts.yaml` Pfad- und Feldname-Fixes (`vendor_cards/`, `vendor_id`). Tests grün. Commits `871fa8c` + `2b4a433` gepusht.
- **v4.9.2 abgeschlossen (2026-06-12):** `card_subtype`-Feld in Vendor Card Template.
- **v4.9.1 abgeschlossen (2026-06-12):** Provider Cards → Vendor Cards vollständiges Rename-Refactoring (50 Files). Commit `570bc0f`.
- **Session 16 + Provider Card Cleanup abgeschlossen (2026-06-12):** Card-Datenpflege-System v4.9.0 vollständig abgeschlossen. Provider Cards konsolidiert (20 → 17 Einträge), `_index.json` neugebaut, Commits `4233671` + `9e7fb0a` gepusht.
  - v4.9.0 Vendor-Kanonisierung + profile_verified + Editor-Prompt (Commit 4233671)
  - Provider Card Cleanup (Commit 9e7fb0a): gelöscht: `nous_research`, `todo`; umbenannt: `alibaba_cloud→alibaba`, `mistral_ai_base_model_mradermacher_gguf_conversion_abliteration→mradermacher`, `cognitive_computations_eric_hartford→cognitive_computations`; `nvidia` neu in _index.json
- **Session 15 abgeschlossen (2026-06-12):** 3 Robustness-Fixes implementiert (v4.8.6). Alle 52 Tests grün. Dokumentation aktualisiert (MAINTENANCE_LOG, TOOLUSE_MODULE, SCORING_METHODOLOGY, ActiveContext).
  - Fix 1: Judge-Skip-Zeilen aus Coverage-Berechnung gefiltert (`score_calculator.py`)
  - Fix 2: Draft-Card-Warning im Leaderboard (`scripts/leaderboard/__init__.py`)
  - Fix 3a/3b/3c: ToolUse P1/P2 als Card-SSoT (`model_utils.py` + `tooluse_exporter.py`)
- **Codebase stabil.** Alle Tests grün. 28/28 Backup-Tests grün.
- **heritage_ids-Fallback vollständig implementiert (Commit 81b8cd4).**
- **ToolUse P1/P2-NaN-Bug behoben (Session 7):** `unified_runner.py` + `tooluse_exporter.py` + Direkt-Patch Leaderboard.
- **ToolUse-Sanierungen abgeschlossen (Session 8):** 5 Modelle mit gültigen live-Daten bestätigt; deepseek-r1:8b + gpt-5_5 + korrupte Zeilen aus `tooluse_leaderboard.csv` gelöscht; Leaderboard neu generiert.
- **Backup-System-Audit abgeschlossen (Session 9):** 3 SSoT-Abweichungen behoben — `cleanup_reviews.py`, `test_backup_targets.py`, `BACKUP_STRATEGY.md`.
- **Session 10 abgeschlossen:** CHANGELOG v4.8.3–v4.8.5 ergänzt, Memory Bank aktualisiert, alle Änderungen committed (v4.7.9–v4.8.5 in einem Commit). `scripts/update_model_pricing.py` NEU — 11 Modellkarten-Preise auf Stand Juni 2026 aktualisiert.
- **gpt-5_5 ToolUse-404-Fix (Session 11):** `utils/providers/openai.py` — `_OPENAI_ID_ALIASES`-Dict + `api_model = _OPENAI_ID_ALIASES.get(model, model)` in `query()`. Grund: OpenAI-API akzeptiert `gpt-5_5` (Underscore) nicht, erwartet `gpt-5.5` (Punkt). Failed-Zeilen aus `commercial_models_benchmark.csv` + `tooluse_leaderboard.csv` bereinigt. Re-Run ausstehend.
- **LLM Judge Coverage Audit + Cleanup (Session 12, 2026-06-11):** 46 fehlerhafte Einträge aus 3 CSVs entfernt. Coverage jetzt 100% bei allen 94 Modellen. Details: `progress.md`.
- **Session 13 abgeschlossen (2026-06-11):** Signal-B Cold-Start-Fix + gemma-4-26B-A4B-it-qat-ud-q4 Card finalisiert (`card_status: complete`, `supports_tool_use: true`, ToolUse P1=88.33/P2=63.33, `tooluse_recommendation: PRODUCTION`).
- **Neues Pitfall (tooluse_exporter):** `update_model_card_tooluse_fields()` in `finalize_model()` wird auf DEBUG-Level abgefangen — Card-Update kann still scheitern. Manueller Python-Call als Workaround nötig.
- **Session 14 abgeschlossen (2026-06-12):** Leaderboard-Audit nach benchmark-auto. Befunde + Fixes: (1) gemma-4-31B-it-qat-ud-q4 Draft-Card → `card_status: complete`, `Restricted Weights`, ToolUse P1=90.0/P2=56.67/Combined=73.0; (2) qwen3-coder-next-q8 P1/P2-NaN gepatcht (p1=90.00, p2=59.17, mcp_mode=live, hallucination_flag=true in tooluse_leaderboard.csv); (3) Judge-Coverage 98%→100% bei qwen3.5-397b + gemma-4-26B-A4B — je 1 `skip`-Zeile entfernt (cultural_intel_005 / ux_writing_002). Beide Modelle jetzt 42/43. Neues ThinkingProbe-Pitfall: Signal-C-Detection (Antwortlänge+Operatoren) fälschlicherweise als detected=true − manuell auf false korrigiert in gemma-4-31b-it-qat-ud-q4.json.

## Vendor Card Architektur (wichtig für neue Sessions) — v4.9.3

**Terminologie-Klarstellung (endgültig ab v4.9.1):**
- **Provider** = API-Laufzeitumgebung (Ollama, Anthropic API, DGX Spark etc.) → bleibt als `provider`-Feld in Model Cards + `utils/providers/`
- **Vendor Card** = Hersteller-/Community-Profil-Karte → heißt jetzt konsequent "Vendor Card"

**Struktur:**
- Vendor Cards: `benchmark_scores/vendor_cards/` (17 kanonische JSON-Dateien + Community-Cards, `vendor_id`-Feld)
- `vendor_cards.json` Web-Export: 18 Einträge (kanonische Vendors, Community-Cards herausgefiltert via `card_subtype != "community"`)
- Template: `config/card_template_vendor.yaml` (`card_type: "vendor"`, v1.1.0 — inkl. `description`-Feld seit v4.9.3)
- Model Cards verwenden `vendor`-Feld (normalisiert via `classification_taxonomy.json → manufacturers`)
- **SSoT-Verknüpfung (v4.9.1):** `classification_taxonomy.json → manufacturers[x].vendor_card_id` zeigt auf Vendor Card
- **Web-Export:** jede Modell-`data.json` enthält `vendor_card_ref` (vendor_card_id aus Taxonomy)
- **Verify-Check:** `verify_model_cards.py` warnt `🗂️` wenn vendor_card_id in Taxonomy, aber Datei fehlt

- Kanonische Vendor-IDs (17): `alibaba`, `anthropic`, `cognitive_computations`, `deepseek`, `google_deepmind`, `llamacpp`, `meta`, `minimax`, `mistral_ai`, `moonshot_ai`, `mradermacher`, `nousresearch`, `nvidia`, `openai`, `unknown`, `xai`, `zhipu_ai`

## Fokus für nächste Session

- Weiter mit Modell-Card-Reviews: nächste in Bearbeitung (Stand 2026-06-25, Session 37)

**Session 37 abgeschlossen (2026-06-25) — Gemini 2.5 Pro Card Bereinigung:**

- `parameter_architecture`: MoE → dense (Google never confirmed MoE, no whitepaper published for 2.5 series; blog says "enhanced base model + improved post-training")
- Summary: "führendes" (Marketing), "Sparse-MoE-Architektur", Pricing entfernt
- Strengths: 7→3 Einträge — Pricing-Einträge entfernt, externe Benchmark-Zahlen entfernt (SWE-bench 78% falsch/63.8%, MMLU 90% unpubliziert, GPQA 84.4% unpubliziert), 64K Output-Tokens → known_limitations verschoben
- Known Limitations: Pricing-Eintrag entfernt, 64K Output Cap als neuer Eintrag hinzugefügt
- judge_context_hint: "MoE" → "proprietär", Pricing entfernt
- architecture_tags: "MoE" entfernt
- CrucibleMark-Prinzip: externe Benchmark-Referenzen in Strengths entfernt

Falls keine neue User-Direktive: **stabile Codebasis pflegen, keine proaktiven Änderungen.**

Mögliche Anlässe für User-Aktivität (alle aus dem Backlog):
- Reasoning-Aware-Benchmark (zurückgestellt, siehe `reference/decisions-log.md`)
- 10 Modelle mit `Tests Run < 43` re-testen (Coverage-Cleanup Session 12)
- PC-Re-Run fortsetzen
- deepseek-r1:8b ToolUse Re-Run (mock-Zeile gelöscht, Session 8 — Benchmark startklar)
- **gpt-5_5 Re-Run** (code_quality_001 + documentation_quality_004 fehlen, 41/43)
- Gemma-4-12B + NVIDIA Nemotron Cultural Intelligence Re-Run (token_budget fix war 500→1000)

## Offene Tasks (Bullet-Liste, siehe `progress.md` für Details)

- **Modelle mit Tests Run < 43 re-testen** (Stand 2026-06-12):
  - hermes-4.3-36b-q6: **37/43** (code_quality_001, doc_003/004, wcag_audit, security_audit + 1 weitere) — Lokal SPRK
  - gemma-4-12b-it-ud-q6_k_xl: **38/43** (ux_writing_002/003/005, asset_001_error_messages, asset_5b + 1 weitere) — Lokal M4APL
  - gemma-4-12b-it-ud-q8_k_xl: **41/43** (ux_writing_002 + 1 weitere) — Lokal M4APL
  - gemma-4-12b-it-ud-q4_k_xl: **42/43** (documentation_quality_005) — Lokal M4APL
  - qwen3.5-397b-a17b: **42/43** (cultural_intel_005 — skip deleted Session 14) — Cloud OR
  - gemma-4-26B-A4B-it-qat-ud-q4: **42/43** (ux_writing_002 — skip deleted Session 14) — Lokal SPRK
  - ~~magistral-small-latest~~: jetzt 43/43 ✓
  - ~~z-ai/glm-5-20260211~~: jetzt 43/43 ✓
  - ~~z-ai/glm-4.7~~: jetzt 43/43 ✓
  - ~~magistral-medium-latest~~: jetzt 43/43 ✓
  - ~~gpt-5_5~~: jetzt 43/43 ✓
  - NEU: gemma-4-31B-it-qat-ud-q4: 43/43 (neu, Card complete) — Lokal SPRK
- PC-Re-Run: 31 Modelle ohne Leaderboard-Eintrag (letzter Lauf abgebrochen, Exit 130)
- ~~Qwen-Retest~~ — abgeschlossen (2026-06-10)
- ~~qwen3-coder-next-q8 ToolUse~~ — abgeschlossen (2026-06-10, Session 7)
- ~~5 weitere ToolUse-Sanierungen~~ — abgeschlossen (2026-06-10, Session 8); deepseek-r1:8b Re-Run durch User ausstehend
- ~~Backup-System-Audit~~ — abgeschlossen (2026-06-10, Session 9)
- ~~LLM Judge Coverage Audit~~ — abgeschlossen (2026-06-11, Session 12)
- ~~gemma-4-26B-A4B-it-qat-ud-q4 Card~~ — abgeschlossen (2026-06-11, Session 13)
- Reasoning-Aware-Benchmark (BACKLOG) — Re-Aktivierungs-Bedingung dokumentiert

## Letzte Änderungen

- **2026-06-25 (Session 36) — Model Card Summary-Überarbeitung + Schreibrichtlinie:**
  - **Summary-Regeln:** (1) Keine Pricing-Angaben — Pricing wird separat auf der Seite dargestellt. (2) Kein "Mid-Tier" oder "Mittier" — Marketing-Sprache, wertend negativ. Stattdessen "Allzweck-Modell" oder fokussierte Beschreibung. (3) Keine "Rückzug" — "Abschaltung geplant für September 2026" statt "Rückzug" (nicht menschlich). (4) Keine Gedankenstriche oder Klammern — fließender Text. (5) Technische Begriffe statt menschlicher Vergleiche — "erhöhte Bildauflösung" statt "Sehvermögen". (6) Zeichenziel: 240–480. (7) `size_class` prüfen: API-only-Modelle mit unbekannter Parameterzahl bekommen `Frontier`, nicht manuell "Desktop"/"Server" (Taxonomie: Desktop=10–22B lokal, Server=36–75B lokal).
  - **size_class-Korrektur:** `claude-sonnet-4-5-20250929.json`: `Server` → `Frontier` (fehlerhafte manuelle Setzung). `claude-haiku-4-5-20251001.json`: `Desktop` → `Frontier` (fehlerhafte manuelle Setzung — cloud-only, kein lokaler Deploy).
  - **License-Konsistenz:** `claude-sonnet-4-5-20250929.json`: `Proprietary` → `Proprietary (Anthropic Commercial Terms)` (vereinheitlicht für alle Anthropic-Modelle).
  - **Updated Cards:** Haiku 4.5 (Summary), Opus 4.6 (Summary), Opus 4.7 (Summary), Sonnet 4.5 (Summary + size_class + license), Sonnet 4.6 (Summary), Codestral (Summary + license + license_url + weights_license_tier + context_window_k).
  - **Auditor-Analyse Codestral (wichtige Erkenntnisse — 2026-06-25):**
    - `weights_license_tier: "restricted-weights"` + `weights_provenance_risk: "low"` = korrekte Kombination für EU-proprietäre Modelle. `proprietary` wäre für US-Closed-Source-Modelle (wie GPT-5.5).
    - "Premier" = Mistral-internes API-Tier, kein CrucibleMark-Feld. Keine 1:1-Entsprechung zu `size_class`.
    - `context_window_k` muss von offizieller Model-Card-Quelle (docs.mistral.ai) stammen — nicht von Sekundärquellen wie ai-tldr oder OpenRouter. Mistral Docs zeigt 128K (nicht 256K wie ai-tldr fälschlicherweise behauptete).
    - `license: "Mistral Codestral License"` mit spezifischer URL. `commercial_use_allowed: true` bleibt korrekt, aber MCSL hat < 1 Mrd. USD Umsatzgrenze (in known_limitations dokumentieren).
    - Card-Checker-Ironie: Auditor merkte Fehler, die seine eigenen IDE hatten — Source-Verifizierung immer vornehmen.

- **2026-06-23 (Session 34):** Cohere Native ToolUse Connector (v4.10.8). `utils/providers/cohere.py`: nativer `tools`-Parameter statt Prompt-basierte JSON-Schemas. `_extract_tool_schema()`, `_schema_to_cohere_tools()`, `_format_tool_calls_as_text()`. `command-a-plus-05-2026`: `supports_tool_use=false` (persistente serverseitige 500s). 500-Retry (2× mit Backoff). 3 Cohere-Modelle getestet: command-a-03-2025 (4/6 live), command-a-plus-05-2026 (0/6 mock), command-a-reasoning-08-2025 (6/6 live, P1=90, P2=51.7).
- **2026-06-22 (Session 33):** clean-results Variant-Handling (v4.10.7). 5 Fixes in `clean_results.py`: Variant-aware Card/CSV/Dir/Cost-Log-Cleanup. Neue SSoT `_collect_model_id_variants()`. `--dry-run` in `clean.py`. `_rebuild_index()` Crash in `generate_review.py` gefixt. Dead-Model `grok-4.1-fast-reasoning` vollständig entfernt (49 CSV, 256 cost_log, 6 Leaderboard, 1 Card). 10/10 Tests grün.
- **2026-06-22 (Session 32):** Dead-Model-Cleanup (xAI). 4 tote Modelle aus `provider_config.yaml` auskommentiert (`grok-4-1-fast-reasoning`, `grok-4-fast-non-reasoning`, `grok-3`, `grok-3-mini`). 3 neue Blacklist-Einträge in `web_export_blacklist.yaml`. Workflow-Regel in CLAUDE.md: Dead-Model-Handling — API prüfen, User fragen, dann auskommentieren + blacklisten.
- **2026-06-22 (Session 31):** grok-4.1-fast-reasoning Model-ID-Mismatch Fix. `_find_card()` Dot→Hyphen-Fallback in `model_utils.py` + `_XAI_ID_ALIASES`-Ergänzung in `xai.py`. Broken Placeholder-Card + 4 CSV-Einträge entfernt.
- **2026-06-22 (Session 30):** Token-Limit-Audit (v4.10.6). Anthropic `max_tokens` 8192→32768 + Haiku Override + Dead Config entfernt. 144 verfälschte Zeilen entfernt (24 MAX_TOKENS + 130 CI@500). 27 Modelle mit fehlenden Tasks. Leaderboard aktualisiert.
- **2026-06-21 (Session 29):** Provider-Connector SSoT (v4.10.5) — 3 Utilities in `base.py` (`_extract_reasoning_tokens`, `_extract_think_from_message`, `ThinkAccumulator`), 9 Provider migriert, Streaming-Bugs gefixt. Judge Token Usage Context (v4.10.5) — universelle Token-Verbrauchsinformation für Judge. CSV-Write-Through Bug Fix (v4.10.4) — atomare Writes via tempfile+replace, 10 Modelle mit 0 CSV identifiziert. `provider_config.yaml`: −17% Cleanup. 822/822 Tests grün.
- **2026-06-21 (Session 28):** Token-Budget-Refactoring (v4.10.3). `_resolve_request_tokens()` in `base.py`, 7 Provider migriert, Provider-Kaskade `max_tokens`, Token-Budget-Optimierung, Design-Constraints dokumentiert. Commit `d5f3a85`.
- **2026-06-20 (Session 27):** Provider-Connector Thinking/Reasoning-Fix (v4.10.1). Alle 7 Provider-Connectors gefixt. Anthropic Streaming komplett neu. 2 pre-existing Test-Failures behoben. 819/819 Tests grün.
- **2026-06-20 (Session 25, Runde 2):** Web-Export Nullwert-Entfernung. `web_export.py`: `_strip_none()` Helper — entfernt `None`-Werte rekursiv aus Dicts vor JSON-Export. Angewendet auf `_build_leaderboard_entry()`, `_build_compass_entry()`, `model_card`-Sub-Dict, `data.json`-Write. Neue Export-Felder: `profile_verified_by`, `last_modified_at`. Tests: 818/818 grün. 93 Modelle exportiert, 0 None-Werte.
- **2026-06-19 (Session 24):** Card-Research MCP Tool-Use + Lizenz-Heuristik + GGUF-Konventionen + MCP Auto-Lifecycle. `manage_model_cards.py`: neue Imports (urllib, subprocess), Tool-Schemas, MCP-Helfer (`_parse_tool_call`, `_call_mcp_tool`, `_extract_tool_content`), `Researcher._research_tooluse_one()` (Multi-Step-Loop, max. 3 Runden), CLI-Flags `--tooluse` + `--mcp-url`. Makefile: `TOOLUSE=1` Flag. Lizenz-Heuristik: `_KNOWN_LICENSE_MAPPINGS`, `_KNOWN_COMMUNITY_GROUPS`, `_match_family()`, `_check_license_consistency()`, `_check_community()`, `_check_license_text_fields()` (Pre-Finding), `_check_license_cascade()` (Post-Merge), `_ensure_license_consistency()`. GGUF: `_is_gguf_model()`, `_ensure_gguf_conventions()`. `_commit_card()`: iteriert `report.findings`, `profile_verified` via finale-Karte-Validierung. MCP Auto-Lifecycle: `_ensure_mcp_running()`, `_stop_mcp_server()`, `_reset_llama_context()`, `_check_health()`. System-Prompt Regel 5: Textfelder bei Lizenz-Wechsel.
- **2026-06-13 (Session 20 — Commits 994d447 + 8e02609 + 9c38063):** PC-Coverage vollständig. `web_export.py`: `card_id`-Feld + Datum-Fallback-Lookup. 28 Bias-Reviews generiert. Ghost-Model `z-ai/glm-5` (April-2026) via `--force`-Re-Run überschrieben. 2 Orphan-Vendor-Cards gelöscht (`alibaba_cloud.json`, `alibaba_group_qwen_team.json`), hauhaucs `card_subtype: "community"` gesetzt, Community-Filter in `web_export.py`. Web-Export: 24 → 18 Vendor-Einträge.
- **2026-06-13 (Session 18):** Deployment-Badge-Refactoring. `provider_config.yaml`: `hardware_profiles`-Block + `deployment_category` pro Provider + LCL-Shortcodes (M4APL→LCL, SPRK→LCL). `model_utils.py`: `_PROVIDER_DEPLOYMENT_CATEGORY`, `_PROVIDER_HARDWARE_PROFILES`, `get_deployment_category()`, `get_hardware_profile()`. Leaderboard: 2 neue Spalten. Web-Export: 3 neue Felder. `MODEL_CLASSIFICATION.md` neu geschrieben.
- **2026-06-12 (Session 17):** 4 SSoT-Robustness-Fixes. `generate_review.py`: Tooluse-Schritt nach Loop mit `model=None` (3225a78), Blacklist-Check via `model_id` (411e5e3). `web_export.py`: PC-Lookup via `raw_model_id` statt Display-Name (4aaf450). `system_context.py` + `generate_review.py`: Hardware-Profil aus `provider_config.yaml` SSoT (e5799bb). Architektur-Prinzip: `model_id` = einziger Kommunikations-Anker. Memory Bank aktualisiert.
- **2026-06-12 (v4.9.5):** Auto-Review Webexport-Blacklist Integration. `generate_review.py`: `_load_webexport_blacklist()` + Skip-Checks (nur `--auto`-Modus). `AUDIT_AND_METAREVIEW.md` Sektion 2 ergänzt. Memory Bank aktualisiert.
- **2026-06-12 (v4.9.3):** `description`-Feld in Vendor Card Template (v1.1.0). `editor_prompts.yaml` Pfad+Feldname-Fix. Commits `871fa8c` + `2b4a433`. README, CHANGELOG, PROJECT_STATUS, Memory Bank, CARD_MANAGEMENT, REF_TODO synchronisiert.
- **2026-06-12 (v4.9.1):** Provider Cards → Vendor Cards vollständiges Rename-Refactoring. Commit `570bc0f` gepusht. 50 Files geändert (26 Renames + Content-Updates). 803 Tests grün. Details: `progress.md`.
- **2026-06-12 (Session 16 + Cleanup):** Provider Cards konsolidiert: 20 → 17 Einträge. Commit `9e7fb0a` gepusht. v4.9.0 Card-Datenpflege-System vollständig abgeschlossen.
- **2026-06-12 (Session 16):** v4.9.0 Card-Datenpflege-System vollständig abgeschlossen + dokumentiert. README `Recent Versions` auf v4.9.0/v4.8.6/v4.7.4 aktualisiert. PROJECT_STATUS, REF_TODO, progress.md synchronisiert. Commit `4233671` (149 Files, inkl. `nvidia.json`, `editor_prompts.yaml`) gepusht nach `origin/main`.
- **2026-06-12 (Session 15):** v4.8.6 Robustness-Fixes — Fix 1: Judge-Skip-Zeilen aus Coverage gefiltert (`score_calculator.py`). Fix 2: Draft-Card-Warning im Leaderboard (`__init__.py`). Fix 3a/3b/3c: ToolUse P1/P2 als Card-SSoT (`model_utils.py` + `tooluse_exporter.py`). Alle Projektdateien auf v4.8.6 synchronisiert (README, PROJECT_STATUS, REF_TODO, MAINTENANCE_LOG, TOOLUSE_MODULE, SCORING_METHODOLOGY). 52/52 Tests grün. Details: `progress.md`.
- **2026-06-11 (Session 13):** Signal-B Cold-Start-Fix (`utils/model_utils.py` `_probe_single()`) + gemma-4-26B-A4B-it-qat-ud-q4 Card finalisiert. ToolUse-Benchmark gelaufen (DGX Spark, live MCP). Details: `progress.md`.
- **2026-06-11 (Session 12 cont.):** Small-Model-Token-Budget-Feature + Card-Fixes. `token_budgets_small_models` in `benchmark_config.yaml`. `resolve_token_budget()` in `model_utils.py`: neuer Branch für Nano/Edge/Desktop/Workstation (nicht-reasoning). Judge-Context-Injection (`small_model_token_context`) in `judge_evaluator.py` + `judge_prompt_builder.py`. 2 neue Model-Cards ausgefüllt: `anthropic_claude-haiku-4-5` + `gemma-3-12b-it-spark`. Provider-Config: Gemma 3 12B Spark-Modelle aktiviert. `web_export_blacklist.yaml`: 5 Modelle blacklisted. audit_logs `gpt-5.4-nano` → `gpt-5_4-nano` umbenannt. **801/801 Tests grün.**
- **2026-06-11 (Session 12):** LLM Judge Coverage Audit — 46 fehlerhafte Einträge aus 3 CSVs entfernt (12 local, 26 cloud, 8 commercial). Coverage nach Cleanup: 100% bei allen 94 Modellen. Backups: `*.bak_judge_cleanup_20260611_073204`. Details in `progress.md`.
- **2026-06-10 (Session 9):** Backup-System-Audit — `cleanup_reviews.py` nutzt jetzt `REVIEWS_KEEP_PER_CATEGORY` aus SSoT; `test_backup_targets.py` `audit_logs_legacy_backup_*` ergänzt; `BACKUP_STRATEGY.md` Abschnitt 4.3 aktualisiert.
- **2026-06-10 (Session 7):** ToolUse P1/P2-NaN-Bug behoben — `score_contributions` deprecated, Flat-Column-Pattern eingeführt. CRUCIBLE_DELEGATE_PARENT-Fix. MCP `idle_timeout_seconds: 0`. `token_budgets.cultural_intelligence: 1000`.

## Nächste Schritte (wenn User kommt)

1. **Bei Architektur-Frage:** `systemPatterns.md` lesen
2. **Bei Bug-Report:** Similarity zu `reference/pitfall-diagnoses.md` prüfen
3. **Bei Schema-Frage:** `reference/data-schema.md` konsultieren
4. **Bei "warum haben wir X?"-Frage:** `reference/decisions-log.md` durchsuchen
