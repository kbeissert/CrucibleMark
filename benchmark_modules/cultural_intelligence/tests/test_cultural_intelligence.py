#!/usr/bin/env python3
"""
Cultural Intelligence Test Module

Evaluates Cultural Intelligence / Fit in German context:
- Tech Localization (Code-Switching Denglisch/German)
- Inclusive Language (Gender Neutrality)
- Tone/Register Adaptation (Formal vs. Creative/Agency)
"""

import time
from typing import Dict, Any, Tuple, List
from benchmark_modules.base_test import BaseTest


class CulturalIntelligenceTest(BaseTest):
    """
    Evaluates Cultural Intelligence / Fit in German context.

    Methods:
    - Tech Localization (Code-Switching Denglisch/German)
    - Inclusive Language (Gender Neutrality)
    - Tone/Register Adaptation (Formal vs. Creative/Agency)
    """

    def execute(
        self, model: str, llm_client: Any, provider: str = "ollama"
    ) -> Dict[str, Any]:
        """
        Executes the benchmark test using the provided LLM client.
        """
        start_time = time.time()

        # Build prompt from asset
        prompt = self.asset.get("prompt", "")
        if not prompt:
            prompt = self.asset.get("input_text", "")

        system_prompt = (
            "You are a helpful AI assistant specialized in German language and culture."
        )

        full_prompt = f"{system_prompt}\n\n{prompt}"

        # Execute via client
        try:
            response_text = llm_client.query(
                prompt=full_prompt, model=model, provider=provider, temperature=0.5
            )
        except Exception as e:
            response_text = f"Error executing model: {str(e)}"

        execution_time = time.time() - start_time

        return {
            "response": response_text,
            "raw_response": response_text,
            "execution_time": execution_time,
            "metadata": {"model": model, "provider": provider},
        }

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Scores the response based on the active asset's criteria.
        """
        # Support both flat and metadata structure (just in case)
        meta = self.asset.get("metadata", {})
        asset_id = meta.get("id", self.asset.get("id", ""))

        response_lower = response.lower()
        score = 0.0
        feedback = []

        if asset_id == "cultural_intel_001":
            score, feedback = self._evaluate_tech_localization(response_lower)
        elif asset_id == "cultural_intel_002":
            score, feedback = self._evaluate_inclusive_job_ad(response_lower)
        elif asset_id == "cultural_intel_003":
            score, feedback = self._evaluate_agency_vibe(response_lower)
        else:
            feedback.append(f"Unknown asset ID: {asset_id}")
            score = 0.0

        # Create standard result structure
        # BaseTest expects: total_score (int 0-100), category_scores (dict)
        final_score = int(score * 100)

        return {
            "total_score": final_score,
            "max_score": 100,
            "category_scores": {
                "Cultural Fit": {"achieved": final_score, "max": 100},
                "Language Proficiency": {"achieved": final_score, "max": 100},
            },
            "feedback": "; ".join(feedback),
            "scoring_explanation": " | ".join(feedback),
        }

    def _evaluate_tech_localization(self, text: str) -> Tuple[float, List[str]]:
        """
        10-Point Glossary Check.
        Terms: Push, Commit, Remote, Repo, Merge, Build(n), Build(v), Issue, Branch, Pull.
        """
        # Rules defined as (Name, Lambda check)
        rules = [
            ("Push", lambda t: "push" in t and "drück" not in t),
            (
                "Commit",
                lambda t: "commit" in t
                and "verpflicht" not in t
                and "begehen" not in t,
            ),
            ("Remote", lambda t: "remote" in t or "entfernt" in t or "server" in t),
            ("Repository", lambda t: "repo" in t or "repository" in t),
            ("Merge", lambda t: "merge" in t and "verschmelz" not in t),
            ("Build(Noun)", lambda t: "build" in t or "version" in t),
            (
                "Build(Verb)",
                lambda t: any(w in t for w in ["bau", "erstell", "kompilier"]),
            ),
            # "Issue" check excludes "ausgabe" which is a false positive translation for "issue" in some contexts
            (
                "Issue",
                lambda t: any(w in t for w in ["issue", "problem", "fehler", "ticket"])
                and "ausgabe" not in t,
            ),
            ("Branch", lambda t: "branch" in t and "zweig" not in t),
            ("Pull", lambda t: "pull" in t and "zieh" not in t),
        ]

        score = 0.0
        feedback = []
        hits = 0

        for name, check_func in rules:
            if check_func(text):
                score += 0.1
                hits += 1
            else:
                feedback.append(f"✗ {name}")

        feedback.insert(0, f"Found {hits}/10 Terms")
        return min(1.0, hits / 10.0), feedback

    def _evaluate_inclusive_job_ad(self, text: str) -> Tuple[float, List[str]]:
        """
        10-Point Diversity Check.
        Remove 5 Toxic, Fix 5 Gender.
        """
        hits = 0
        feedback = []

        # Define check rules: (Description, Validation Function)
        # Function returns True if passed, False if failed
        checks = [
            # --- Toxic Removal (Must NOT be present) ---
            ("No 'Ninja'", lambda t: "ninja" not in t),
            (
                "No 'Kill'",
                lambda t: not any(x in t for x in ["kill", "töt", "umbring"]),
            ),
            ("No 'Dominate'", lambda t: "dominie" not in t and "dominate" not in t),
            (
                "No 'WorkHardPlayHard'",
                lambda t: not any(
                    x in t for x in ["work-hard", "work hard", "play hard"]
                ),
            ),
            ("No 'Manly Courage'", lambda t: "manly" not in t and "männlich" not in t),
            # --- Gender Fixes (Must be replaced/neutral) ---
            ("No 'Manpower'", lambda t: "manpower" not in t),
            (
                "No 'Craftsman'",
                lambda t: "craftsman" not in t and "handwerker" not in t,
            ),
            ("No 'Er muss'", lambda t: "er muss" not in t),
            (
                "No 'Guy/Kerl/Typ'",
                lambda t: "guy" not in t and "kerl" not in t and "typ" not in t,
            ),
            (
                "Inclusive Formatting (*in/mwd)",
                lambda t: any(m in t for m in ["(m/w/d)", "*in", ":in"]),
            ),
        ]

        for desc, check_fn in checks:
            if check_fn(text):
                hits += 1
            else:
                feedback.append(f"✗ Failed: {desc}")

        feedback.insert(0, f"Score {hits}/10 Checks")
        return min(1.0, hits / 10.0), feedback

    def _evaluate_agency_vibe(self, text: str) -> Tuple[float, List[str]]:
        """
        9-Point Buzzword Filter (FIXED v8: removed 'lösung' and 'ganzheitlich' conflicts).
        Start 0, +11.11% for each removed buzzword.

        CHANGELOG v8:
        - Removed 'lösung' from 'solution' variants (conflicted with Expected Output)
        - Removed 'ganzheitlich' from 'holistic' variants (too common in normal German)
        - Now scores 9 buzzwords instead of 10 (100% / 9 = 11.11% per buzzword)
        """
        score = 0.0
        feedback = []
        hits = 0

        # Buzzwords to avoid (EN & likely DE translations)
        # FIXED: Removed problematic variants that conflicted with Expected Output
        buzzwords = {
            "holistic": [
                "holistic",
                "holistisch",
            ],  # REMOVED 'ganzheitlich' (too common)
            "ecosystem": ["ecosystem", "ökosystem"],
            "synergy": ["synergy", "synergie"],
            "paradigm": ["paradigm", "paradigmen"],
            "gamechanger": ["gamechanger", "spielveränderer"],
            "deep-dive": [
                "deep-dive",
                "deep dive",
                "tiefeneintauch",
                "tiefes eintauch",
            ],
            "next-level": ["next-level", "nächste ebene", "next level"],
            "disruptive": ["disruptiv", "störend"],
            # REMOVED: "solution": ["solution", "lösung"],  # ← Conflicted with Expected Output "Lösungen"!
            "360-degree": ["360-degree", "360 grad", "360-grad", "360°"],
        }

        for term, variants in buzzwords.items():
            if not any(v in text for v in variants):
                score += 1 / 9  # 9 buzzwords instead of 10
                hits += 1
            else:
                feedback.append(f"✗ Kept '{term}'")

        feedback.insert(0, f"Cleaned {hits}/9 Buzzwords")
        # Use hits for precision
        return min(1.0, hits / 9.0), feedback


if __name__ == "__main__":
    print("Cultural Intelligence Test Module")
    print("Use run_benchmark.py to execute tests")
