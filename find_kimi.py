import pandas as pd
import glob

files = glob.glob("benchmark_scores/*benchmark.csv")
for f in files:
    try:
        df = pd.read_csv(f)
        if 'model' in df.columns:
            kimi = df[df['model'] == 'moonshotai/kimi-k2-instruct']
            for _, row in kimi.iterrows():
                # Let's check judge related columns
                # 'judge_score', 'eval_score', 'reasoning', 'error'
                if pd.isna(row.get('judge_score')) or str(row.get('judge_score')) == 'nan' or str(row.get('judge_score')) == '0.0' or row.get('status') != 'success':
                    print(f"File: {f}, Test: {row.get('asset_id')}, Status: {row.get('status')}, Judge Score: {row.get('judge_score')}, Eval Score: {row.get('eval_score')}, Error: {row.get('error')}")
    except Exception as e:
        pass
