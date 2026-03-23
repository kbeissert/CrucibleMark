import re
from pathlib import Path

runs_dir = Path("outputs/runs")
files = list(runs_dir.glob("results_*.json"))
pattern = re.compile(r"results_(.*)_(\d{8}_\d{6})\.json")

models = set()
for f in files:
    match = pattern.match(f.name)
    if match:
        models.add(match.group(1))

print(models)
