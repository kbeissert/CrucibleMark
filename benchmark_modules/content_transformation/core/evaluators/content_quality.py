"""
Content Quality Evaluator
Scores solution quality (creativity, flow, format compliance)
"""



class ContentQualityEvaluator:
    """Evaluates solution quality dimensions"""

    @staticmethod
    def score_solution_quality(
        response_lower: str, config: dict
    ) -> tuple[float, list[str], float]:
        """
        Scores solution quality based on criteria (e.g., creativity, CTA presence).

        Returns:
            (score, details, max_possible)
        """
        score = 0.0
        details = []
        criteria = config.get("criteria", [])
        max_possible = sum(c.get("points", 0) for c in criteria)

        for criterion in criteria:
            name = criterion.get("name", "Unknown")
            points = criterion.get("points", 0)
            keywords = criterion.get("keywords", [])
            check_method = criterion.get("check_method", "keyword_presence")
            min_keywords = criterion.get("min_keywords", 1)

            if check_method == "keyword_presence":
                found_keywords = [kw for kw in keywords if kw.lower() in response_lower]
                if len(found_keywords) >= min_keywords:
                    earned = points
                    score += earned
                    details.append(
                        f"✓ {name}: {len(found_keywords)}/{len(keywords)} keywords found "
                        f"(min {min_keywords}) +{earned:.1f}p"
                    )
                else:
                    details.append(
                        f"○ {name}: {len(found_keywords)}/{len(keywords)} keywords "
                        f"(min {min_keywords} required)"
                    )

            elif check_method == "negative_keyword_presence":
                bad_keywords = criterion.get("forbidden_keywords", [])
                found_bad = [kw for kw in bad_keywords if kw.lower() in response_lower]
                if not found_bad:
                    score += points
                    details.append(f"✓ {name}: No forbidden keywords found +{points}p")
                else:
                    details.append(
                        f"✗ {name}: Forbidden keywords found: {', '.join(found_bad)}"
                    )

            else:
                details.append(f"○ {name}: unsupported check_method '{check_method}'")

        return round(score, 2), details, max_possible
