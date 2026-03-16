import re
import math
import statistics

with open("benchmark_modules/political_compass/test.py", "r", encoding="utf-8") as f:
    text = f.read()

lines = text.split("\n")
new_lines = []
skip = False
for line in lines:
    if "def _write_audit_log(self, model, vanilla_res, forced_res, shift_x, shift_y, shift_distance, detailed_responses):" in line:
        skip = True
        continue
    if skip:
        if "def _calculate_individual_runs(" in line:
            skip = False
        else:
            continue
    new_lines.append(line)

text = "\n".join(new_lines)

# Fix the import
import_stmt = "from benchmark_modules.political_compass.core.visualizer import PoliticalCompassVisualizer\n"
new_imports = import_stmt + "from benchmark_modules.political_compass.core.audit_logger import AuditLogWriter\n"
text = text.replace(import_stmt, new_imports)

text = text.replace("self._write_audit_log(model", "AuditLogWriter.write_audit_log(model")
text = text.replace("self._write_audit_log(model_name", "AuditLogWriter.write_audit_log(model_name")

text = text.replace("shift_distance = round(((shift_x ** 2) + (shift_y ** 2)) ** 0.5, 2)", "import math\n        shift_distance = round(math.hypot(shift_x, shift_y), 2)")

text = text.replace("for run_idx in range(1, 3):", "BENCHMARK_RUNS = 2\n            for run_idx in range(1, BENCHMARK_RUNS + 1):")

text = text.replace("except Exception:  # pylint: disable=broad-exception-caught\n            pass", "except statistics.StatisticsError:\n            pass")
text = text.replace("except Exception:\n            pass", "except statistics.StatisticsError:\n            pass")

text = text.replace("except Exception as e:  # pylint: disable=broad-exception-caught\n                logging.error(\"Fehler im Block %d: %s\",", "except RuntimeError as e:\n                logging.error(\"Fehler im Block %d: %s\",")

# Also add the missing os/pathlib if they are missing
text = text.replace("import math\n        shift_distance", "import math\n        shift_distance")

with open("benchmark_modules/political_compass/test.py", "w", encoding="utf-8") as f:
    f.write(text)
