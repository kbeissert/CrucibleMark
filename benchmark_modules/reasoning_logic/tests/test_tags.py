#!/usr/bin/env python3
"""Quick test for <think> tag support."""

import sys
import yaml
from pathlib import Path

# Add project root to path (3 levels up from tests/)
PROJECT_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from benchmark_modules.reasoning_logic.core.evaluators import ReasoningEvaluator

# Load asset (using dynamic path)
asset_path = PROJECT_ROOT / 'benchmark_modules/reasoning_logic/assets/reasoning_metacog_001.yaml'
# Fallback to checking potential name changes if known
if not asset_path.exists():
    # Try looking for just metacog_001 if the name changed in dev
    potential_matches = list(asset_path.parent.glob('*metacog_001.yaml'))
    if potential_matches:
        asset_path = potential_matches[0]

with open(asset_path) as f:
    asset = yaml.safe_load(f)

evaluator = ReasoningEvaluator(asset)

print("\n" + "="*80)
print("TEST: Thought Tag Recognition")
print("="*80)

# Test 1: DeepSeek with <think> tags
deepseek = '''<think>
Let me think about this carefully.
The phrase "all but 9" means 9 survive.
</think>

Answer: 9'''

print("\n1. DeepSeek <think> tags:")
parsed = evaluator.parse_thought_tags(deepseek)
print(f"   Has tags: {parsed['has_thought_tags']}")
print(f"   Tag type: {parsed['thought_tag_type']}")
print(f"   Thought length: {parsed['thought_length']} words")

# Test 2: Qwen with <thought> tags
qwen = '''<thought>
The phrase "all but 9" means 9 survive.
</thought>

Answer: 9'''

print("\n2. Qwen <thought> tags:")
parsed = evaluator.parse_thought_tags(qwen)
print(f"   Has tags: {parsed['has_thought_tags']}")
print(f"   Tag type: {parsed['thought_tag_type']}")
print(f"   Thought length: {parsed['thought_length']} words")

# Test 3: Score DeepSeek response
print("\n3. Scoring DeepSeek response:")
result = evaluator.score_response(deepseek)
score = result.get("total_score", 0)
breakdown = result.get("category_scores", {})

print(f"   Total Score: {score:.0f}/100")
for k, v in breakdown.items():
    print(f"   - {k}: {v['achieved']:.0f}/100")

# Test 4: Score Qwen response
print("\n4. Scoring Qwen response:")
result = evaluator.score_response(qwen)
score = result.get("total_score", 0)
breakdown = result.get("category_scores", {})

print(f"   Total Score: {score:.0f}/100")
for k, v in breakdown.items():
    print(f"   - {k}: {v['achieved']:.0f}/100")

print("\n" + "="*80)
