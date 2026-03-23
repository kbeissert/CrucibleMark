from pathlib import Path
import yaml
with open("Makefile", "r") as f:
    text = f.read()

import re
backup_target = re.search(r'backup:.*?(?=\n\w|\Z)', text, re.DOTALL)
if backup_target:
    print("BACKUP TARGET FOUND:")
    print(backup_target.group(0))
else:
    print("NOT FOUND")
