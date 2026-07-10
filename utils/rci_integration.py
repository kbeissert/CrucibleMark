#!/usr/bin/env python3
"""
RCI Integration Helper
======================

Utilities für Integration von RCI in Benchmark-Runner und Leaderboards.
Ermöglicht einfache Berechnung und Speicherung von RCI-Scores.
"""

from typing import Any
from pathlib import Path
import csv
from benchmark_modules.reasoning_logic.core.evaluators import (
    calculate_rci,
    classify_model,
)


class RCIIntegrator:
    """Helper class for RCI integration into benchmark pipelines."""

    def __init__(self, results_dir: str = "outputs"):
        """Initialize integrator."""
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def extract_scores_from_results(
        self,
        reasoning_results: dict[str, Any],
        tier_filter: str = "all",
    ) -> dict[str, list[float]]:
        """
        Extract Tier 1-2 and Tier 3 scores from reasoning module results.

        Args:
            reasoning_results: Dictionary with asset_id -> score mappings
            tier_filter: "tier1_2", "tier3", or "all"

        Returns:
            Dictionary with "tier1_2_scores" and "tier3_scores"
        """
        tier1_2_scores = []
        tier3_scores = []

        for asset_id, result in reasoning_results.items():
            score = result.get("total_score", 0) if isinstance(result, dict) else result
            score = float(score)

            # Classify by asset ID
            if "metacog" in asset_id.lower():
                tier3_scores.append(score)
            else:
                tier1_2_scores.append(score)

        result_dict = {}
        if tier_filter in ("tier1_2", "all"):
            result_dict["tier1_2_scores"] = tier1_2_scores
        if tier_filter in ("tier3", "all"):
            result_dict["tier3_scores"] = tier3_scores

        return result_dict

    def compute_rci(
        self,
        reasoning_results: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Compute RCI from complete reasoning results.

        Args:
            reasoning_results: Dictionary with all reasoning test results

        Returns:
            Dictionary with rci, classification, and breakdown
        """
        scores = self.extract_scores_from_results(reasoning_results)

        tier1_2_scores = scores.get("tier1_2_scores", [])
        tier3_scores = scores.get("tier3_scores", [])

        # Compute RCI
        rci = calculate_rci(tier1_2_scores, tier3_scores)
        classification = classify_model(rci)

        return {
            "rci": rci,
            "classification": classification,
            "tier1_2_avg": (
                sum(tier1_2_scores) / len(tier1_2_scores) if tier1_2_scores else None
            ),
            "tier3_avg": (
                sum(tier3_scores) / len(tier3_scores) if tier3_scores else None
            ),
            "tier1_2_count": len(tier1_2_scores),
            "tier3_count": len(tier3_scores),
        }

    def update_leaderboard_csv(
        self,
        csv_path: str,
        model_name: str,
        rci_data: dict[str, Any],
        additional_data: dict[str, Any] = None,
    ) -> None:
        """
        Update leaderboard CSV with RCI scores.

        Args:
            csv_path: Path to leaderboard CSV
            model_name: Model name
            rci_data: Dictionary from compute_rci()
            additional_data: Extra columns to add
        """
        csv_file = Path(csv_path)
        file_exists = csv_file.exists()

        fieldnames = [
            "model",
            "rci",
            "classification",
            "tier1_2_avg",
            "tier3_avg",
            "thought_quality",
            "output_quality",
        ]

        if additional_data:
            fieldnames.extend(additional_data.keys())

        row = {
            "model": model_name,
            "rci": f"{rci_data['rci']:.1f}",
            "classification": rci_data["classification"],
            "tier1_2_avg": (
                f"{rci_data['tier1_2_avg']:.1f}"
                if rci_data["tier1_2_avg"] is not None
                else "N/A"
            ),
            "tier3_avg": (
                f"{rci_data['tier3_avg']:.1f}"
                if rci_data["tier3_avg"] is not None
                else "N/A"
            ),
            "thought_quality": (
                f"{rci_data['tier3_avg']:.1f}%"
                if rci_data["tier3_avg"] is not None
                else "N/A"
            ),
            "output_quality": (
                f"{rci_data['tier1_2_avg']:.1f}%"
                if rci_data["tier1_2_avg"] is not None
                else "N/A"
            ),
        }

        if additional_data:
            row.update(additional_data)

        with open(csv_file, "a" if file_exists else "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)


# Example usage in benchmark runner
INTEGRATION_EXAMPLE = """
# In your benchmark runner after reasoning tests:

from utils.rci_integration import RCIIntegrator

integrator = RCIIntegrator(results_dir="outputs")

# After running reasoning tests, you have results like:
reasoning_results = {
    "reasoning_001_river": 75.0,
    "reasoning_5a_001": 80.0,
    "reasoning_5b_001": 85.0,
    "reasoning_5c_001": 70.0,
    "reasoning_5d_001": 65.0,
    "reasoning_metacog_001": 80.0,
    "reasoning_metacog_002": 85.0,
    "reasoning_metacog_003": 75.0,
    "reasoning_metacog_004": 90.0,
    "reasoning_metacog_005": 88.0,
}

# Compute RCI
rci_data = integrator.compute_rci(reasoning_results)

# Update leaderboard
integrator.update_leaderboard_csv(
    "benchmark_scores/reasoning_leaderboard.csv",
    model_name="dolphin:7b",
    rci_data=rci_data,
    additional_data={
        "provider": "ollama",
        "timestamp": "2026-01-28T14:00:00",
    },
)

print(f"✅ RCI Score: {rci_data['rci']:.1f}")
print(f"✅ Classification: {rci_data['classification']}")
"""
