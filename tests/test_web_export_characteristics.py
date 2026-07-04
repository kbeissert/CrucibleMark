"""Tests for _build_characteristics() (seit v4.10.12).

Verifiziert die Trennung von categories (Filter-Facetten) und features
(Display-Badges). Stellt sicher, dass Tags mit display_role='category'
(Thinking, Thinking-Optional, Multimodal, Agentic, Coder, General,
Open-Weight) NICHT in features landen — sie sind bereits über dedizierte
Card-Felder (thinking_mode, use_case_primary, etc.) als categories
abgedeckt.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.web_export import _build_characteristics
from utils.card_utils import get_tag_display_roles


_CATEGORY_TAGS = {
    "Thinking", "Thinking-Optional", "Multimodal",
    "Agentic", "Coder", "General", "Open-Weight",
}


class TestBuildCharacteristicsCategories:
    """categories = Filter-Facetten aus dedizierten Card-Feldern."""

    def test_thinking_mode_partial(self):
        ch = _build_characteristics(None, "partial", [])
        cat = ch["categories"]["thinking"]
        assert cat["value"] == "partial"
        assert cat["label"] == "Adaptive Thinking"

    def test_thinking_mode_thinking(self):
        ch = _build_characteristics(None, "thinking", [])
        assert ch["categories"]["thinking"]["value"] == "thinking"
        assert ch["categories"]["thinking"]["label"] == "Thinking"

    def test_thinking_mode_standard(self):
        ch = _build_characteristics(None, "standard", [])
        assert ch["categories"]["thinking"]["value"] == "standard"
        assert ch["categories"]["thinking"]["label"] == "Standard"

    def test_use_case_from_card(self):
        card = {"use_case_primary": "agentic"}
        ch = _build_characteristics(card, "standard", [])
        assert ch["categories"]["use_case"] == {"value": "agentic", "label": "Agentic"}

    def test_use_case_coding_label(self):
        card = {"use_case_primary": "coding"}
        ch = _build_characteristics(card, "standard", [])
        assert ch["categories"]["use_case"]["label"] == "Coder"

    def test_parameter_architecture_moe(self):
        card = {"parameter_architecture": "moe"}
        ch = _build_characteristics(card, "standard", [])
        assert ch["categories"]["architecture"] == {"value": "moe", "label": "MoE"}

    def test_license_tier_from_card(self):
        card = {"weights_license_tier": "open-weights"}
        ch = _build_characteristics(card, "standard", [])
        assert ch["categories"]["license"]["value"] == "open-weights"
        assert ch["categories"]["license"]["label"] == "Open Weights"

    def test_modalities_vision(self):
        card = {"input_modalities": ["text", "image"]}
        ch = _build_characteristics(card, "standard", [])
        mod = ch["categories"]["modalities"]
        assert mod == [
            {"slug": "text", "label": "Text"},
            {"slug": "image", "label": "Vision"},
        ]

    def test_modalities_multimodal(self):
        card = {"input_modalities": ["text", "image", "audio"]}
        ch = _build_characteristics(card, "standard", [])
        assert ch["categories"]["modalities"] == [
            {"slug": "text", "label": "Text"},
            {"slug": "image", "label": "Vision"},
            {"slug": "audio", "label": "Audio"},
        ]

    def test_modalities_text_only_emits_text(self):
        card = {"input_modalities": ["text"]}
        ch = _build_characteristics(card, "standard", [])
        assert ch["categories"]["modalities"] == [{"slug": "text", "label": "Text"}]

    def test_no_card_only_thinking_category(self):
        ch = _build_characteristics(None, "standard", [])
        assert list(ch["categories"].keys()) == ["thinking"]

    def test_empty_card_fields_omit_categories(self):
        card = {"use_case_primary": None, "parameter_architecture": None}
        ch = _build_characteristics(card, "standard", [])
        assert "use_case" not in ch["categories"]
        assert "architecture" not in ch["categories"]


class TestBuildCharacteristicsFeatures:
    """features = Display-Badges aus architecture_tags (nur display_role=badge)."""

    def test_badge_tags_appear_in_features(self):
        tags = ["Long-Context", "Preview"]
        ch = _build_characteristics(None, "standard", tags)
        slugs = [f["slug"] for f in ch["features"]]
        assert slugs == ["Long-Context", "Preview"]

    def test_features_have_labels(self):
        ch = _build_characteristics(None, "standard", ["Uncensored"])
        assert ch["features"][0]["label"] == "Uncensored"

    def test_category_tags_excluded_from_features(self):
        tags = ["Thinking", "Thinking-Optional", "Multimodal", "Agentic",
                "Coder", "General", "Open-Weight"]
        ch = _build_characteristics(None, "standard", tags)
        slugs = [f["slug"] for f in ch["features"]]
        assert slugs == []

    def test_mixed_tags_split_correctly(self):
        tags = ["General", "Thinking", "Thinking-Optional", "Agentic-Orchestrator",
                "Long-Context", "Coder", "Vision-Capable"]
        ch = _build_characteristics(None, "standard", tags)
        feat_slugs = [f["slug"] for f in ch["features"]]
        assert feat_slugs == ["Agentic-Orchestrator", "Long-Context", "Vision-Capable"]

    def test_empty_tags_empty_features(self):
        ch = _build_characteristics(None, "standard", [])
        assert ch["features"] == []

    def test_unknown_tag_defaults_to_badge(self):
        ch = _build_characteristics(None, "standard", ["Unknown-Tag"])
        assert ch["features"][0]["slug"] == "Unknown-Tag"
        assert ch["features"][0]["label"] == "Unknown-Tag"

    def test_duplicate_dual_thinking_resolved(self):
        """Claude Opus 4.6 scenario: both Thinking + Thinking-Optional."""
        tags = ["General", "Thinking", "Thinking-Optional",
                "Agentic-Orchestrator", "Long-Context"]
        card = {"use_case_primary": "agentic", "parameter_architecture": "dense",
                "weights_license_tier": "proprietary",
                "input_modalities": ["text", "image"]}
        ch = _build_characteristics(card, "partial", tags)
        feat_slugs = [f["slug"] for f in ch["features"]]
        assert "Thinking" not in feat_slugs
        assert "Thinking-Optional" not in feat_slugs
        assert "General" not in feat_slugs
        assert feat_slugs == ["Agentic-Orchestrator", "Long-Context"]
        assert ch["categories"]["thinking"]["value"] == "partial"

    def test_vision_capable_deduped_when_image_modality_present(self):
        """Vision-Capable-Badge wird unterdrückt, wenn 'image' als Modality
        gerendert wird — verhindert doppeltes 'Vision'-Badge (Modality grau +
        Feature transparent). Siehe Bug-Report Claude Opus 4.8."""
        tags = ["General", "Agentic-Orchestrator", "Long-Context",
                "Vision-Capable"]
        card = {"input_modalities": ["text", "image"]}
        ch = _build_characteristics(card, "standard", tags)
        feat_slugs = [f["slug"] for f in ch["features"]]
        assert "Vision-Capable" not in feat_slugs
        assert feat_slugs == ["Agentic-Orchestrator", "Long-Context"]
        mod_labels = [m["label"] for m in ch["categories"]["modalities"]]
        assert "Vision" in mod_labels

    def test_vision_capable_kept_when_no_image_modality(self):
        """Ohne image-Modality bleibt Vision-Capable als einziges Vision-Signal."""
        tags = ["Vision-Capable", "Long-Context"]
        card = {"input_modalities": ["text"]}
        ch = _build_characteristics(card, "standard", tags)
        feat_slugs = [f["slug"] for f in ch["features"]]
        assert "Vision-Capable" in feat_slugs


class TestBuildCharacteristicsStructure:
    """Strukturelle Integrität des Rückgabe-Objekts."""

    def test_returns_dict_with_categories_and_features(self):
        ch = _build_characteristics(None, "standard", [])
        assert set(ch.keys()) == {"categories", "features"}

    def test_categories_always_has_thinking(self):
        ch = _build_characteristics(None, "standard", [])
        assert "thinking" in ch["categories"]

    def test_features_is_list(self):
        ch = _build_characteristics(None, "standard", [])
        assert isinstance(ch["features"], list)

    def test_no_category_tag_leakage_globally(self):
        """Kein Tag mit display_role='category' darf in features erscheinen."""
        for tag in _CATEGORY_TAGS:
            ch = _build_characteristics(None, "standard", [tag])
            slugs = [f["slug"] for f in ch["features"]]
            assert tag not in slugs, f"{tag} leaked into features"


class TestTagDisplayRolesConsistency:
    """Stellt sicher, dass card_vocabulary.yaml display_role konsistent definiert."""

    def test_all_category_tags_are_known(self):
        roles = get_tag_display_roles()
        for tag in _CATEGORY_TAGS:
            assert roles.get(tag) == "category", f"{tag} should be category"

    def test_thinking_optional_is_category(self):
        roles = get_tag_display_roles()
        assert roles.get("Thinking-Optional") == "category"

    def test_badge_tags_present(self):
        roles = get_tag_display_roles()
        assert roles.get("Long-Context") == "badge"
        assert roles.get("Agentic-Orchestrator") == "badge"
        assert roles.get("Vision-Capable") == "badge"
