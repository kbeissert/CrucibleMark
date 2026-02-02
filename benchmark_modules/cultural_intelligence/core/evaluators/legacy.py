# pylint: skip-file
from typing import Tuple, List, Dict, Any

class LegacyEvaluator:
    """
    Legacy evaluation logic (v1.0) for backward compatibility.
    """
    
    def __init__(self, asset: Dict[str, Any]):
        self.asset = asset

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Scores the response based on the active asset's criteria using v1 logic.
        """
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
        elif asset_id == "cultural_intel_004":
            score, feedback = self._evaluate_formal_informal(response_lower)
        elif asset_id == "cultural_intel_005":
            score, feedback = self._evaluate_german_idioms(response_lower)
        else:
            feedback.append(f"Unknown asset ID: {asset_id}")
            score = 0.0

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
            "details": feedback # Compatibility for result manager
        }

    def _evaluate_tech_localization(self, text: str) -> Tuple[float, List[str]]:
        rules = [
            ("Push", lambda t: "push" in t and "drück" not in t),
            ("Commit", lambda t: "commit" in t and "verpflicht" not in t and "begehen" not in t),
            ("Remote", lambda t: "remote" in t or "entfernt" in t or "server" in t),
            ("Repository", lambda t: "repo" in t or "repository" in t),
            ("Merge", lambda t: "merge" in t and "verschmelz" not in t),
            ("Build(Noun)", lambda t: "build" in t or "version" in t),
            ("Build(Verb)", lambda t: any(w in t for w in ["bau", "erstell", "kompilier"])),
            ("Issue", lambda t: any(w in t for w in ["issue", "problem", "fehler", "ticket"]) and "ausgabe" not in t),
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
        hits = 0
        feedback = []
        checks = [
            ("No 'Ninja'", lambda t: "ninja" not in t),
            ("No 'Kill'", lambda t: not any(x in t for x in ["kill", "töt", "umbring"])),
            ("No 'Dominate'", lambda t: "dominie" not in t and "dominate" not in t),
            ("No 'WorkHardPlayHard'", lambda t: not any(x in t for x in ["work-hard", "work hard", "play hard"])),
            ("No 'Manly Courage'", lambda t: "manly" not in t and "männlich" not in t),
            ("No 'Manpower'", lambda t: "manpower" not in t),
            ("No 'Craftsman'", lambda t: "craftsman" not in t and "handwerker" not in t),
            ("No 'Er muss'", lambda t: "er muss" not in t),
            ("No 'Guy/Kerl/Typ'", lambda t: "guy" not in t and "kerl" not in t and "typ" not in t),
            ("Inclusive Formatting (*in/mwd)", lambda t: any(m in t for m in ["(m/w/d)", "*in", ":in"])),
        ]
        for desc, check_fn in checks:
            if check_fn(text):
                hits += 1
            else:
                feedback.append(f"✗ Failed: {desc}")
        feedback.insert(0, f"Score {hits}/10 Checks")
        return min(1.0, hits / 10.0), feedback

    def _evaluate_agency_vibe(self, text: str) -> Tuple[float, List[str]]:
        score = 0.0
        feedback = []
        hits = 0
        buzzwords = {
            "holistic": ["holistic", "holistisch"],
            "ecosystem": ["ecosystem", "ökosystem"],
            "synergy": ["synergy", "synergie"],
            "paradigm": ["paradigm", "paradigmen"],
            "gamechanger": ["gamechanger", "spielveränderer"],
            "deep-dive": ["deep-dive", "deep dive"],
            "next-level": ["next-level", "nächste ebene", "next level"],
            "disruptive": ["disruptiv", "störend"],
            "360-degree": ["360-degree", "360 grad", "360-grad", "360°"],
        }
        for term, variants in buzzwords.items():
            if not any(v in text for v in variants):
                score += 1/9
                hits += 1
            else:
                feedback.append(f"✗ Kept '{term}'")
        feedback.insert(0, f"Cleaned {hits}/9 Buzzwords")
        return min(1.0, hits / 9.0), feedback

    def _evaluate_formal_informal(self, text: str) -> Tuple[float, List[str]]:
        hits = 0
        feedback = []
        def count_words(t, words):
            return sum(t.count(w) for w in words)
        
        du_forms = ["du", "dir", "dich", "dein", "deine", "deinem", "deinen"]
        du_count = count_words(text, du_forms)
        if du_count >= 2:
            hits += 2
            feedback.append(f"✓ Frequent 'Du' usage ({du_count}x)")
        elif du_count == 1:
            hits += 1
            feedback.append("~ Weak 'Du' usage (only 1x)")
        else:
            feedback.append("✗ No 'Du' forms found")

        sie_forms = [" sie ", " ihnen ", " ihr ", " ihre ", " ihren "]
        sie_count = 0
        for form in sie_forms:
            if form in text:
                sie_count += text.count(form)
        if sie_count == 0:
            hits += 2
            feedback.append("✓ Clean (No 'Sie/Ihnen')")
        elif sie_count == 1:
            hits += 1
            feedback.append("~ Tolerable (1 'Sie' found)")
        else:
            feedback.append(f"✗ Too formal ({sie_count}x 'Sie/Ihnen')")

        casual_greetings = ["hallo", "hi", "hey", "moin", "liebe", "servus"]
        if any(g in text for g in casual_greetings):
            hits += 1
            feedback.append("✓ Casual Greeting")
        else:
            feedback.append("✗ Formal/Missing Greeting")

        casual_closings = ["viele grüße", "liebe grüße", "grüße", "lg", "bis dann", "cheers", "besten gruß"]
        if any(c in text for c in casual_closings):
            hits += 1
            feedback.append("✓ Casual Closing")
        else:
            feedback.append("✗ Formal/Missing Closing")

        swaps = [
            ("bezüglich/betreffs", lambda t: "bezüglich" not in t and "betreffs" not in t),
            ("herunterladen -> laden/hol dir", lambda t: "herunterladen" not in t),
            ("Sollten Sie -> Falls du", lambda t: "sollten sie" not in t),
            ("kontaktieren -> melden/schreiben", lambda t: "kontaktieren" not in t),
        ]
        for name, check in swaps:
            if check(text):
                hits += 1
            else:
                feedback.append(f"✗ Kept formal '{name.split()[0]}'")
        feedback.insert(0, f"Score {hits}/10 Register Switch")
        return min(1.0, hits / 10.0), feedback

    def _evaluate_german_idioms(self, text: str) -> Tuple[float, List[str]]:
        score = 0.0
        feedback = []
        hits = 0
        idiom_checks = [
            ("went south", lambda t: any(x in t for x in ["ging schief", "lief schief", "scheiterte", "ging daneben", "aus dem ruder", "missglückte", "in die hose", "bach runter", "in die brüche"]), 2),
            ("outside the box", lambda t: any(x in t for x in ["kreativ", "um die ecke", "neu denken", "anders denken", "unkonventionell", "neue wege", "tellerrand", "quer"]), 2),
            ("game plan", lambda t: any(x in t for x in ["plan", "strategie", "konzept", "vorgehen", "schlachtplan"]) and "game plan" not in t, 2),
            ("touch base", lambda t: any(x in t for x in ["kurz sprechen", "abstimmen", "melden", "in kontakt", "besprechen", "austauschen", "kurzschließen", "reden"]) and "touch base" not in t, 2),
            ("get the ball rolling", lambda t: any(x in t for x in ["ins rollen", "loslegen", "starten", "anfangen", "beginnen", "in gang", "auftakt"]), 2),
        ]
        for idiom_name, check_fn, points in idiom_checks:
            if check_fn(text):
                score += points / 10.0
                hits += 1
            else:
                feedback.append(f"✗ {idiom_name}")
        feedback.insert(0, f"Translated {hits}/5 Idioms")
        return min(1.0, score), feedback
