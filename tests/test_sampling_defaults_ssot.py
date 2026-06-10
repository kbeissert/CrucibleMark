"""
Tests für die v4.7.2 Sampling-Default-Felder und Top-Level-Field-Whitelist.

Stellt sicher, dass:
  1. Alle 7 Sampling-Default-Felder im Template sind
  2. Alle 112 Karten die 7 Schlüssel haben (mit null)
  3. Validator warnt bei unbekanntem Top-Level-Feld in complete-Card
  4. Validator toleriert unbekannte Felder in draft-Cards
  5. add_sampling_keys.py ist idempotent
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# sys.path-Fix für direkten pytest-Aufruf
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


SAMPLING_KEYS = [
    "top_p",
    "top_k",
    "repetition_penalty",
    "frequency_penalty",
    "presence_penalty",
    "seed",
    "stop_sequences",
]


def _load_template() -> dict:
    import yaml
    with open("config/card_template_model.yaml") as f:
        return yaml.safe_load(f)


def test_all_sampling_keys_in_template():
    """Alle 7 Sampling-Felder müssen im optional_fields-Block sein."""
    template = _load_template()
    opt_names = {f["name"] for f in template.get("optional_fields", [])}
    missing = [k for k in SAMPLING_KEYS if k not in opt_names]
    assert not missing, f"Sampling-Keys fehlen im Template: {missing}"


def test_sampling_keys_have_null_default():
    """Sampling-Felder müssen default: null haben (Pipeline-Default greift)."""
    template = _load_template()
    for f in template.get("optional_fields", []):
        if f["name"] in SAMPLING_KEYS:
            assert f.get("default") is None, (
                f"Sampling-Feld {f['name']} hat default={f.get('default')!r}, "
                f"erwartet None"
            )


def test_all_cards_have_sampling_keys():
    """Alle 112 Cards müssen die 7 Sampling-Schlüssel enthalten (mit null)."""
    cards_dir = Path("benchmark_scores/model_cards")
    n_missing = 0
    for path in sorted(cards_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        for k in SAMPLING_KEYS:
            if k not in data:
                n_missing += 1
                print(f"  Missing: {path.name} → {k}")
    assert n_missing == 0, f"{n_missing} Sampling-Keys fehlen in Karten"


def test_validator_warns_on_unknown_field_in_complete_card():
    """Validator muss bei unbekanntem Top-Level-Feld in complete-Card warnen."""
    from scripts.dev.validate_model_cards import _get_template_field_names
    known = _get_template_field_names()
    assert len(known) > 0, "Template-Whitelist leer"

    # Synthetische complete-Card mit unbekanntem Feld
    test_card = {
        "model_id": "test-model",
        "display_name": "Test",
        # ... nur das eine unbekannte Feld ist für den Test relevant
        "absolutely_unknown_field": "should_warn",
    }
    test_card["card_status"] = "complete"
    from scripts.dev.validate_model_cards import check_card
    issues = check_card(Path("dummy.json"), test_card)
    unknown_warnings = [
        i for i in issues if "unbekanntes Top-Level-Feld" in i and "absolutely_unknown_field" in i
    ]
    assert unknown_warnings, f"Erwartete WARN für 'absolutely_unknown_field', bekam: {issues}"


def test_validator_tolerates_unknown_field_in_draft_card():
    """In draft-Cards werden unbekannte Felder toleriert."""
    test_card = {
        "model_id": "test-model",
        "card_status": "draft",
        "absolutely_unknown_field": "should_not_warn",
    }
    from scripts.dev.validate_model_cards import check_card
    issues = check_card(Path("dummy.json"), test_card)
    unknown_warnings = [
        i for i in issues if "unbekanntes Top-Level-Feld" in i and "absolutely_unknown_field" in i
    ]
    assert not unknown_warnings, (
        f"Unbekannte Felder sollten in draft-Cards toleriert werden, "
        f"bekam aber: {unknown_warnings}"
    )


def test_add_sampling_keys_script_idempotent(tmp_path, monkeypatch):
    """add_sampling_keys.py darf beim zweiten Lauf nichts ändern."""
    # Kopiere Cards in tmp_path
    src = Path("benchmark_scores/model_cards")
    dst = tmp_path / "cards"
    dst.mkdir()
    for p in src.glob("*.json"):
        (dst / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    # Patche CARDS_DIR im Script
    script = Path("scripts/dev/add_sampling_keys.py").read_text(encoding="utf-8")
    patched = script.replace(
        'CARDS_DIR = Path("benchmark_scores/model_cards")',
        f'CARDS_DIR = Path("{dst}")',
    )
    tmp_script = tmp_path / "add_sampling_keys.py"
    tmp_script.write_text(patched, encoding="utf-8")

    # Erster Lauf
    result1 = subprocess.run(
        [sys.executable, str(tmp_script)],
        capture_output=True, text=True, cwd="."
    )
    assert result1.returncode == 0
    n_changed_run1 = sum(
        1 for line in result1.stdout.split("\n")
        if "hinzugefügt" in line or "würde hinzufügen" in line
    )

    # Zweiter Lauf muss idempotent sein
    result2 = subprocess.run(
        [sys.executable, str(tmp_script)],
        capture_output=True, text=True, cwd="."
    )
    assert result2.returncode == 0
    n_changed_run2 = sum(
        1 for line in result2.stdout.split("\n")
        if "hinzugefügt" in line or "würde hinzufügen" in line
    )
    assert n_changed_run2 == 0, (
        f"Idempotenz verletzt: Lauf 1 änderte {n_changed_run1} Karten, "
        f"Lauf 2 änderte nochmal {n_changed_run2} Karten"
    )
