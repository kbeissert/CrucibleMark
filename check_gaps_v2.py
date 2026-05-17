import json
import glob
import os
from pathlib import Path

def print_json_info(pattern, filter_fn, label):
    print(f"\n--- {label} ---")
    files = glob.glob(pattern, recursive=True)
    if not files:
        print(f"No files found for pattern: {pattern}")
        return
    
    found_any = False
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # If the json is a list of results
            results = data if isinstance(data, list) else data.get('results', [])
            
            # Check for model in top-level if available
            file_model = data.get('model_id') if isinstance(data, dict) else None
            
            rows = [r for r in results if filter_fn(r, file_model)]
            
            if rows:
                found_any = True
                print(f"File: {file}")
                # Print keys of the first row to know "field names"
                if rows:
                    print(f"Keys: {list(rows[0].keys())}")
                for row in rows:
                    relevant = {k: row.get(k) for k in ['model', 'module', 'task_id', 'score', 'refusal_flag', 'judge_score', 'token_count', 'total_tokens', 'reasoning_content'] if k in row}
                    print(relevant)
        except Exception as e:
            print(f"Error reading {file}: {e}")
            
    if not found_any:
        print("No matching records found in existing JSON files.")

# Gap 1 & 2: Magistral models
magistral_models = ["magistral-small", "magistral-medium"]
magistral_modules = ["reasoning_logic", "ux_writing", "code_quality", "documentation_quality"]

print_json_info("outputs/runs/*.json", 
               lambda r, m_id: (any(m in str(r.get('model', '')) or m in str(m_id or '') for m in magistral_models)) and r.get('module') in magistral_modules,
               "Gap 1 & 2: Magistral Small/Medium")

# Gap 3: Minimax
print_json_info("outputs/runs/*.json",
               lambda r, m_id: "minimax-m2.7" in str(r.get('model', '')) or "minimax-m2.7" in str(m_id or ''),
               "Gap 3: Minimax m2.7")

# Gap 4: Task IDs ct_003, ct_004, ux_005
tasks_to_check = ["ct_003", "ct_004", "ux_005"]
print_json_info("outputs/runs/*.json",
               lambda r, m_id: r.get('task_id') in tasks_to_check,
               "Gap 4: ct_003, ct_004, ux_005")

# Gap 5: gpt-5.4-mini
print_json_info("outputs/runs/*.json",
               lambda r, m_id: ("gpt-5.4-mini" in str(r.get('model', '')) or "gpt-5.4-mini" in str(m_id or '')) and r.get('module') == 'cultural_intelligence',
               "Gap 5: gpt-5.4-mini in cultural_intelligence")

