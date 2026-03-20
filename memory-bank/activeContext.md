# Active Context

- Abgeschlossen: Metakognitions-Prüfung (`<thought>`-Tags) implementiert, CLI-Scoring auf natives llm_judge überführt, Judge Parser-Fallbacks eingebaut und Meta-Review Prompting in YAML exportiert.
- Nächster Schritt: Cross-Model-Runs für `reasoning_logic` und fehlende `code_quality`-Logs via `--force` erfolgreich abschließen, um alle neuen Leaderboard-Felder zu füllen.
- Offen/Risiko: Tiefe API-Token-Limits können bei alten Modellen trotz 4096-Erhöhung große JSON-Scoring-Strukturen abbrechen.
