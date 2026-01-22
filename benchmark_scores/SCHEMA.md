# CrucibleMark CSV Schema v1.0

## Columns (v1.0 - 2026-01-22)
- `model`: String (Ollama tag or API identifier)
- `total_score`: Float (0-100)
- `reasoning_score`: Float (Tier 2 score)
- `routine_score`: Float (Tier 1 score)
- `execution_time`: Float (seconds)
- `timestamp`: ISO 8601

## Breaking Changes
- v1.1 (planned): Add `cost_per_run` for commercial models
