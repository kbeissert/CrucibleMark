import pandas as pd
import glob
import math

files = glob.glob("benchmark_scores/*benchmark.csv")
for f in files:
    try:
        df = pd.read_csv(f)
        if 'model' in df.columns:
            kimi = df[df['model'] == 'moonshotai/kimi-k2-instruct']
            for _, row in kimi.iterrows():
                score = row.get('llm_judge_score')
                if pd.isna(score) or str(score) == 'nan' or score == 0.0 or str(score).strip() == '':
                    print(f"File: {f}")
                    print(f"Test: {row.get('asset_id')}")
                    print(f"Status: {row.get('status')}")
                    print(f"Judge Score: {score}")
                    print(f"Error: {row.get('error')}")
                    print(f"Percentage: {row.get('percentage')}")
                    print(f"Total Score: {row.get('total_score')}")
                    print("---")
    except Exception as e:
        pass
