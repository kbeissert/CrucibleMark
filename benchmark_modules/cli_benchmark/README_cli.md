# CLI Benchmark Module

## Overview
Erweitertes Crucible Mark Benchmark-Modul zur sicheren Evaluation lokaler LLMs im Bereich Kommandozeilensteuerung (CLI). Das Modul nutzt eine simulierte Shell-Umgebung (ShellSimulator), um potentiell gefährliche Befehle (wie `rm -rf /`) während des Evaluierungsprozesses sicher abzufangen und dennoch eine präzise Bewertung der Modell-Logs vorzunehmen.

## Metrics & Scoring
Die Aufgaben basieren auf 5 Tiers (1: Basic -> 5: Complex) und werden gegen folgende Metriken evaluiert:
- **solutionquality (0-100)**: Erfüllt das Modell den Hauptzweck?
- **errordetection**: Werden gefährliche Parameter oder unzureichend verknüpfte Befehle vermieden?
- **tool-call-f1**: Werden die in den Aufgaben definierten Werkzeuge (`du`, `find`, `docker` etc.) explizit verwendet?

## Local API & M4-24GB Optimierung
Das Modul ist ausgelegt auf Ausführungen in High-Performant Local-Environments (z.B. M4-24GB RAM):
- Q6_K Quantisierungen für beste Routine-Reasoning Balance.
- Unterstützt Modelle wie `qwen2.5-coder-14b`, `ministral-38b`.
- Hard-Fail für Timeouts (>120s pro Task).

## Execution
Du kannst das Modul direkt über den standard `run_benchmark.py` Flow aufrufen:
```bash
python run_benchmark.py --module cli_benchmark --model qwen2.5-coder:14b
```

Oder alternativ den pytest runner bemühen, um den Simulator isoliert zu testen:
```bash
pytest benchmark_modules/cli_benchmark/test_cli.py -v
```

## Structure
- `tasks.py`: Lädt die mitgelieferte `cli_benchmark_tasks.csv` und konvertiert sie als Dataset für den Runner.
- `shell_sim.py`: Sandboxed Shell Mock zur Regex-Evaluation.
- `evaluator.py`: Kombiniert die Simulation mit Tools-Usage Metrics und formatiert diese in CrucibleMark Metrics.
- `test.py`: Die native Ausführungsklasse (integriert via `benchmark_config.yaml`).
