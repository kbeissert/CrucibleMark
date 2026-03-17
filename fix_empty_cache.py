import json
import glob

files = glob.glob('outputs/temp/session_*.json')
count = 0
for f in files:
    with open(f, 'r') as file:
        try:
            chk = json.load(file)
        except Exception:
            continue
    
    modified = False
    if 'detailed_responses' in chk:
        to_delete = []
        for k, v in chk['detailed_responses'].items():
            if not v.get('raw_response') or str(v.get('raw_response')).strip() == "":
                to_delete.append(k)
        for k in to_delete:
            del chk['detailed_responses'][k]
            modified = True
            count += 1
            
    if modified:
        with open(f, 'w') as file:
            json.dump(chk, file, indent=2)

print(f"Removed {count} empty cached responses from {len(files)} files.")
