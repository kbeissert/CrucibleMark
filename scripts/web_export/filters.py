from __future__ import annotations

import json
import logging
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml

from utils.model_utils import _safe_name

from .constants import _BLACKLIST_PATH

def _build_vendor_alias_map(config_dir: Path) -> dict[str, str]:
    """Liest Hersteller-Aliases aus classification_taxonomy.json und gibt
    ein alias→kanonischer-Name-Mapping zurück.

    Beispiel: {"Alibaba Cloud": "Alibaba", "Google DeepMind": "Google", ...}
    """
    taxonomy_path = config_dir / "classification_taxonomy.json"
    alias_map: dict[str, str] = {}
    try:
        with taxonomy_path.open("r", encoding="utf-8") as f:
            taxonomy = json.load(f)
        manufacturers = taxonomy.get("manufacturers", {}).get("values", {})
        for canonical_name, entry in manufacturers.items():
            # Canonical selbst ist immer gültig
            alias_map[canonical_name] = canonical_name
            for alias in entry.get("aliases", []):
                alias_map[alias] = canonical_name
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        logging.warning("Vendor-Alias-Map konnte nicht geladen werden: %s", exc)
    return alias_map


def _build_vendor_card_id_lookup(config_dir: Path) -> dict[str, str]:
    """Gibt ein dict kanonischer_vendor_name → vendor_card_id zurück (aus Taxonomy).

    Wird im Web-Export verwendet um vendor_card_ref pro Modell zu setzen.
    Graceful: leeres Dict bei Ladefehler.
    """
    taxonomy_path = config_dir / "classification_taxonomy.json"
    result: dict[str, str] = {}
    try:
        with taxonomy_path.open("r", encoding="utf-8") as f:
            taxonomy = json.load(f)
        for name, entry in taxonomy.get("manufacturers", {}).get("values", {}).items():
            vid = entry.get("vendor_card_id")
            if vid:
                result[name] = vid
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        logging.warning("Vendor-Card-ID-Lookup konnte nicht geladen werden: %s", exc)
    return result


def _normalize_vendor(vendor: str | None, alias_map: dict[str, str]) -> str | None:
    """Normalisiert einen vendor-Wert auf den kanonischen Hersteller-Namen.

    Lookup-Reihenfolge:
    1. Exakter Match im Alias-Map.
    2. Compound-String-Fallback: Bei ``/``-getrennten Vendors wird jedes Segment
       (getrimmt) gegen den Alias-Map geprüft. Erster Match gewinnt.
       Beispiel: ``"Google DeepMind / Unsloth (Quantisierung)"`` → Segment
       ``"Google DeepMind"`` → ``"Google"``.
    3. Bei keinem Match: WARNING + Originalwert (Callers wie Web-Export können
       den Wert als Fallback verwenden).

    Warum Compound-Fallback
    -----------------------
    Community-Quantisierungen erzeugen neue Compound-Vendor-Strings
    (Basis-Entwickler + Distributor). Jede mögliche Kombination als Alias
    in die Taxonomy aufzunemen skaliert nicht. Stattdessen wird der erste
    Segment (Basis-Entwickler) extrahiert und normalisiert.
    """
    if vendor is None:
        return None
    normalized = alias_map.get(vendor)
    if normalized is not None:
        return normalized

    # Compound-String-Fallback: "Google DeepMind / Unsloth (Quantisierung)"
    # → erster Segment "Google DeepMind" → Alias "Google"
    if "/" in vendor:
        for segment in vendor.split("/"):
            segment = segment.strip()
            if not segment:
                continue
            seg_normalized = alias_map.get(segment)
            if seg_normalized is not None:
                logging.debug(
                    "Vendor-Compound-Fallback: '%s' → Segment '%s' → '%s'",
                    vendor, segment, seg_normalized,
                )
                return seg_normalized

    logging.warning(
        "Unbekannter vendor '%s' — nicht in classification_taxonomy.json/manufacturers. "
        "Bitte eintragen oder Alias hinzufügen.",
        vendor,
    )
    return vendor


def _build_community_alias_map(config_dir: Path) -> dict[str, str]:
    """Liest Community-Gruppen-Aliases aus classification_taxonomy.json und gibt
    ein alias→kanonischer-Name-Mapping zurück.

    Beispiel: {"unslothai": "Unsloth", "Unsloth AI": "Unsloth", ...}
    """
    taxonomy_path = config_dir / "classification_taxonomy.json"
    alias_map: dict[str, str] = {}
    try:
        with taxonomy_path.open("r", encoding="utf-8") as f:
            taxonomy = json.load(f)
        groups = taxonomy.get("community_groups", {}).get("values", {})
        for canonical_name, entry in groups.items():
            alias_map[canonical_name] = canonical_name
            for alias in entry.get("aliases", []):
                alias_map[alias] = canonical_name
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        logging.warning("Community-Alias-Map konnte nicht geladen werden: %s", exc)
    return alias_map


def _build_community_card_id_lookup(config_dir: Path) -> dict[str, str]:
    """Gibt ein dict kanonischer_community_name → vendor_card_id zurück (aus Taxonomy).

    Wird im Web-Export verwendet um community_card_ref pro Modell zu setzen.
    """
    taxonomy_path = config_dir / "classification_taxonomy.json"
    result: dict[str, str] = {}
    try:
        with taxonomy_path.open("r", encoding="utf-8") as f:
            taxonomy = json.load(f)
        for name, entry in taxonomy.get("community_groups", {}).get("values", {}).items():
            vid = entry.get("vendor_card_id")
            if vid:
                result[name] = vid
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        logging.warning("Community-Card-ID-Lookup konnte nicht geladen werden: %s", exc)
    return result


def _normalize_community(community: str | None, alias_map: dict[str, str]) -> str | None:
    """Normalisiert einen community-Wert auf den kanonischen Gruppen-Namen.

    Kein WARNING bei None (community ist optional). WARNING nur bei bekannt-falschem Wert.
    """
    if community is None:
        return None
    normalized = alias_map.get(community)
    if normalized is not None:
        return normalized
    logging.warning(
        "Unbekannte community '%s' — nicht in classification_taxonomy.json/community_groups. "
        "Bitte eintragen oder Alias hinzufügen.",
        community,
    )
    return community


_PLACEHOLDER_VENDOR_IDS: frozenset[str] = frozenset({"todo", "unknown"})

def _collect_vendor_cards(root_dir: Path, *, exclude_community: bool = False) -> list[dict[str, Any]]:
    """Sammelt alle Provider-Card-JSONs aus benchmark_scores/vendor_cards/.

    SSoT: benchmark_scores/vendor_cards/ ist die einzige Quelle.
    Spurious-Files (_index.json, ...) werden ueber 'vendor_id'-Key gefiltert.
    Defense-in-Depth: Placeholder-IDs (todo, unknown) und unknown=true Cards
    werden ausgefiltert, sodass sie nicht im Web-Export erscheinen.
    Mit exclude_community=True werden Community-Karten (card_subtype=community)
    ausgeklammert (sie landen in community_cards.json).
    """
    cards_dir = root_dir / "benchmark_scores" / "vendor_cards"
    if not cards_dir.exists():
        return []
    result: list[dict[str, Any]] = []
    for fp in sorted(cards_dir.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logging.debug("Vendor-Card kaputt: %s (%s)", fp.name, exc)
            continue
        if not isinstance(data, dict) or "vendor_id" not in data:
            continue  # Skip index/metadata files
        # Defense-in-Depth: Placeholder und unknown ausklammern
        if data.get("vendor_id") in _PLACEHOLDER_VENDOR_IDS:
            continue
        if data.get("unknown"):
            continue
        # Community-Subset-Filter (optional)
        if exclude_community and data.get("card_subtype") == "community":
            continue
        result.append(data)
    return result


def _collect_community_cards(root_dir: Path) -> list[dict[str, Any]]:
    """Gibt alle Vendor-Cards mit card_subtype == 'community' zurück."""
    return [c for c in _collect_vendor_cards(root_dir) if c.get("card_subtype") == "community"]


def _load_export_blacklist(
    config_path: Path | None = None,
    *,
    root_dir: Path | None = None,
) -> tuple[set[str], set[str], int, bool]:
    """Liest die Web-Export-Blacklist und splittet in exakte + Pattern-Eintraege.

    Returns:
        (exact_set, pattern_set, total_entries, file_loaded)
        - exact_set:    IDs, die per ``raw_model_id in set`` gematcht werden (O(1)).
        - pattern_set:  fnmatch-Patterns (``*``, ``?``, ``[seq]``).
        - total_entries: Anzahl Eintraege in der Config (Summe beider Sets).
        - file_loaded:  True wenn Datei existiert hat und geladen wurde.

    Datei fehlt:    (set(), set(), 0, False) — graceful default, keine Filterung.
    Parse-Error:    WARNING-Log + (set(), set(), 0, False) — nicht fatal.
    Leere Datei:    (set(), set(), 0, True)  — geladen, aber leer.
    """
    if config_path is not None:
        path = config_path
    elif root_dir is not None:
        path = root_dir / "config" / "web_export_blacklist.yaml"
    else:
        path = _BLACKLIST_PATH
    if not path.exists():
        return set(), set(), 0, False

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        logging.warning("  [WARN] Web-Export-Blacklist nicht lesbar (%s): %s", path, exc)
        return set(), set(), 0, False

    # Leere Datei: yaml.safe_load gibt None -> als leeres Dict behandeln,
    # KEIN WARNING (Datei ist nicht kaputt, sie hat nur keine Eintraege).
    if data is None:
        return set(), set(), 0, True

    if not isinstance(data, dict):
        logging.warning("  [WARN] Web-Export-Blacklist hat ungueltiges Format (kein dict): %s", path)
        return set(), set(), 0, False

    raw_entries = data.get("blacklist", [])
    if not isinstance(raw_entries, list):
        logging.warning("  [WARN] Web-Export-Blacklist 'blacklist' ist keine Liste: %s", path)
        return set(), set(), 0, False

    exact: set[str] = set()
    pattern: set[str] = set()
    for entry in raw_entries:
        if not isinstance(entry, str) or not entry.strip():
            continue
        entry = entry.strip()
        if any(ch in entry for ch in ("*", "?", "[")):
            pattern.add(entry)
        else:
            exact.add(entry)
    return exact, pattern, len(exact) + len(pattern), True


def _is_blacklisted(model_id: str, exact: set[str], pattern: set[str]) -> bool:
    """Prueft ob model_id (oder ein Pattern davon) in der Blacklist ist.

    Normalisierung via _safe_name(): Blacklist-Eintraege werden in der
    kanonischen Underscore-Form geschrieben (z.B. deepseek_deepseek-chat-v3_1),
    waehrend die raw_model_id aus dem Leaderboard Provider-Prefix und Punkte
    enthaelt (z.B. deepseek/deepseek-chat-v3.1). Ohne Normalisierung
    matchen 12/34 Eintraege nicht und Modelle werden versehentlich exportiert.
    Wir normalisieren BEIDE Seiten.
    """
    if model_id in exact:
        return True
    normalized_model = _safe_name(model_id)
    if normalized_model in exact:
        return True
    return any(fnmatch(model_id, p) or fnmatch(normalized_model, p) for p in pattern)

