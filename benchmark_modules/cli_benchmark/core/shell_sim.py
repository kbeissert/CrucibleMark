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
