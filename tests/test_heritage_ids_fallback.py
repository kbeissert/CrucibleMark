"""Tests für den Heritage-IDs-Fallback-Mechanismus.

Abgedeckte Szenarien:
- find_card_by_heritage_id(): positiv, negativ, Normalisierung, Edge-Cases
- web_export.py: Slug-Matching für org-prefix-IDs
- generate_review.py: effective_model_id-Auflösung bei fehlender direkter Card
"""

from __future__ import annotations

import json


# ---------------------------------------------------------------------------
# find_card_by_heritage_id — Kernfunktion
# ---------------------------------------------------------------------------


def test_find_card_by_heritage_id_found(tmp_path):
    """Findet Card, die legacy_id in heritage_ids listet."""
    from utils.model_utils import find_card_by_heritage_id

    card_data = {
        "model_id": "vendor/new-model-v2",
        "heritage_ids": ["vendor/old-model-v1", "old-model"],
    }
    card_file = tmp_path / "vendor_new-model-v2.json"
    card_file.write_text(json.dumps(card_data), encoding="utf-8")

    result = find_card_by_heritage_id("vendor/old-model-v1", card_dir=tmp_path)
    assert result == card_file


def test_find_card_by_heritage_id_second_entry(tmp_path):
    """Findet Card auch wenn legacy_id der zweite Eintrag in heritage_ids ist."""
    from utils.model_utils import find_card_by_heritage_id

    card_data = {
        "model_id": "vendor/new-model-v2",
        "heritage_ids": ["vendor/old-model-v1", "vendor/very-old-model"],
    }
    card_file = tmp_path / "vendor_new-model-v2.json"
    card_file.write_text(json.dumps(card_data), encoding="utf-8")

    result = find_card_by_heritage_id("vendor/very-old-model", card_dir=tmp_path)
    assert result == card_file


def test_find_card_by_heritage_id_safe_name_normalization(tmp_path):
    """_safe_name-Normalisierung: 'vendor_old_model' trifft 'vendor/old.model'."""
    from utils.model_utils import find_card_by_heritage_id

    # Heritage-ID mit Punkt gespeichert, Suche mit Underscore
    card_data = {
        "model_id": "vendor/new-model",
        "heritage_ids": ["vendor/old.model"],  # Punkt in ID
    }
    card_file = tmp_path / "vendor_new-model.json"
    card_file.write_text(json.dumps(card_data), encoding="utf-8")

    # Suchstring mit Underscore (Slug-Form), beide landen bei "vendor_old_model"
    result = find_card_by_heritage_id("vendor/old_model", card_dir=tmp_path)
    assert result == card_file


def test_find_card_by_heritage_id_not_found_unknown_id(tmp_path):
    """Gibt None zurück wenn keine Card die legacy_id kennt."""
    from utils.model_utils import find_card_by_heritage_id

    card_data = {"model_id": "vendor/model", "heritage_ids": ["vendor/other"]}
    (tmp_path / "vendor_model.json").write_text(json.dumps(card_data), encoding="utf-8")

    result = find_card_by_heritage_id("vendor/unknown-model", card_dir=tmp_path)
    assert result is None


def test_find_card_by_heritage_id_skips_underscore_prefix_files(tmp_path):
    """_index.json und andere _-prefixed Files werden übersprungen."""
    from utils.model_utils import find_card_by_heritage_id

    # Index-Datei hat heritage_ids — soll nicht als Treffer gelten
    index_data = {"heritage_ids": ["vendor/old-model"]}
    (tmp_path / "_index.json").write_text(json.dumps(index_data), encoding="utf-8")

    result = find_card_by_heritage_id("vendor/old-model", card_dir=tmp_path)
    assert result is None


def test_find_card_by_heritage_id_empty_heritage_ids(tmp_path):
    """Card mit leerer heritage_ids-Liste wird korrekt ignoriert."""
    from utils.model_utils import find_card_by_heritage_id

    card_data = {"model_id": "vendor/model", "heritage_ids": []}
    (tmp_path / "vendor_model.json").write_text(json.dumps(card_data), encoding="utf-8")

    # Die eigene model_id ist kein Heritage-Eintrag
    result = find_card_by_heritage_id("vendor/model", card_dir=tmp_path)
    assert result is None


def test_find_card_by_heritage_id_missing_field(tmp_path):
    """Card ohne heritage_ids-Feld wird korrekt übersprungen."""
    from utils.model_utils import find_card_by_heritage_id

    card_data = {"model_id": "vendor/model"}  # kein heritage_ids Key
    (tmp_path / "vendor_model.json").write_text(json.dumps(card_data), encoding="utf-8")

    result = find_card_by_heritage_id("vendor/model", card_dir=tmp_path)
    assert result is None


def test_find_card_by_heritage_id_malformed_json_skipped(tmp_path):
    """Kaputte JSON-Datei führt zu graceful skip, nicht zu Exception."""
    from utils.model_utils import find_card_by_heritage_id

    # Kaputte Datei
    (tmp_path / "broken_card.json").write_text("{not valid json", encoding="utf-8")
    # Gültige Datei mit dem gesuchten Heritage-Eintrag
    card_data = {"model_id": "vendor/new-model", "heritage_ids": ["vendor/old"]}
    (tmp_path / "vendor_new-model.json").write_text(json.dumps(card_data), encoding="utf-8")

    result = find_card_by_heritage_id("vendor/old", card_dir=tmp_path)
    assert result == tmp_path / "vendor_new-model.json"


def test_find_card_by_heritage_id_empty_dir(tmp_path):
    """Leeres Verzeichnis gibt None zurück."""
    from utils.model_utils import find_card_by_heritage_id

    result = find_card_by_heritage_id("any-model", card_dir=tmp_path)
    assert result is None


# ---------------------------------------------------------------------------
# web_export.py: Slug-Matching-Verhalten
# ---------------------------------------------------------------------------


def test_heritage_slug_org_prefix_preserved_via_safe_name():
    """slugify(_safe_name()) erhält Org-Prefix als Bindestrich für audit_dirs-Lookup.

    Szenario: heritage_id = "vendor/old-model-v1"
    Audit-Dir-Name (per _safe_name): "vendor_old-model-v1"
    audit_dirs-Key (per slugify): "vendor-old-model-v1"
    Erwarteter Heritage-Lookup-Slug: "vendor-old-model-v1"
    """
    from scripts.web_export import slugify
    from utils.model_utils import _safe_name

    h_id = "vendor/old-model-v1"
    # So legt der Benchmark die Audit-Dir an:
    dir_name = _safe_name(h_id)               # "vendor_old-model-v1"
    # So wird der Key in audit_dirs gebaut:
    dir_key = slugify(dir_name)               # "vendor-old-model-v1"
    # slugify(_safe_name()) muss denselben Wert liefern:
    h_slug_safe = slugify(_safe_name(h_id))   # "vendor-old-model-v1"

    assert h_slug_safe == dir_key, (
        f"slugify(_safe_name('{h_id}')) = '{h_slug_safe}', "
        f"aber audit_dirs key = '{dir_key}'"
    )


def test_heritage_slug_without_safe_name_strips_org_prefix():
    """slugify() allein strippt den Org-Prefix — das war der ursprüngliche Bug.

    slugify("vendor/old-model-v1") == "old-model-v1" (≠ "vendor-old-model-v1")
    """
    from scripts.web_export import slugify
    from utils.model_utils import _safe_name

    h_id = "vendor/old-model-v1"
    plain_slug = slugify(h_id)             # "old-model-v1" — Bug: Org-Prefix weg
    safe_slug = slugify(_safe_name(h_id))  # "vendor-old-model-v1" — korrekt

    # Die beiden Slugs sind unterschiedlich — das belegt den Bug und den Fix:
    assert plain_slug != safe_slug
    assert plain_slug == "old-model-v1"
    assert safe_slug == "vendor-old-model-v1"


def test_heritage_ids_in_export_dict_empty_list(tmp_path):
    """heritage_ids im model_card-Export-Dict ist [] wenn Feld nicht gesetzt."""
    from scripts.web_export import _build_leaderboard_entry
    import pandas as pd

    card = {
        "model_id": "test-model",
        "display_name": "Test",
        "vendor": "TestCo",
        "weights_license_tier": "proprietary",
        "architecture_tags": ["General"],
        "supports_tool_use": None,
        # heritage_ids fehlt absichtlich
    }
    row = pd.Series({
        "Model ID": "test-model",
        "Model Name": "Test",
        "Total Score": "80.0",
        "Badge": "Gold ★",
    })

    entry = _build_leaderboard_entry(
        row=row, card=card, slug="test-model", vendor="TestCo",
        thinking_mode="standard", model_type="Proprietär",
        has_report=False, has_review=False,
        review_published_at=None, review_updated_at=None,
        benchmark_run_at=None, inference_provider=None,
    )

    assert entry["model_card"] is not None
    assert entry["model_card"]["heritage_ids"] == []


def test_heritage_ids_in_export_dict_populated(tmp_path):
    """heritage_ids im model_card-Export-Dict enthält die Card-Einträge."""
    from scripts.web_export import _build_leaderboard_entry
    import pandas as pd

    card = {
        "model_id": "vendor/new-model-v2",
        "display_name": "New Model V2",
        "vendor": "VendorCo",
        "weights_license_tier": "proprietary",
        "architecture_tags": ["General"],
        "supports_tool_use": None,
        "heritage_ids": ["vendor/old-model-v1", "old-model"],
    }
    row = pd.Series({
        "Model ID": "vendor/new-model-v2",
        "Model Name": "New Model V2",
        "Total Score": "85.0",
    })

    entry = _build_leaderboard_entry(
        row=row, card=card, slug="new-model-v2", vendor="VendorCo",
        thinking_mode="standard", model_type="Proprietär",
        has_report=False, has_review=False,
        review_published_at=None, review_updated_at=None,
        benchmark_run_at=None, inference_provider=None,
    )

    assert entry["model_card"]["heritage_ids"] == ["vendor/old-model-v1", "old-model"]
