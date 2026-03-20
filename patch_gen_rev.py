import re
with open("scripts/analysis/generate_review.py", "r") as f:
    content = f.read()

benchmark_pattern = r'if review_type == "benchmark":\n\s+prompt_template = """Du bist ein erfahrener Tech-Journalist.*?Verzichte strikt auf Begrüßungsfloskeln. Beginne sofort mit der #-Hauptüberschrift."""'

new_benchmark = """if review_type == "benchmark":
        try:
            import yaml
            with open(ROOT_DIR / "config" / "meta_reviewer_prompt.yaml", "r", encoding="utf-8") as f:
                prompt_yaml = yaml.safe_load(f)
                prompt_template = prompt_yaml.get("meta_reviewer", {}).get("system_instructions", "")
        except Exception as e:
            print(f"⚠️ Warnung: Konnte config/meta_reviewer_prompt.yaml nicht laden: {e}")
            prompt_template = \"\"\"Fehler beim Laden des Prompts.\"\"\""""

content = re.sub(benchmark_pattern, new_benchmark, content, flags=re.DOTALL)

with open("scripts/analysis/generate_review.py", "w") as f:
    f.write(content)
print("done")
