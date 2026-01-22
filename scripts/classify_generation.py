#!/usr/bin/env python3
"""
Model Generation Classifier (Hybrid Approach).
Combines Auto-Classification (Metrics) + Heuristics (Patterns) + Manual Overrides.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional

ROOT_DIR = Path(__file__).parent.parent
HEURISTICS_FILE = ROOT_DIR / "generation_heuristics.yaml"
OVERRIDES_FILE = ROOT_DIR / "model_overrides.yaml"

class GenerationClassifier:
    """Hybrid Classifier for LLM Generations."""

    def __init__(self):
        self.heuristics = self._load_yaml(HEURISTICS_FILE)
        self.overrides = self._load_yaml(OVERRIDES_FILE).get("overrides", {})

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"⚠️ Error loading {path.name}: {e}")
            return {}

    def classify(self, model_name: str, stats: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Main classification entry point.
        Priority:
        1. Manual Override
        2. Auto-Classification (High Confidence)
        3. Heuristic Pattern Match
        4. Auto-Classification (Low/Medium Confidence)
        """
        model_key = model_name.lower()
        
        # 1. Check Overrides
        if model_name in self.overrides:
            ov = self.overrides[model_name]
            return {
                "generation": ov["generation"],
                "confidence": "OVERRIDE",
                "reason": f"Manual Override: {ov.get('reason', 'No reason provided')}"
            }
        
        # 2. Auto-Classification (if stats available)
        auto_result = {"confidence": "NONE"}
        if stats:
            auto_result = self._auto_classify_metrics(model_name, stats)
            if auto_result["confidence"] == "HIGH":
                return auto_result

        # 3. Heuristic Patterns (Name based) - fallback for Medium/Low confidence
        heuristic_gen = self._check_heuristic_patterns(model_name)
        if heuristic_gen:
            # Upgrade confidence if heuristic matches
            return {
                "generation": heuristic_gen,
                "confidence": "HIGH",
                "reason": f"Heuristic Pattern Match ({heuristic_gen}) + {auto_result.get('reason', '')}"
            }

        # 4. Return Auto Result (Medium/Low) or Default
        if auto_result["confidence"] != "NONE":
             return auto_result
             
        return {
            "generation": "Gen 1 (Pattern Matcher)",
            "confidence": "LOW",
            "reason": "Default fallback (no stats, no patterns)"
        }

    def _check_heuristic_patterns(self, model_name: str) -> Optional[str]:
        """Checks model name against known patterns."""
        name = model_name.lower()
        patterns = self.heuristics.get("patterns", {})

        # Gen 3
        for pat in patterns.get("gen3_manual_only", []):
            if pat in name:
                return "Gen 3 (Pure Reasoner)"
                
        # Gen 2
        for pat in patterns.get("gen2_names", []):
            if pat in name:
                # Check blacklist for Gen 2 (e.g. "coder" variants of R1 might be tricky, but usually strict)
                blacklist = patterns.get("gen1_blacklist", [])
                # Exception: if it is explicitly r1, ignore 'coder' blacklist if needed, 
                # but user specified blacklist overrides heuristics usually.
                # User's logic: "Außer wenn 'r1' im Namen" -> Handled in _auto_classify but valid here too.
                is_blacklisted = any(b in name for b in blacklist)
                if "r1" in name: 
                    is_blacklisted = False # R1 is R1, even if it says coder (usually)
                
                if not is_blacklisted:
                    return "Gen 2 (Distilled Reasoner)"
                    
        return None

    def _auto_classify_metrics(self, model_name: str, stats: Dict[str, float]) -> Dict[str, Any]:
        """Classifies based on benchmark metrics."""
        avg_time = stats.get("avg_time", 0)
        r_score = stats.get("reasoning_score", 0)
        c_score = stats.get("code_quality", 0)
        name = model_name.lower()

        # BLACKLIST: Force Gen 1
        blacklist = self.heuristics.get("patterns", {}).get("gen1_blacklist", [])
        if any(b in name for b in blacklist):
            if "r1" not in name:
                return {
                    "generation": "Gen 1 (Pattern Matcher)",
                    "confidence": "HIGH",
                    "reason": "Blacklisted keyword (coder/uncensored)"
                }

        # Gen 2 Detection
        # Criteria: Slower than standard (>40s), High Reasoning (>70), Reasoning significantly better than code
        score_gap = r_score - c_score
        
        if (40 <= avg_time <= 150) and (r_score >= 70) and (score_gap > 5):
            # If name supports it, HIGH confidence
            patterns = self.heuristics.get("patterns", {}).get("gen2_names", [])
            if any(p in name for p in patterns):
                return {
                    "generation": "Gen 2 (Distilled Reasoner)",
                    "confidence": "HIGH",
                    "reason": f"Metrics + Name match (Time={avg_time:.1f}s, R-Score={r_score})"
                }
            else:
                 return {
                    "generation": "Gen 2 (Distilled Reasoner)",
                    "confidence": "MEDIUM",
                    "reason": f"Metrics indicate Reasoning model but name unknown",
                    "flag_for_review": True
                }

        # Gen 1 Detection (Fast & Reliable)
        if avg_time < 50 or r_score < 65:
             return {
                "generation": "Gen 1 (Pattern Matcher)",
                "confidence": "HIGH",
                "reason": f"Standard metrics (Time={avg_time:.1f}s, R-Score={r_score})"
            }

        # Suspicious / Ambiguous
        return {
            "generation": "Gen 1 (Pattern Matcher)",
            "confidence": "LOW",
            "reason": f"Ambiguous metrics (Time={avg_time:.1f}s, R-Score={r_score})",
            "flag_for_review": True
        }

if __name__ == "__main__":
    # Test run
    cls = GenerationClassifier()
    print("Testing Classifier...")
    
    test_cases = [
        ("deepseek-r1:8b", {"avg_time": 73.05, "reasoning_score": 65.42, "code_quality": 30}), # Metrics weak but name strong
        ("phi4:latest", {"avg_time": 40.1, "reasoning_score": 79.2, "code_quality": 52}),
        ("cogito:14b", {"avg_time": 30.1, "reasoning_score": 76.25, "code_quality": 0}),     # Override test
        ("unknown-slow-model", {"avg_time": 90.0, "reasoning_score": 75.0, "code_quality": 60})
    ]
    
    for name, s in test_cases:
        res = cls.classify(name, s)
        print(f"[{res['confidence']}] {name}: {res['generation']} ({res['reason']})")
