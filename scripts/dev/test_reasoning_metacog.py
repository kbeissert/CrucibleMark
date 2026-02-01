#!/usr/bin/env python3
"""
Reasoning Logic Tier 3 (Metacognition) Performance Test
========================================================

Tests alle 5 METACOG Assets gegen Ollama-Modelle und berechnet RCI.
Speichert Ergebnisse in outputs/reasoning_metacog_results.csv

Usage:
    python scripts/test_reasoning_metacog.py                      # Interaktiv
    python scripts/test_reasoning_metacog.py --model dolphin --quick
    python scripts/test_reasoning_metacog.py --model deepseek-r1  # Mit Reasoning
"""

import argparse
import csv
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.benchmark_utils import load_asset_yaml, select_from_list
from utils.llm_client import LLMClient
from utils.module_loader import load_test_class
from benchmark_modules.reasoning_logic.core.evaluators import (
    calculate_rci,
    classify_model,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
REASONING_MODULE_PATH = Path("benchmark_modules/reasoning_logic")
OUTPUTS_DIR = Path("outputs/metacog_results")
METACOG_ASSET_IDS = [
    "reasoning_metacog_001",
    "reasoning_metacog_002",
    "reasoning_metacog_003",
    "reasoning_metacog_004",
    "reasoning_metacog_005",
]
TIER_1_2_ASSET_IDS = [
    "reasoning_001_river",
    "reasoning_5a_001",
    "reasoning_5b_001",
    "reasoning_5c_001",
    "reasoning_5d_001",
]


class MetacogPerformanceTester:
    """Tests Tier 3 Metacognition Assets."""

    def __init__(self):
        """Initialize tester."""
        self.outputs_dir = OUTPUTS_DIR
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.llm_client = LLMClient()
        self.results: Dict[str, Any] = {}

    @staticmethod
    def get_ollama_models() -> List[str]:
        """Get available Ollama models."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            models = []
            for line in result.stdout.strip().split("\n")[1:]:
                if line.strip():
                    models.append(line.split()[0])
            return sorted(models)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("Ollama not available: %s", e)
            return []

    def select_model(self, model_name: Optional[str] = None) -> Optional[str]:
        """Interactive or direct model selection."""
        models = self.get_ollama_models()
        if not models:
            logger.error("❌ No Ollama models found!")
            print("Install models with: ollama pull dolphin:latest")
            return None

        if model_name:
            if model_name in models:
                logger.info("✓ Using model: %s", model_name)
                return model_name
            else:
                logger.error("❌ Model not found: %s", model_name)
                return None

        selected = select_from_list(
            models,
            lambda m: m,
            prompt="Select a model",
            title="🤖 Available Ollama Models",
        )
        return selected

    def load_metacog_assets(self) -> Dict[str, dict[str, Any]]:
        """Load all METACOG assets."""
        assets_path = REASONING_MODULE_PATH / "assets"
        assets = {}

        for asset_id in METACOG_ASSET_IDS:
            # Find YAML file
            yaml_files = list(assets_path.glob(f"*{asset_id}*.yaml"))
            if not yaml_files:
                logger.warning("❌ Asset not found: %s", asset_id)
                continue

            asset = load_asset_yaml(yaml_files[0])
            if asset:
                assets[asset_id] = asset

        logger.info("✓ Loaded %d METACOG assets", len(assets))
        return assets

    def test_asset(
        self,
        model: str,
        asset_id: str,
        asset: dict[str, Any],
    ) -> Dict[str, Any]:
        """Test single asset with model."""
        logger.info("  Testing %s...", asset_id)

        try:
            # Load test class and execute
            test_class = load_test_class(
                "benchmark_modules.reasoning_logic", "ReasoningLogicTest"
            )
            if not test_class:
                logger.error("  ❌ Could not load test class")
                return {"error": "Could not load test class"}

            # Create test instance
            test_instance = test_class(asset)

            # Execute test
            start_time = time.time()
            result = test_instance.execute(
                model=model,
                llm_client=self.llm_client,
                provider="ollama",
            )
            elapsed = time.time() - start_time

            # Score response
            score_result = test_instance.score_response(
                result.get("raw_response", "")
            )

            return {
                "asset_id": asset_id,
                "model": model,
                "execution_time": elapsed,
                "total_score": score_result.get("total_score", 0),
                "max_score": score_result.get("max_score", 100),
                "tier": score_result.get("tier", "Unknown"),
                "details": score_result.get("details", []),
                "category_scores": score_result.get("category_scores", {}),
            }

        except Exception as e:
            logger.error("  ❌ Error testing %s: %s", asset_id, str(e))
            return {
                "error": str(e),
                "asset_id": asset_id,
                "model": model,
            }

    def run_metacog_benchmark(self, model: str, quick: bool = False) -> Dict[str, Any]:
        """Run full Tier 3 benchmark."""
        logger.info("\n" + "=" * 70)
        logger.info("🧠 TIER 3 METACOGNITION BENCHMARK: %s", model)
        logger.info("=" * 70)

        assets = self.load_metacog_assets()
        if not assets:
            logger.error("❌ No assets loaded!")
            return {}

        test_results = {}
        scores = []

        # Test each asset
        asset_ids_to_test = METACOG_ASSET_IDS if not quick else METACOG_ASSET_IDS[:2]

        for asset_id in asset_ids_to_test:
            if asset_id not in assets:
                logger.warning("⚠️ Skipping %s (not loaded)", asset_id)
                continue

            result = self.test_asset(model, asset_id, assets[asset_id])
            test_results[asset_id] = result

            if "error" not in result:
                score = result.get("total_score", 0)
                scores.append(score)
                logger.info(
                    "    ✅ Score: %.1f/100 (%.1fs)",
                    score,
                    result.get("execution_time", 0),
                )
            else:
                logger.info("    ❌ Error: %s", result.get("error"))

        # Calculate averages and RCI
        avg_score = sum(scores) / len(scores) if scores else 0.0
        tier3_scores = scores

        logger.info("\n" + "-" * 70)
        logger.info("📊 TIER 3 RESULTS (Metacognition)")
        logger.info("-" * 70)
        logger.info("Average Score: %.1f/100", avg_score)
        logger.info("Tests Run: %d/%d", len(scores), len(asset_ids_to_test))

        # For now, use Tier 3 scores as placeholder for RCI
        # In full integration, would need Tier 1-2 scores
        tier1_2_scores = [avg_score] * 4  # Placeholder
        rci = calculate_rci(tier1_2_scores, tier3_scores)
        classification = classify_model(rci)

        logger.info("RCI Score: %.1f", rci)
        logger.info("Classification: %s", classification)
        logger.info("=" * 70)

        return {
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "tier3_results": test_results,
            "tier3_avg": avg_score,
            "rci": rci,
            "classification": classification,
            "tests_run": len(scores),
            "tests_total": len(asset_ids_to_test),
        }

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save results to CSV and JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON detailed results
        json_path = self.outputs_dir / f"metacog_detailed_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info("✓ Saved detailed results: %s", json_path)

        # CSV summary
        csv_path = self.outputs_dir / "metacog_results_summary.csv"
        file_exists = csv_path.exists()

        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "model",
                    "tier3_avg",
                    "rci",
                    "classification",
                    "tests_run",
                    "tests_total",
                ],
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(
                {
                    "timestamp": results["timestamp"],
                    "model": results["model"],
                    "tier3_avg": results["tier3_avg"],
                    "rci": results["rci"],
                    "classification": results["classification"],
                    "tests_run": results["tests_run"],
                    "tests_total": results["tests_total"],
                }
            )

        logger.info("✓ Saved summary: %s", csv_path)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Reasoning Logic Tier 3 (Metacognition) Assets"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Model name (e.g., dolphin, deepseek-r1:14b)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test (only first 2 assets)",
    )
    args = parser.parse_args()

    tester = MetacogPerformanceTester()

    # Select model
    model = tester.select_model(args.model)
    if not model:
        sys.exit(1)

    # Run benchmark
    results = tester.run_metacog_benchmark(model, quick=args.quick)

    # Save results
    if results:
        tester.save_results(results)
    else:
        logger.error("❌ No results to save")


if __name__ == "__main__":
    main()
