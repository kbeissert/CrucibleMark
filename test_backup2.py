from pathlib import Path
with open("Makefile", "r") as f:
    text = f.read()
import re
target = re.search(r'clean-runs.*?:.*?(?=\n\w|\Z)', text, re.DOTALL)
if target:
    print(target.group(0))
