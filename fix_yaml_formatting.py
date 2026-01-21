import os
import glob

assets_dir = 'benchmark_modules/political_compass/assets'
files = glob.glob(os.path.join(assets_dir, '*.yaml'))

print(f"Found {len(files)} files in {assets_dir}")

for file_path in files:
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('='):
            new_lines.append('# ' + line)
        else:
            new_lines.append(line)
            
    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    print(f"Fixed {file_path}")
