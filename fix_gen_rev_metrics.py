import re

with open('scripts/analysis/generate_review.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace get_model_metrics
old_func = """def get_model_metrics(model_name: str) -> dict:
    import csv
    detailed_csv = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard_detailed.csv"
    if not detailed_csv.exists():
        return {}
    try:
        with open(detailed_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_model = row.get("Model Name", "")
                if model_name == csv_model or model_name.startswith(f"{csv_model}-") or model_name.startswith(f"{csv_model}_"):
                    return row
    except Exception:
        pass
    return {}"""

new_func = """def get_model_metrics(model_name: str) -> dict:
    import csv
    detailed_csv = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard_detailed.csv"
    if not detailed_csv.exists():
        return {}

    def normalize(s):
        return s.replace(":", "_").replace("-", "_").lower()

    norm_target = normalize(model_name)
    try:
        with open(detailed_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_model = row.get("Model Name", "")
                norm_csv = normalize(csv_model)
                if norm_target == norm_csv or norm_target.startswith(f"{norm_csv}_"):
                    return row
    except Exception:
        pass
    return {}"""

code = code.replace(old_func, new_func)

# Replace template_vars
old_vars = """    template_vars = {
        "tested_model_name": tested_model_name,
        "hardware_context": hardware_context,
        "csv_data": csv_data,
        "log_data": log_data,
        "tier_metaphor_rules": tier_metaphor_rules,
        "model_specialization": get_model_specialization(tested_model_name),
        "model_p95_time": safe_round(model_metrics.get("P95 Time (s)")),
        "model_tokens_per_second": safe_round(model_metrics.get("Performance/s")),
    }"""

new_vars = """    timeout_count = model_metrics.get("Timeout Count", "n/a")
    tests_run = model_metrics.get("Tests Run", "n/a")
    if tests_run != "n/a" and "/" in tests_run:
        tests_run = tests_run.split("/")[-1]

    timeout_rate_str = f"{timeout_count}/{tests_run}" if timeout_count != "n/a" else "n/a"

    template_vars = {
        "tested_model_name": tested_model_name,
        "hardware_context": hardware_context,
        "csv_data": csv_data,
        "log_data": log_data,
        "tier_metaphor_rules": tier_metaphor_rules,
        "model_specialization": get_model_specialization(tested_model_name),
        "model_p95_time": safe_round(model_metrics.get("P95 Time (s)")),
        "model_tokens_per_second": safe_round(model_metrics.get("Performance/s")),
        "model_timeout_rate": timeout_rate_str,
        "model_provider_type": model_metrics.get("Type", "n/a")
    }"""

code = code.replace(old_vars, new_vars)

with open('scripts/analysis/generate_review.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated generate_review.py")
