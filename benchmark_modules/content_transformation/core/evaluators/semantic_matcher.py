"""
Semantic Matching Logic
Handles keyword detection with semantic fallback for fuzzy matching
"""

import re
from typing import List
from utils.similarity import SemanticSimilarity
from ..constants import SEMANTIC_THRESHOLDS


class SemanticMatcher:
    """Handles keyword and semantic matching for issue detection"""

    @staticmethod
    def check_issue_mentioned(
        response_lower: str,
        keywords: List[str],
        tier_name: str,
        min_keyword_threshold: float = 0.40,
    ) -> bool:
        """
        Checks if keywords are present via exact match OR semantic similarity.

        Args:
            response_lower: Lowercased LLM response
            keywords: List of keywords to detect
            tier_name: Tier level (labeled/standard/advanced/expert)
            min_keyword_threshold: Minimum % of exact keywords required

        Returns:
            True if issue is mentioned (either exact or semantically close)
        """
        if not keywords:
            return False

        # Get tier-specific semantic threshold from constants
        semantic_threshold = SEMANTIC_THRESHOLDS.get(tier_name.lower(), 0.55)

        # 1. Exact Keyword Matching
        matches = sum(1 for kw in keywords if kw.lower() in response_lower)
        match_rate = matches / len(keywords)

        # 2. Expert Tier: Require 100% exact match OR semantic validation
        if tier_name.lower() == "expert":
            if match_rate == 1.0:
                return True
            # Fall through to semantic check for missing keywords

        # 3. Standard Tiers: Pass if threshold met
        elif match_rate >= min_keyword_threshold:
            return True

        # 4. Semantic Fallback
        return SemanticMatcher._semantic_check(
            response_lower, keywords, semantic_threshold, tier_name
        )

    @staticmethod
    def _semantic_check(
        response_lower: str, keywords: List[str], threshold: float, tier_name: str
    ) -> bool:
        """
        Performs semantic similarity check using sentence-transformers.
        Expert mode validates EACH missing keyword individually.
        """
        try:
            # Split response into sentence chunks
            chunks = [
                s.strip()
                for s in re.split(r"[.!?\n]+", response_lower)
                if len(s.strip()) > 15
            ]
            if not chunks:
                chunks = [response_lower]

            # Expert Mode: Validate each missing keyword individually
            if tier_name.lower() == "expert":
                missing = [kw for kw in keywords if kw.lower() not in response_lower]
                for kw in missing:
                    score = SemanticSimilarity.find_best_match(kw, chunks)
                    if score < threshold:
                        return False  # Any missing keyword below threshold = fail
                return True

            # Standard Mode: Check if general concept (all keywords) is present
            query = " ".join(keywords)
            best_score = SemanticSimilarity.find_best_match(query, chunks)
            return best_score >= threshold

        except Exception:  # pylint: disable=broad-exception-caught
            # Fallback: if semantic check fails, return False
            return False
