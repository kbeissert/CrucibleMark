import glob
import json
import csv
import re

def get_model_version(model_name: str) -> str:
    """Returns exactly the canonical version mapping matching latest framework logic."""
    if "claude" in model_name:
        match = re.search(r"claude-\d+(?:-\w+)?-(202\d{5})", model_name)
        if match: return match.group(1)
        if "-4-6" in model_name: return "4.6"
        if "-4-5" in model_name: return "4.5"
        if "3-5" in model_name: return "3.5"
        if "haiku-20240307" in model_name: return "20240307"
    if "gpt" in model_name:
        match = re.search(r"-(202\d{5})$|-(0\d{3})$", model_name)
        if match: return match.group(1) or match.group(2)
        if "gpt-4o-mini" in model_name: return "2024-07-18"
        if "gpt-4o" in model_name: return "2024-05-13"
        return "latest"
    if "gemini" in model_name:
        if "3.1" in model_name: return "3.1-pro-preview"
        if "3-flash-preview" in model_name: return "3-flash-preview"
        if "flash" in model_name: return "2.5-flash"
        if "pro" in model_name: return "2.5-pro"
        return "k.A."
    if "mistral" in model_name or "pixtral" in model_name:
        match = re.search(r"-(24\d{2})$", model_name)
        if match: return match.group(1)
        if "large" in model_name: return "2411"
        if "medium" in model_name: return "2312"
    if "grok" in model_name:
        return "latest"
    if "lfm" in model_name:
        return "latest"
    if "o3-mini" in model_name:
        return "2026-01-30"
    if "o1" in model_name:
        return "latest"
    return "k.A."

# 1. READ VERSIONS FROM CACHE FILES TO BE ABSOLUTELY SURE
json_files = glob.glob('outputs/**/*.json', recursive=True)

for filepath in json_files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        changed = False
        if isinstance(data, dict):
            if 'model' in data:
                model_name = data['model']

                # Cleanup naming for opus
                if model_name == 'claude-3-5-opus-latest':
                    data['model'] = 'claude-opus-4-6'
                    model_name = 'claude-opus-4-6'
                    changed = True

                new_version = get_model_version(model_name)

                if data.get('model_version') != new_version:
                    data['model_version'] = new_version
                    changed = True

        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f'Updated JSON cache: {filepath}')
    except Exception:
        pass

# 2. Update CSV files ("Datenbank-Einträge")
csv_files = [f for f in glob.glob('benchmark_scores/*.csv') if 'leaderboard' not in f]
for filepath in csv_files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames

        changed = False
        for row in rows:
            model_name = row.get('model', row.get('model_name'))
            if not model_name: continue

            if model_name == 'claude-3-5-opus-latest':
                if 'model' in row: row['model'] = 'claude-opus-4-6'
                if 'model_name' in row: row['model_name'] = 'claude-opus-4-6'
                model_name = 'claude-opus-4-6'
                changed = True

            new_version = get_model_version(model_name)

            if row.get('model_version') != new_version:
                row['model_version'] = new_version
                changed = True

        if changed:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f'Updated DB CSV: {filepath}')
    except Exception:
        pass

print("Update complete.")
