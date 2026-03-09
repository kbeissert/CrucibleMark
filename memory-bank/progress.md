# Progress

## Completed

- [DONE] Konfigurations-Hierarchie und Laufzeitparameter vereinheitlicht
- [DONE] Fix infinite loops in Hermes3 (Code Quality Module)
- [DONE] Integration von Google Gemini (2.5 / 3.0 Serie) und xAI Grok (3 / 4) in Config und Pricing-Pipeline
- [DONE] Bugfix im `reasoning_logic` Evaluator: Parsing-Cutoffs bei `implicit_separator` ("**Answer:**") für Standard Logic-Tests verhindert
- [DONE] Refaktorierung von `cli_benchmark` für korrekte `BaseTest`-Integration und Einzel-Test Ausführung.
- [DONE] Fix Leaderboard-Asterisk Bug (`*`) durch Ergänzung des Modul-Präfix in der `cli_benchmark/config.yaml`.
- [DONE] MyPy-Fehler Zeile 35 in `run_commercial_benchmark.py` behoben (Optional-Import Type-Hint). Pylint: 10/10.

## Ongoing

- [ ] Re-run des `reasoning_logic` Benchmarks für (lokale) Modelle, um verfälschte 0-Punkte Resultate auszugleichen
- [ ] Analyse der Stabilität von `gpt-oss` (vorheriger Absturz-Kandidat)
- [ ] Monitor full benchmark suite execution
- [ ] Volldurchlauf des Benchmarks für alle lokalen Modelle starten, um das finale Leaderboard (43/43 Tests) zu befüllen.
