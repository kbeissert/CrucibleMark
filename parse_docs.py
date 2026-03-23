import re
from pathlib import Path

docs = [Path("docs/USER_GUIDE.md"), Path("README.md")]

found_commands = set()
for path in docs:
    if path.exists():
        text = path.read_text()
        matches = re.findall(r'make\s+[a-zA-Z0-9_-]+', text)
        for m in matches:
            cmd = m.split()[1]
            found_commands.add(f"{path.name}: {cmd}")

with open("found_commands.txt", "w") as f:
    for cmd in sorted(found_commands):
        f.write(cmd + "\n")
