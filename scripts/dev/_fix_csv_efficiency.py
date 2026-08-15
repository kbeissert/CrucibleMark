"""One-shot script (EXECUTED 2026-08 — DO NOT RE-RUN): Rename 'Efficiency Score'
column to 'Tokens/s' in leaderboard CSVs.

Historisches Artefakt der Spalten-Rename-Migration. Bleibt als Dokumentation
erhalten — ein erneuter Lauf ist ein No-Op (String kommt nicht mehr vor),
sollte aber bewusst nicht ausgeführt werden. Unterstrich-Prefix verhindert
versehentliche Ausführung über Glob-Iterationen.
"""
import sys

if __name__ == "__main__":
    print("DO NOT RUN: One-Shot-Migration bereits 2026-08 ausgeführt "
          "(Efficiency Score → Tokens/s).", file=sys.stderr)
    sys.exit(1)

# Ursprüngliche Implementierung (dokumentativ, nicht mehr ausführbar):
# from pathlib import Path
# files = [
#     Path("benchmark_scores/benchmark_leaderboard.csv"),
#     Path("benchmark_scores/benchmark_leaderboard_detailed.csv"),
# ]
# for fp in files:
#     content = fp.read_text(encoding="utf-8")
#     fp.write_text(content.replace("Efficiency Score", "Tokens/s"), encoding="utf-8")
