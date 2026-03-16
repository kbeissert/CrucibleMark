"""
Tone Evaluator
Analyzes text for formality, professionalism, and spoken style attributes.
"""

import re
from typing import Dict, Set, Any


class ToneEvaluator:
    """Evaluates the tone and style of content."""

    # Static word lists
    # Note: Move to external config if these grow large
    FORMAL_WORDS: Set[str] = {
        "therefore",
        "consequently",
        "furthermore",
        "regarding",
        "facilitate",
        "utilize",
        "commence",
        "assistance",
        "implementation",
        "verify",
        "ensure",
        "collaboration",
        "objective",
        "demonstrate",
        "however",
        "approximately",
        "sufficient",
        "indicate",
    }

    CASUAL_WORDS: Set[str] = {
        "hey",
        "cool",
        "stuff",
        "awesome",
        "crazy",
        "grab",
        "wanna",
        "gonna",
        "super",
        "actually",
        "basically",
        "pretty",
        "weird",
        "total",
        "literally",
        "totally",
        "sure",
        "yep",
        "nope",
        "okay",
        "kid",
        "guy",
        "job",
    }

    SPOKEN_MARKERS: Set[str] = {
        "um",
        "uh",
        "like",
        "mean",
        "right?",
        "sort of",
        "kind of",
    }

    @staticmethod
    def measure_formality(response: str) -> float:
        """
        Calculates a formality score from 0.0 (very casual) to 1.0 (very formal).
        Based on keyword density and presence of contractions.
        """
        if not response:
            return 0.5

        text_lower = response.lower()
        words = re.findall(r"\b\w+\b", text_lower)
        total_words = len(words)

        if total_words == 0:
            return 0.5

        formal_count = sum(1 for w in words if w in ToneEvaluator.FORMAL_WORDS)
        casual_count = sum(1 for w in words if w in ToneEvaluator.CASUAL_WORDS)

        # Check for contractions (strong indicator of informality)
        # e.g., don't, can't, it's, we're
        contractions = len(re.findall(r"\b\w+'[a-z]{1,2}\b", text_lower))

        # Weights
        # Formal words increase score
        # Casual words and contractions decrease score

        # Start neutral
        base_score = 0.5

        # Normalize impact by length (density) to some degree, but keep simple for now
        # Each formal word adds 0.05, casual/contraction removes 0.05
        # Cap at 0 and 1

        adjustment = (
            (formal_count * 0.05) - (casual_count * 0.05) - (contractions * 0.03)
        )

        final_score = base_score + adjustment
        return max(0.0, min(1.0, final_score))

    @staticmethod
    def measure_professionalism(response: str) -> float:
        """
        Measures professionalism based on absence of slang, profanity, and shouting.
        Returns 0.0 to 1.0.
        """
        if not response:
            return 1.0

        text_lower = response.lower()

        # Slang/Profanity penalty
        slang_words = [
            "lmao",
            "lol",
            "wtf",
            "omg",
            "crap",
            "suck",
            "freaking",
            "idiot",
            "stupid",
        ]
        slang_hits = sum(1 for w in slang_words if w in text_lower)

        # Base score
        if slang_hits > 0:
            # Start low if slang is present
            score = 0.5 - (slang_hits * 0.15)
        else:
            score = 1.0

        # Formatting penalty: excessive exclamation marks
        exclamations = response.count("!")
        if exclamations > 3:
            score -= 0.1

        # Formatting penalty: ALL CAPS SHOUTING
        # Heuristic: Check if > 30% of characters are upper case (and text is long enough)
        if len(response) > 20:
            caps_count = sum(1 for c in response if c.isupper())
            if (caps_count / len(response)) > 0.30:
                score -= 0.3

        return max(0.0, min(1.0, score))

    @staticmethod
    def detect_spoken_style(response: str) -> Dict[str, Any]:
        """
        Detects if the text sounds like spoken conversation.
        Returns a dictionary with details.
        """
        text_lower = response.lower()

        # Detect fillers like "um, like, you know"
        fillers_found = []
        for marker in ToneEvaluator.SPOKEN_MARKERS:
            # Check for marker as a whole word/phrase
            if re.search(r"\b" + re.escape(marker) + r"\b", text_lower):
                fillers_found.append(marker)

        # Conversational contractions
        contractions = re.findall(r"\b\w+'[a-z]{1,2}\b", text_lower)

        # Direct address
        has_direct_address = re.search(r"\byou\b|\byour\b", text_lower) is not None

        # Question count
        questions_count = response.count("?")

        is_conversational = (len(fillers_found) > 0) or (len(contractions) > 2)

        return {
            "is_conversational": is_conversational,
            "fillers_detected": fillers_found,
            "contraction_count": len(contractions),
            "uses_direct_address": has_direct_address,
            "questions_count": questions_count,
        }
