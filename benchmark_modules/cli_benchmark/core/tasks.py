import yaml
from pathlib import Path
from typing import List, Dict, Any

class CLITaskLoader:
    def __init__(self, assets_dir: str = None):
        if assets_dir is None:
            self.assets_dir = Path(__file__).parent.parent / "assets"
        else:
            self.assets_dir = Path(assets_dir)

    def load_tasks(self) -> List[Dict[str, Any]]:
        """Liest die YAML Tasks aus dem assets Ordner."""
        tasks = []
        if not self.assets_dir.exists():
            return tasks

        for file_path in sorted(self.assets_dir.glob("cli*.yaml")):
            try:
                with open(file_path, "r", encoding="utf-8") as yf:
                    data = yaml.safe_load(yf)
                    if not data or "metadata" not in data:
                        continue
                    
                    task = {
                        "id": data["metadata"].get("id", file_path.stem),
                        "name": data["metadata"].get("name", "Unknown"),
                        "tier": data["metadata"].get("tier", 1),
                        "description": data.get("description", ""),
                        "tools": data.get("tools", []),
                        "golden": data.get("golden", {})
                    }
                    tasks.append(task)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                
        return tasks
