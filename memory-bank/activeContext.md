# Active Context

## Abgeschlossen
- Bugfixes (Local LM Hash Truncation, Meta-Reviewer Parser Error).
- Umstellung auf asymmetrisches akademisches Tiersystem (Platin ab 95%, Gold ab 80%) als Maßnahme gegen Noteninflation bei holistischen Benchmarks.
- "Prompt-as-Config"-Pattern auf Scoring-Tiers ausgeweitet: System-Grenzgrenzwerte sind nun in `benchmark_config.yaml` zentralisiert. `formatter.py` und `generate_review.py` laden Ränge/Prompts dynamisch.

## Nächster Schritt
- Political Compass Modul (Score-Kategorisierung und Auswertung) stark überarbeiten, um in Meta-Reviews tiefgreifende Ethik/Bias-Kategorien (wie Wirtschaft v. Gesellschaft) anstelle eines einzelnen Rankings abzubilden.

## Offen / Risiko
- Keine