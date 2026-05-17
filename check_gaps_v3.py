import json
import glob
import os
from pathlib import Path

def print_result_info(pattern, model_names, modules=None, tasks=None, label=""):
    print(f"\n--- {label} ---")
    files = glob.glob(pattern)
    if not files:
        print(f"No files found for pattern: {pattern}")
        return
    
    found_any = False
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract results list
            results = []
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict):
                # Common keys for results in various formats
                results = data.get('results', data.get('tasks', []))
            
            # File-level model check
            file_model = data.get('model', data.get('model_id', '')).lower() if isinstance(data, dict) else ""
            
            target_model = False
            for m in model_names:
                if m.lower() in file_model:
                    target_model = True
                    break
            
            if not target_model:
                # Check results for model names
                rows = []
                for r in results:
                    r_model = str(r.get('model', '')).lower()
                    if any(m.lower() in r_model for m in model_names):
                        rows.append(r)
            else:
                rows = results

            # Filter by module/task
            if modules:
                rows = [r for r in rows if r.get('module') in modules]
            if tasks:
                rows = [r for r in rows if r.get('task_id') in tasks]
            
            if rows:
                found_any = True
                print(f"File: {file}")
                # Print "fields"
                all_keys = set()
                for r in rows:
                    all_keys.update(r.keys())
                print(f"Available Keys in entries: {sorted(list(all_keys))}")
                
                # Show first few matching entries
                for r in rows[:10]:
                    relevant = {k: r.get(k) for k in ['model', 'module', 'task_id', 'score', 'refusal_flag', 'judge_score', 'token_count', 'total_tokens', 'reasoning_content'] if k in r}
                    print(relevant)
                if len(rows) > 10:
                    print(f"... and {len(rows)-10} more entries.")
                    
        except Exception as e:
            # print(f"Error reading {file}: {e}")
            pass
            
    if not found_any:
        print(f"No matching records found for Models: {model_names}, Modules: {modules}, Tasks: {tasks}")

# Gap 1 & 2: Magistral
magistral_models = ["magistral-small", "magistral-medium", "mistral-ai/magistral-small"]
magistral_modules = ["reasoning_logic", "ux_writing", "code_quality", "documentation_quality"]
print_result_info("outputs/runs/*.json", magistral_models, modules=magistral_modules, label="Gap 1 & 2: Magistral Small/Medium")

# Gap 3: Minimax
print_result_info("outputs/runs/*.json", ["minimax-m2.7", "minimax/minimax-m2.7"], label="Gap 3: Minimax m2.7")

# Gap 4: Task IDs
tasks_to_check = ["ct_003", "ct_004", "ux_005"]
print_result_info("outputs/runs/*.json", [""], tasks=tasks_to_check, label="Gap 4: ct_003, ct_004, ux_005")

# Gap 5: gpt-5.4-mini
print_result_info("outputs/runs/*.json", ["gpt-5.4-mini"], modules=["cultural_intelligence"], label="Gap 5: gpt-5.4-mini in cultural_intelligence")

