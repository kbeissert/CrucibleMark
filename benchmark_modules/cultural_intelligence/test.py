import re
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

    def execute(self, model: str, llm_client: Any, provider: str = 'ollama') -> Dict[str, Any]:
        """
        Executes the benchmark test using the provided LLM client.
        """
        start_time = time.time()
        
        # Build prompt from asset
        prompt = self.asset.get('prompt', '')
        if not prompt:
             prompt = self.asset.get('input_text', '')

        system_prompt = "You are a helpful AI assistant specialized in German language and culture."
        full_prompt = f"{system_prompt}\n\n{prompt}"

        # Execute via client
        try:
            response_text = llm_client.query(
                prompt=full_prompt,
                model=model,
                provider=provider,
                temperature=0.5
            )
        except Exception as e:
            response_text = f"Error executing model: {str(e)}"

        execution_time = time.time() - start_time

        return {
            'response': response_text,
            'raw_response': response_text,
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
        # Support both flat and metadata structure (just in case)
        meta = self.asset.get('metadata', {})
        asset_id = meta.get('id', self.asset.get('id', ''))
        
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
            'max_score': 100,
            'category_scores': {
                'Cultural Fit': {'achieved': final_score, 'max': 100},
                'Language Proficiency': {'achieved': final_score, 'max': 100}
            },
            'feedback': "; ".join(feedback),
            'scoring_explanation': " | ".join(feedback)
        }

    def _evaluate_tech_localization(self, text: str) -> Tuple[float, List[str]]:
        """
        10-Point Glossary Check.
        Terms: Push, Commit, Remote, Repo, Merge, Build(n), Build(v), Issue, Branch, Pull.
        """
        score = 0.0
        feedback = []
        hits = 0

        # Term 1: Push
        if "push" in text and "drück" not in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Push")

        # Term 2: Commit
        if "commit" in text and "verpflicht" not in text and "begehen" not in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Commit")

        # Term 3: Remote
        if "remote" in text or "entfernt" in text or "server" in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Remote")

        # Term 4: Repository
        if "repo" in text or "repository" in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Repository")

        # Term 5: Merge
        if "merge" in text and "verschmelz" not in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Merge")
        
        # Term 6: Build (Noun) - "der build" / "dem build"
        if "build" in text or "version" in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Build(Noun)")

        # Term 7: Build (Verb) - "failed to build" context
        # "bauen", "erstellen", "kompilieren", "schlug fehl" (implies action)
        if any(w in text for w in ["bau", "erstell", "kompilier"]):
            score += 0.1; hits += 1
        else: feedback.append("✗ Build(Verb)")

        # Term 8: Issue
        if any(w in text for w in ["issue", "problem", "fehler", "ticket"]) and "ausgabe" not in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Issue")

        # Term 9: Branch
        if "branch" in text and "zweig" not in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Branch")

        # Term 10: Pull
        if "pull" in text and "zieh" not in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Pull")
        
        # Bonus: Clean
        if "clean" in text or "bereinig" in text or "leeren" in text:
            # Tie breaker or bonus, max 1.0
            pass

        feedback.insert(0, f"Found {hits}/10 Terms")
        return min(1.0, hits / 10.0), feedback

    def _evaluate_inclusive_job_ad(self, text: str) -> Tuple[float, List[str]]:
        """
        10-Point Diversity Check.
        Remove 5 Toxic, Fix 5 Gender.
        """
        score = 0.0
        feedback = []
        hits = 0

        # --- Toxic Removal (Must NOT be present) ---
        toxic_map = {
            "Ninja": ["ninja"],
            "Kill": ["kill", "töt", "umbring"],
            "Dominate": ["dominie", "dominate"],
            "WorkHardPlayHard": ["work-hard", "work hard", "play hard"],
            "Manly Courage": ["manly", "männlich"] # Context "manly courage"
        }

        for k, v in toxic_map.items():
            if not any(bad in text for bad in v):
                score += 0.1
                hits += 1
            else:
                feedback.append(f"✗ Kept '{k}'")

        # --- Gender Fixes (Must be replaced/neutral) ---
        # 1. Manpower -> Personal, Kraft, Power
        if "manpower" not in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Used 'Manpower'")

        # 2. Craftsman -> Entwickler*in, Engineer, Fachkraft
        if "craftsman" not in text and "handwerker" not in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Used 'Craftsman'")

        # 3. He -> Neutral or Inclusive
        # Check if 'er' is used as standalone subject repeatedly? Hard. 
        # Easier: Check if inclusive marker is used, which fixes the pronouns usually.
        # Or check absence of "He must be". "Er muss"
        if "er muss" not in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Used 'Er muss'")

        # 4. Guy -> Mensch / Person
        if "guy" not in text and "kerl" not in text and "typ" not in text:
            score += 0.1; hits += 1
        else: feedback.append("✗ Used 'Guy/Kerl/Typ'")

        # 5. Generic 'Manly' check (the word itself)
        # Covered in Toxic? User wanted 10 points. 
        # Let's count "Ninja" type tokens as 5 and "Gender" tokens as 5.
        # "Don't be a guy" -> "Guy"
        # "Manly courage" -> "Manly" (Included in Toxic list above? Let's split semantics)
        # I used 'Manly' in toxic list. Let's add a check for the inclusive REPLACEMENT of Manpower/Craftsman
        
        # Replacement Check: Did they use *in or m/w/d?
        if any(m in text for m in ["(m/w/d)", "*in", ":in"]):
            score += 0.1; hits += 1
        else: feedback.append("✗ No inclusive Formatting")

        feedback.insert(0, f"Score {hits}/10 Checks")
        return min(1.0, hits / 10.0), feedback

    def _evaluate_agency_vibe(self, text: str) -> Tuple[float, List[str]]:
        """
        10-Point Buzzword Filter.
        Start 0, +10 for each removed buzzword.
        """
        score = 0.0
        feedback = []
        hits = 0
        
        # Buzzwords to avoid (EN & likely DE translations)
        buzzwords = {
            "holistic": ["holistic", "holistisch", "ganzheitlich"],
            "ecosystem": ["ecosystem", "ökosystem"],
            "synergy": ["synergy", "synergie"],
            "paradigm": ["paradigm", "paradigmen"],
            "gamechanger": ["gamechanger", "spielveränderer"],
            "deep-dive": ["deep-dive", "deep dive", "tiefeneintauch", "tiefes eintauch"],
            "next-level": ["next-level", "nächste ebene", "next level"],
            "disruptive": ["disruptiv", "störend"],
            "solution": ["solution", "lösung"], # 'Lösung' might be too common? Context "disruptive solutions". 
            # If they rewrite "solutions" to "Ideen" or "Ansätze", it's good. 
            # But "Lösungen" is very common German. I'll penalize only "Solutions" or "Lösungen" in buzzword context. 
            # Let's be strict: The text prompts to remove buzzwords. "Lösungen" is often empty corporate speak. 
            # Authentic agencies say "Sachen", "Produkte", "Ergebnisse".
            # I will check 'solution' and 'lösung' but give leeway if it seems normal? No, strict for benchmark.
            
            "360-degree": ["360-degree", "360 grad", "360-grad", "360°"]
        }

        for term, variants in buzzwords.items():
            if not any(v in text for v in variants):
                score += 0.1
                hits += 1
            else:
                feedback.append(f"✗ Kept '{term}'")

        feedback.insert(0, f"Cleaned {hits}/10 Buzzwords")
        # Use hits for precision
        return min(1.0, hits / 10.0), feedback

