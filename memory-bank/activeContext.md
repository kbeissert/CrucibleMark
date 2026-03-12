# Active Context

## Status
Erster erfolgreicher Lauf (Production) mit LLM Judge bestätigt, nun auch als primärer Score aktiv!

## Was wurde heute fertiggestellt? 
- Integration des LLM Judge Scores in `total_score` und `percentage` für qualitative Module bei erfolgreichem Parsing.
- Einführung des `scoring_method` (llm_judge | regex_fallback | skipped) Flags im CSV-Export (und Update in `ResultManager`).
- Dynamischer zur-Laufzeit-Fallback (`ANTHROPIC_API_KEY`-Prüfung in `judge_runner.py` via `os.getenv`), um nahtlos auf Ollama zurückzufallen.
- CLI-Modul Test-Fix für fehlerhafte Mock-Klasse.

## Was ist der nächste logische Schritt?
- Volldurchlauf aller lokalen Modelle starten, um das finale Leaderboard mit Judge-Daten zu befüllen.
- Umsetzung des **Batch-Mode** (Phase 3.5), da per-task Loading (~40s Overhead pro Task bei 9GB Modellen) extrem teuer ist.

## Offene Risiken / Bekannte Baustellen
- LLM Judge Latency: Jeder Judge-Aufruf lädt das Judge-Modell neu (9GB Model = ~40s).
- Post-run CSV Verifizierung der neu befüllten Scores, insbesondere `scoring_method`.
