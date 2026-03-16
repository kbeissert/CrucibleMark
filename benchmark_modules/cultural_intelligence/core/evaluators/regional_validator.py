"""
Regional Consistency Validator module.

Checks for consistency in regional language usage (DE/AT/CH).
"""

# pylint: disable=relative-beyond-top-level
from ..constants import REGIONAL_EXPRESSIONS


class RegionalConsistencyValidator:
    """
    Validates regional consistency in German responses.

    Ensures no mixing of DE/AT/CH terms (e.g., "Brötchen" + "Semmel" = inconsistent).
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def validate_consistency(response: str) -> dict:
        """
        Check if response mixes regional expressions.

        Returns:
            {
                "is_consistent": bool,
                "violations": list[str],
                "dominant_region": str,
                "regional_markers": dict[str, list[str]]
            }
        """
        response_lower = response.lower()
        regional_markers: dict[str, list[str]] = {"de": [], "at": [], "ch": []}

        # Find all regional markers
        for region, categories in REGIONAL_EXPRESSIONS.items():
            for category, terms in categories.items():
                for term in terms:
                    if term in response_lower:
                        regional_markers[region].append(f"{term} ({category})")

        # Count markers per region
        marker_counts = {k: len(v) for k, v in regional_markers.items() if v}

        if len(marker_counts) == 0:
            return {
                "is_consistent": True,
                "violations": [],
                "dominant_region": "unknown",
                "regional_markers": regional_markers,
            }

        # Dominant region has most markers
        dominant_region = max(marker_counts, key=lambda k: marker_counts[k])

        # Check for inconsistencies (markers from other regions)
        violations = []
        for region, markers in regional_markers.items():
            if region != dominant_region and markers:
                violations.append(
                    f"Mixed {region.upper()} terms with {dominant_region.upper()}: "
                    f"{', '.join(markers)}"
                )

        is_consistent = len(violations) == 0

        return {
            "is_consistent": is_consistent,
            "violations": violations,
            "dominant_region": dominant_region,
            "regional_markers": regional_markers,
        }
