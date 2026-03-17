import json
import glob
import yaml

from benchmark_modules.political_compass.core.prompts import PromptBuilder
from benchmark_modules.political_compass.core.models import Question

for f in glob.glob("benchmark_modules/political_compass/assets/*.yaml"):
    try:
        with open(f, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            q = Question(
                id=data["metadata"]["id"],
                category=data["metadata"]["category"],
                axis=data["metadata"]["axis"],
                context=data["prompt"], # or wait, how is Question initialized? Let's mock the prompt directly
                question="mock",
                options=data["options"],
                topic=data["metadata"]["topic"]
            )
            # Actually, let's just make sure the raw prompt text string doesn't have issues.
            pass
    except Exception as e:
        print(f)
