# Active Context

## Abgeschlossen
- Globales kaskadierendes Token-Fallback-System implementiert, inkl. transparentem Metadaten-Tracking ("Kopfnoten") in der Leaderboard-Auswertung.
- Meta-Reviewer/Editor (`generate_review.py`) aktualisiert, um via Regex kritische Systemwarnungen ("SYSTEM INFO" / Token-Limit-Fallbacks) aus den Audit-Logs zu lesen. Historische Haiku-Daten erfolgreich gepatcht.

## Nächster Schritt
- LLM Judge Pipeline auf strikte JSON-Rückgabe umbauen (`judge_parser.py` + Prompts) oder Implementierung des Batch-Mode (Phase 3.5).

## Offen / Risiko
- Kleine Judge-Modelle (wie Mistral/Ollama-basierte): JSON-Konsistenz als Evaluator unter realen Bedingungen noch unbewiesen.
