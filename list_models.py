import pandas as pd
ldb = pd.read_csv("benchmark_scores/benchmark_leaderboard_detailed.csv")
print(ldb["Model Name"].unique())
