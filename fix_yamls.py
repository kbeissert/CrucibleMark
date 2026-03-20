import glob

for fpath in glob.glob("benchmark_modules/cli_benchmark/assets/*.yaml"):
    with open(fpath, "r") as f:
        lines = f.readlines()

    out_lines = []
    for line in lines:
        if line.startswith("  prompt:"):
            out_lines.append(line[2:])
        elif line.startswith("    Task:"):
            out_lines.append(line[2:])
        elif line.startswith("    Description:"):
            out_lines.append(line[2:])
        elif line.startswith("    Tools:"):
            out_lines.append(line[2:])
        elif line.startswith("    Generate the bash commands"):
            out_lines.append(line[2:])
        elif 'echo "alias bm=\\\'ollama' in line:
            out_lines.append('      - "echo \\"alias bm=\'ollama-benchmark-cli\'\\" >> ~/.zshrc"\n')
        elif "echo \\'alias bm=ollama" in line:
            out_lines.append('      - "echo \'alias bm=ollama-benchmark-cli\' >> ~/.zshrc"\n')
        else:
            out_lines.append(line)

    with open(fpath, "w") as f:
        f.writelines(out_lines)
print("Yamls fixed.")
