import yaml
import glob
import json

for f in glob.glob("benchmark_modules/political_compass/assets/political_compass_7.4*.yaml"):
    try:
        with open(f, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            j = json.dumps(data)
            # check for surrogates or weird things
            for k, v in data.items():
                if isinstance(v, str):
                    v.encode('utf-8')
    except Exception as e:
        print(f"Error in {f}: {e}")
print("Check done.")
