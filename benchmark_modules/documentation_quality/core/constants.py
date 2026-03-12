"""
Configuration constants for Documentation Quality module.

Thresholds:
- TIER_THRESHOLDS: Keyword match ratios per tier (lower = stricter)
- SIMILARITY_THRESHOLD: Semantic similarity baseline (0.70 = 70% match)
- MIN_SENTENCE_LENGTH: Minimum chars for sentence chunking

Asset-specific overrides in ASSET_SPECIFIC_CONFIG.
"""

# Constants
TOKEN_MULTIPLIER = 1.3
DEFAULT_TEMPERATURE = 0.3
TIER_THRESHOLDS = {"labeled": 0.40, "standard": 0.40, "advanced": 0.35, "expert": 0.30}
SIMILARITY_THRESHOLD = 0.70  # Lowered from 0.78 for better recall on small models
MIN_SENTENCE_LENGTH = 15

# Asset-specific configuration for fine-tuning thresholds
# Keys match the asset file stems (e.g. asset_001_readme_quality)
ASSET_SPECIFIC_CONFIG = {
    "asset_001_readme_quality": {"semantic_threshold": 0.35},
    "asset_002_rest_api_documentation": {"semantic_threshold": 0.35},
    "asset_003_component_props_documentation": {"semantic_threshold": 0.35},
    "asset_004_setup_guide_troubleshooting": {"semantic_threshold": 0.35},
    "asset_005_changelog_release_notes": {"semantic_threshold": 0.30},
}

DOC_TYPE_SCHEMAS = {
    "readme": {
        "required_sections": ["installation", "usage", "examples"],
        "min_code_blocks": 1,
        "min_headings": 3,
    },
    "api_docs": {
        "required_sections": ["endpoint", "parameters", "response", "example"],
        "min_code_blocks": 2,
        "min_headings": 4,
    },
    "setup_guide": {
        "required_sections": ["prerequisites", "steps", "troubleshooting"],
        "min_code_blocks": 1,
        "min_headings": 3,
    },
}
