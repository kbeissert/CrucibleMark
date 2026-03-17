import json
import glob
import yaml

failures = []
for f in glob.glob("benchmark_modules/political_compass/assets/*.yaml"):
    with open(f, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
        text = data.get("prompt", "") + str(data.get("options", ""))
        for char in text:
            if ord(char) < 32 and char not in ('\n', '\r', '\t'):
                print(f"Control character {ord(char)} found in {f}")
