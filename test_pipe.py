import json
import yaml
import glob
from benchmark_modules.political_compass.core.prompts import PromptBuilder
from benchmark_modules.political_compass.core.models import Question

for f in glob.glob('benchmark_modules/political_compass/assets/political_compass_7.4-*.yaml'):
    with open(f, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    q = Question(id=data['metadata']['id'], category=data['metadata']['category'], axis=data['metadata']['axis'], context=data['prompt'], question='Wähle...', options=data['options'], topic=data['metadata']['topic'])
    prompt, _ = PromptBuilder.create_shuffled(q, seed=42)
    payload = {'model': 'x', 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0.1}
    j = json.dumps(payload)
print('Done.')
