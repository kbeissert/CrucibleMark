import yaml

def update_yaml(file_path, new_golden_fields):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    data['scoring']['method'] = 'llm_judge'

    # Add new fields to golden
    if 'golden' in data:
        for k, v in new_golden_fields.items():
            data['golden'][k] = v

    with open(file_path, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False)

update_yaml('benchmark_modules/cli_benchmark/assets/cli001_disk.yaml', {
    'functional_goal': 'Scan /tmp, delete files larger than 1GB, and report disk space savings without deleting the root or /tmp directory itself.',
    'accept_equivalents': ['find ... -size +1G', 'du -sh']
})

update_yaml('benchmark_modules/cli_benchmark/assets/cli002_library.yaml', {
    'functional_goal': 'Package ollama-benchmark-cli must be installed via pip or brew, and its version verified.',
    'accept_equivalents': ['--version', 'pip show', 'pip list | grep', 'conda list']
})

update_yaml('benchmark_modules/cli_benchmark/assets/cli003_repo.yaml', {
    'functional_goal': 'Clone the repository and display the contents of the README file.',
    'accept_equivalents': ['cat README.md', 'less README.md', 'more README.md', 'head README.md']
})

update_yaml('benchmark_modules/cli_benchmark/assets/cli004_zshrc.yaml', {
    'functional_goal': 'Set an alias bm=ollama-benchmark-cli, persist it specifically to ~/.zshrc, source the file, and test the alias with --help.',
    'accept_equivalents': ['echo "alias bm=..." >> ~/.zshrc', 'source ~/.zshrc', 'bm --help']
})

update_yaml('benchmark_modules/cli_benchmark/assets/cli005_swarmui.yaml', {
    'functional_goal': 'Deploy SwarmUI using Docker Compose with the specified image, listen on 0.0.0.0:7801, and test it via curl.',
    'accept_equivalents': ['docker-compose up', 'docker run -p 7801:7801 ghcr.io...']
})

update_yaml('benchmark_modules/cli_benchmark/assets/cli006_ollama.yaml', {
    'functional_goal': 'Move the ~/.ollama/models directory to /Volumes/External/ollama-models, create a symlink back, and ensure `ollama list` still works.',
    'accept_equivalents': ['mv ...', 'ln -s ...', 'ollama ls']
})
