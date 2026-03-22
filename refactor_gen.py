import re

def main():
    with open('scripts/analysis/generate_review.py', 'r', encoding='utf-8') as f:
        code = f.read()

    # Entfernen der alten Getter-Funktionen
    code = re.sub(r'def get_performance_time.*?return "n/a"\n\n', '', code, flags=re.DOTALL)
    code = re.sub(r'def get_p95_time.*?return "n/a"\n\n', '', code, flags=re.DOTALL)

    # Neue Metriken-Funktion einfügen vor get_latest_audit_dir
    new_func = """def get_model_metrics(model_name: str) -> dict:
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
    return {}

"""
    code = code.replace('def get_latest_audit_dir(', new_func + 'def get_latest_audit_dir(')

    # Das Format-Statement aktualisieren
    old_format = """    prompt = prompt_template.format(
        tested_model_name=tested_model_name,
        hardware_context=hardware_context,
        csv_data=csv_data,
        log_data=log_data,
        tier_metaphor_rules=tier_metaphor_rules,
        model_specialization=get_model_specialization(tested_model_name),
        model_p95_time=get_p95_time(tested_model_name),
        model_tokens_per_second=get_performance_time(tested_model_name)
    )"""

    new_format = """    model_metrics = get_model_metrics(tested_model_name)

    template_vars = {
        "tested_model_name": tested_model_name,
        "hardware_context": hardware_context,
        "csv_data": csv_data,
        "log_data": log_data,
        "tier_metaphor_rules": tier_metaphor_rules,
        "model_specialization": get_model_specialization(tested_model_name),
        "model_p95_time": model_metrics.get("P95 Time (s)", "n/a"),
        "model_tokens_per_second": model_metrics.get("Performance/s", "n/a"),
    }

    try:
        prompt = prompt_template.format(**template_vars)
    except KeyError as e:
        print(f"⚠️ Warnung im Prompt-Template: Fehlende Variable {e}")
        template_vars[e.args[0]] = "n/a"
        prompt = prompt_template.format(**template_vars)"""

    code = code.replace(old_format, new_format)

    with open('scripts/analysis/generate_review.py', 'w', encoding='utf-8') as f:
        f.write(code)

if __name__ == "__main__":
    main()
