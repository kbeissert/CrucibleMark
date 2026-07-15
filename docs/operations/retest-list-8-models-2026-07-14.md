# Retest-Liste: 8 Modelle, je 1–3 Befehle pro Modell

**Stand:** 2026-07-14

**Quelle:** Gap-Detection auf `outputs/audit_logs/` (Dateinamen-Klassifikation) vs. `benchmark_leaderboard_detailed.csv`.

**Was NICHT auf der Liste steht (und warum nicht):**
- `gemini-2.5-pro`, `llama-3.3-70b-versatile`, `grok-4.3`, `qwen2.5-coder-7b` — vollständige `audit_logs/` vorhanden, nur fehlt der LB-Eintrag. **Kein Re-Test**, ein `make leaderboard` rendert sie nach.
- 24 OpenRouter-Modelle mit "Tests 48/49" — alle Module vollständig in `audit_logs/`, LB zählt falsch. → `make leaderboard` reicht.
- `meta-llama/llama-4-scout-17b-16e-instruct`, `qwen/qwen3.7-max`, `qwen/qwen3.6-plus`, `minimax/minimax-m2.7-20260318` — `audit_logs/` vollständig, LB-Eintrag nur unvollständig gerendert. → `make leaderboard`.

---

## Die 8 echten Retest-Kandidaten

### 1. `qwable-3.6-35b-q5` (Spark llamacpp)
Kein `audit_dir` vorhanden — Modell wurde noch nie getestet.

```bash
make benchmark MODEL=qwable-3.6-35b-q5 MODULE=code_quality
make benchmark MODEL=qwable-3.6-35b-q5 MODULE=cli_benchmark
make benchmark MODEL=qwable-3.6-35b-q5 MODULE=ux_writing
make benchmark MODEL=qwable-3.6-35b-q5 MODULE=documentation_quality
make benchmark MODEL=qwable-3.6-35b-q5 MODULE=content_transformation
make benchmark MODEL=qwable-3.6-35b-q5 MODULE=cultural_intelligence
make benchmark MODEL=qwable-3.6-35b-q5 MODULE=reasoning
make benchmark-tooluse MODEL=qwable-3.6-35b-q5
make political-compass MODEL=qwable-3.6-35b-q5
```

### 2. `command-a-plus-05-2026` (Cohere)
`audit_logs` vollständig (alle 7 Score-Module + PC), aber ToolUse fehlt komplett.

```bash
make benchmark-tooluse MODEL=command-a-plus-05-2026
```

### 3. `gpt-5-mini-2025-08-07` (OpenAI)
Score-Module + PC vollständig, ToolUse 1 von 6 Assets.

```bash
make benchmark-tooluse MODEL=gpt-5-mini-2025-08-07
```

### 4. `openai/gpt-oss-20b` (OpenRouter)
Score-Module + PC vollständig, ToolUse fehlt komplett.

```bash
make benchmark-tooluse MODEL=openai/gpt-oss-20b
```

### 5. `deepseek-r1-distill-qwen-32b` (lokal)
Score-Module + PC vollständig, ToolUse fehlt komplett.

```bash
make benchmark-tooluse MODEL=deepseek-r1-distill-qwen-32b
```

### 6. `qwen3_6-27B-thinking` (vLLM-Spark)
Score-Module + PC vollständig, ToolUse fehlt komplett.

```bash
make benchmark-tooluse MODEL=qwen3_6-27B-thinking
```

### 7. `gemma-4-31b-it-creative-wordsmith-q8` (lokal)
ToolUse vollständig, Score-Lücken: `content_transformation` 5/6 + `political_compass` fehlt.

```bash
make benchmark MODEL=gemma-4-31b-it-creative-wordsmith-q8 MODULE=content_transformation
make political-compass MODEL=gemma-4-31b-it-creative-wordsmith-q8
```

### 8. `hermes-4.3-36b-q6` (lokal)
ToolUse vollständig, Score-Lücken: `code_quality` 2/5 + `documentation_quality` 3/5.

```bash
make benchmark MODEL=hermes-4.3-36b-q6 MODULE=code_quality
make benchmark MODEL=hermes-4.3-36b-q6 MODULE=documentation_quality
```

---

## Abschluss

```bash
make leaderboard
```

Rendert `benchmark_leaderboard.csv` aus den vervollständigten `audit_logs/` neu.

---

## Aufwands-Schätzung

| Modell | Befehle | Geschätzter Aufwand |
|---|---|---|
| 1. qwable-3.6-35b-q5 | 9 | hoch (komplett neu) |
| 2–6. 5× ToolUse-Only | je 1 | niedrig (nur 6 Assets) |
| 7. gemma-4-31b-it-… | 2 | mittel |
| 8. hermes-4.3-36b-q6 | 2 | mittel |
| **Summe** | **17 Befehle** | statt 8× voller Benchmark = 392 Tests |

Statt 392 Benchmark-Aufrufen für die 8 Modelle werden durch die Modul-spezifischen Befehle nur die echten Lücken geschlossen.