# Active Context

## Status
Erster erfolgreicher Lauf (Production) mit LLM Judge bestätigt.

## Was wurde zuletzt fertiggestellt? 
- Namespace-Kollision (sys.modules) im dynamischen module_loader repariert (Routing-Bug behoben).
- VRAM Memory Leaks durch unsaubere Thread-Terminierungen aufgelöst.

- LLM Judge Modul ist vollständig implementiert und getestet.
- LLM Judge Markdown-Ausreißer geparsed (`judge_parser.py` Regex erweitert).
- Ollama Judge Request Timeout hochgesetzt (30s auf 120s in SSOT Config).
- Hardcoding in `judge_health.py` entfernt, liest nun komplett aus `benchmark_config.yaml`.
- Pydantic Validierungs-Bug (ValidationError in Config) und Leaderboard TypeError `None` Bug in `__init__.py` behoben. Alle 165 Tests grün.

## Was ist der nächste Schritt?

- Option B: Umsetzung des **Batch-Mode** (Phase 3.5)
- Option B: Umsetzung des **Batch-Mode** (Phase 3.5), da per-task Loading (~40s Overhead pro Task bei 9GB Modellen) extrem teuer ist.

## Offene Risiken / Bekannte Baustellen

- LLM Judge Latency: Jeder Judge-Aufruf lädt das Judge-Modell neu (9GB Model = ~40s). Erfordert Batch-Mode.
- Post-run CSV verification of llm_judge_* columns.
- Re-run reasoning_logic Benchmark (lokale Modelle, verfälschte 0-Punkte).
- Volldurchlauf aller lokalen Modelle (43/43) für finales Leaderboard.
