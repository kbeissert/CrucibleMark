"""Tests for the SSoT-Wrapper helpers added in Phase 1 (v4.10.11).

SSoT-Wrapper sind:
- safe_name_for_filesystem: _safe_name() für Filesystem-Pfade
- safe_slugify: slugify(_safe_name()) für URL/Ordner-Slugs
- normalize_for_comparison: lowercase + _safe_name für Cross-List-Vergleiche
"""
from utils.model_utils import (
    _safe_name,
    safe_name_for_filesystem,
    safe_slugify,
    normalize_for_comparison,
)


class TestSafeNameForFilesystem:
    def test_identity_with_safe_name(self):
        """safe_name_for_filesystem ist exakt _safe_name."""
        for model_id in ["gpt-5.5-pro", "deepseek/deepseek-chat-v3.1", "claude-haiku-4-5"]:
            assert safe_name_for_filesystem(model_id) == _safe_name(model_id)

    def test_hf_ollama_prefix_stripped(self):
        assert safe_name_for_filesystem("hf.co/author/model-v1.0") == "model-v1_0"


class TestSafeSlugify:
    def test_slash_to_hyphen(self):
        assert safe_slugify("vendor/model") == "model"

    def test_dots_and_underscores_normalized(self):
        assert safe_slugify("gpt-5.5-pro") == "gpt-5-5-pro"

    def test_lowercase(self):
        assert safe_slugify("GPT-5-Pro") == "gpt-5-pro"

    def test_multiple_separators_collapsed(self):
        assert safe_slugify("vendor//model...v2") == "model-v2"


class TestNormalizeForComparison:
    def test_case_insensitive(self):
        assert normalize_for_comparison("GPT-5-Pro") == normalize_for_comparison("gpt-5-pro")

    def test_dot_underscore_insensitive(self):
        assert normalize_for_comparison("deepseek/deepseek-chat-v3.1") == \
               normalize_for_comparison("deepseek_deepseek-chat-v3_1")

    def test_blacklist_matching_pattern(self):
        """Real-world scenario: Blacklist-Entry matched raw_model_id."""
        blacklist_entry = "deepseek_deepseek-chat-v3_1"
        raw_model_id = "deepseek/deepseek-chat-v3.1"
        assert normalize_for_comparison(blacklist_entry) == normalize_for_comparison(raw_model_id)
