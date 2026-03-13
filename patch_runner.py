import re

with open("scripts/core/run_local_benchmark.py", "r") as f:
    text = f.read()

# 1. We find the if getattr(self, "audit_mode", False): block and its contents and DELETE IT from _build_result_dict
audit_block_regex = r'(\s*if getattr\(self, "audit_mode", False\):.*?save_audit_log\([^)]+\)\n)'
match = re.search(audit_block_regex, text, re.DOTALL)
if match:
    audit_block_raw = match.group(1)
    # Delete from current location
    text = text.replace(audit_block_raw, "")
else:
    print("Could not find audit block")
    exit(1)

# 2. We adjust the audit_block to use `response` instead of `response_preview`
audit_block_adjusted = audit_block_raw.replace("response_preview", "response")

# 3. We find the exact ending of _process_single_test where it returns result
end_of_process_single_test = r'(        # ---------------------------------------------------------------------\n\s*return result)'

def replace_fn(m):
    return audit_block_adjusted + "\n" + m.group(1)

new_text = re.sub(end_of_process_single_test, replace_fn, text, count=1)

if new_text == text:
    print("Could not find where to insert the new block")
    exit(1)

with open("scripts/core/run_local_benchmark.py", "w") as f:
    f.write(new_text)

print("Patched run_local_benchmark.py successfully")
