import pandas as pd
from pathlib import Path
from utils.model_utils import get_model_category

def migrate():
    local_path = Path("benchmark_scores/local_models_benchmark.csv")
    comm_path = Path("benchmark_scores/commercial_models_benchmark.csv")
    cloud_path = Path("benchmark_scores/cloud_models_benchmark.csv")

    dfs_to_save = {}

    for path, source in [(local_path, "local"), (comm_path, "commercial")]:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)

            # Identify cloud models
            cloud_mask = df.apply(
                lambda row, s=source: get_model_category(
                    row.get("model", ""),
                    s,
                    provider=row.get("provider", None)
                ) == "Cloud (Open-Weights)",
                axis=1
            )

            cloud_rows = df[cloud_mask]
            keep_rows = df[~cloud_mask]

            if not cloud_rows.empty:
                print(f"Moving {len(cloud_rows)} cloud rows from {path.name} to cloud CSV...")
                dfs_to_save[path] = keep_rows

                # Append to existing cloud rows
                if cloud_path in dfs_to_save:
                    dfs_to_save[cloud_path] = pd.concat([dfs_to_save[cloud_path], cloud_rows], ignore_index=True)
                else:
                    if cloud_path.exists():
                        dfs_to_save[cloud_path] = pd.concat([pd.read_csv(cloud_path), cloud_rows], ignore_index=True)
                    else:
                        dfs_to_save[cloud_path] = cloud_rows

        except Exception as e:
            print(f"Error processing {path.name}: {e}")

    # Save
    for path, df in dfs_to_save.items():
        print(f"Saving {len(df)} rows to {path.name}")
        df.to_csv(path, index=False)

if __name__ == "__main__":
    migrate()
