import re
import time
from typing import Dict, Any, Tuple, List
from ..base_test import BaseTest

class CulturalIntelligenceTest(BaseTest):
    """
    Evaluates Cultural Intelligence / Fit in German context.
    Methods:
    - Tech Localization (Code-Switching Denglisch/German)
    - Inclusive Language (Gender Neutrality)
    - Tone/Register Adaptation (Formal vs. Creative/Agency)
    """

    def execute(self, model: str, llm_client: Any, provider: str = 'ollama') -> Dict[str, Any]:
        """
        Executes the benchmark test using the provided LLM client.
        """
        start_time = time.time()
        
        # Build prompt from asset
        prompt = self.asset.get('input_text', '')
        if not prompt:
             # Fallback if asset key differs (some legacy assets use 'prompt')
             prompt = self.asset.get('prompt', '')

        system_prompt = "You are a helpful AI assistant specialized in German language and culture."

        # Execute via client
        try:
            response_text = llm_client.query(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.5
            )
        except Exception as e:
            response_text = f"Error executing model: {str(e)}"

        execution_time = time.time() - start_time

        return {
            'response': response_text,
            'execution_time': execution_time,
            'metadata': {
                'model': model,
                'provider': provider
            }
        }

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Scores the response based on the active asset's criteria.
        """
        asset_id = self.asset.get('id', '')
        response_lower = response.lower()
        
        score = 0.0
        feedback = []

        if asset_id == 'cultural_intel_001':
            score, feedback = self._evaluate_tech_localization(response_lower)
        elif asset_id == 'cultural_intel_002':
            score, feedback = self._evaluate_inclusive_job_ad(response_lower)
        elif asset_id == 'cultural_intel_003':
            score, feedback = self._evaluate_agency_vibe(response_lower)
        else:
            feedback.append(f"Unknown asset ID: {asset_id}")
            score = 0.0

        # Create standard result structure
        # BaseTest expects: total_score (int 0-100), category_scores (dict)
        final_score = int(score * 100)
        
        return {
            'total_score': final_score,
            'category_scores': {
                'Cultural Fit': final_score,
                'Language Proficiency': final_score
            },
            'feedback': "; ".join(feedback),
            'scoring_explanation': " | ".join(feedback)
        }

    def _evaluate_tech_localization(self, text: str) -> Tuple[float, List[str]]:
        """
        Expects English terms for Standards (Pull Request) but German for Actions (Cancel).
        """
        score = 0.0
        feedback = []

        # 1. Check for kept English terms (Standard jargon)
        # Term: Pull Request
        if "pull request" in text and "zieh-anfrage" not in text and "zieh anfrage" not in text:
            score += 0.25
            feedback.append("✓ Kept 'Pull Request'")
        else:
            feedback.append("✗ Failed 'Pull Request'")
        
        # Term: Merge / Merge Request
        if "merge" in text and "zusammenführungsanforderung" not in text:
            score += 0.25
            feedback.append("✓ Kept 'Merge/Merge Request'")
        else:
             feedback.append("✗ Failed 'Merge'")

        # 2. Check for translated UI verbs
        # Cancel -> Abbrechen
        if "abbrechen" in text:
            score += 0.25
            feedback.append("✓ Translated 'Cancel' -> 'Abbrechen'")
        else:
            feedback.append("✗ 'Abbrechen' missing")

        # Submit -> Absenden / Bestätigen / Einreichen
        if any(w in text for w in ["absenden", "bestätigen", "einreichen"]):
            score += 0.25
            feedback.append("✓ Translated 'Submit' correctly")
        else:
            feedback.append("✗ 'Submit' translation missing")
        
        # Negative constraints (Penalty)
        if "zieh-anfrage" in text or "zieh anfrage" in text:
            score = max(0, score - 0.25)
            feedback.append("⚠️ Used 'Zieh-Anfrage'")

        return score, feedback

    def _evaluate_inclusive_job_ad(self, text: str) -> Tuple[float, List[str]]:
        """
        Expects m/w/d, gender neutral terms, removal of 'Craftsman'.
        """
        score = 0.0
        feedback = []

        # 1. Inclusion Marker (m/w/d)
        if any(m in text for m in ["(m/w/d)", "(m/f/d)", "(w/m/d)", "(d/w/m)"]):
            score += 0.3
            feedback.append("✓ Found inclusion marker (m/w/d)")
        else:
            feedback.append("✗ Missing '(m/w/d)'")

        # 2. Gender Neutral formulation
        gender_matches = re.search(r"(\w+\*in|\w+:in|\w+_in|entwickelnde)", text)
        if gender_matches:
            score += 0.4
            feedback.append("✓ Found gender-neutral formulation")
        else:
            feedback.append("✗ No gender-neutral formatting (*in/:in/Entwickelnde)")

        # 3. Removal of "Craftsman"
        if "craftsman" in text:
            feedback.append("✗ Failed to remove 'Craftsman'")
        elif "handwerker" in text:
            feedback.append("✗ Literal translation 'Handwerker' invalid here")
        else:
            if any(w in text for w in ["engineer", "developer", "entwickler"]):
                score += 0.3
                feedback.append("✓ Replaced 'Craftsman' with standard term")
            else:
                feedback.append("? Removed Craftsman but standard replacement unclear")

        return score, feedback

    def _evaluate_agency_vibe(self, text: str) -> Tuple[float, List[str]]:
        """
        Expects 'Du', informal tone, removal of stiffness.
        """
        score = 0.0
        feedback = []

        # 1. Addressing correctness: Du / Euch / Dir
        du_matches = re.search(r"\b(du|euch|dir|deine|eure)\b", text)
        sie_matches = re.search(r"\b(sie|ihnen|ihre)\b", text)

        if du_matches:
            score += 0.5
            feedback.append("✓ Used informal 'Du' address")
        else:
            feedback.append("✗ Missing 'Du' address")
        
        if sie_matches:
            score = max(0, score - 0.5) 
            feedback.append("✗ Found formal 'Sie' (Register break)")

        # 2. Vibe Keywords
        vibe_words = ["cool", "vibe", "ding", "check", "hallo", "hey", "hi", "start"]
        hits = [w for w in vibe_words if w in text]
        
        if len(hits) >= 1:
            score += 0.5
            feedback.append(f"✓ Found creative/informal keywords")
        else:
            feedback.append("✗ Text feels too stiff")

        return min(1.0, score), feedback

