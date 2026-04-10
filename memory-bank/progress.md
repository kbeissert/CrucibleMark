# Progress

## Ongoing
- [ ] gpt-5.4-mini cultural_intel 108-Token-Anomalie: --force Re-Run prüfen
- [ ] Backup-Dateien löschen: local_models_benchmark.csv.bak, political_compass_leaderboard.csv.bak, *.pre_retest_bak
- [ ] Phase 4: Finale E2E Systemtests und CI/CD Review
- [ ] LLM Judge: Batch-Mode (Phase 3.5)

## Abgeschlossen (Meilensteine)
- [DONE] v3.4.2 Vollständige Preis-Datenbasis & Sync-Tool (2026-04-09): cost_limits.yaml alle 25 Modelle mit verifizierten Preisen (gpt-5.4, gpt-5.4-mini, o1, gemini-2.5-pro, gemini-3-flash-preview, gemini-3.1-pro-preview + Groq/ollama_cloud neu). sync_cost_limits.py als neues Dev-Tool (make sync-cost-limits [FIX=1]). LLM Judge Avg als ★-Format. USER_GUIDE.md dokumentiert. Commit 6b917f9.
- [DONE] Scorer-Bugfix: metacog_004 Monty Hall (2026-04-09): `_has_correct_probability()` und `_has_switch_intent()` neu geschrieben mit EN+DE Regex, Float-Toleranz ±0.05, Dezimalformat. `iterative_refinement` von `"initial"/"first"` auf 30 bilinguale Rethinking-Phrasen umgebaut. `probability_analysis` prüft jetzt `thought OR answer`. Alle 24 stale CSV-Zeilen entfernt (local 8, cloud 3, commercial 13). Scorer-Ergebnis: 34–73% statt systematisch 0%.
- [DONE] Scorer-Bugfix: documentation_quality max_score (2026-04-09): `test.py` `execute()` hatte `max_score=100.0` hardcoded, alle 5 Assets haben aber `total_points: 130`. Fix in `score_response()`: `result.max_score = score_dict.get("max_score", result.max_score)`. Alle 45 stale CSV-Zeilen entfernt (local 30, cloud 15). README-Scoring-Tabelle korrigiert (70/30% → 77/23% Rohpunkte). Fallstrick: `execute()` kennt `total_points` nicht — nur `score_response()` hat Zugriff auf den Evaluator-Output.
- [DONE] v3.4.1 Token-Verbrauch im Leaderboard (2026-04-08): Tokens Total/per-Modul auf scoring_df-Basis (PC exkl.), Cost per 1K via cost_limits.yaml-Lookup (kein Typ-Hardcode), Benchmark Cost-Spalte, K-Formatierung, Spaltenreihenfolge. Commit 2bd951a.
- [DONE] v3.4.0 Token-Budget & Verbosity-Transparenz (2026-04-08): max_tokens API-Cap in base_runner.py, [!NOTE]-Block in benchmark_utils.py, {token_efficiency_context} + Verbosity-Diagnostik in generate_review.py + meta_reviewer_prompt.yaml. Vollständige Doku-Aktualisierung (README, CHANGELOG, PROJECT_STATUS, REF_TODO, 3 docs/*.md, 6 Modul-READMEs). CSV-Cleanup (189 obsolete Zeilen, 11 Dateien, gpt-5-mini aus Config).
- [DONE] Modul-READMEs v2 (2026-04-08): Alle 7 READMEs vollständig neu geschrieben mit per-Asset-Dokumentation, Transparenz-Sektionen und Scoring-Methodik-Tabellen für externe Entwickler.
- [DONE] Political Compass Integration (2026-04-08): io_manager.py +model_category +cloud-provider_type-Erkennung; political_compass_handler.py append→upsert; clean_results.py +PC Leaderboard +asset_id-Guard; einmalige CSV-Bereinigung 66→56 Zeilen.
- [DONE] CSV-Anomalie-Cleanup (2026-04-08): 6 Cloud-Modell-Einträge aus local_models_benchmark.csv entfernt (495→489); quota-exhaustion skip-Logik in benchmark_auto.py + unified_runner.py.
- [DONE] v3.3.0 Language Compliance & Prompt Hardening (2026-04-07): Language Compliance Pipeline (judge_prompt_builder.py required_language/language_weight, metacog-Assets mit language:de), Editorial Audit 30 Fixes in 21 Assets (Token-Limit-Leaks, Höflichkeitsformeln, Pseudolabels, Unicode-Artefakt in asset_6a, GS-Grammatik asset_6e), 492 stale CSV-Zeilen bereinigt, Versionssynchro README/CHANGELOG/docs auf v3.3.0. Commits 404a670, 8c5eec3, d7e939b.

## Abgeschlossen (Meilensteine)
- [DONE] Audit Fixes & Scoring Integrity Patch (2026-04-07): Hard Constraints via YAML `constraints.max_expected_words`, progressive 3-Tier-Penalty, Language Mismatch Auto-Flag (`unified_runner.py`), uxwriting002 Two-Step Headers, Asset Hardening (WCAG 2.2 + Security), Docs. Commit 31615c5.
- [DONE] Vollständiger CSV-Reset & Rubric-Cleanup (2026-04-06): Alle non-political_compass-Einträge aus 3 CSVs gelöscht (alte Rubric-Scores nicht mehr vergleichbar). Provider-Bug gefixt (Groq-Modelle mit `/` wurden als "commercial" statt "open_weights_cloud" klassifiziert). kimi-k2-instruct Doppeleintrag bereinigt (model_version-Feld).
- [DONE] Modell-Architektur-Tags (v3.2.x): Dynamische Tag-Extraktion (Thinking, Instruct, Preview, Uncensored) in model_utils.py implementiert und in LLM-Judge (`judge_prompt_builder.py`) sowie Meta-Reviewer verankert, um architektonische Eigenheiten fair in die Bewertung (z.B. Verbosity) einfließen zu lassen.
- [DONE] Performance & Cache Repair (v3.2.1): Data-Routing in CSV-Logs stabilisiert (Fehlzuweisungen in lokale Tabellen behoben). Lazy Loading für Transformers eingeführt. Konsolen-Summary inklusive Kostenanzeige reanimiert. Groq Provider repariert.
- [DONE] Kategorien-SSOT (v3.2.0): "Local Cloud" Deprecation und vollständige Migration auf "Cloud (Open-Weights)" (Groq, etc.) in Utilities, Leaderboard und Meta-Reviewer Logik.
- [DONE] Metakognitions-Prüfung (<thought>-Tags) in Modulen und CSV integrieren
- [DONE] CLI-Benchmark auf Hybrid LLM-Judge umstellen
- [DONE] LLM Judge: Umbau auf natives JSON-Output (`judge_parser.py` + Prompts)
- [DONE] Web-Export Pipeline (`scripts/web_export.py`) als Bindeglied für unabhängiges 11ty Frontend-Projekt entwickelt. Konvertiert CSVs in hierarchisches JSON und dedupliziert Markdown-Logs für Templating-Engines. Konfigurierbarer Ausgabeordner etabliert (`output.web_export_dir`). Maintenance Skripte (`clean.py`) für Virtual Environments stabilisiert.
- [DONE] SSOT Provider Refactoring & Fail-Fast Fallback-Löschung für alle Integrationen (google, anthropic, mistral). Pylint Score auf pure 10/10 inkl. Pyright Type-Ignore `reportPrivateImportUsage`.
- [DONE] "Judge: skip (zu kurz/abgelehnt)" Output in `unified_runner.py` implementiert, um transparente Ablehnungen im Log abzubilden.
- [DONE] Runner-Konsolidierung (`UnifiedBenchmarkRunner`), CLI-Fixes und strikte Pylint/Pylance Fehlerbehebung.
- [DONE] Local/Commercial Model Versioning bereinigt (`latest` & `k.A.` Entries), Regex Parser in `model_utils.py` für O1/O3/Grok + korrekte Ollama-Hash-Auflösung von Local-Community Models implantiert.
- [DONE] Off-by-one Parsing Bug & Grammatik Halluzinationen im LLM Judge (meta_reviewer_prompt.yaml) durch strukturelle Anker gelöst.
- [DONE] Pydantic Validation Error in `BenchmarkResult` für `model_version` (`None` -> `"unknown"`) gefixt und Lazy-Import in `xai.py` ausgebessert.
- [DONE] LLM Judge Bugfix (0% vs 20% Base-Score behoben, Skala korrigiert auf 0-5).
- [DONE] Verwaisten Golden-Standard Ordner entfernt und Makefile-Cleans nachgezogen.
- [DONE] Phase 3 Refactoring: Code-Modularisierung (utils/providers/), Namespace-Bereinigung, Magic-Numbers extrahiert, Pytest/Mypy/Pylint Pipeline-Erfolg.
- [DONE] Release v2.6.1: Stability & Context Handling (API Trimming gegen Token Loops).
- [DONE] Documentation Consolidation (README, REF_TODO, PROJECT_STATUS strukturell an benchmark_config.yaml angeglichen)
- [DONE] Git Freeze (v2.6.1 Tag) gesetzt.
- [DONE] Political Compass vollumfänglich von Score-System entkoppelt (44/43 Bug behoben), Position/Token-Bias durch Random-Alphas eliminiert.
- [DONE] Akademisches "Prompt-as-Config" Tier-System (Platin ab 95%) etabliert und in Pipelines integriert.
- [DONE] "System Info" Warnungen + Token Fallback Extraktion in Meta-Reviewer.
- [DONE] Globales kaskadierendes Token-Fallback & Provider Error Handling ("Fast-Fail" für Budget, Metadaten in Ergebnissen)
- [DONE] Golden Standard Validierung und SSOT-Konsolidierung (`asset.yaml` Blöcke verifiziert, obsoletes LLM-Referenz-Raw-Log System entfernt). Project Status geupdated.
- [DONE] LLM Judge Modul vollständig implementiert (Phase 1–3.5): Provider-Abstraktion,
  Fallback-Chain, Pipeline-Integration, ResultManager-Schema, Batch-Vorbereitung
- [DONE] Hybrid-Scoring Architektur: gewichtete Regex/Judge-Scores, Fallback-Weights
- [DONE] Konfig-Architektur finalisiert: `benchmark_config.yaml` als SSOT,
  `config.example.yaml` auf Modul-Override verschlankt
- [DONE] Code-Qualität: Mypy/Pylint clean, pandas-stubs, IDE-Formatierung
- [DONE] Erste echte Benchmark-Runs erfolgreich (Single Module + Cache-Validierung)
- [DONE] Kritische Bugfixes: Namespace-Kollision (importlib), Parser-Cutoff
  (implicit_separator), is_complete()-Deadlock, Leaderboard-Asterisk Bug
- [DONE] Architektur-Refactoring (v3.2.2): Übergang von 2-CSV auf 3-CSV Datenpersistenz (lokal, cloud, commercial) in `benchmark_config.yaml`, core result_manager logic und Leaderboard Aggregation.
