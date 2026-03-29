import pandas as pd
import os

local_csv = 'benchmark_scores/local_models_benchmark.csv'
comm_csv = 'benchmark_scores/commercial_models_benchmark.csv'

df_local = pd.read_csv(local_csv, dtype=str) if os.path.exists(local_csv) else pd.DataFrame()
df_comm = pd.read_csv(comm_csv, dtype=str)

models_to_move = ['gpt-oss:120b-cloud']
rows_to_move = df_comm[df_comm['model'].isin(models_to_move)]

if not rows_to_move.empty:
    print(f"Found {len(rows_to_move)} rows of 'gpt-oss:120b-cloud' in commercial CSV. Moving back to local.")

    if not df_local.empty and 'asset_id' in df_local.columns and 'model' in df_local.columns:
        local_keys = set(zip(df_local['model'], df_local['asset_id']))
        mask = ~rows_to_move.apply(lambda row: (row['model'], row['asset_id']) in local_keys, axis=1)
        rows_to_move = rows_to_move[mask]

    df_local = pd.concat([df_local, rows_to_move], ignore_index=True)
    df_comm = df_comm[~df_comm['model'].isin(models_to_move)]

    df_local.to_csv(local_csv, index=False)
    df_comm.to_csv(comm_csv, index=False)
    print("Restore complete.")
else:
    print("No gpt-oss:120b-cloud rows found in commercial CSV.")
