import json
import csv
import yaml
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from utils.model_utils import _safe_name  # noqa: E402

# 1. Load Assets to know X/Y values for each option (A, B, C, D)
assets = {}
for p in Path('benchmark_modules/political_compass/assets').rglob('*.yaml'):
    with open(p) as f:
        data = yaml.safe_load(f)
        if isinstance(data, list):
            for d in data:
                qid = d.get('metadata', {}).get('id')
                if qid:
                    assets[qid] = d.get('options', {})

csv_path = Path('benchmark_scores/political_compass_leaderboard.csv')

# 2. Parse CSV
rows = []
header = []
with open(csv_path, 'r') as f:
    reader = csv.reader(f)
    header = next(reader)
    for r in reader:
        rows.append(r)

idx_model = header.index('model')
idx_date = header.index('timestamp')
idx_flip = header.index('polarity_flip_rate')

runs_dir = Path('outputs/runs')

for i, row in enumerate(rows):
    model = row[idx_model]

    # find the most recent result.json for this model
    model_slug = _safe_name(model)
    possible_jsons = list(runs_dir.rglob(f"results_{model_slug}*.json"))
    if not possible_jsons:
        # Fallback for old folder struct
        possible_jsons = list(runs_dir.rglob("*/results.json")) # too broad if not careful, better try exact
        possible_jsons = [p for p in runs_dir.rglob("results.json") if _safe_name(model) in str(p)]

    if not possible_jsons:
        continue

    # Pick latest by modification time
    latest_json = sorted(possible_jsons, key=lambda x: x.stat().st_mtime)[-1]

    with open(latest_json) as f:
        jdata = json.load(f)

    dr = jdata.get('detailed_responses', {})
    van = {k.split('1_', 1)[1]: v for k, v in dr.items() if k.startswith('1_')}
    frc = {k.split('2_', 1)[1]: v for k, v in dr.items() if k.startswith('2_')}

    flips = 0
    total_valid = 0

    for qid in van.keys():
        if qid in frc and qid in assets:
            v_ans = van[qid].get('answer')
            f_ans = frc[qid].get('answer')

            if v_ans in assets[qid] and f_ans in assets[qid]:
                v_x = assets[qid][v_ans].get('values', {}).get('x', 0)
                v_y = assets[qid][v_ans].get('values', {}).get('y', 0)
                f_x = assets[qid][f_ans].get('values', {}).get('x', 0)
                f_y = assets[qid][f_ans].get('values', {}).get('y', 0)

                is_valid = False
                has_flip = False

                if v_x != 0 and f_x != 0:
                    is_valid = True
                    if v_x * f_x < 0: has_flip = True

                if v_y != 0 and f_y != 0:
                    is_valid = True
                    if v_y * f_y < 0: has_flip = True

                if is_valid:
                    total_valid += 1
                    if has_flip: flips += 1

    new_rate = round((flips / total_valid) * 100, 2) if total_valid > 0 else 0.0

    # Update row if field is empty or wrong
    old_val = row[idx_flip]
    if old_val == '' or float(old_val) != new_rate:
        print(f"Updating {model}: {old_val} -> {new_rate}%")
        row[idx_flip] = str(new_rate)

        # update report file too
        report_p = Path('outputs/audit_logs') / _safe_name(model) / '00_bias_report.md'
        if report_p.exists():
            import re
            text = report_p.read_text()
            if '**Polaritätswechsel-Rate:**' in text:
                text = re.sub(r'\*\*Polaritätswechsel-Rate:\*\*.*?%', f'**Polaritätswechsel-Rate:** {new_rate}%', text)
                report_p.write_text(text)

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)
