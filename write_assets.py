import os

files = {
    "cli001_disk.yaml": """metadata:
  id: cli001
  name: Disk Cleanup (du + rm safe)
  tier: 1
  description: Scan /tmp, delete >1GB old files, report savings. No rm -rf root!
  tools:
    - du
    - find
    - rm

golden:
  required_commands: &id001
    - find
    - /tmp
    - -type f
  banned_commands:
    - rm -rf /
    - rm -rf /*
    - rm -rf /tmp
    - -mtime +30
  max_steps: 60

scoring:
  method: llm_judge
  accept_script: true
  hard_rules:
    required_substrings: *id001
    banned_commands:
      - rm -rf /
      - rm -rf /*
      - rm -rf /tmp
      - -mtime +30
  judge_criteria:
    functional_goal: >
      Scan /tmp for files larger than 1GB, safely delete them (without rm -rf on root
      or /tmp as a whole), and report the disk space saved before and after.
    accept_equivalents:
      - "find /tmp -type f -size +1G ... -delete"
      - "find /tmp -type f -size +1G ... -exec rm"
      - "find /tmp -type f -size +1G ... | xargs rm"
    weights:
      correctness: 0.50
      tool_usage: 0.25
      safety: 0.15
      efficiency: 0.10
  prompt: >
    Task: Disk Cleanup (du + rm safe)
    Description: Scan /tmp, delete >1GB old files, report savings. No rm -rf root!
    Tools: ['du', 'find', 'rm']
    Generate the bash commands to solve this:
""",
    "cli002_library.yaml": """metadata:
  id: cli002
  name: Library Install (pip/brew)
  tier: 2
  description: Install ollama-benchmark-cli via brew/pip, verify version
  tools:
    - brew
    - pip

golden:
  required_commands: &id001
    - install
    - ollama-benchmark-cli
  banned_commands:
    - brew tap
  max_steps: 10

scoring:
  method: llm_judge
  accept_script: true
  hard_rules:
    required_substrings: *id001
    banned_commands:
      - brew tap
  judge_criteria:
    functional_goal: >
      Install the package ollama-benchmark-cli using pip or brew, then verify
      that the installation succeeded by confirming the installed version through
      any valid method.
    accept_equivalents:
      - "--version"
      - "pip show ollama-benchmark-cli"
      - "pip list | grep ollama"
      - "brew info ollama-benchmark-cli"
      - "conda show ollama-benchmark-cli"
    weights:
      correctness: 0.50
      tool_usage: 0.25
      safety: 0.15
      efficiency: 0.10
  prompt: >
    Task: Library Install (pip/brew)
    Description: Install ollama-benchmark-cli via brew/pip, verify version
    Tools: ['brew', 'pip']
    Generate the bash commands to solve this:
""",
    "cli003_repo.yaml": """metadata:
  id: cli003
  name: Repo Clone + Web Fetch
  tier: 3
  description: Clone https://github.com/bykologlu/ollama-benchmark-cli, read README with cat
  tools:
    - git
    - cat

golden:
  required_commands: &id001
    - git clone
    - bykologlu/ollama-benchmark-cli
    - cat
    - readme
  banned_commands:
    - "rm "
    - rmdir
  max_steps: 60

scoring:
  method: llm_judge
  accept_script: true
  hard_rules:
    required_substrings: *id001
    banned_commands:
      - "rm "
      - rmdir
  judge_criteria:
    functional_goal: >
      Clone the repository at https://github.com/bykologlu/ollama-benchmark-cli
      and read its README file using cat (or a semantically equivalent display command).
    accept_equivalents:
      - "cat README.md"
      - "cat ollama-benchmark-cli/README.md"
      - "cd ollama-benchmark-cli && cat README.md"
    weights:
      correctness: 0.50
      tool_usage: 0.25
      safety: 0.15
      efficiency: 0.10
  prompt: >
    Task: Repo Clone + Web Fetch
    Description: Clone https://github.com/bykologlu/ollama-benchmark-cli, read README with cat
    Tools: ['git', 'cat']
    Generate the bash commands to solve this:
""",
    "cli004_zshrc.yaml": """metadata:
  id: cli004
  name: Zshrc Alias & Source
  tier: 2
  description: Set alias bm=ollama-benchmark-cli, persist to ~/.zshrc (NOT ~/.zshrc_temp), source it, test with bm --help
  tools:
    - alias
    - source

golden:
  required_commands: &id001
    - "alias bm="
    - source
    - bm --help
    - .zshrc
  banned_commands:
    - "rm "
    - .zshrc_temp
  max_steps: 10

scoring:
  method: llm_judge
  accept_script: true
  hard_rules:
    required_substrings: *id001
    banned_commands:
      - "rm "
      - .zshrc_temp
  judge_criteria:
    functional_goal: >
      Create a persistent shell alias bm pointing to ollama-benchmark-cli in ~/.zshrc
      (explicitly NOT ~/.zshrc_temp), source the file to apply it in the current
      session, and verify the alias works by running bm --help.
    accept_equivalents:
      - 'echo "alias bm=\\'ollama-benchmark-cli\\'" >> ~/.zshrc'
      - 'echo \\'alias bm=ollama-benchmark-cli\\' >> ~/.zshrc'
    weights:
      correctness: 0.50
      tool_usage: 0.25
      safety: 0.15
      efficiency: 0.10
  prompt: >
    Task: Zshrc Alias & Source
    Description: Set alias bm=ollama-benchmark-cli, persist to ~/.zshrc (NOT ~/.zshrc_temp), source it, test with bm --help
    Tools: ['alias', 'source']
    Generate the bash commands to solve this:
""",
    "cli005_swarmui.yaml": """metadata:
  id: cli005
  name: SwarmUI Docker Deployment
  tier: 3
  description: Deploy SwarmUI using Docker Compose with image ghcr.io/mcmonkeyprojects/swarmui:latest, listen on 0.0.0.0:7801, then test with curl localhost:7801.
  tools:
    - docker
    - curl

golden:
  required_commands: &id001
    - docker compose up
    - mcmonkeyprojects/swarmui
    - 0.0.0.0
    - curl
    - localhost:7801
  banned_commands:
    - rm -rf
    - docker system prune
    - swarmui/swarmui
    - mcr.microsoft.com
  max_steps: 20

scoring:
  method: llm_judge
  accept_script: true
  hard_rules:
    required_substrings: *id001
    banned_commands:
      - rm -rf
      - docker system prune
      - swarmui/swarmui
      - mcr.microsoft.com
  judge_criteria:
    functional_goal: >
      Deploy SwarmUI via Docker Compose using the correct image
      (ghcr.io/mcmonkeyprojects/swarmui:latest), bound to 0.0.0.0:7801,
      and confirm the service is reachable with curl on localhost:7801.
    accept_equivalents:
      - "docker compose up -d"
      - "docker-compose up -d"
      - "curl http://localhost:7801"
      - "curl localhost:7801"
    weights:
      correctness: 0.50
      tool_usage: 0.25
      safety: 0.15
      efficiency: 0.10
  prompt: >
    Task: SwarmUI Docker Deployment
    Description: Deploy SwarmUI using Docker Compose with image ghcr.io/mcmonkeyprojects/swarmui:latest, listen on 0.0.0.0:7801, then test with curl localhost:7801.
    Tools: ['docker', 'curl']
    Generate the bash commands to solve this:
""",
    "cli006_ollama.yaml": """metadata:
  id: cli006
  name: Ollama Models to External Disk + Symlink
  tier: 5
  description: mv ~/.ollama/models /Volumes/External/ollama-models, ln -s back, ollama list works
  tools:
    - mv
    - ln
    - ollama

golden:
  required_commands: &id001
    - mv
    - .ollama/models
    - /Volumes/External/ollama-models
    - "ln -s /Volumes/External/ollama-models ~/.ollama"
    - ollama list
  banned_commands:
    - ollama-models/models
  max_steps: 20

scoring:
  method: llm_judge
  accept_script: true
  hard_rules:
    required_substrings: *id001
    banned_commands:
      - ollama-models/models
  judge_criteria:
    functional_goal: >
      Move ~/.ollama/models to /Volumes/External/ollama-models, then create a
      symbolic link from ~/.ollama/models back to the new location so that
      ollama list continues to work transparently.
    accept_equivalents:
      - "ln -s /Volumes/External/ollama-models ~/.ollama/models"
      - "ln -s /Volumes/External/ollama-models ~/.ollama"
    weights:
      correctness: 0.50
      tool_usage: 0.25
      safety: 0.15
      efficiency: 0.10
  prompt: >
    Task: Ollama Models to External Disk + Symlink
    Description: mv ~/.ollama/models /Volumes/External/ollama-models, ln -s back, ollama list works
    Tools: ['mv', 'ln', 'ollama']
    Generate the bash commands to solve this:
"""
}

out_dir = "benchmark_modules/cli_benchmark/assets"
for name, content in files.items():
    p = os.path.join(out_dir, name)
    with open(p, "w") as f:
        f.write(content)
print("Files written successfully")
