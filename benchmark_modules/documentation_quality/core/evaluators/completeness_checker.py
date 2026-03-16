"""
Completeness Checker module.
Verifies presence of required documentation sections using fuzzy matching.
"""

import re
from typing import Dict, List, Any
from ..constants import DOC_TYPE_SCHEMAS


class CompletenessChecker:
    """
    Checks for required sections in documentation based on document type.
    Uses fuzzy matching to handle naming variations.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def check_completeness(response: str, doc_type: str) -> Dict[str, Any]:
        """
        Calculates completeness score and identifies missing sections.
        """
        schema = DOC_TYPE_SCHEMAS.get(doc_type)
        if not schema:
            return {"score": 1.0, "missing_sections": [], "present_sections": []}

        required = schema.get("required_sections", [])
        assert isinstance(required, list)
        if not required:
            return {"score": 1.0, "missing_sections": [], "present_sections": []}

        headings = CompletenessChecker._extract_headings(response)
        missing = []
        present = []

        for req in required:
            # Check overlap between any heading and required section
            match_found = False
            for heading in headings:
                if CompletenessChecker._fuzzy_match_section(heading, req):
                    match_found = True
                    break

            if match_found:
                present.append(req)
            else:
                missing.append(req)

        score = len(present) / len(required)

        return {
            "score": round(score, 2),
            "missing_sections": missing,
            "present_sections": present,
        }

    @staticmethod
    def _extract_headings(response: str) -> List[str]:
        """
        Extracts all markdown headings (minus #).
        """
        # Extract title text
        return [
            m.strip() for m in re.findall(r"^#{1,6}\s+(.+)$", response, re.MULTILINE)
        ]

    @staticmethod
    def _fuzzy_match_section(heading: str, required: str) -> bool:
        """
        Matches heading against required section using Levenshtein distance.
        Target: Distance < 3 or substring match.
        """
        h_norm = heading.lower()
        r_norm = required.lower()

        # 1. Direct match
        if h_norm == r_norm:
            return True

        # 2. Substring match
        if r_norm in h_norm:
            return True

        # 3. Levenshtein distance
        dist = CompletenessChecker._levenshtein(h_norm, r_norm)
        return dist < 3

    @staticmethod
    def _levenshtein(seq1: str, seq2: str) -> int:
        """
        Calculates Levenshtein distance between two strings.
        """
        if len(seq1) < len(seq2):
            return CompletenessChecker._levenshtein(seq2, seq1)  # pylint: disable=arguments-out-of-order

        if len(seq2) == 0:
            return len(seq1)

        previous_row: List[int] = list(range(len(seq2) + 1))
        for i, char1 in enumerate(seq1):
            current_row: List[int] = [i + 1]
            for j, char2 in enumerate(seq2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (char1 != char2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]
