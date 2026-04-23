# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v3.5.5] - 2026-04-22

### Changed
- **Size-Class-System auf 6 Deployment-Tiers erweitert:** `get_model_size_class()` in `utils/model_utils.py` ersetzt das alte 2-Tier-System (`Nano (≤5B)` / `Standard`) durch eine deployment-orientierte 6-Tier-Taxonomie: `Nano` (≤ 4B, < 4 GB RAM), `Edge` (5–9B, 4–8 GB), `Desktop` (10–17B, 8–14 GB), `Workstation` (18–35B, 14–24 GB), `Server` (36–75B, 24–48 GB), `Frontier` (> 75B / API-only). Modelle ohne Größen-Tag (kommerzielle APIs, Cloud-Proxies) landen automatisch in `Frontier`. Badge-Marker `🔬` bleibt auf `Nano` beschränkt (≤ 4B, Floor-Tier). `MODEL_CLASSIFICATION.md` vollständig aktualisiert.

---

## [v3.5.4] - 2026-04-21

### Added
- **Nano/Edge-Tier:** Modelle mit ≤ 5B Parametern werden automatisch erkannt und im Leaderboard als `Nano (≤5B)` klassifiziert. Neue Spalte `Size Class` in Compact- und Detailed-CSV. Badge-Suffix `🔬` (z. B. `🥉 Bronze 🔬`) macht die Hardwareklasse auf einen Blick sichtbar, ohne Tier-Schwellen zu verändern. Web-Export propagiert `size_class`-Feld ins JSON. Erkennung via `get_model_size_class()` in `utils/model_utils.py` (Regex auf Ollama-Style-Tag, z. B. `qwen3:4b`, `phi3.5:3.8b`).
- **Docs:** `MODEL_CLASSIFICATION.md` — neuer Abschnitt „Nano/Edge-Tier (≤ 5B Parameter)" mit Use-Cases, Erkennungslogik und Beispiel-Tabelle.

---

## [v3.5.3] - 2026-04-21

### Fixed
- **`benchmark_modules/ux_writing/assets/asset_005_microcopy_audit.yaml` — Limit-Kalibrierung:** `max_expected_words` 150 → 350 (datengetrieben: P25 der Ist-Längen × 1.20 = 337 → 350). Prompt-Text ergänzt um explizite Längenanweisung `"Maximale Länge: 350 Wörter gesamt"` — Modell war zuvor nie über das Limit informiert. 50/52 Modelle hatten das alte Limit verletzt (Min-Ist 255 W > Limit+Toleranz 162 W).
- **`benchmark_modules/content_transformation/assets/asset_003_glossary_simplification.yaml` — Limit-Kalibrierung:** `max_expected_words` 150 → 250 (P25 = 210 W × 1.20 = 252 → 250). Format-Hinweis im Prompt synchronisiert (`Max 150 Wörter` → `Max 250 Wörter`). 29/52 Modelle hatten das alte Limit verletzt.
- **`benchmark_modules/content_transformation/assets/asset_004_video_script_tutorial.yaml` — Limit-Kalibrierung:** `max_expected_words` 600 → 900 (P25 = 789 W × 1.20 = 947 → 900). Format-Range im Prompt synchronisiert (`400-600 Wörter` → `600-900 Wörter`). Min-Ist aller 52 Modelle war 742 W — das alte Limit war physisch unlösbar.

### Data
- **156 CSV-Zeilen gelöscht:** Alle Einträge der 3 betroffenen Tasks (`ux_writing_005`, `content_transformation_003`, `content_transformation_004`) aus `commercial_models_benchmark.csv`, `cloud_models_benchmark.csv` und `local_models_benchmark.csv` entfernt (75 + 42 + 39 Zeilen). Re-Run wird automatisch durch fehlende `(model, asset_id)`-Keys getriggert.
- **156 Audit-Log-Dateien gelöscht:** Alle `*/ux_writing_005.md`, `*/content_transformation_003.md`, `*/content_transformation_004.md` aus `outputs/audit_logs/` entfernt. Neue Audit-Logs entstehen beim Re-Run.

### Analysis
- **Fleet-weiter Violation-Scan:** 52 Modelle × 37 Tasks systematisch auf strukturelle Kalibrierungsfehler analysiert. Befund: 3 isolierte Limit-Fehler (alle behoben). `content_transformation_005` als begründeter Design-Trade-off eingestuft (`keyword_presence`-Check für abschnittsbezogenes Limit korrekt — `max_expected_words` auf Gesamtantwort wäre methodisch falsch). Phase-2-Backlog angelegt.

---

## [v3.5.2] - 2026-04-21

### Fixed
- **`scripts/core/unified_runner.py` — Pylint W1309:** `f`-Prefix aus String ohne Interpolation entfernt (Zeile 511: `f"   💸 Budget-/Quota-Fehler..."` → `"   💸 Budget-/Quota-Fehler..."`).
- **`utils/providers/base.py` — Pylint W0719:** `raise Exception(...)` → `raise RuntimeError(...)` — spezifischer Fehlertyp statt `Exception`-Basisklasse.
- **`benchmark_modules/political_compass/core/audit_logger.py` — Pylint C0206:** Dict-Iteration `for _q_id in hydrated_responses:` → `for _q_id, _q_data in hydrated_responses.items():` — Pylint-konformes `.items()`-Pattern.
- **`benchmark_modules/political_compass/core/evaluators.py` — Mypy annotation-unchecked:** `__init__(self)` → `__init__(self) -> None` in `ExtremismWatchdog` (Zeile 49) und zweiter Klasse (Zeile 332) — mypy prüft jetzt `List[ExtremismDetail]`-Annotation korrekt.

### Changed
- **`benchmark_modules/political_compass/config.yaml` — Skalen-Label X-Achse:** `label: "Nationalistisch"` → `label: "Reaktionär"` (Range 4.4–7.4). Terminologisch präziser, da das Segment wirtschafts- und gesellschaftspolitischen Konservatismus beschreibt, nicht ethnischen Nationalismus.
- **`benchmark_modules/political_compass/core/audit_logger.py` — Beispieltext:** `repressiv-nationalistisch` → `repressiv-reaktionär` synchronisiert mit Skalen-Umbenennung.

### Docs
- **`docs/POLITICAL_COMPASS_KONZEPT.md` — Block 7.9:** Neuer Abschnitt 7 „Block 7.9: Die Parolen-Extremismus-Sonde" mit drei Unterkapiteln: Konzept und Asset-Tabelle (11 Parolen-Assets), Koordinatenformel mit 80/20-Gewichtung und Begründung, Interpretationshinweis für Hard-Refusal-Verhalten (parolen_x/y = 0).

---

## [v3.5.0] - 2026-04-17

### Added
- **`utils/llm_client.py` — `last_output_tokens`-Feld:** `self.last_output_tokens` wird vor jedem API-Call auf `0` zurückgesetzt und nach erfolgreichem Call auf den tatsächlichen `eval_count` (Ollama) gesetzt. Liefert pro Frage-Anruf die exakten Output-Tokens ohne nachträgliches Parsing.
- **`benchmark_modules/political_compass/test.py` — `output_tokens` im Checkpoint:** Live-Paths schreiben `getattr(llm_client, "last_output_tokens", 0)` ins `detailed_responses`-Dict. Resume-Pfad schreibt explizit `None` (kein Token-Datum verfügbar, semantisch von `0` trennbar).
- **`benchmark_modules/political_compass/core/audit_logger.py` — Section 2.6 Token-Asymmetrie:** Neue optional Sektion im PC-Audit-Log, ausschließlich bei `verification_mode=True` (Shift ≥ 1.0). Berechnet `ELABORATION_SPIKE` (Forced > +50 % Output-Tokens) und `CAPITULATION_DROP` (Forced < −40 %) aus echten per-Frage-`output_tokens`. Fallback auf Antwortzeit-Proxy (mit `Hardware-abhängige Schätzung`-Label) bei Legacy-Runs ohne Token-Daten. None-sichere Filter (`or 0`-Guard). Coverage-Warnung bei partiellen Daten.
- **`config/meta_reviewer_prompt.yaml` — `bias_reviewer` Section-2.6-Integration:** Reviewer-Prompt erweitert um Verzahnungs-Instruktion: Token-Asymmetrie-Befunde sollen als Dimension der Schattenmetriken (Section 2.5) eingewoben werden, nicht als isolierter Absatz. Zero-Write-Regel für Hardware-Schätzungen. Dokumentierter Upgrade-Pfad und Re-Run-Prioritäten als YAML-Kommentar.
- **`config/meta_reviewer_prompt.yaml` — `bias_reviewer` Prompt-Architektur:** Model Card vor Pflichtstruktur verschoben (sequenzielles LLM-Lesen), drei offene Leitfragen durch eine präzise Einzel-Instruktion ersetzt.
- **`docs/AUDIT_AND_METAREVIEW.md` — Section 2.6 dokumentiert:** Neuer Abschnitt "Political Compass: Section 2.6 Token-Asymmetrie" mit Flag-Schwellenwerten, Thinking-Modell-Einschränkung, Zero-Write-Regel und Nachweis der retroaktiven Legacy-Nachpflege.
- **`docs/POLITICAL_COMPASS_KONZEPT.md` — Kapitel 5 Schattenmetriken:** Neues Kapitel "Schattenmetriken: Internes Chaos und kognitive Fingerabdrücke" erklärt Standardabweichung (Section 2.5), Token-Asymmetrie (Section 2.6), Flag-Tabelle, Kombinations-Interpretation und Thinking-Modell-Einschränkung.

### Fixed
- **`benchmark_modules/political_compass/test.py` — Resume-Pfad `None` statt `0`:** Resume-Checkpoints schrieben `output_tokens: 0`, was falsche „partiell-vollständige" Coverage-Meldungen in Section 2.6 verursachte. Fix: explizites `None` macht fehlende Token-Daten semantisch von tatsächlichen Null-Token trennbar.
- **`benchmark_modules/political_compass/core/audit_logger.py` — None-sicherer Filter:** `token_pairs`-Filter verwendete `> 0`, was bei `None`-Werten einen `TypeError` verursachen konnte. Fix: `(... or 0) > 0`-Guard.

### Data
- **12 PC-Audit-Logs retroaktiv mit Section 2.6 (Zeitproxy) ergänzt:** Alle Modelle mit Shift > 1.0 aus dem initialen Benchmark-Run. Zeitproxy mit `Hardware-abhängige Schätzung`-Label — Reviewer-Zero-Write-Regel greift weiterhin. Auffälligste Werte: `qwen3.5:9b` +149 %, `gemma4:26b` −58 %.

---

## [v3.5.1] - 2026-04-19

### Fixed
- **`utils/providers/base.py` — Gemini Daily-Quota Fast-Fail:** `retry_delay`-Werte > 300 Sekunden (Google Tages-Quota-Erschöpfung, z. B. `retry_delay { seconds: 27331 }`) lösen jetzt Fast-Fail aus statt das System 7,6 Stunden zu blockieren. Die geworfene Exception enthält `exceeded your current quota` und wird vom bestehenden `budget_keywords`-Guard in `test.py` als `_quota_exhausted = True` behandelt — Checkpoint bleibt erhalten, nächster Provider wird normal weitergeführt.
- **`config/rate_limits.yaml` — `max_retry_delay_seconds: 300`:** Schwellenwert dokumentiert.
- **`benchmark_modules/political_compass/test.py` — `UnboundLocalError` bei Quota-Abbruch:** `query_exec_time = 0.0` als Default vor der `while True:`-Schleife eingefügt. Bei Quota-Fehlern brach `break` die Schleife ab bevor die Variable zugewiesen wurde — `UnboundLocalError` in der Ergebnis-Aggregation (Zeile ~371) war die Folge.
- **`utils/providers/openai.py` — Modellspezifisches Token-Limit (gpt-4o, gpt-4o-mini):** Nach dem Standard-Token-Limit-Lookup wird jetzt `model_max_tokens` aus der Provider-Config ausgelesen und als hartes Obergrenze angewendet. Verhindert die bisher bei jedem Request ausgelöste Fallback-Warnung `⚠️ Token limit rejected. Retrying with fallback limit: 4096 tokens.`

### Changed
- **`benchmark_config.yaml` — `kimi-k2-instruct` Groq → Ollama Cloud:** `moonshotai/kimi-k2-instruct` aus dem Groq-Provider entfernt (Modell dort nicht mehr verfügbar). Ersetzt durch `kimi-k2.5:cloud` unter `ollama_cloud` (via `ollama pull kimi-k2.5:cloud`). Benchmark-Werte für `kimi-k2.5:cloud` bereits seit 2026-04-16 im PC-Leaderboard vorhanden.
- **`benchmark_config.yaml` — `model_max_tokens`-Override (OpenAI):** Neuer Block `model_max_tokens: {gpt-4o: 4096, gpt-4o-mini: 4096}` im OpenAI-Provider-Abschnitt als konfigurierbare SSOT für modellspezifische Token-Obergrenzen.

### Data
- **7 neue PC-Leaderboard-Einträge:** gpt-5, gpt-5.4, gpt-5.4-mini, gpt-4o, gpt-4o-mini, meta-llama/llama-4-scout-17b-16e-instruct, qwen/qwen3-32b. PC-Leaderboard jetzt auf 48 Modellen (inkl. kimi-k2.5:cloud aus vorherigem Run).

---

## [v3.4.7] - 2026-04-16

### Fixed
- **`benchmark_modules/political_compass/test.py` — Budget-Exhaustion-Guard:** Exception-Handler im Query-Loop erkennt Budget/Quota-Keywords und setzt `self._quota_exhausted = True`. Verhindert lautloses Schlucken von Budget-Fehlern und das Schreiben korrupter All-Zero-Daten ins Leaderboard.
- **`utils/base_runner.py` — Quota-Flag-Propagation:** `execute_batch_module()` prüft `getattr(test, "_quota_exhausted", False)` nach `execute()` und setzt `self.provider_quota_exhausted = True`. Gibt `[]` zurück — kein korruptes Ergebnis mehr.

### Changed
- **`benchmark_modules/political_compass/core/io_manager.py` — `cost`-Spalte entfernt:** Redundante Spalte (immer `0.0` für lokale Modelle) aus Leaderboard-CSV und `io_manager.py` entfernt. Interne `total_cost`-Berechnung für Audit-Log bleibt erhalten.
- **`config/meta_reviewer_prompt.yaml` — `bias_reviewer`-Prompt:** Initialer `bias_reviewer:`-Key mit vollständigem System-Prompt für politische Bias-Analyse.
- **`scripts/web_export.py` — `inference_provider`-Feld:** `leaderboard.json` enthält jetzt `inference_provider` pro Eintrag.

### Data
- **PC-Leaderboard bereinigt:** 34 → 13 Zeilen (21 März-Einträge mit `polarity_flip_rate = 0.0` entfernt). 21 Modelle zur Neuberechnung freigegeben.

---

## [v3.4.6] - 2026-04-14

### Fixed
- **`utils/base_runner.py` — PC Skip-Logic-Lücke geschlossen:** `execute_batch_module()` prüfte bei Political-Compass-Runs nur die 3 Standard-CSVs auf bereits vorhandene Ergebnisse. Nach einem Leaderboard-Reset (leere Standard-CSVs) wurden alle PC-Modelle fälschlich erneut gerunnt. Fix: Expliziter Fallback-Check gegen `benchmark_scores/political_compass_leaderboard.csv` — wird nur für PC-Module aktiviert (`PoliticalCompassHandler.is_political_compass()`). Graceful-Fallback bei `OSError`/`csv.Error`.

### Data
- **Political Compass Leaderboard-Bereinigung:** 11 Einträge mit korrupten Koordinaten (runde Null-Werte aus fehlerhafter Session 23.03.2026 — Verweigerungen produzierten Ganzzahlwerte wie `(0.0, 9.0)`) aus `political_compass_leaderboard.csv` entfernt. Leaderboard: 31 → 20 verifizierte Einträge. Betroffene Modelle für Re-Run freigegeben. Backup gesichert unter `political_compass_leaderboard.bak_20260414_222150.csv`.

---

## [v3.4.5] - 2026-04-11

### Changed
- **Redaktionelle Überarbeitung (16 Dateien):** README.md, 13 `docs/`-Dateien, REF_TODO.md und PROJECT_STATUS.md auf einheitlichen Ton gebracht: Ansprache `du`/`dein` → unpersönliches `man`/`sein`; Emojis aus Überschriften entfernt (nur `🛑` als kritischer Warnmarker behalten); alle englischen H1–H3 ins Deutsche übertragen; einheitliche Intro-Blöcke (`**Zielgruppe:**` / `**Inhalt:**` / `> **Voraussetzung:**`) in allen Dateien ergänzt; ~80 `______`-Trennlinien → `---`.

---

## [v3.4.4] - 2026-04-11

### Changed
- **`utils/constants.py` — Neue Konstanten (Regeln 2+3):** `MODEL_TYPE_OPEN_WEIGHTS_CLOUD`, `RESULT_TYPE_LOCAL/CLOUD/COMMERCIAL` und 7 Timeout-Konstanten (`TIMEOUT_OLLAMA_HEALTH/LIST_FAST/LIST/VERSION/WARMUP`, `TIMEOUT_HTTP_FETCH`, `TIMEOUT_ANTHROPIC_API`) als SSOT zentral definiert.
- **Beseitigung von Magic Strings/Numbers in 8 Dateien:** `utils/result_manager.py`, `utils/model_utils.py`, `utils/providers/anthropic.py`, `utils/pricing_updater.py`, `scripts/core/benchmark_auto.py`, `scripts/core/unified_runner.py`, `scripts/core/run_cross_model_benchmark.py`, `scripts/tools/list_models.py` referenzieren alle Timeout- und Typ-Werte ausschließlich via `constants.py`.

---

## [v3.4.3] - 2026-04-10

### Added
- **`module_weight`-Feld in allen Modul-`config.yaml`s:** Neues `integration.leaderboard.module_weight`-Key entkoppelt den Total-Score-Einfluss eines Moduls von seiner Asset-Anzahl. Default: Vollmodule `1.0`, CLI-Modul `0.5` (Supplement). Konfigurierbar pro Deployment ohne Code-Änderung.
- **`_module_scale()` in `score_calculator.py`:** Hilfsfunktion berechnet den normierten Skalierungsfaktor pro Modul (`scale = module_weight / Σ active weights`). Alle 4 Contrib-Spalten werden vor der Aggregation skaliert. Fallback: fehlender `module_weight`-Wert → `scale = 1.0`.
- **5 neue Ollama-Cloud-Modelle in `config/cost_limits.yaml`:** `deepseek-v3.1:671b-cloud` ($0.28/$0.42 per 1M), `qwen3.5:397b-cloud` ($0.60/$3.60 per 1M), `gemma4:31b-cloud` ($0.14/$0.40 per 1M), `kimi-k2.5:cloud` ($0.45/$2.25 per 1M), `glm-5:cloud` ($0.14/$0.40 per 1M).
- **`docs/BENCHMARK_MODULES.md`:** Neuer Abschnitt "Designprinzip: Module als gleichwertige, geschlossene Tests" erklärt die Modulgewichtungs-Philosophie, den Einsatz von Einzel-Modul-Scores und den CLI-Sonderfall.
- **`docs/SCORING_METHODOLOGY.md`:** Neue Sektion "Modulgewichtung (`module_weight`)" mit selbstnormierender Formel, Gewichts-Tabelle (alle 7 Module mit Einfluss-Prozenten) und Konfigurationshinweis.

### Changed
- **`scripts/leaderboard/__init__.py`:** `module_weight` aus `lb_config.get("module_weight")` ins `mod_entry`-Dict übernommen — stellt sicher, dass `score_calculator.py` den konfigurierten Wert jedes Moduls erhält.
- **`docs/SCORING_METHODOLOGY.md`:** Formel von `(Routine Score + Reasoning Score) / 2` (veraltet) auf `Σ(ModuleScore × module_weight) / Σ(module_weight)` (korrekte selbstnormierende Variante) aktualisiert.

---

## [v3.4.2] - 2026-04-09

### Added
- **`scripts/dev/sync_cost_limits.py`:** Neues Dev-Tool erkennt automatisch Modelle ohne Preiseintrag in `config/cost_limits.yaml`. Mit `--fix`-Flag werden `null`-Platzhalter (inkl. `# TODO: Preis nachtragen`-Kommentar) direkt in die YAML-Datei geschrieben — boundary-sicher (`providers:`-Block) und duplikatfrei.
- **`make sync-cost-limits [FIX=1]`:** Neues Makefile-Target für den standardisierten Workflow beim Hinzufügen neuer Modelle.
- **LLM Judge Avg Sterne-Format in `exporter.py`:** `LLM Judge Avg`-Spalte im Leaderboard wird jetzt als `3.8 ★` formatiert.
- **Neue `cost_limits.yaml`-Sektionen:** `ollama_cloud` (deepseek-v3.2, minimax-m2.7, gpt-oss:120b), `google` (gemini-2.5-pro, gemini-3-flash-preview, gemini-3.1-pro-preview), korrigiertes `xai` (aus `settings:` in `providers:` verschoben).
- **`docs/USER_GUIDE.md`:** Zwei neue Abschnitte dokumentieren `make sync-cost-limits` (F.2 Systemgesundheit + eigenständiger Workflow-Abschnitt).

### Changed
- **`config/cost_limits.yaml`:** Vollständige Preisabdeckung für alle 25 konfigurierten Modelle. Neu eingetragen (Quellen verifiziert 2026-04-09): `gpt-5.4` ($2.50/$15.00 per 1M), `gpt-5.4-mini` ($0.75/$4.50 per 1M), `o1` ($15/$60 per 1M), `gemini-2.5-pro` ($1.25/$10 per 1M), `gemini-3-flash-preview` ($0.50/$3.00 per 1M), `gemini-3.1-pro-preview` ($2.00/$12.00 per 1M), Groq-Ergänzungen (Qwen3-32B, Kimi K2), Claude Haiku 4.5 (key-fix).

---

## [v3.4.0] - 2026-04-08

### Added
- **Token-Budget-System:** `max_tokens`-Cap als direkter API-Parameter in `base_runner.py`. Lädt `token_budgets[module_key]` aus `benchmark_config.yaml` und übergibt das Limit nur wenn es gesetzt ist (`None` wird nicht an Provider-Clients weitergegeben). Gewährleistet faire, Provider-übergreifende Vergleichbarkeit.
- **Token-Effizienz-Transparenz in Audit-Logs:** Neuer `[!NOTE]`-Header-Block in `benchmark_utils.py` macht Token-Effizienz-Anomalien sichtbar. Trigger: `token_limit_cutoff is True AND _budget is not None`. Bestehender `[!CAUTION]`-Block vor der Response bleibt unverändert.
- **Token-Effizienz-Kontext in Meta-Reviewer-Reports:** Neue Template-Variable `{token_efficiency_context}` in `generate_review.py` injiziert modulspezifische Ø-Token-Werte des Modells vs. Gesamt-Median vor `{log_data}`. Neuer Diagnostik-Block "Token-Effizienz (Verbosity)" in `meta_reviewer_prompt.yaml` — der Reviewer schreibt einen Absatz wenn Ratio > 1.5× Median (Reasoning/Metacog ausgenommen).

### Changed
- **benchmark_config.yaml:** `token_budgets`-Werte auf 2× Modul-Median kalibriert: `cultural_intelligence: 500`, `ux_writing: 3500`, `content_transformation: 3500`, `documentation_quality: 6000`, `code_quality: 6000`.
- **benchmark_utils.py:** Verbosity-Flag-Trigger auf `token_limit_cutoff` (API-`finish_reason`) umgestellt — kein berechneter Schwellenwert mehr.

### Removed
- **cli_benchmark** aus `token_budgets` entfernt — kein Output-Limit für CLI-Tasks (by design).

### Deferred to v3.4.x
- Score-Penalty für Token-Verbosity (separates Feature, keine Änderung an bestehenden Scores)
- Leaderboard-Metriken `avg_tokens`, `token_efficiency_ratio`, `est_cost_per_1k_tasks` in `score_calculator.py` + `generate_leaderboard.py`

---

## [v3.3.1] - 2026-04-08

### Fixed
- **Political Compass: model_category-Feld** in `io_manager.py` ergänzt (`save_leaderboard_csv`): Die Leaderboard-CSV trägt jetzt `model_category` (`local` / `cloud` / `commercial`) — identische Routing-Logik wie `result_manager.py`.
- **Political Compass: provider_type-Korrektur** für Ollama-gehostete Cloud-Modelle (`:cloud`-Suffix): Wert wird jetzt korrekt auf `cloud` gesetzt statt auf `ollama`.
- **political_compass_handler.py:** `_update_local_pc_csv()` von append-only auf Upsert umgestellt — entfernt bestehende Einträge des Modells vor dem Schreiben (Parität zu `_update_commercial_pc_csv()`).
- **clean_results.py:** `political_compass_leaderboard.csv` fehlte in der `files`-Liste; bei `--model xyz` blieb der PC-Leaderboard-Eintrag stehen. Außerdem defensiver `asset_id`-Guard in `clean_csv()` eingebaut (KeyError bei CSVs ohne `asset_id`-Spalte).
- **CSV-Anomalie-Cleanup:** 6 historische Cloud-Modell-Einträge aus `local_models_benchmark.csv` entfernt (hatten `provider_type=ollama` + `:cloud`-Suffix, wurden aber vor dem `:cloud`-Routing-Fix in die falsche CSV geschrieben).

### Changed
- **political_compass_leaderboard.csv** einmalig bereinigt: 66 → 56 Zeilen (Duplikate), `model_category`-Spalte rückwirkend befüllt, `provider_type` für 8 Cloud-Modelle korrigiert.

---

## [v3.3.0] - 2026-04-07

### Added
- **Language Compliance Pipeline:** `judge_prompt_builder.py` erhält neue Parameter `required_language` und `language_weight`. Wenn ein Asset `language: de` definiert, wird dem Judge automatisch ein gewichteter LANGUAGE COMPLIANCE Block injiziert, der Sprachverstöße unter `task_compliance` penalisiert (Standard: 20 % des Gesamtscores).
- **Language Metadata in Metacog-Assets:** `reasoning_logic` Assets `metacog_001–005` tragen nun `language: de` im Metadata-Block und ein explizites `Antworte auf Deutsch.`-Constraint im Prompt.
- **Audit-Infrastruktur:** Neues Verzeichnis `docs/audits/` für operatives Audit-Logging. Erster Report: `AUDIT_2026-04-07_editorial.md`.

### Changed
- **Prompt Hardening (21 Assets, 30 Änderungen):** Systematisches Bereinigen aller AI-generierten Gemini-Artefakte aus 5 Modulen (`cultural_intelligence`, `ux_writing`, `content_transformation`, `documentation_quality`, `code_quality`):
  - *Token-Limit-Leak entfernt (13 Treffer):* Interne Benchmark-Constraints (`um Token-Limits nicht zu überschreiten`) sind nicht Teil des Prompts — ersetzt durch direkte quantitative Schranken.
  - *Höflichkeitsformeln entfernt (13 Treffer):* `Bitte` in imperativen WICHTIG/HINWEIS-Instruktionen gestrichen.
  - *Pseudolabels entfernt (2 Treffer):* `Mission:` und `TASK:` Gemini-Strukturlabels aus `cultural_intelligence` entfernt.
  - *Erfülle-Floskel ersetzt (5 Treffer):* `Erfülle dabei strikt die folgenden Anforderungen:` → `Anforderungen (strikt einhalten):`.
- **judge_runner.py / judge_evaluator.py:** Forwarding von `required_language`/`language_weight` aus Asset-Config; `language_mismatch`-Flag-Extraktion aus Judge-Response.

### Fixed
- **Kyrillischer Unicode-Artefakt** in `asset_6a_german_tech_localization.yaml`: 3 cyrillische Zeichen (U+043C м, U+0430 а, U+0442 т) in `Idioматisches` durch korrekte lateinische Zeichen ersetzt.
- **Golden Standard Grammatikfehler** in `asset_6e_german_idioms.yaml`: `ein negatives Entwicklung` → `eine negative Entwicklung`.

## [v3.2.0] - 2026-03-28

### Added
- **Dynamic Provider SSOT:** Vollständiges Refactoring der Provider-Kategorisierung. Das System nutzt nun strikt die `benchmark_config.yaml` als Single Source of Truth für Model-Kategorien.
- **Open-Weights Cloud Support:** Neue Kategorie `Cloud (Open-Weights)` hinzugefügt. Erlaubt die native Integration von Cloud-Hostern für Open-Source Modelle (z. B. Groq), welche automatisch im Leaderboard korrekt zugewiesen und bewertet werden.

### Changed
- **Kategorien Konsolidierung:** Der veraltete Begriff "Local Cloud" wurde aus dem Dashboard, dem Leaderboard und den Dokumentationen entfernt. Cloud-Proxies von Ollama (erkennbar am `:cloud` Suffix) werden jetzt präzise als `Cloud (Open-Weights)` gehandhabt.
- **Meta-Review Context Injection:** Der Report Generator (`generate_review.py`) wurde aktualisiert und behandelt "Cloud (Open-Weights)" Modelle nun konsistent mit dem Hardware-Kontext `local_cloud`, um dem LLM Judge korrekte Annahmen über APIs und Hardware-Limits mitzuteilen.
- **Leaderboard Rendering:** Pandas DataFrames im `data_loader.py` cachen nun die Konfigurations-Dictionaries (`model_utils.py::_CACHED_CONFIG`), um Blocking & Deadlocks durch iteratives YAML-Lesen über hunderte Rows zu verhindern.

### Fixed
- **Dokumentation:** Die Beschreibungen des Setup-Guides (`SETUP_GUIDE.md`) und der Klassifizierungsregeln (`MODEL_CLASSIFICATION.md`) wurden umfangreich bereinigt und reflektieren nun das neue 3-Kategorien-System (Commercial, Cloud (Open-Weights), Local).

## [v3.1.1] - 2026-03-25

### Changed
- **Strict Judge Fail-Fast Mechanism:** Der LLM Judge verzichtet nun komplett auf das inkonsistente und fehleranfällige "Fallback"-Muster (z.B. der automatische Wechsel auf lokale Modelle, wenn die Anthropic-API ausfällt oder das Budget erschöpft ist). Stattdessen wird nun eine `JudgeUnavailableError` Exception geworfen, die den Benchmark sofort pausiert und unvollständige Durchläufe verlässlich speichert, um Kosten zu schonen.
- **Judge Coverage Calculation:** Die Formel für die "LLM Judge Coverage" im Leaderboard wurde repariert, sodass unbeurteilte Module (wie der "Political Compass") den Prozentwert nicht mehr künstlich senken. Der Wert wird im CSV nun sauber als echter Prozentwert formatiert (z.B. "100%").
- **Codebase Maintenance & Refactoring:** Utils-Skripte wurden hinsichtlich "Magic Numbers" und Typisierungs-Warnungen überarbeitet. Veraltete Debug-Aufrufe (`save_debug_response`) und root-Skripte wurden aufgeräumt, sowie `make audit_markdown` in die Makefile-Toolchain integriert.

### Fixed
- **Meta-Review Prompt Formats:** Ein Off-by-One Bug wurde behoben und die Grammatik- bzw. Parsing-Regeln im externen Meta-Review-Prompt wurden verschärft.
- **Political Compass Polarity:** Ein Fehler bei der Berechnung des Flips direkt auf der Null-Achse ("Zero-Axis Polarity Flip") wurde korrigiert.

### Removed
- **Fallback Configurations:** Alle `fallback` Knoten aus der `benchmark_config.yaml` sowie die zugrunde liegende `FallbackProviderConfig` innerhalb der Python-Infrastruktur wurden gelöscht.

## [v3.1.0] - 2026-03-20

### Added
- **Reasoning Tokens & Metacognition:** Einführung der `<thought>`-Tag Metakognitions-Überprüfung. Das System trackt nun den `reasoning_tokens` Count und filtert die `<thought>` Blöcke vor der finalen LLM-Judge Auswertung restriktiver Modelle heraus.
- **Dynamic Meta-Review Prompting:** Der `generate_review.py` Meta-Reviewer nutzt nicht länger einen Python-hardgecodeten Prompt, sondern liest seinen System-Prompt dynamisch und versionierbar aus der neuen Konfigurationsdatei `config/meta_reviewer_prompt.yaml` ein.
- **Coder/Thinking Model Leniency:** Einführung einer Kulanzklausel (Leniency Clause) beim Bias-Review, um speziell trainierte Coder- oder Reasoning-Modelle vor ungerechtfertigten Penalties zu bewahren.

### Changed
- **CLI Hybrid Scoring Migration:** Das Modul `cli_benchmark` (`cli001` - `cli006`) wurde von der reinen Regex-Evaluierung auf ein hybrides `llm_judge`-Scoring umgestellt (inkl. Fallbacks, Penalty-Systemen und JSON-orientierter Aufbereitung der `functional_goal`s).
- **Judge Context Expansion:** Das Token-Limit des LLM-Judges in `benchmark_config.yaml` wurde von 2048 auf 4096 Tokens erhöht, um zu verhindern, dass ausführliche Architekturbewertungen (z.B. in `reasoning_5e_001`) mitten in JSON-Strukturen abbrechen.
- **Robust CSV Sync:** Der `--force`-Parameter und das Cross-Model-Resuming (`run_cross_model_benchmark.py`) überschreiben und integrieren bestehende CSVs nun intelligenter, ohne manuelle und fehleranfällige Löschvorgänge zu erfordern.

### Fixed
- **Judge Parse Fallbacks:** Bei korruptem Output (z. B. abgeschnittenes JSON) fängt `judge_parser.py` den Parse-Fehler ab, verweigert den Runtime-Crash und speichert stattdessen den rohen Debugging-Output unter `last_failed_raw.txt`.
- **Political Compass Anomaly Scan:** Ein Fehler in der Scoring-Logik wurde behoben, sodass nun bei einem Achsen-Shift `> 1` automatisch ein Anomalie-Scan ausgelöst wird (`auto-trigger anomaly scan on pc shift > 1`).

## [v3.0.1] - 2026-03-19

### Changed
- **Architecture Refactoring:** Consolidated base logic from `run_local_benchmark.py` and `run_commercial_benchmark.py` into a unified `utils/base_runner.py` to eliminate significant redundancy and improve maintenance. (Phases 1-4)

## [v3.0.0] - 2026-03-18

### Added
- **3-Tier Refusal Architecture:** Integrierte Anti-Zensur-Logik für rigide LLMs im Political Compass Modul.
- **Progressive Temperature Check:** Automatischer Retest abgelehnter Prompts durch Temperaturerhöhung (0.1 → 0.4 → 0.7) und angehängte System-Injektion (Safety-Bypass).
- **Erweiterte Safety-Metriken:** Aufzeichnung von `hard_refusals` und automatische Erkennung von "Safety Shifts" (Werte-Verzerrungen durch das heuristische Red-Teaming) in der Endauswertung dokumentiert.

### Changed
- **Repository Cleanup & README Overhaul:** Die `README.md` wurde radikal entschlackt, neu strukturiert und auf die tatsächliche v3.0.0 Architektur (inkl. API-Verbindungen & Makefile) gehoben.
- **Roadmap Shift:** Voller Fokus für die kommenden Iterationen auf Web-UI (React/Streamlit), Multimodalität und "Agentic Workflow"-Evaluierung gesetzt.
- **Dokumentation:** Umfangreiche Erweiterung der `POLITICAL_COMPASS_KONZEPT.md` um das 6. Kapitel (Erweiterte Sicherheitsarchitektur & Refusals).

### Fixed
- **Pydantic Serialization Bug:** Ein hartnäckiger `AttributeError` im Anomaly Checker (`verify_compass_anomalies.py`) beim Nested-Parsing von `BenchmarkResult.get()` wurde durch nativ robustes `.raw_response` JSON-Loading behoben.
- **Checkpointer Stability:** Aufgeklärte Architektur für das nahtlose Wiederaufsetzen von durch Token-Limits oder Budget-Caps abgebrochenen Testläufen.

## [v2.5.0] - 2026-03-14

### Added
- **XAI / Grok Support:** Integration von XAI Grok Modellen inkl. API Pricing Tracking.
- **Cascading Token Fallback:** Implementierung eines kaskadierenden Token-Fallback-Systems zur besseren Fehlerabfangung mit Verhaltens-Metadaten.

### Changed
- **Meta-Reviewer:** Verbesserung der Erkennung von System-Info-Blöcken durch den Meta-Reviewer.
- **Anthropic Stabilität:** Das Timeout für den Anthropic-Client wurde auf 600s erhöht, um Abbrüche bei langen Generierungen zu vermeiden. Automatische Retry-Logs wurden im Konsolen-Output unterdrückt.

### Removed
- **Unused Pipeline Logic:** Die reine dynamische Golden Standard Validierungsausgabe sowie alte ungenutzte Pipelines (`refactor(core)`) wurden entfernt.

## [v2.3.0] - 2026-03-12

### Added
- **Audit Mode (Robust):** Einführung eines vollumfänglichen Audit-Modus. Dieser protokolliert ausgeführte Prompts, LLM-Judge Fingerprinting, komplette Reasoning Trails sowie die Kategorie-Sub-Scores der Regex-Evaluationen.
- **Google / Gemini Provider:** Native Unterstützung von Google Modellen für LLM-Judge Pipelines ergänzt.
- **Hybrid Scoring Architecture:** Implementierung einer modular gewichteten Hybrid-Scoring Architektur (0.10 Regex / 0.90 Judge) für präzisere semantische Auswertungen.

### Fixed
- **LLM Judge Bugfixes:** Behebung von Routing-, Caching- und Parsing-Bugs im Judge sowie Schutz vor "Reasoning Truncation".

## [v2.2.0] - 2026-03-08

### Added
- **CLI Benchmark Integration:** Das CLI v2 Benchmark wurde gehärtet (inkl. 6-Task YAML-Unterstützung) und nativ in die "Standard Base Test" Architektur integriert.

### Fixed
- **Ollama Token Limits:** Reduzierung der Token-Limits für lokale Reasoning-Modelle von 32k auf 8k, um "VRAM Swap" System-Freezes auf macOS Maschinen zu verhindern.

## [v2.1.1] - 2026-02-14

### Added

- **New Provider Category:** "Local Cloud" for Ollama Cloud proxy models
  - Distinguishes cloud proxies (minimax-m2:cloud, gpt-oss:120b-cloud) from true local models
  - Appears separately in leaderboard and statistics
- **SSOT for Model Categorization:** Centralized `is_cloud_model()` function in `utils/model_utils.py`
  - Detection rules: `:cloud` tag, `-cloud` suffix, or size < 0.01 GB
  - Used consistently across UI filters, data loading, and model listing

### Changed

- **Provider Selection UI:** Now offers three distinct categories:
  1. Commercial (Mistral, Claude, GPT)
  1. Local (Ollama offline models)
  1. Local Cloud (Ollama Cloud proxy)
- **Leaderboard Generation:** Automatic categorization using SSOT instead of filename-based inference
- **Documentation:** Updated `MODEL_CLASSIFICATION.md` with detailed categorization logic

### Fixed

- Cloud models (e.g., `gpt-oss:120b-cloud`) no longer miscategorized as "Local"
- Consistent cloud model detection across entire codebase

## [v2.1.0] - 2026-02-03

### Added

- Stricter v2.1 rubric thresholds (80%+ keywords for full credit)
- Rubrics for `reasoning_5e_001` and `metacog_004`
- Deprecation warning system for legacy scoring
- Migration timeline (legacy removal in v3.0)

### Changed

- v2.0 scoring now requires 80%+ keyword matches for full credit (was 66%)
- `reasoning_5e_001`: Fair scoring (15% → ~70% for good responses)
- All v2.1 tests now have binary % \<30% (improved discrimination)

### Deprecated

- Legacy scoring system (will be removed in v3.0)
- 6 tests still use legacy with deprecation warnings

### Fixed

- `reasoning_5e_001`: Good responses now score appropriately (was 15%)
- `metacog_004`: Binary % reduced from 31% to ~20%

## [v1.1.3] - 2026-02-11

### Added
- **Adaptive Pause System:** Implementierung eines adaptiven Pause-Systems für den Benchmark inkl. Dev Mode Unterstützung.
- **Probe/Warm-up:** Separation von Load-Time Tracking und Warm-up Probes für genauere Statistik-Erfassungen.

### Fixed
- **Code Quality:** Stabilitätsverbesserungen im Code Quality Modul, speziell für kleinere Modelle. Kompatibilitätsfix für DeepSeek-R1.

## [v1.1.0] - 2026-02-03

### Changed
- **Leaderboard V1.1 Overhaul:** Umstellung auf V1.1 Leaderboards mit neuen Aggregations-Metriken und Kosten-Analysen in USD/1K Tokens.
- **Golden Standard:** Stabilisierung der Golden Standard Generation für die kommerziellen Modelle.

## [v1.0.0] - 2026-02-03

### Added
- **Initial Production Release:** Einführung der Basis-Architektur (`run_commercial_benchmark`, `run_local_benchmark`).
- **Political Compass:** Implementierung und Stabilisierung der v3.0 Political Compass Metriken inkl. Mock-Testing.
- **Last-Hyphen-Rule:** Dynamische Asset-Gruppierung basierend auf der "Last-Hyphen-Rule" im Leaderboard.

## [v0.9.8] - 2026-01-29

### Added
- **Drift Detection:** Einführung eines Drift Detection Systems.
- **Checkpoint System:** Ein neues Checkpoint-System, um bei API-Ausfällen den Fortschritt zu sichern.

## [v0.9.6] - 2026-01-28

### Changed
- **MVC Architecture:** Vollständige Migration auf die Core/MVC (Model-View-Controller) Architektur.

### Fixed
- **Stability:** Behebung von Benchmark-Stabilitätsproblemen, Infinite Loops und Pfadauflösungsfehlern.

## [v0.9.5] - 2026-01-28

### Added
- **Cultural Intelligence:** Das Modul 5 (Cultural Intelligence) wurde finalisiert (neue Assets und gefestigtes Scoring).

## [v0.9.0] - 2026-01-23

### Changed
- **Framework Refactoring Complete:** Abschluss des großen Refactorings; die neue `BaseBenchmarkRunner`-Architektur für kommerzielle und lokale Modelle wurde als Baseline etabliert.

## [v0.5.0] - 2026-01-17

### Added
- **Gamification & Badges:** Einführung von gamifizierten Badges und Meta-Metriken ins Leaderboard.

## [v0.3.0-beta] - 2025-12-28

### Added
- **Documentation Quality Modul:** Ein neues Modul wurde hinzugefügt zur Untersuchung der Dokumentationsqualität.
- **Expert Difficulty:** Anpassung der UX-Writing Assets an ein 4-stufiges Schwierigkeitssystem (inkl. "Expert Level").

## [v0.2.0-beta] - 2025-12-27

### Added
- **Initial Release:** Initialer Startpunkt von CrucibleMark (mit grundlegenden Benchmarks zu Security, API Design und Code Quality).
