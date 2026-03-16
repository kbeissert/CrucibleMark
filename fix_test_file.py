import re
import math
import statistics

with open("benchmark_modules/political_compass/test.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove the old _write_audit_log method entirely
pattern_remove_audit = re.compile(r"    def _write_audit_log[\s\S]*?logging\.error\(\"Failed to write audit log: %s\", e\)", re.DOTALL | re.MULTILINE)
content = pattern_remove_audit.sub("", content)

# Fix the import
import_stmt = "from benchmark_modules.political_compass.core.visualizer import PoliticalCompassVisualizer\n"
new_imports = import_stmt + "from benchmark_modules.political_compass.core.audit_logger import AuditLogWriter\n"
content = content.replace(import_stmt, new_imports)

# Replace the call to _write_audit_log
content = content.replace("self._write_audit_log(model_name, vanilla_res, forced_res, shift_x, shift_y, shift_distance, detailed_responses)", "AuditLogWriter.write_audit_log(model_name, vanilla_res, forced_res, shift_x, shift_y, shift_distance, detailed_responses)")
content = content.replace("self._write_audit_log(model, vanilla_res, forced_res, shift_x, shift_y, shift_distance, detailed_responses)", "AuditLogWriter.write_audit_log(model, vanilla_res, forced_res, shift_x, shift_y, shift_distance, detailed_responses)")

# Replace ** 0.5 with math.hypot
content = content.replace("shift_distance = round(((shift_x ** 2) + (shift_y ** 2)) ** 0.5, 2)", "import math\n        shift_distance = round(math.hypot(shift_x, shift_y), 2)")

# Replace magic numbers
content = content.replace("for run_idx in range(1, 3):", "BENCHMARK_RUNS = 2\n        for run_idx in range(1, BENCHMARK_RUNS + 1):")

# Fix bare exceptions
content = content.replace("except Exception:  # pylint: disable=broad-exception-caught\n            pass", "except statistics.StatisticsError:\n            pass")
content = content.replace("except Exception: \n            pass", "except statistics.StatisticsError:\n            pass")

content = content.replace("except Exception as e:  # pylint: disable=broad-exception-caught\n            logging.error(\"Error parsing line '%s': %s\"", "except ValueError as e:\n            logging.error(\"Error parsing line '%s': %s\"")

with open("benchmark_modules/political_compass/test.py", "w", encoding="utf-8") as f:
    f.write(content)
