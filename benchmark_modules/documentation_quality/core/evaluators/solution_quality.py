"""
Solution Quality Evaluator module.
Evaluates positive criteria like code examples and best practices.
"""



class SolutionQualityEvaluator:
    """
    Evaluates the quality of the solution based on positive criteria
    (e.g. code examples, best practices).
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def score_criteria(response: str, criteria: list[dict]) -> tuple[float, list[str]]:
        """
        Scores a list of positive criteria.

        Args:
            response: The response string.
            criteria: List of criteria definitions.

        Returns:
            Tuple containing:
            - score (float)
            - details (list of strings)
        """
        score = 0.0
        details = []

        for criterion in criteria:
            check_method = criterion.get("check_method", "keyword_presence")
            c_name = criterion.get("name")

            if check_method == "keyword_presence":
                earned, msg = SolutionQualityEvaluator._check_keyword_presence(
                    response, criterion
                )
                score += earned
                details.append(msg)
            elif check_method == "code_block_count":
                # Placeholder for Phase 2
                details.append(
                    f"○ {c_name}: check_method 'code_block_count' not implemented yet"
                )
            elif check_method == "readability_score":
                # Placeholder for Phase 2
                details.append(
                    f"○ {c_name}: check_method 'readability_score' not implemented yet"
                )
            else:
                details.append(f"○ {c_name}: unsupported check_method '{check_method}'")

        return round(score, 2), details

    @staticmethod
    def _check_keyword_presence(response: str, criterion: dict) -> tuple[float, str]:
        """Checks if required keywords are present."""
        name = criterion.get("name", "Unknown")
        points = criterion.get("points", 0)
        keywords = criterion.get("keywords", [])
        min_keywords = criterion.get("min_keywords", 1)

        found_keywords = [kw for kw in keywords if kw.lower() in response.lower()]

        if len(found_keywords) >= min_keywords:
            return float(points), (
                f"✓ {name}: {len(found_keywords)}/{len(keywords)} keywords found "
                f"(min {min_keywords}) +{points:.1f}p"
            )

        return 0.0, (
            f"○ {name}: {len(found_keywords)}/{len(keywords)} keywords "
            f"(min {min_keywords} required)"
        )
