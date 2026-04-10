"""One-shot script: Rename 'Efficiency Score' column to 'Tokens/s' in leaderboard CSVs."""
from pathlib import Path

files = [
    Path("benchmark_scores/benchmark_leaderboard.csv"),
    Path("benchmark_scores/benchmark_leaderboard_detailed.csv"),
]

for fp in files:
    if not fp.exists():
        print(f"SKIP (not found): {fp}")
        continue
    content = fp.read_text(encoding="utf-8")
    updated = content.replace("Efficiency Score", "Tokens/s")
    fp.write_text(updated, encoding="utf-8")
    print(f"Fixed: {fp}")
