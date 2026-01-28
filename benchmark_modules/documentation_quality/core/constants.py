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
