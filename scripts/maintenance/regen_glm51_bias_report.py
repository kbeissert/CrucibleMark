"""One-shot: Regenerate 00_bias_report.md for glm-5.1:cloud from checkpoint data."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from benchmark_modules.political_compass.core.audit_logger import AuditLogWriter

checkpoint = json.loads(
    Path("outputs/temp/session_glm_5_1_cloud.json").read_text(encoding="utf-8")
)
detailed = checkpoint.get("detailed_responses", {})

AuditLogWriter.write_audit_log(
    model="glm-5.1:cloud",
    vanilla_res={"score_x": 0.0, "score_y": 0.0},
    forced_res={"score_x": 0.0, "score_y": 0.0},
    shift_x=0.0,
    shift_y=0.0,
    shift_distance=0.0,
    polarity_flip_rate=0.0,
    detailed_responses=detailed,
    verification_mode=False,
    safety_metadata=None,
    execution_time=3008.60,
    total_tokens=0,
    cost="0.000000",
    provider="ollama",
)
print("Done → outputs/audit_logs/glm-5.1_cloud/00_bias_report.md")
