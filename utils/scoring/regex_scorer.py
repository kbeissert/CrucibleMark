"""
Regex/Rule-based Scorer implementation.
Evaluates responses based on defined criteria (Regex, Keywords, etc).
"""
import re
from typing import Any, Dict, List, Tuple
from .base import BaseScorer
from .helpers import ScoringHelpers

class RegexScorer(BaseScorer):
    """
    Scores responses using a list of rule-based criteria.
    Iterates through scoring configuration and applies matching logic.
    """
    
    def __init__(self):
        self.helpers = ScoringHelpers()

    def score_response(
        self, 
        response: str, 
        asset: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Implementation of the BaseScorer interface for Rule/Regex scoring.
        """
        scoring_config = asset.get("scoring", {})
        
        # Initialize result structure
        results = {
            "status": "success",
            "total_score": 0.0,
            "max_score": scoring_config.get("total_points", 100),
            "category_scores": {},
            "details": [],
            "violations": []
        }
        
        response_lower = response.lower()
        
        # Iterate over specific categories if defined, or just criteria list
        # This mirrors the logic found in CodeQualityEvaluator but generalized
        # For now, we assume the asset has 'scoring' -> 'criteria' list or named categories
        # But wait, existing assets have structured categories like 'solution_quality', 'formatting'
        
        # TODO: Refactor existing modules to standardize this config structure
        # Or adapt this scorer to handle flexible keys.
        
        # Simplified implementation for now:
        # Check standard categories
        for key, conf in scoring_config.items():
            if not isinstance(conf, dict) or "criteria" not in conf:
                continue
                
            cat_score = 0.0
            cat_max = conf.get("weight", 0)
            
            for criterion in conf.get("criteria", []):
                points, msg = self._dispatch_criterion(criterion, response, response_lower)
                cat_score += points
                results["details"].append(msg)
                
            # Clamp and Record
            actual_score = min(cat_score, cat_max)
            results["category_scores"][key] = {
                "achieved": round(actual_score, 2),
                "max": cat_max
            }
            results["total_score"] += actual_score

        return results

    def _dispatch_criterion(self, criterion: Dict[str, Any], response: str, response_lower: str) -> Tuple[float, str]:
        """Dispatches to the correct helper method."""
        method = criterion.get("check_method")
        method_name = f"score_{method}"
        
        if hasattr(self.helpers, method_name):
            scorer = getattr(self.helpers, method_name)
            # Param dispatch
            if method in ["keyword_presence", "list_detection"]:
                return scorer(response_lower, criterion)
            return scorer(response, criterion)
            
        return 0.0, f"Unknown method: {method}"
