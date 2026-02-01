#!/usr/bin/env python3
"""
Ground Truth Dataset for Metacognition Assets.

Provides gold-standard responses with validated scores for reproducibility
and inter-rater reliability validation.
"""

import os
import glob
import yaml

# Path to ground truth YAML files
GROUND_TRUTH_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "ground_truth"
)

def load_ground_truth_datasets() -> dict:
    """Load all YAML ground truth definitions."""
    datasets = {}
    
    if not os.path.exists(GROUND_TRUTH_DIR):
        print(f"Warning: Ground truth directory not found: {GROUND_TRUTH_DIR}")
        return {}

    yaml_files = glob.glob(os.path.join(GROUND_TRUTH_DIR, "*.yaml"))
    
    for file_path in yaml_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if "asset_id" in data:
                    datasets[data["asset_id"]] = data
        except yaml.YAMLError as e:
            print(f"Error loading {file_path}: {e}")
            
    return datasets

GROUND_TRUTH_DATASETS = load_ground_truth_datasets()


def validate_response_against_ground_truth(
    asset_id: str,
    response_type: str,  # "perfect", "good", "minimal", "wrong"
    actual_score: float,
    tolerance: float = 10.0  # Allow ±10 point variance
) -> dict:
    """
    Validate that actual score matches ground truth within tolerance.
    
    Args:
        asset_id: Asset identifier
        response_type: Type of response ("perfect", "good", "minimal", "wrong")
        actual_score: Actual score from evaluator
        tolerance: Acceptable score variance (default: ±10)
    
    Returns:
        Validation result with pass/fail and details
    """
    if asset_id not in GROUND_TRUTH_DATASETS:
        return {
            "success": False,
            "message": f"Asset {asset_id} not in ground truth database"
        }
    
    dataset = GROUND_TRUTH_DATASETS[asset_id]
    
    if response_type not in dataset["gold_responses"]:
        return {
            "success": False,
            "message": f"Response type '{response_type}' not found in {asset_id}"
        }
    
    expected = dataset["gold_responses"][response_type]["expected_score"]
    variance = abs(actual_score - expected)
    passed = variance <= tolerance
    
    return {
        "success": passed,
        "asset_id": asset_id,
        "response_type": response_type,
        "expected_score": expected,
        "actual_score": actual_score,
        "variance": variance,
        "tolerance": tolerance,
        "message": (
            "✅ PASS" if passed 
            else f"❌ FAIL: Expected {expected}±{tolerance}, got {actual_score}"
        )
    }


if __name__ == "__main__":
    # Display dataset structure
    for asset_id, dataset in GROUND_TRUTH_DATASETS.items():
        print(f"\n{'='*70}")
        print(f"Asset: {dataset['test_name']}")
        print(f"{'='*70}")
        
        for response_type, response_data in dataset["gold_responses"].items():
            print(f"\n{response_type.upper()}: {response_data['expected_score']}pts")
            print(f"  Breakdown: {response_data['scoring_breakdown']}")
            print(f"  Evidence: {response_data['evidence']}")
