# Active Context

## Abgeschlossen
- Golden Standards in YAML als SSOT konsolidiert; obsolete rohe Referenzdaten (`outputs/reference-logs/`) zugunsten verdichteten ("Design by Intention") Standards gelöscht.
- Tooling zur Inhaltsvalidierung existiert für Audit-Zwecke, manueller Workflow aber etabliert.

## Nächster Schritt
- LLM Judge Pipeline auf strikte JSON-Rückgabe umbauen (`judge_parser.py` + Prompts) oder Implementierung des Batch-Mode (Phase 3.5).

## Offen / Risiko
- Kleine Judge-Modelle (wie Mistral/Ollama-basierte): JSON-Konsistenz als Evaluator unter realen Bedingungen noch unbewiesen.
