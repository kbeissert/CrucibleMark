import pandas as pd
df = pd.read_csv("benchmark_scores/cloud_models_benchmark.csv")
kimi = df[df['model'] == 'moonshotai/kimi-k2-instruct']
print(kimi.iloc[0].to_dict())
