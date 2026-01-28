#!/usr/bin/env python3
"""
Benchmark Baseline Comparator
=============================

Compares two benchmark result JSON files to detect regression or deviation.
Useful for:
1. Differential Testing (Commercial vs Local)
2. Regression Testing (New Code vs Old Code)
3. Consistency Checks

Usage:
    python scripts/compare_baselines.py --ref path/to/ref.json --test path/to/test.json
"""

import sys
import json
import argparse
from typing import Dict, Any, List
import math

class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

def load_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"{Colors.FAIL}Error loading {path}: {e}{Colors.ENDC}")
        sys.exit(1)

def compare_political_compass(ref: Dict[str, Any], test: Dict[str, Any], threshold: float):
    """Specific comparison logic for Political Compass results."""
    print(f"\n{Colors.HEADER}🧭 Political Compass Comparison{Colors.ENDC}")
    
    ref_coords = ref.get("coordinates", {})
    test_coords = test.get("coordinates", {})
    
    ref_x = ref_coords.get("x", 0.0)
    ref_y = ref_coords.get("y", 0.0)
    
    test_x = test_coords.get("x", 0.0)
    test_y = test_coords.get("y", 0.0)
    
    delta_x = test_x - ref_x
    delta_y = test_y - ref_y
    
    # Calculate Euclidean distance shift
    shift = math.sqrt(delta_x**2 + delta_y**2)
    
    print(f"{'Metric':<10} {'Reference':<10} {'Test':<10} {'Delta':<10}")
    print("-" * 45)
    print(f"{'Axis X':<10} {ref_x:>10.2f} {test_x:>10.2f} {delta_x:>10.2f}")
    print(f"{'Axis Y':<10} {ref_y:>10.2f} {test_y:>10.2f} {delta_y:>10.2f}")
    print("-" * 45)
    
    color = Colors.GREEN if shift < 2.0 else Colors.WARNING
    if shift > 4.0:
        color = Colors.FAIL
    
    print(f"Total Shift (Euclidean): {color}{shift:.2f}{Colors.ENDC} (Threshold: 2.0/4.0)")
    
    # Compare Archetypes
    ref_arch = ref.get("archetype", {}).get("label", "Unknown")
    test_arch = test.get("archetype", {}).get("label", "Unknown")
    
    if ref_arch != test_arch:
        print(f"\n{Colors.WARNING}⚠️  Archetype changed: {ref_arch} -> {test_arch}{Colors.ENDC}")
    else:
        print(f"\n{Colors.GREEN}✅ Archetype stable: {ref_arch}{Colors.ENDC}")

def compare_standard_benchmark(ref: List[Dict[str, Any]], test: List[Dict[str, Any]], threshold: float):
    """Compares standard list-based benchmark results."""
    print(f"\n{Colors.HEADER}📊 Score Comparison{Colors.ENDC}")
    
    # Index by Asset ID
    ref_map = {item.get("id", item.get("asset_id", "unknown")): item for item in ref}
    test_map = {item.get("id", item.get("asset_id", "unknown")): item for item in test}
    
    common_ids = set(ref_map.keys()) & set(test_map.keys())
    missing_ids = set(ref_map.keys()) - set(test_map.keys())
    # new_ids = set(test_map.keys()) - set(ref_map.keys())
    
    print(f"{'Asset ID':<30} {'Ref %':<8} {'Test %':<8} {'Delta':<8} {'Status'}")
    print("-" * 75)
    
    warnings = 0
    total_delta = 0.0
    
    for aid in sorted(common_ids):
        r_item = ref_map[aid]
        t_item = test_map[aid]
        
        r_score = r_item.get("percentage", r_item.get("score", 0) * 100)
        t_score = t_item.get("percentage", t_item.get("score", 0) * 100)
        
        delta = t_score - r_score
        total_delta += abs(delta)
        
        status = "OK"
        color = Colors.ENDC
        
        if abs(delta) > (threshold * 100):
            status = "DEV ⚠️"
            color = Colors.WARNING
            warnings += 1
        
        if abs(delta) > 50: # Massive swing
            status = "DIFF ❗"
            color = Colors.FAIL
        
        print(f"{aid[:30]:<30} {r_score:>8.1f} {t_score:>8.1f} {delta:>+8.1f} {color}{status}{Colors.ENDC}")

    if missing_ids:
        print(f"\n{Colors.WARNING}Missing in Test ({len(missing_ids)}): {', '.join(list(missing_ids)[:5])}...{Colors.ENDC}")
        
    avg_delta = total_delta / len(common_ids) if common_ids else 0
    print("-" * 75)
    print(f"Average Absolute Deviation: {avg_delta:.1f}%")
    
    if warnings > 0:
        print(f"\n{Colors.WARNING}⚠️  Found {warnings} significant deviations (> {threshold*100}%){Colors.ENDC}")
    else:
        print(f"\n{Colors.GREEN}✅ Results correspond to baseline.{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description="Compare Benchmark Results")
    parser.add_argument("--ref", required=True, help="Reference JSON file")
    parser.add_argument("--test", required=True, help="Test JSON file")
    parser.add_argument("--threshold", type=float, default=0.15, help="Warning threshold (e.g. 0.15 for 15 percent)")
    
    args = parser.parse_args()
    
    ref_data = load_json(args.ref)
    test_data = load_json(args.test) # Fixed: Using args.test instead of args.ref
    
    # Detect Type
    is_pol_compass = isinstance(ref_data, dict) and "coordinates" in ref_data
    
    if is_pol_compass:
        compare_political_compass(ref_data, test_data, args.threshold)
    elif isinstance(ref_data, list):
        compare_standard_benchmark(ref_data, test_data, args.threshold)
    else:
        print(f"{Colors.FAIL}Unknown Result Format.{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
