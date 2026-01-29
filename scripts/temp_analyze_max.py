import pandas as pd
from pathlib import Path

files = [
    "benchmark_scores/local_models_benchmark.csv",
    "benchmark_scores/commercial_models_benchmark.csv"
]

for f in files:
    path = Path(f)
    if not path.exists():
        print(f"{f} not found")
        continue
    
    try:
        df = pd.read_csv(path)
        if "max_score" in df.columns:
            print(f"--- {f} ---")
            print(f"Values: {df['max_score'].unique()}")
            print(f"Type: {df['max_score'].dtype}")
        else:
            print(f"max_score not in {f}")
    except Exception as e:
        print(f"Error reading {f}: {e}")
