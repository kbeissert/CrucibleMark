import re

with open("config/meta_reviewer_prompt.yaml", "r", encoding="utf-8") as f:
    text = f.read()

pc_start_marker = "    WICHTIG (Political Compass):"
pc_end_marker = "    Ziehe ein klares, professionell begründetes Fazit (mit Empfehlungen für Einsatzzwecke).\n"

idx_start = text.find(pc_start_marker)
idx_end = text.find(pc_end_marker)

if idx_start != -1 and idx_end != -1:
    pc_content = text[idx_start:idx_end]
    new_text = text[:idx_start] + text[idx_end:]
else:
    print("Could not find PC markers in yaml")
    exit(1)

with open("scripts/analysis/generate_review.py", "r", encoding="utf-8") as f:
    py_text = f.read()


bias_start = r'        prompt_template = """Du bist ein unabhängiger Ethik-Prüfer'
bias_end = r' Beginne sofort mit der #-Hauptüberschrift "# Bias & Alignment Review: {tested_model_name}"."""'

import re
match = re.search(re.escape(bias_start) + r'(.*?)' + re.escape(bias_end), py_text, re.DOTALL)

if match:
    # Get the inner group
    bias_prompt = bias_start.replace('        prompt_template = """', '') + match.group(1) + bias_end.replace('"""', '')
else:
    print("Could not find bias prompt in py")
    exit(1)

bias_prompt = bias_prompt.replace("\n", "\n    ")
bias_prompt_yaml = f"bias_reviewer:\n  system_instructions: |\n    {bias_prompt}\n\n    ### CrucibleMark Archetypen-Definitionen:\n"
bias_prompt_yaml += pc_content

new_yaml_text = new_text + "\n" + bias_prompt_yaml

with open("config/meta_reviewer_prompt.yaml", "w", encoding="utf-8") as f:
    f.write(new_yaml_text)

print("Updated yaml")
