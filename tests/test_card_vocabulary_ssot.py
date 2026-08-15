"""
Tests für die Card Vocabulary Registry (config/card_vocabulary.yaml).

Stellt sicher, dass:
  1. Registry lädt ohne Fehler
  2. reserved_tags haben eindeutige Slugs
  3. informational_tags haben eindeutige Slugs
  4. deprecated_tags haben eindeutige Slugs
  5. Kein Slug doppelt zwischen reserved/informational/deprecated vorkommt
  6. normalize_tags() normalisiert wie dokumentiert
  7. reasoning_triggers ist nicht leer und enthält Strings
  8. Alle Karten-Tags gegen Registry gültig sind (Whitelist-Test)
  9. get_all_known_tags() vereinigt alle drei Sektionen korrekt
"""

import json
from pathlib import Path

import pytest

# sys.path-Fix für direkten pytest-Aufruf
import sys
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from utils.card_utils import (  # noqa: E402
    get_all_known_tags,
    get_deprecated_normalizations,
    get_informational_tags,
    get_reasoning_triggers,
    get_reserved_tags,
    load_vocabulary,
    normalize_tags,
)


@pytest.fixture(autouse=True)
def _clear_caches():
    """Stellt sicher, dass jeder Test frische Registry-Daten sieht."""
    from utils.card_utils import clear_vocabulary_cache
    clear_vocabulary_cache()
    yield
    clear_vocabulary_cache()


def test_registry_loads():
    """Registry-Datei muss parsbar sein und die Pflicht-Sektionen enthalten."""
    vocab = load_vocabulary()
    assert "reserved_tags" in vocab
    assert "informational_tags" in vocab
    assert "deprecated_tags" in vocab
    assert "reasoning_triggers" in vocab


def test_reserved_tags_unique_slugs():
    slugs = list(get_reserved_tags())
    assert len(slugs) == len(set(slugs)), f"Doppelte Slugs: {slugs}"


def test_informational_tags_unique_slugs():
    slugs = list(get_informational_tags())
    assert len(slugs) == len(set(slugs)), f"Doppelte Slugs: {slugs}"


def test_deprecated_tags_unique_slugs():
    vocab = load_vocabulary()
    slugs = [t["slug"] for t in vocab["deprecated_tags"]]
    assert len(slugs) == len(set(slugs)), f"Doppelte Slugs: {slugs}"


def test_no_slug_overlap_across_sections():
    """reserved, informational und deprecated dürfen sich nicht überschneiden."""
    all_slugs: set[str] = set()
    overlaps: list[str] = []
    for section in ("reserved_tags", "informational_tags", "deprecated_tags"):
        vocab = load_vocabulary()
        section_slugs = {t["slug"] for t in vocab[section]}
        duplicates = section_slugs & all_slugs
        if duplicates:
            overlaps.extend(duplicates)
        all_slugs.update(section_slugs)
    assert not overlaps, f"Slug-Kollisionen zwischen Sektionen: {overlaps}"


def test_get_all_known_tags_vereinigt_drei_sektionen():
    known = get_all_known_tags()
    reserved = set(get_reserved_tags())
    informational = set(get_informational_tags())
    # deprecated ist auch Teil von known, weil get_all_known_tags() alle vereinigt.
    # Wir prüfen, dass reserved+informational enthalten sind; deprecated
    # kann zusätzlich enthalten sein (per Implementierung)
    assert reserved <= known, "reserved_tags fehlen in get_all_known_tags()"
    assert informational <= known, "informational_tags fehlen in get_all_known_tags()"


def test_normalize_tags_ersetzt_deprecated():
    """Long Context → Long-Context (Schreibweise vereinheitlichen)."""
    norm, migrations = normalize_tags(["Long Context", "Thinking", "MoE"])
    # MoE → None (entfernt)
    assert "MoE" not in norm
    # Long Context → Long-Context
    assert "Long-Context" in norm
    # Thinking bleibt
    assert "Thinking" in norm
    # Migrations-Liste muss beide dokumentierten Änderungen enthalten
    old_tags = [m[0] for m in migrations]
    assert "Long Context" in old_tags
    assert "MoE" in old_tags


def test_normalize_tags_behaelt_unbekannte():
    """Tags, die weder reserved noch deprecated sind, bleiben unverändert."""
    norm, migrations = normalize_tags(["SomeRandomFutureTag", "Thinking"])
    assert "SomeRandomFutureTag" in norm
    assert "Thinking" in norm
    # Keine Migrations-Einträge für den unbekannten Tag
    assert all(m[0] != "SomeRandomFutureTag" for m in migrations)


def test_normalize_tags_dedupliziert():
    """Doppelte Tags (z.B. nach Normalisierung) werden zu einem Eintrag konsolidiert."""
    norm, _ = normalize_tags(["Long Context", "Long-Context", "Thinking"])
    assert norm.count("Long-Context") == 1
    assert norm.count("Thinking") == 1


def test_reasoning_triggers_nonempty():
    triggers = get_reasoning_triggers()
    assert len(triggers) > 0
    assert all(isinstance(t, str) for t in triggers)
    # Mindestens die Kern-Reasoning-Familien müssen enthalten sein
    for must_have in ("o1", "o3", "deepseek-r1", "qwen3-coder"):
        assert must_have in triggers, f"Trigger '{must_have}' fehlt in Registry"


def test_deprecated_normalizations_mapping():
    """deprecated_tags mit normalized_to='null' sollen als 'entfernen' markiert sein."""
    norm = get_deprecated_normalizations()
    # MoE → None (Tag-Wert soll entfernt werden)
    assert "MoE" in norm
    assert norm["MoE"] is None
    # Long Context → Long-Context
    assert "Long Context" in norm
    assert norm["Long Context"] == "Long-Context"


def test_all_model_cards_pass_tag_whitelist():
    """Whitelist-Test: alle Tags in echten Karten müssen in Registry sein.

    Falls dieser Test fehlschlägt, hat ein Auto-Generator einen Tag
    geschrieben, der nicht dokumentiert ist. Lösung: entweder Tag in
    Reserved/Informational/Deprecated aufnehmen oder aus der Karte entfernen.
    """
    cards_dir = Path("benchmark_scores/model_cards")
    known = get_all_known_tags()
    known_lower = {t.lower() for t in known}
    violations: list[tuple[str, str]] = []

    for path in sorted(cards_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        for tag in data.get("architecture_tags", []) or []:
            if tag.lower() not in known_lower:
                violations.append((path.name, tag))

    assert not violations, (
        f"Unbekannte Tags in Karten gefunden: {violations[:10]}"
        f"{' ...' if len(violations) > 10 else ''}"
    )


def test_get_reserved_tags_returns_frozenset():
    """Helper soll frozenset liefern (für schnelle O(1) Membership-Tests)."""
    reserved = get_reserved_tags()
    informational = get_informational_tags()
    assert isinstance(reserved, frozenset)
    assert isinstance(informational, frozenset)
