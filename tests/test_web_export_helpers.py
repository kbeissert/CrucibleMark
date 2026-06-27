"""Coverage for 12 web_export.py helper functions (Phase 4).

Vorher: 0/12 Helper direkt getestet. Diese Tests verifizieren Edge-Cases
und schaffen Sicherheitsnetz fuer Phase 5 (Helper-Extraktion).
"""
from pathlib import Path
import sys

# Add project root to path (necessary because web_export is a script not a module)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.web_export import (
    slugify,
    sanitize_audit_log,
    parse_tests_run,
    normalize_pending,
    parse_star_float,
    extract_badge_tier,
    extract_version,
    clean_float,
    _strip_emojis,
    _build_vendor_alias_map,
    _normalize_vendor,
    _build_community_alias_map,
    _normalize_community,
    _load_pc_block_meta,
    _build_block_scores,
)


class TestSlugify:
    def test_lowercase(self):
        assert slugify("GPT-5-Pro") == "gpt-5-pro"

    def test_slash_keeps_last_segment(self):
        assert slugify("vendor/model") == "model"

    def test_special_chars_to_hyphen(self):
        assert slugify("model v2.0!") == "model-v2-0"

    def test_empty(self):
        assert slugify("") == ""


class TestSanitizeAuditLog:
    def test_removes_section_3_before_module_metrics(self):
        content = (
            "## 1. Prompt\nHello\n\n"
            "## 2. Response\nFoo\n\n"
            "## 3. Evaluation / LLM-Judge / Scorer\nSECRET\n\n"
            "---\n\n### 📦 Modul-Metriken\nMetrics"
        )
        result = sanitize_audit_log(content)
        assert "SECRET" not in result
        assert "Modul-Metriken" in result
        assert "Evaluation" not in result

    def test_preserves_prompt_and_response(self):
        content = (
            "## 1. Prompt\nHello\n\n"
            "## 2. Response\nFoo\n\n"
            "## 3. Evaluation / LLM-Judge / Scorer\nSECRET"
        )
        result = sanitize_audit_log(content)
        assert "Hello" in result
        assert "Foo" in result


class TestParseTestsRun:
    def test_valid_format(self):
        assert parse_tests_run("12 / 15") == {"completed": 12, "total": 15}

    def test_with_whitespace(self):
        assert parse_tests_run("  3 / 7  ") == {"completed": 3, "total": 7}

    def test_invalid_returns_none(self):
        assert parse_tests_run("n/a") is None
        assert parse_tests_run("") is None


class TestNormalizePending:
    def test_pending_returns_none(self):
        assert normalize_pending("Pending") is None

    def test_dash_returns_none(self):
        assert normalize_pending("—") is None

    def test_empty_string_returns_none(self):
        assert normalize_pending("") is None

    def test_numeric_string_returns_float(self):
        assert normalize_pending("3.14") == 3.14

    def test_non_numeric_string_returned(self):
        assert normalize_pending("hello") == "hello"


class TestParseStarFloat:
    def test_with_star(self):
        assert parse_star_float("4.0 ★") == 4.0

    def test_without_star(self):
        assert parse_star_float("3.8") == 3.8

    def test_pending_returns_none(self):
        assert parse_star_float("Pending") is None

    def test_invalid_returns_none(self):
        assert parse_star_float("foo") is None


class TestExtractBadgeTier:
    def test_with_label(self):
        assert extract_badge_tier("Gold Tier") == "Tier"

    def test_bare_string(self):
        assert extract_badge_tier("Gold") == "Gold"

    def test_empty_returns_none(self):
        assert extract_badge_tier("") is None


class TestExtractVersion:
    def test_valid_version(self):
        assert extract_version("20250929") == "20250929"

    def test_unknown_returns_none(self):
        assert extract_version("unknown") is None

    def test_empty_returns_none(self):
        assert extract_version("") is None


class TestCleanFloat:
    def test_numeric(self):
        assert clean_float("3.14") == 3.14

    def test_pending_returns_none(self):
        assert clean_float("Pending") is None

    def test_empty_returns_none(self):
        assert clean_float("") is None


class TestStripEmojis:
    def test_strips_from_string(self):
        # Strip entfernt Emojis (Whitespace-Pattern ist Implementation-Detail)
        result = _strip_emojis("Hello 🎉 World")
        assert "🎉" not in result
        assert "Hello" in result and "World" in result

    def test_recursive_dict(self):
        result = _strip_emojis({"a": "🎉", "b": {"c": "🚀"}})
        assert result == {"a": "", "b": {"c": ""}}

    def test_recursive_list(self):
        assert _strip_emojis(["🎉", "ok", ["🚀"]]) == ["", "ok", [""]]

    def test_passthrough_non_string(self):
        assert _strip_emojis(42) == 42
        assert _strip_emojis(None) is None


class TestVendorAliasMap:
    def test_loads_from_real_taxonomy(self):
        """Real config/classification_taxonomy.json muss valide sein."""
        config_dir = ROOT / "config"
        alias_map = _build_vendor_alias_map(config_dir)
        assert isinstance(alias_map, dict)
        assert len(alias_map) > 0, "Taxonomy leer?"

    def test_canonical_is_self(self):
        config_dir = ROOT / "config"
        alias_map = _build_vendor_alias_map(config_dir)
        for canonical in alias_map.values():
            assert alias_map.get(canonical) == canonical

    def test_missing_file_returns_empty(self, tmp_path):
        alias_map = _build_vendor_alias_map(tmp_path)
        assert alias_map == {}


class TestNormalizeVendor:
    def test_canonical_match(self):
        alias_map = {"Google DeepMind": "Google", "Google": "Google"}
        assert _normalize_vendor("Google", alias_map) == "Google"

    def test_alias_match(self):
        alias_map = {"Google DeepMind": "Google"}
        assert _normalize_vendor("Google DeepMind", alias_map) == "Google"

    def test_compound_first_segment_match(self):
        alias_map = {"Google DeepMind": "Google"}
        assert _normalize_vendor("Google DeepMind / Unsloth", alias_map) == "Google"

    def test_unknown_returns_input(self):
        alias_map = {"Foo": "Bar"}
        assert _normalize_vendor("Baz", alias_map) == "Baz"

    def test_none_input(self):
        assert _normalize_vendor(None, {"a": "b"}) is None


class TestCommunityAliasMap:
    def test_loads_or_empty(self):
        config_dir = ROOT / "config"
        alias_map = _build_community_alias_map(config_dir)
        assert isinstance(alias_map, dict)


class TestNormalizeCommunity:
    def test_canonical_match(self):
        alias_map = {"HuggingFace": "HuggingFace"}
        assert _normalize_community("HuggingFace", alias_map) == "HuggingFace"

    def test_alias_match(self):
        alias_map = {"HuggingFace": "HF"}
        assert _normalize_community("HuggingFace", alias_map) == "HF"

    def test_none_input(self):
        assert _normalize_community(None, {"a": "b"}) is None


class TestLoadPCBlockMeta:
    def test_missing_file_returns_fallback(self, tmp_path):
        result = _load_pc_block_meta(tmp_path / "nonexistent.yaml")
        assert "7.1" in result
        assert result["7.1"]["axis"] == "x"

    def test_real_config_loads(self):
        """Real config.yaml im Repo muss PC-Block-Meta enthalten."""
        config_path = ROOT / "benchmark_modules" / "political_compass" / "config.yaml"
        if config_path.exists():
            result = _load_pc_block_meta(config_path)
            assert isinstance(result, dict)
            assert len(result) > 0


class TestBuildBlockScores:
    def test_empty_stats_returns_empty(self):
        assert _build_block_scores({}, {}) == {}

    def test_vanilla_block_axis_x(self):
        module_stats = {"vanilla": {"7.1": {"x": 3.14, "y": 0.0}}}
        block_meta = {"7.1": {"label": "Test", "axis": "x"}}
        result = _build_block_scores(module_stats, block_meta)
        assert result["7.1"]["vanilla"] == 3.14
        assert result["7.1"]["axis"] == "x"

    def test_both_axis(self):
        module_stats = {"vanilla": {"7.9": {"x": 1.0, "y": -1.0}}}
        block_meta = {"7.9": {"label": "Test", "axis": "both"}}
        result = _build_block_scores(module_stats, block_meta)
        assert result["7.9"]["vanilla_x"] == 1.0
        assert result["7.9"]["vanilla_y"] == -1.0
