# Progress

## Ongoing
- [ ] Phase 4: Finale E2E Systemtests und CI/CD Review
- [DONE] Metakognitions-Prüfung (<thought>-Tags) in Modulen und CSV integrieren
- [DONE] CLI-Benchmark auf Hybrid LLM-Judge umstellen
- [DONE] LLM Judge: Umbau auf natives JSON-Output (`judge_parser.py` + Prompts)
- [ ] LLM Judge: Batch-Mode (Phase 3.5)
- [ ] Volldurchlauf aller lokalen Modelle → finales Leaderboard (43/43 Tests)
- [ ] Re-run `reasoning_logic` für lokale Modelle (verfälschte 0-Punkte bereinigen)
- [ ] Stabilität `gpt-oss` analysieren (vorheriger Absturz-Kandidat)

## Abgeschlossen (Meilensteine)
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
