"""
Leaderboard configuration and registry management.
"""

import sys
from pathlib import Path
from typing import Any

import yaml

# Adjust path to allow imports from root
# This file is in scripts/leaderboard/config.py, so root is 3 levels up
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.config_validator import ConfigValidator  # noqa: E402

# Constants - Defaults
DEFAULT_THRESHOLDS = {
    "god_mode_routine": 85,
    "god_mode_reasoning": 80,
    "daily_driver_routine": 80,
    "deep_thinker_reasoning": 80,
}
REGISTRY_FILE = ROOT_DIR / "model_registry.yaml"

# Load Configuration
validator = ConfigValidator()
config = validator.config
output_config = config.get("output", {})
lb_config = config.get("leaderboard", {}).get("thresholds", DEFAULT_THRESHOLDS)

SCORES_DIR = Path(output_config.get("directory", "benchmark_scores"))
COMMERCIAL_CSV = Path(
    output_config.get("commercial_csv", SCORES_DIR / "commercial_models_benchmark.csv")
)
CLOUD_CSV = Path(
    output_config.get("cloud_models_csv", SCORES_DIR / "cloud_models_benchmark.csv")
)
LOCAL_CSV = Path(
    output_config.get("local_models_csv", SCORES_DIR / "local_models_benchmark.csv")
)
OUTPUT_CSV = SCORES_DIR / "benchmark_leaderboard.csv"


def load_model_registry() -> dict[str, Any]:
    """Loads model registry from YAML."""
    if not REGISTRY_FILE.exists():
        return {"models": {}}
    try:
        with open(REGISTRY_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if data else {"models": {}}
    except Exception as e:
        print(f"⚠️ Error loading registry {REGISTRY_FILE}: {e}")
        return {"models": {}}


def save_model_registry(registry_data: dict[str, Any]) -> None:
    """Saves registry back to YAML."""
    try:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            yaml.dump(registry_data, f, sort_keys=False, indent=2, allow_unicode=True)
        print(f"✅ Registry updated: {REGISTRY_FILE}")
    except Exception as e:
        print(f"⚠️ Error saving registry: {e}")
