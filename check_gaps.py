import csv
import glob
import os
from pathlib import Path

def print_csv_info(pattern, filter_fn, label):
    print(f"\n--- {label} ---")
    files = glob.glob(pattern, recursive=True)
    if not files:
        print("No files found.")
        return
    
    for file in files:
        with open(file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = [row for row in reader if filter_fn(row)]
            if rows:
                print(f"File: {file}")
                print(f"Fields: {fieldnames}")
                for row in rows:
                    relevant = {k: row.get(k) for k in ['model', 'module', 'task_id', 'score', 'refusal_flag', 'judge_score', 'token_count', 'total_tokens'] if k in row}
                    print(relevant)

# Gap 1 & 2: Magistral models
magistral_models = [
    "magistral-small", "magistral-small-latest", "mistral-ai/magistral-small",
    "magistral-medium", "magistral-medium-latest"
]
magistral_modules = ["reasoning_logic", "ux_writing", "code_quality", "documentation_quality"]

print_csv_info("outputs/runs/**/*.csv", 
               lambda r: any(m in r.get('model', '') for m in magistral_models) and r.get('module') in magistral_modules,
               "Gap 1 & 2: Magistral Small/Medium")

# Gap 3: Minimax
print_csv_info("outputs/runs/**/*.csv",
               lambda r: "minimax-m2.7" in r.get('model', ''),
               "Gap 3: Minimax m2.7")

# Gap 4: Task IDs ct_003, ct_004, ux_005
tasks_to_check = ["ct_003", "ct_004", "ux_005"]
print_csv_info("outputs/runs/**/*.csv",
               lambda r: r.get('task_id') in tasks_to_check,
               "Gap 4: ct_003, ct_004, ux_005")

# Gap 5: gpt-5.4-mini
print_csv_info("outputs/runs/cultural_intelligence/*.csv",
               lambda r: "gpt-5.4-mini" in r.get('model', ''),
               "Gap 5: gpt-5.4-mini in cultural_intelligence")

# Leaderboard Check
print("\n--- Leaderboard Check ---")
leaderboard = "benchmark_scores/benchmark_leaderboard_detailed.csv"
if os.path.exists(leaderboard):
    with open(leaderboard, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print(f"Leaderboard Fields: {reader.fieldnames}")
        # Sample for relevant models
        for row in reader:
             if any(m in row.get('model', '') for m in magistral_models + ["minimax-m2.7", "gpt-5.4-mini"]):
                 print({k: row[k] for k in ['model', 'module', 'score'] if k in row})
else:
    print("Leaderboard file not found.")

