#!/usr/bin/env python3
"""
Test script to validate the stricter METACOG scoring with realistic Dolphin responses.
"""

import sys
from pathlib import Path

# Add project root to path (3 levels up)
PROJECT_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from benchmark_modules.reasoning_logic.test import ReasoningLogicTest  # noqa: E402

print("=" * 70)
print("🧪 STRICTER METACOG SCORING TEST")
print("=" * 70)

# Load METACOG_001
assets_dir = PROJECT_ROOT / "benchmark_modules/reasoning_logic/assets"
# Dynamic path finding
asset_file = assets_dir / "reasoning_metacog_001.yaml"
if not asset_file.exists():
    asset_file = assets_dir / "asset_metacog_001.yaml"

if not asset_file.exists():
    print(f"Error: Asset not found at {asset_file}")
    sys.exit(1)

test = ReasoningLogicTest(asset_path=str(asset_file))

print("\n" + "=" * 70)
print("TEST 1: METACOG_001 with NO thought tags (Dolphin typical)")
print("=" * 70)

# Realistic Dolphin response (no thought tags, just answer)
response1 = "The answer is 9 sheep."

result1 = test.score_response(response1)
print(f"\nResponse: '{response1}'")

# Handle tuple return (score, breakdown, details)
if isinstance(result1, tuple):
    score, breakdown, details = result1
    print(f"✅ Score: {score}/100")
    print(f"   Breakdown: {breakdown}")
    print("   Expected: ~30 (only output correctness)")
    print(f"   Details: {details}")
else:
    print(f"✅ Score: {result1.get('total_score', 0)}/100")
    print(f"   Breakdown: {result1.get('breakdown', {})}")
    print("   Expected: ~30 (only output correctness)")

print("\n" + "=" * 70)
print("TEST 2: METACOG_001 with minimal thought tags (< 20 words)")
print("=" * 70)

# Dolphin with minimal thought
response2 = """<thought>
17 sheep, all but 9 die, so 9 remain.
</thought>

Answer: 9 sheep"""

result2 = test.score_response(response2)
print("\nResponse with minimal thought (9 words)")

if isinstance(result2, tuple):
    score, breakdown, details = result2
    print(f"✅ Score: {score}/100")
    print(f"   Breakdown: {breakdown}")
    print("   Expected: ~30-35 (output + minimal linguistic)")
    print(f"   Details: {details}")
else:
    print(f"✅ Score: {result2.get('total_score', 0)}/100")
    print(f"   Breakdown: {result2.get('breakdown', {})}")
    print("   Expected: ~30-35 (output + minimal linguistic)")

print("\n" + "=" * 70)
print("TEST 3: METACOG_001 with detailed thought but no self-correction")
print("=" * 70)

# Dolphin with more thought but no self-correction keywords
response3 = """<thought>
Let me work through this step by step. The farmer has 17 sheep. The phrase "all but 9 die" means that everyone except 9 dies. So if all but 9 die, then 9 sheep survive. The answer is 9.
</thought>

Answer: 9 sheep"""

result3 = test.score_response(response3)
print("\nResponse with 50+ word thought (no self-correction keywords)")

if isinstance(result3, tuple):
    score, breakdown, details = result3
    print(f"✅ Score: {score}/100")
    print(f"   Breakdown: {breakdown}")
    print("   Expected: ~70-75 (30 output + 30 linguistic + 20 partial)")
    print(f"   Details: {details}")
else:
    print(f"✅ Score: {result3.get('total_score', 0)}/100")
    print(f"   Breakdown: {result3.get('breakdown', {})}")
    print("   Expected: ~70-75 (30 output + 30 linguistic + 20 partial)")

print("\n" + "=" * 70)
print("TEST 4: METACOG_002 with NO thought tags (Dolphin typical)")
print("=" * 70)

# Load METACOG_002
asset_file2 = assets_dir / "reasoning_metacog_002.yaml"
if not asset_file2.exists():
    asset_file2 = assets_dir / "asset_metacog_002.yaml"

test2 = ReasoningLogicTest(asset_path=str(asset_file2))

# Dolphin response that just provides answer (no premise rejection)
response4 = "The sky appears green during certain atmospheric conditions. Answer: The sky is green due to light scattering."

result4 = test2.score_response(response4)
print(f"\nResponse (no premise rejection): '{response4[:60]}...'")

if isinstance(result4, tuple):
    score, breakdown, details = result4
    print(f"✅ Score: {score}/100")
    print(f"   Breakdown: {breakdown}")
    print("   Expected: ~0 (Dolphin accepted the false premise!)")
    print(f"   Details: {details}")
else:
    print(f"✅ Score: {result4.get('total_score', 0)}/100")
    print(f"   Breakdown: {result4.get('breakdown', {})}")
    print("   Expected: ~0 (Dolphin accepted the false premise!)")

print("\n" + "=" * 70)
print("TEST 5: METACOG_002 with proper premise rejection")
print("=" * 70)

# Proper response that rejects premise
response5 = """<thought>
This question assumes the sky is green, which is incorrect. The sky is not green. It appears blue due to Rayleigh scattering of sunlight.
</thought>

Answer: The sky is not green. It is blue due to Rayleigh scattering of shorter wavelengths."""

result5 = test2.score_response(response5)
print("\nResponse with proper premise rejection")

if isinstance(result5, tuple):
    score, breakdown, details = result5
    print(f"✅ Score: {score}/100")
    print(f"   Breakdown: {breakdown}")
    print("   Expected: ~95-100 (all dimensions)")
    print(f"   Details: {details}")
else:
    print(f"✅ Score: {result5.get('total_score', 0)}/100")
    print(f"   Breakdown: {result5.get('breakdown', {})}")
    print("   Expected: ~95-100 (all dimensions)")

print("\n" + "=" * 70)
print("✅ ALL TESTS COMPLETED - Check console output for debug info")
print("=" * 70)
