# Active Context

## Was wurde heute fertiggestellt?
- Implementierung der voll funktionsfähigen Hybrid Scoring Architecture (Regex + LLM Judge Weighted Formula).
- Config-Hierarchie für `scoring_weights` (Asset-Level) und `scoring.fallback_weights` (Module-Level) in den Modul-Configs ergänzt.
- Neue Framework-Logik `calculate_hybrid_score` in `utils/scoring_utils.py` verankert und Variablen-Propagation im Loader repariert.
- Den Audit-Logger korrigiert, sodass in Hybrid-Logik (Regex + Judge) der Judgescore wieder korrekt in Markdown gerendet wird.

## Was ist der nächste logische Schritt?
- Phase 3.5 angehen: Umsetzung des Batch-Mode (Model Caching) für den LLM Judge, um das extrem hohe Lade-Overhead pro Task abzustellen.
- Alternativ / und danach: Volldurchlauf aller Modelle starten, um das finale Leaderboard mit den Hybrid-Scores zu befüllen.

## Welche offenen Fragen oder Risiken gibt es?
- LLM Judge Latency ohne Batch-Mode zu hoch (~40s pro Task).
- Einfluss der neuen hybriden Gewichtungsfaktoren (z.B. 25% Regex / 75% Judge) auf vorherige Benchmark-Rankings genau beobachten.
