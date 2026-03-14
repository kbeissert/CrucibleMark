# Active Context

## Abgeschlossen
- Globales kaskadierendes Token-Fallback-System implementiert, inkl. transparentem Metadaten-Tracking ("Kopfnoten") in der Leaderboard-Auswertung.

## Nächster Schritt
- LLM Judge Pipeline auf strikte JSON-Rückgabe umbauen (`judge_parser.py` + Prompts) oder Implementierung des Batch-Mode (Phase 3.5).

## Offen / Risiko
- Kleine Judge-Modelle (wie Mistral/Ollama-basierte): JSON-Konsistenz als Evaluator unter realen Bedingungen noch unbewiesen.
