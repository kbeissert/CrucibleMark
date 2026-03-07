import re
from typing import Dict, Tuple, List
from benchmark_modules.cli_benchmark.core.constants import CLI_SILVER_THRESHOLD

class ShellSimulator:
    """
    Mock Shell Environment.
    Extracts shell commands and simulates interactions securely.
    """
    def __init__(self):
        self.state = {
            "tmp_size_mb": 1500,
            "installed_packages": [],
            "alias_set": False,
            "docker_running": False
        }

    def extract_commands(self, llm_output: str) -> List[str]:
        """
        Extrahiert die Bash-Befehle aus Markdown-Codeblöcken oder Text.
        """
        # Suche nach Code-Blöcken (vermutlich bash oder sh)
        pattern = re.compile(r'```(?:bash|sh)?\n(.*?)\n```', re.DOTALL)
        matches = pattern.findall(llm_output)
        
        commands = []
        if matches:
            for match in matches:
                commands.extend([line.strip() for line in match.split('\n') if line.strip() and not line.strip().startswith('#')])
        else:
            commands = [line.strip() for line in llm_output.split('\n') if line.strip() and not line.strip().startswith('#')]
            
        return commands
                score = 50.0
                msg = "Docker commanded but config incomplete."

        elif task_id == "cli006":
            # Ollama Models
            has_mv = "mv " in output_lower and ".ollama/models" in output_lower
            has_symlink = "ln -s" in output_lower and "models" in output_lower
            has_verify = "ollama list" in output_lower or "ollama run" in output_lower
            if has_mv and has_symlink:
                success = True
                score = 100.0 if has_verify else 90.0
                msg = "Models successfully moved and symlinked ✓"

        if success and score >= CLI_SILVER_THRESHOLD:
            return True, score, msg
        return False, score, msg
