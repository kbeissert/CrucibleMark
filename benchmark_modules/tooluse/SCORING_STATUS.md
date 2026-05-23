# Tool Use Scoring — Aktueller Status

## Vorläufige Scores — Kein Golden Standard

Alle P2- und Combined-Scores in `tooluse_leaderboard.csv` sind **vorläufig**.

**Grund:** Der Golden Standard (Referenzantworten pro Asset) ist noch nicht
definiert. P2 bewertet aktuell Keyword-Overlap und semantische Ähnlichkeit
gegen einen vorläufigen Erwartungswert — nicht gegen eine manuell validierte
Idealantwort.

## Was das bedeutet

- P1-Scores (Tool Execution) sind **stabil** — regelbasiert, kein Golden Standard nötig
- P2-Scores (Synthesis Quality) sind **relativ**, nicht absolut
- Combined-Scores sind entsprechend vorläufig
- Sovereignty Gap und Rankings dienen zur Orientierung, nicht als finale Aussage

## Geplante Kalibrierung

Nach dem ersten vollständigen Batch-Run (alle Tool-Use-Modelle):
1. Alle Antworten manuell sichten (`docs/reviews/*/tooluse_review_*.md`)
2. Idealantworten pro Asset als Golden Standard definieren
3. P2-Gewichtung und Keyword-Liste neu justieren
4. Alle Modelle neu berechnen (`make benchmark-tooluse --force`)

## Zeitplan

- [ ] Vollständiger Batch-Run (alle ~25 Tool-Use-Modelle)
- [ ] Manuelle Sichtung der Reports
- [ ] Golden Standard Definition
- [ ] Neukalibrierung P2-Scoring
- [ ] Finale Scores
