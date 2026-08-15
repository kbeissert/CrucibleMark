"""
Semantic Matcher module.
Handles hybrid keyword and semantic similarity matching.
"""

import re
from utils.similarity import SemanticSimilarity
from ..constants import SIMILARITY_THRESHOLD, MIN_SENTENCE_LENGTH, ASSET_SPECIFIC_CONFIG


class SemanticMatcher:
    """
    Hybrid matching engine using both keyword counting and semantic similarity.
    Handles response cleaning (think-tags) and asset-specific thresholds.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def check_match(
        response: str, keywords: list[str], target_matches: int, asset_id: str
    ) -> bool:
        """
        Checks if keywords are present using hybrid approach.
        """
        # 1. Clean think tags
        response_cleaned = SemanticMatcher._clean_think_tags(response)

        if not keywords:
            return False

        # 2. String Matching (Keyword Count)
        matches = sum(1 for kw in keywords if kw.lower() in response_cleaned.lower())

        if matches >= target_matches:
            return True

        # 3. Semantic Similarity (Fallback)
        query = " ".join(keywords)

        sentences = SemanticMatcher._chunk_response(response_cleaned)

        try:
            # Determine threshold
            threshold = SIMILARITY_THRESHOLD

            if asset_id in ASSET_SPECIFIC_CONFIG:
                threshold = ASSET_SPECIFIC_CONFIG[asset_id].get(
                    "semantic_threshold", threshold
                )

            best_score = SemanticSimilarity.find_best_match(query, sentences)
            return best_score > threshold
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    @staticmethod
    def _clean_think_tags(response: str) -> str:
        """Removes <think>...</think> blocks from reasoning models."""
        return re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)

    @staticmethod
    def _chunk_response(response: str) -> list[str]:
        """Splits response into semantic chunks (sentences or character blocks)."""
        sentences = [
            s.strip()
            for s in response.split(".")
            if len(s.strip()) > MIN_SENTENCE_LENGTH
        ]

        if not sentences:
            sentences = [response[i : i + 200] for i in range(0, len(response), 200)]

        return sentences
