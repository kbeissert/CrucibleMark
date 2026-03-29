# Active Context

**Last Updated:** 2026-03-29
**Session:** Data-Routing Bugfix & Performance Optimization (v3.2.1)

## Erledigte Aufgaben (diese Session)

### Performance & Cache Repair (v3.2.1 Bugfixing)
- **Data-Routing Bugfix:** Behebung eines kritischen Fehlers im `UnifiedBenchmarkRunner`, der dazu führte, dass die Ergebnisse von kommerziellen Modellen ins `local_models_benchmark.csv` geschrieben wurden. Dies hat die Auto-Resume-Logik vollständig wiederhergestellt.
- **Datenbereinigung:** Skriptbasiert 75 fehlgeleitete Scores von der lokalen in die kommerzielle Tabelle überführt, ohne Datenverlust herzustellen.
- **Lazy Loading Implementation:** `sentence_transformers` in `utils/similarity.py` wird erst zur Laufzeit geladen (massiv reduziertes Boot-Up).
- **Groq API Ping repariert:** Der Connection-Bouncer wurde auf `llama-3.1-8b-instant` umgestellt.
- **CLI Metrics Update:** In `unified_runner.py` wurde der Summary Output im Terminal überarbeitet. Durchschnitts-Scores, Geschwindigkeiten und Tokens/USD Preise werden jetzt wieder korrekt direkt nach Abschluss visualisiert.

### Textüberarbeitung & SSOT (vorhergehende Session - v3.2.0)
- Veraltete Hardcodings für "Local Cloud" wurden aus Data Loadern, Utilities und Judge-Scripts entfernt.
- Neue Kategorie `Cloud (Open-Weights)` (Groq) verankert.
- Konfigurations-Driven Provider (`benchmark_config.yaml` als echte SSOT).
