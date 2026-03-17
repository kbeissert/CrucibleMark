import yaml
import glob
for f in glob.glob("benchmark_modules/political_compass/assets/*.yaml"):
    try:
        with open(f, "r") as file:
            data = yaml.safe_load(file)
            import json
            json.dumps(data)
    except Exception as e:
        print(f"Failed to parse or serialize {f}: {e}")
print("Done.")
