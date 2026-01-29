import pandas as pd
from pathlib import Path

# Mapping based on 'ollama list' output
ID_MAP = {
    "cogito:14b": "d0cac86a2347",
    "deepseek-r1:14b": "c333b7232bdb",
    "qwen2.5:14b-instruct": "7cdf5a0187d5",
    "dolphin-llama3:8b": "613f068e29f8",
    "gemma2:9b": "ff02c3702f32",
    "mistral-nemo:latest": "e7e06d107c6c",
    "phi4:latest": "ac896e5b8b34"
}

CSV_PATH = Path("benchmark_scores/local_models_benchmark.csv")

def update_versions():
    if not CSV_PATH.exists():
        print("CSV not found.")
        return

    # Read CSV
    df = pd.read_csv(CSV_PATH)
    
    updated_count = 0
    
    def fix_version(row):
        model = row['model']
        current_ver = row.get('model_version', 'unknown')
        
        # Only update if unknown or missing
        if pd.isna(current_ver) or current_ver == 'unknown' or current_ver == 'nan':
            if model in ID_MAP:
                return ID_MAP[model]
        return current_ver

    # Apply
    # We must access via row index to count changes effectively if needed, 
    # but map is faster.
    
    old_versions = df['model_version'].copy()
    df['model_version'] = df.apply(fix_version, axis=1)
    
    # Check changes
    changes = df[df['model_version'] != old_versions]
    print(f"Updated {len(changes)} rows.")
    for model in changes['model'].unique():
        print(f"  - Fixed {model}")

    # Write back
    df.to_csv(CSV_PATH, index=False)
    print("CSV saved.")
    
if __name__ == "__main__":
    update_versions()
