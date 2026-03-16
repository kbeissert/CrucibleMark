import os
import subprocess
import json

def get_python_files(exclude_dirs=('.venv', 'venv', '.git', '__pycache__')):
    py_files = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    return py_files

files = get_python_files()
print(f"Running pylint on {len(files)} files...")
res = subprocess.run(['pylint', '--score=y'] + files, capture_output=True, text=True)
with open('pylint_report.txt', 'w') as f:
    f.write(res.stdout)
