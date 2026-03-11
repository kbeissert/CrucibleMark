import sys
from utils.config_validator import ConfigValidator
val = ConfigValidator()
print(val.config.get("llm_judge", {}).get("provider", {}).get("model"))
