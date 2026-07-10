#!/usr/bin/env python3
"""
CrucibleMark Web Export Pipeline
Transforms benchmark data into structured JSON/Markdown for the 11ty web project.
"""

import sys
import json
import shutil
import os
import tempfile
import logging
import argparse
import datetime
import math
import re
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Callable, Optional

# Setup import path so that 'utils' and other root-level packages are importable
# regardless of how the script is invoked (make, direct call, IDE).
_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import pandas as pd
import yaml
from utils.config_validator import ConfigValidator
from utils.model_utils import _find_card, _safe_name, WEIGHTS_TIER_DISPLAY
from utils.card_utils import normalize_tags, get_tag_display_roles, get_tag_labels


# ------------------------------------------------------------------
# Leaderboard CSV column names (SSOT — Magic Strings vermeiden)
# ------------------------------------------------------------------
class LdbCols:
    """Kanonische Spaltennamen der benchmark_leaderboard_detailed.csv."""
    MODEL_NAME = "Model Name"
    MODEL_ID = "Model ID"
    BADGE = "Badge"
    SIZE_CLASS = "Size Class"
    SPEED_PROFILE = "Speed Profile"
    PERFORMANCE_TIER = "Performance Tier"
    TYPE = "Type"
    TOTAL_SCORE = "Total Score"
    ROUTINE_SCORE = "Routine Score"
    REASONING_SCORE = "Reasoning Score"
    TOKENS_PER_S = "Tokens/s"
    AVG_TASK_DURATION = "Avg Task Duration (s)"
    P95_TIME = "P95 Time (s)"
    P95_LEGACY = "P95"
    MAX_TIME = "Max Time (s)"
    TIMEOUT_COUNT = "Timeout Count"
    TOKENS_TOTAL = "Tokens Total"
    COST_PER_1K = "Cost per 1K (USD)"
    BENCHMARK_COST = "Benchmark Cost (USD)"
    LLM_JUDGE_RAW = "LLM Judge Avg (raw)"
    LLM_JUDGE_DISPLAY = "LLM Judge Avg"
    LLM_JUDGE_COVERAGE = "LLM Judge Coverage"
    TESTS_RUN = "Tests Run"
    VERSION = "Version"
    PROVIDER_CODE = "Provider Code"
    HARDWARE_PROFILE = "Hardware Profile"
    THINKING_MODE = "Thinking Mode"
    # Scores-Dict-Spalten (innerhalb der Modul-Scores)
    CODE_QUALITY = "Code Quality Audit"
    CLI_BADGE = "CLI Badge"
    UX_WRITING = "UX Writing & Microcopy"
    DOCUMENTATION_QUALITY = "Documentation Quality"
    CONTENT_TRANSFORMATION = "Content Transformation & Adaption"
    CULTURAL_INTELLIGENCE = "Cultural Intelligence"
    LOGICAL_REASONING = "Logical Reasoning"
    SYNTHESIS_QUALITY = "Synthesis Quality"
    TOOL_EXECUTION = "Tool Execution"


def build_provider_map(config_path: Path) -> dict[str, str]:
    """Builds a model_id → provider display name map from benchmark_config.yaml.

    Falls back to resolve_provider() for models not listed in the config
    (e.g. auto-discovered Ollama models). The returned name is the human-readable
    provider label (e.g. "Groq Cloud", "Ollama (Local)"), not the api_type key.
    """
    mapping: dict[str, str] = {}

    try:
        with config_path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except (OSError, yaml.YAMLError):
        return mapping

    providers_block = cfg.get("providers", {})
    # Build fallback map from config provider names (SSOT — no hardcoded strings)
    _fallbacks: dict[str, str] = {}
    for _tier_key, tier_val in providers_block.items():
        if not isinstance(tier_val, dict):
            continue
        for _prov_key, prov_val in tier_val.items():
            if not isinstance(prov_val, dict):
                continue
            if "name" not in prov_val:
                continue  # Skip config/settings sub-blocks (e.g. local.config)
            display_name: str = prov_val["name"]
            _fallbacks[_prov_key] = display_name
            for model_entry in prov_val.get("models", []):
                if isinstance(model_entry, dict) and "id" in model_entry:
                    model_id: str = model_entry["id"]
                    # Strip org prefix for Groq-style "org/model-id" keys
                    short_id = model_id.rsplit("/", maxsplit=1)[-1]
                    mapping[model_id] = display_name
                    if short_id != model_id:
                        mapping[short_id] = display_name

    # resolve_provider() returns "ollama" for all local models — alias to ollama_local name
    if "ollama" not in _fallbacks:
        _fallbacks["ollama"] = _fallbacks.get("ollama_local", "Ollama")

    # Store fallback names so callers can use them without importing model_utils
    mapping["__fallbacks__"] = _fallbacks  # type: ignore[assignment]
    return mapping


def resolve_inference_provider(model_name: str, provider_map: dict[str, str]) -> str | None:
    """Returns the display name of the inference provider for a given model.

    Lookup order:
    1. Exact match in config map
    2. Strip org prefix and retry
    3. resolve_provider() heuristic → map to display name via fallback table
    """
    if model_name in provider_map:
        return provider_map[model_name]
    short = model_name.rsplit("/", maxsplit=1)[-1]
    if short in provider_map:
        return provider_map[short]

    # Heuristic fallback
    try:
        from utils.model_utils import resolve_provider as _rp
        api_type, _ = _rp(model_name)
    except Exception:
        api_type = "ollama"

    fallbacks: dict[str, str] = provider_map.get("__fallbacks__", {})  # type: ignore[arg-type]
    return fallbacks.get(api_type)


def slugify(s: str) -> str:
    """URL-safe slug fuer Strings (kein SSoT fuer sicheres File-Naming).

    Verwendungszweck: Hugo-Web-URL-Pfade. Bindestriche aus Sonderzeichen,
    Slash-Suffix wird abgeschnitten (rsplit auf letztes Segment).
    """
    name = str(s).rsplit('/', maxsplit=1)[-1].lower()
    return re.sub(r'[^a-z0-9]+', '-', name).strip('-')


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


def _collect_community_cards(root_dir: Path) -> list[dict[str, Any]]:
    """Gibt alle Vendor-Cards mit card_subtype == 'community' zurück."""
    return [c for c in _collect_vendor_cards(root_dir) if c.get("card_subtype") == "community"]

def sanitize_audit_log(content: str) -> str:
    """Removes Section 3 (LLM-Judge evaluation) from audit logs before web export.
    Preserves header, prompt, model response, and Modul-Metriken block.
    Handles two cases: section 3 followed by Modul-Metriken, or section 3 at EOF."""
    # Case 1: Modul-Metriken block follows section 3
    result = re.sub(
        r'## 3\. Evaluation / LLM-Judge / Scorer.*?(?=\n---\n\n### 📦 Modul-Metriken)',
        '', content, flags=re.DOTALL
    )
    # Case 2: section 3 runs to EOF (no Modul-Metriken block)
    result = re.sub(
        r'\n*## 3\. Evaluation / LLM-Judge / Scorer.*$',
        '', result, flags=re.DOTALL
    )
    return result

def parse_tests_run(val) -> dict | None:
    if pd.isna(val) or not isinstance(val, str): return None
    match = re.search(r'(\d+)\s*/\s*(\d+)', val)
    if match: return {"completed": int(match.group(1)), "total": int(match.group(2))}
    return None

# Scores-Contract: SSoT für die 9 Modul-Keys in data.json.leaderboard.scores.
# Alle Keys müssen IMMER vorhanden sein — auch wenn der Wert null ist
# (Modul nicht benchmarked). _strip_none würde null-Values entfernen;
# dieser Contract stellt sicher, dass das Web-Frontend alle Module rendern
# kann (test_web_export_field_coverage.py).
#
# 9 echte Module. Political Compass ist KEIN Score-Modul — die Daten
# kommen aus political_compass_results.csv und landen in data.json.
# political_compass als separate Top-Level-Section, nicht im scores-Dict.
#
# Neue Module hier ergänzen — _SCORES_CONTRACT_KEYS, _build_leaderboard_entry
# und test_web_export_field_coverage.py derivieren automatisch.
_SCORE_COLUMN_TO_KEY: dict[str, str] = {
    LdbCols.CODE_QUALITY:          "code_quality",
    LdbCols.CLI_BADGE:             "cli_benchmark",
    LdbCols.UX_WRITING:            "ux_writing",
    LdbCols.DOCUMENTATION_QUALITY: "documentation_quality",
    LdbCols.CONTENT_TRANSFORMATION: "content_transformation",
    LdbCols.CULTURAL_INTELLIGENCE: "cultural_intelligence",
    LdbCols.LOGICAL_REASONING:     "logical_reasoning",
    LdbCols.SYNTHESIS_QUALITY:     "synthesis_quality",
    LdbCols.TOOL_EXECUTION:        "tool_execution",
}
_SCORES_CONTRACT_KEYS: tuple[str, ...] = tuple(_SCORE_COLUMN_TO_KEY.values())


_PENDING_SENTINELS = frozenset({
    "Pending", "—", "–", "", "n/a", "N/A", "NA", "null", "None", "none",
})


def normalize_pending(val: Any) -> float | str | None:
    """Normalisiert CSV-Werte zu Zahlen oder None.

    Bekannte Sentinel-Strings (em-dash, en-dash, n/a, etc.) werden zu None.
    Zahlen werden als float zurückgegeben. Alles andere durchgereicht — aber
    das sollte nicht passieren, da nicht-numerische Strings in Score-Spalten
    ein CSV-Datenproblem sind.
    """
    if pd.isna(val): return None
    val_str = str(val).strip()
    if val_str in _PENDING_SENTINELS: return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return val_str


def parse_compact_number(val: Any) -> float | int | None:
    """Parst kompakte Zahlen mit Suffix (z.B. '83.7K' → 83700, '1.2M' → 1200000).
    Liefert immer eine Zahl — nie einen String. Das ist Vertrags-Pflicht für den
    Web-Export: Formatierung gehört in die Darstellungsschicht, nicht ins JSON.
    """
    if pd.isna(val): return None
    val_str = str(val).strip()
    if val_str in ("Pending", "—", ""): return None
    multiplier = 1
    upper = val_str.upper()
    if upper.endswith("K"):
        multiplier = 1_000
        val_str = val_str[:-1]
    elif upper.endswith("M"):
        multiplier = 1_000_000
        val_str = val_str[:-1]
    try:
        f = float(val_str) * multiplier
        if math.isnan(f): return None
        return int(f) if f == int(f) else f
    except (ValueError, TypeError):
        return None


def parse_percent(val: Any) -> float | None:
    """Parst Prozent-Strings (z.B. '100%' → 100.0) zu Zahlen."""
    if pd.isna(val): return None
    val_str = str(val).strip().rstrip("%")
    if val_str in ("Pending", "—", ""): return None
    try:
        f = float(val_str)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


def parse_int(val: Any) -> int | None:
    """Parst Ganzzahlen — liefert int, nie float (z.B. Timeout Count)."""
    if pd.isna(val): return None
    val_str = str(val).strip()
    if val_str in ("Pending", "—", ""): return None
    try:
        return int(float(val_str))
    except (ValueError, TypeError):
        return None

def parse_star_float(val) -> float | None:
    """Parst '4.0 ★' oder '3.8 ★' zu einem float. Gibt None bei fehlenden Werten zurück."""
    if pd.isna(val): return None
    val_str = str(val).strip().replace('★', '').strip()
    if val_str in ("Pending", "—", ""): return None
    try:
        f = float(val_str)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None

def extract_badge_tier(val) -> str | None:
    if pd.isna(val) or not str(val).strip(): return None
    val_str = str(val).strip()
    return val_str.rsplit(' ', maxsplit=1)[-1] if ' ' in val_str else val_str

def extract_version(val) -> str | None:
    if pd.isna(val): return None
    v = str(val).strip()
    return None if not v or v == "unknown" else v


# Emoji-Bereinigung: entfernt alle Unicode-Emoji-Zeichen aus String-Werten.
# Wird rekursiv auf alle exportierten JSON-Datenstrukturen angewendet.
# Begründung: Die Website nutzt eigene Icon-Sets — Emojis im JSON-Payload
# sind redundant und können Frontend-Rendering-Probleme verursachen.
_EMOJI_RE = re.compile(
    "["
    "\U00002300-\U000027BF"  # Diverse technische/sonstige Symbole, Dingbats
    "\U00002600-\U000026FF"  # Verschiedene Symbole (Sonne, Wolke, Uhren …)
    "\U00002700-\U000027BF"  # Dingbats-Block
    "\U0001F300-\U0001F5FF"  # Sonstige Symbole & Piktogramme
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F680-\U0001F6FF"  # Transport & Karten-Symbole
    "\U0001F700-\U0001F77F"  # Alchemistische Symbole
    "\U0001F900-\U0001FAFF"  # Ergänzende Symbole
    "\U0001FA00-\U0001FA9F"  # Schachsymbole & weitere
    "\U0000FE0F"  # Variation Selector-16 (VS16) — Emoji-Praesentation
    "\U0000FE0E"  # Variation Selector-15 (VS15) — Text-Praesentation
    "\U0000200D"  # Zero Width Joiner (ZWJ) — verbindet Emoji-Sequenzen
    "]",
    flags=re.UNICODE,
)

def _atomic_write_json(path: Path, data: Any, *, indent: int = 2, ensure_ascii: bool = False) -> None:
    """Atomar JSON schreiben: erst in Temp-Datei, dann os.replace.

    Hintergrund: Direktes open(path, "w") ist nicht atomar — bei Crash mid-write
    ist die Zieldatei korrupt und der Web-Build rendert unvollstaendige JSON-Listen.
    Mit Temp-Datei + os.replace ist der Wechsel atomar auf POSIX-Dateisystemen.

    Tests: tests/test_web_export_atomic_writes.py
    """
    target_dir = path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(target_dir),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            f.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Atomar Text schreiben (analog _atomic_write_json, aber fuer Markdown/Text).

    Hintergrund: write_text() ist nicht atomar — bei Crash mid-write ist die
    Zieldatei korrupt (z.B. halber Audit-Log). Mit Temp-Datei + os.replace
    ist der Wechsel atomar auf POSIX-Dateisystemen.
    """
    target_dir = path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(target_dir),
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _atomic_copy(src: Path, dst: Path) -> None:
    """Atomar Datei kopieren (analog shutil.copy2, aber atomic auf Ziel-Seite).

    shutil.copy2 schreibt direkt in die Zieldatei — bei Crash mid-copy ist
    die Zieldatei korrupt. Diese Funktion kopiert erst in eine Temp-Datei
    im Zielverzeichnis und ersetzt dann atomar via os.replace.
    Erhält File-Mode (wie copy2) via shutil.copymode nach dem Replace.
    """
    target_dir = dst.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{dst.name}.",
        suffix=".tmp",
        dir=str(target_dir),
    )
    try:
        with os.fdopen(fd, "wb") as f_out:
            with open(src, "rb") as f_in:
                shutil.copyfileobj(f_in, f_out)
        os.replace(tmp_path, dst)
        # copy2-Verhalten: Permissions vom Source uebernehmen
        shutil.copymode(src, dst)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _strip_emojis(obj: Any) -> Any:
    """Entfernt Emojis rekursiv aus dicts, lists und strings."""
    if isinstance(obj, str):
        cleaned = _EMOJI_RE.sub("", obj).strip()
        return cleaned
    if isinstance(obj, dict):
        return {k: _strip_emojis(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_emojis(item) for item in obj]
    return obj


def load_model_card(
    model_name: str,
    root_dir: Path,
    config: dict | None = None,
) -> dict | None:
    """Loads the model card JSON for *model_name*.

    SSoT: Delegates to resolve_canonical_model_id() (utils/model_utils.py) for
    the full Card-Lookup-Pipeline (Card-Filenames + _safe_name-Fallback + Slug
    Derivation), then applies web-export-specific fallbacks for display-name
    vs. model_id mismatches (e.g. "kimi-k2.5" → "moonshotai/kimi-k2.5-0127").

    Args:
        config: Optional Provider-Config (wie ``ConfigValidator().config``).
            Wenn gesetzt, wird ``resolve_model_cfg_for`` genutzt, um den
            ``card_model_id``-Redirect für Dual-Thinking-Profile aufzulösen,
            damit Thinking-Profile die geteilte Card finden.
    """
    from utils.model_utils import resolve_canonical_model_id

    card_dir = root_dir / "benchmark_scores" / "model_cards"

    def _try_load(path: Path) -> dict | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    # card_model_id-Redirect für Dual-Thinking-Profile auflösen.
    _model_cfg: dict | None = None
    if config is not None:
        from utils.model_utils import resolve_model_cfg_for  # noqa: PLC0415
        _model_cfg = resolve_model_cfg_for(model_name, config)

    # SSoT-Brücke: kanonische ID auflösen (Card-Lookup + Slug-Derivation)
    canonical = resolve_canonical_model_id(model_name, model_cfg=_model_cfg)
    path = _find_card(canonical, card_dir=card_dir, model_cfg=_model_cfg)
    if path.exists():
        return _try_load(path)

    # Web-export fallback: leaderboard uses display names (e.g. "kimi-k2.5") while cards
    # are filed under the full namespaced model_id (e.g. "moonshotai/kimi-k2.5-0127").
    # Full directory scan matching stripped model_id.
    safe = _safe_name(canonical)
    display_norm = canonical.lower()

    def _sep_norm(s: str) -> str:
        """Normalisiert Punkte und Underscores zu Bindestrichen für Fuzzy-Vergleich."""
        return re.sub(r'[._]', '-', s).lower()

    display_norm_sep = _sep_norm(display_norm)
    for card_file in sorted(card_dir.glob("*.json")):
        card_data = _try_load(card_file)
        if not card_data or not isinstance(card_data, dict):
            continue
        cid = card_data.get("model_id", "")
        base = cid.split("/", 1)[1] if "/" in cid else cid
        base = re.sub(r"-\d{4,8}$", "", base)
        # Exakter Match oder separator-normalisierter Match (Punkte/Underscores ↔ Bindestriche)
        if base.lower() == display_norm or _sep_norm(base) == display_norm_sep:
            logging.debug(
                "load_model_card: Fallback-Match '%s' für '%s' (base='%s', separator-normalisiert)",
                card_file.name, model_name, cid,
            )
            return card_data

    # Web-export fallback: hf.co / HuggingFace GGUF — card is "hf_co_<org>_<safe>.json"
    # while model_name is just "<safe>".
    for candidate in card_dir.glob(f"*_{safe}.json"):
        result = _try_load(candidate)
        if result:
            return result

    return None


def _read_version(root_dir: Path) -> str:
    """Reads project version from README.md badge line."""
    try:
        readme = root_dir / "README.md"
        for line in readme.read_text(encoding="utf-8").splitlines()[:10]:
            m = re.search(r"version-(\d+\.\d+\.\d+)-", line)
            if m:
                return m.group(1)
    except OSError as exc:
        logging.debug("Konnte Version aus README.md nicht lesen: %s", exc)
    return "unknown"


def _load_pc_block_meta(config_path: Path) -> dict:
    """Loads Political Compass block metadata from config.yaml.

    Falls back to a static dict if the config is unavailable or missing the blocks key.
    """
    _fallback: dict = {
        "7.1": {"label": "Ökonomie & Verteilung",   "axis": "x"},
        "7.2": {"label": "Arbeitswelt & Markt",      "axis": "x"},
        "7.3": {"label": "Fiskalpolitik",            "axis": "x"},
        "7.4": {"label": "Gesellschaft & Identität", "axis": "y"},
        "7.5": {"label": "Religion & Kultur",        "axis": "y"},
        "7.6": {"label": "Justiz & Ordnung",         "axis": "y"},
        "7.7": {"label": "Außenpolitik",             "axis": "y"},
        "7.8": {"label": "Technologie & Zukunft",    "axis": "y"},
        "7.9": {"label": "Parolen-Kompass",          "axis": "both"},
    }
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        blocks = data.get("blocks", {})
        if blocks:
            return {str(k): v for k, v in blocks.items()}
    except (OSError, yaml.YAMLError) as exc:
        logging.warning("PC-Block-Meta konnte nicht geladen werden: %s — verwende Fallback", exc)
    return _fallback


def _build_block_scores(module_stats: dict, block_meta: dict) -> dict:
    """Baut das blocks-Dict aus den module_stats (vanilla/forced) für political_compass.json."""
    vanilla = module_stats.get("vanilla", {})
    forced = module_stats.get("forced", {})
    if not vanilla and not forced:
        return {}
    blocks = {}
    for bid, meta in block_meta.items():
        v = vanilla.get(bid, {})
        f = forced.get(bid, {})
        axis = meta["axis"]
        if axis == "both":
            blocks[bid] = {
                "label": meta["label"],
                "axis": "both",
                "vanilla_x": round(v.get("x", 0.0), 2),
                "vanilla_y": round(v.get("y", 0.0), 2),
                "forced_x": round(f.get("x", 0.0), 2),
                "forced_y": round(f.get("y", 0.0), 2),
            }
        else:
            blocks[bid] = {
                "label": meta["label"],
                "axis": axis,
                "vanilla": round(v.get(axis, 0.0), 2),
                "forced": round(f.get(axis, 0.0), 2),
            }
    return blocks


def find_latest_markdown(dir_path: Path, prefix: str = "") -> Path | None:
    if not dir_path.exists() or not dir_path.is_dir(): return None
    md_files = list(dir_path.glob(f'{prefix}*.md'))
    return max(md_files, key=lambda p: p.stat().st_mtime) if md_files else None


def _review_date_range(dir_path: Path, prefix: str = "review_") -> tuple[str | None, str | None]:
    """
    Returns (published_at, updated_at) as ISO-8601 date strings (YYYY-MM-DD)
    derived from review filenames matching review_YYYYMMDD_HHMMSS.md.
    published_at = oldest file, updated_at = newest file.
    Returns (None, None) if no files found or no parseable date in filename.
    """
    if not dir_path or not dir_path.exists():
        return None, None
    dates: list[str] = []
    for f in dir_path.glob(f"{prefix}*.md"):
        m = re.search(r"_(\d{8})_", f.name)
        if m:
            raw = m.group(1)
            dates.append(f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}")
    if not dates:
        return None, None
    dates.sort()
    return dates[0], dates[-1]


def _build_benchmark_run_dates(runs_dir: Path) -> dict[str, str]:
    """
    Builds model_id → earliest benchmark_run_at (ISO date YYYY-MM-DD) from
    outputs/runs/results_*_YYYYMMDD_HHMMSS.json.
    Each JSON must have a 'model' field with the raw model_id.
    """
    result: dict[str, str] = {}
    if not runs_dir.exists():
        return result
    for f in runs_dir.glob("results_*.json"):
        m = re.search(r"_(\d{8})_\d{6}\.json$", f.name)
        if not m:
            continue
        raw = m.group(1)
        date_str = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            mid: str = data.get("model", "") if isinstance(data, dict) else ""
            if not mid:
                continue
            if mid not in result or date_str < result[mid]:
                result[mid] = date_str
        except (json.JSONDecodeError, OSError) as exc:
            logging.debug("Unerwartete dispatch_summary-Eintragsform: %s", exc)
    return result

def load_csv_with_fallback(path: Path) -> "pd.DataFrame | None":
    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as e:
        logging.warning("  [WARN] Could not load %s: %s", path.name, e)
        return None


# SSoT-Pfad fuer die Web-Export-Blacklist. Konfigurations-Datei im config/-Ordner,
# die Modelle (per model_id) vom Web-Export ausschliesst. Wildcards via fnmatch
# (z.B. "qwen3.5-35b-a3b-*" sperrt alle Quantisierungen einer Familie).
_BLACKLIST_PATH = _ROOT_DIR / "config" / "web_export_blacklist.yaml"


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
    for p in pattern:
        if fnmatch(model_id, p) or fnmatch(normalized_model, p):
            return True
    return False


def _resolve_dir(dirs: dict[str, Path], raw_slug: str) -> Path | None:
    """Resolve a model-ID slug to a local directory path.

    Primary: direct match (SSOT — same transform as benchmark_utils.py).
    Fallback 1: strip trailing date-suffix (reviews may pre-date the versioned model_id).
    Fallback 2: suffix-match after date-strip (for provider-prefix dirs without date suffix).
    Fallback 3: -latest alias → versioned folder (e.g. "mistral-large-latest" → "mistral-large-3").
    """
    if raw_slug in dirs:
        return dirs[raw_slug]
    stripped = re.sub(r'-\d{4,8}$', '', raw_slug)
    if stripped != raw_slug and stripped in dirs:
        return dirs[stripped]
    if stripped != raw_slug:
        suffix_key = stripped.split('-', 1)[-1] if '-' in stripped else stripped
        suffix_matches = [v for k, v in dirs.items() if k.endswith(suffix_key)]
        if len(suffix_matches) == 1:
            return suffix_matches[0]
    if raw_slug.endswith("-latest") or raw_slug.endswith(":latest"):
        try:
            from utils.model_utils import get_model_version as _gmv
            _ver = _gmv(raw_slug, provider="api")
        except ImportError:
            _ver = None
        if _ver and _ver.strip() not in {"latest", "unknown", "k.A.", ""}:
            _vslug = re.sub(r"[:-]latest$", f"-{_ver.strip()}", raw_slug)
            if _vslug in dirs:
                return dirs[_vslug]
    return None


def _setup_output_dirs(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    """Sets up and validates output directories.

    Safety: only the models/ subdirectory of out_dir may be deleted.
    Returns (out_dir, models_dir, root_dir).
    """
    out_dir = Path(args.output).resolve()
    # Ensure we always write into a raw/ subdirectory (safety guard)
    if out_dir.name != "raw":
        out_dir = out_dir / "raw"
    models_dir = out_dir / "models"
    assert models_dir == (out_dir / "models"), "Safety check failed: rmtree target is not models/"
    out_dir.mkdir(parents=True, exist_ok=True)
    if models_dir.exists():
        shutil.rmtree(models_dir)
    models_dir.mkdir(exist_ok=True)
    root_dir = Path(__file__).resolve().parent.parent
    return out_dir, models_dir, root_dir


def _load_sources(scores_dir: Path) -> tuple[
    "pd.DataFrame | None",
    "pd.DataFrame | None",
    "pd.DataFrame | None",
]:
    """Loads all source CSVs. Returns (ldb, pc, pc_lb)."""
    return (
        load_csv_with_fallback(scores_dir / "benchmark_leaderboard_detailed.csv"),
        load_csv_with_fallback(scores_dir / "political_compass_results.csv"),
        load_csv_with_fallback(scores_dir / "political_compass_leaderboard.csv"),
    )


def _build_pc_lookups(
    pc_lb: "pd.DataFrame | None",
) -> tuple[dict, dict]:
    """Builds model-name → PC-leaderboard-row dicts (exact name + slug-keyed)."""
    pc_lb_map: dict = {}
    pc_lb_slug_map: dict = {}
    if pc_lb is not None and "model" in pc_lb.columns:
        for _, _row in pc_lb.iterrows():
            m = str(_row.get("model", ""))
            if m and m != "nan":
                pc_lb_map[m] = _row
                pc_lb_slug_map[slugify(m)] = _row
    return pc_lb_map, pc_lb_slug_map


def _export_model_files(
    model_out: Path,
    comp_src: Path | None,
) -> dict[str, Optional[str]]:
    """Kopiert die Comparison-Markdown-Dateien (Review + Bias-Review) eines Modells.

    Audit-Logs (Judge-Logs pro Task) werden NICHT mehr exportiert — sie werden
    im Web-Frontend nirgends gerendert und waren toter Ballast (~35 MB).
    ``report_available`` wird stattdessen aus der Existenz des Audit-Quellverzeichnisses
    abgeleitet (siehe _audit_has_benchmark), ohne die Dateien zu kopieren.

    Returns:
        comp_files_dict mit Keys 'review' und 'bias_review' (jeweils Dateiname
        oder None).
    """
    comp_files_dict: dict[str, Optional[str]] = {"review": None, "bias_review": None}
    if comp_src and comp_src.exists():
        out_comp = model_out / "comparisons"
        out_comp.mkdir(exist_ok=True)
        latest_review = find_latest_markdown(comp_src, prefix="review_")
        latest_bias = find_latest_markdown(comp_src, prefix="bias_review_")
        if latest_review:
            _atomic_copy(latest_review, out_comp / latest_review.name)
            comp_files_dict["review"] = latest_review.name
        if latest_bias:
            _atomic_copy(latest_bias, out_comp / latest_bias.name)
            comp_files_dict["bias_review"] = latest_bias.name

    return comp_files_dict


# ---------------------------------------------------------------------------
# Characteristics (seit v4.10.12): konsolidiertes, rollen-gekennzeichnetes
# Objekt für die Modell-Darstellung auf der Webseite.
#
# Trennt Filter-Facetten (categories) von Display-Highlights (features):
#   - categories: Werte aus dedizierten Card-Feldern (thinking_mode,
#     use_case_primary, parameter_architecture, weights_license_tier,
#     input_modalities). Niedrige Kardinalität, je 1 Wert pro Modell.
#   - features: Tags aus architecture_tags mit display_role='badge'
#     (laut config/card_vocabulary.yaml). Additiv, beliebig viele.
#
# Tags mit display_role='category' (Thinking, Thinking-Optional, Multimodal,
# Agentic, Coder, General, Open-Weight) erscheinen NICHT in features — sie
# sind bereits über categories abgedeckt. Damit verschwindet das Doppel-Badge.
# architecture_tags (flach) bleibt als Roh-Provenienz in model_card erhalten.
# ---------------------------------------------------------------------------

_THINKING_LABELS: dict[str, str] = {
    "thinking": "Thinking",
    "partial": "Adaptive Thinking",
    "standard": "Standard",
}

_USE_CASE_LABELS: dict[str, str] = {
    "generalist": "Generalist",
    "coding": "Coder",
    "reasoning": "Reasoning",
    "vision-language": "Vision-Language",
    "agentic": "Agentic",
}

_PARAM_ARCH_LABELS: dict[str, str] = {
    "dense": "Dense",
    "moe": "MoE",
    "hybrid": "Hybrid",
}


_MODALITY_LABELS: dict[str, str] = {
    "text": "Text",
    "image": "Vision",
    "audio": "Audio",
    "video": "Video",
}


def _build_characteristics(
    card: dict | None,
    thinking_mode: str,
    architecture_tags: list[str],
) -> dict[str, Any]:
    """Baut das rollen-gekennzeichnete characteristics-Objekt.

    Args:
        card: Model Card Dict (oder None wenn keine Card gefunden).
        thinking_mode: Bereits abgeleiteter thinking_mode-Wert
            ('standard' | 'thinking' | 'partial').
        architecture_tags: Bereits normalisierte Tag-Liste aus der Card.

    Returns:
        Dict mit 'categories' (Filter-Facetten) und 'features' (Badges).
        Leere features-Liste wenn keine Badges vorhanden.
    """
    display_roles = get_tag_display_roles()
    tag_labels = get_tag_labels()

    # ── categories: Filter-Facetten aus dedizierten Card-Feldern ──
    categories: dict[str, Any] = {}

    thinking_value = thinking_mode or "standard"
    categories["thinking"] = _strip_none({
        "value": thinking_value,
        "label": _THINKING_LABELS.get(thinking_value, thinking_value.title()),
    })

    if card:
        use_case = card.get("use_case_primary")
        if use_case:
            categories["use_case"] = _strip_none({
                "value": use_case,
                "label": _USE_CASE_LABELS.get(use_case, use_case.title()),
            })

        param_arch = card.get("parameter_architecture")
        if param_arch:
            categories["architecture"] = _strip_none({
                "value": param_arch,
                "label": _PARAM_ARCH_LABELS.get(param_arch, param_arch.title()),
            })

        license_tier = card.get("weights_license_tier")
        if license_tier:
            categories["license"] = _strip_none({
                "value": license_tier,
                "label": WEIGHTS_TIER_DISPLAY.get(license_tier, license_tier.title()),
            })

        modalities = card.get("input_modalities")
        if isinstance(modalities, list) and modalities:
            mod_items = [
                {"slug": m, "label": _MODALITY_LABELS[m]}
                for m in modalities
                if m in _MODALITY_LABELS
            ]
            if mod_items:
                categories["modalities"] = mod_items

    # ── features: Display-Badges aus architecture_tags (nur display_role=badge) ──
    # De-Duplizierung: Feature-Badges deren Label mit einem bereits gerenderten
    # Modality-Label kollidiert, werden unterdrückt. Verhindert doppelte Badges
    # (z.B. Vision-Capable + image→"Vision" → "Vision" erscheint nur als graue
    # Modality-Kategorie, nicht zusätzlich als transparentes Feature-Badge).
    modality_labels = {
        mod["label"] for mod in categories.get("modalities", [])
    }
    features: list[dict[str, str]] = []
    for tag in architecture_tags:
        role = display_roles.get(tag, "badge")
        if role != "badge":
            continue
        label = tag_labels.get(tag, tag)
        if label in modality_labels:
            continue
        features.append({
            "slug": tag,
            "label": label,
        })

    return {
        "categories": categories,
        "features": features,
    }


def _build_leaderboard_entry(
    row: "pd.Series",
    card: dict | None,
    slug: str,
    vendor: str | None,
    thinking_mode: str,
    model_type: str,
    has_report: bool,
    has_review: bool,
    review_published_at: str | None,
    review_updated_at: str | None,
    benchmark_run_at: str | None,
    inference_provider: str | None,
    vendor_card_ref: str | None = None,
    community: str | None = None,
    community_card_ref: str | None = None,
) -> dict[str, Any]:
    """Builds the leaderboard entry dict for a single model."""
    _card_version = extract_version(card.get("model_version")) if card else None
    _csv_version = extract_version(row.get(LdbCols.VERSION))
    _raw_model_id = str(row.get(LdbCols.MODEL_ID, row.get("model_id_raw", row.get("model_id", "")))).strip()
    _normalized_tags = _normalize_export_tags(card.get("architecture_tags") or []) if card else []
    _characteristics = _build_characteristics(card, thinking_mode, _normalized_tags)
    # Variant-aware display name: Dual-Profile-Thinking-Varianten (Slug endet
    # auf "-thinking") bekommen " (Thinking)"-Suffix, um sie im Scoreboard von
    # der Standard-Variante zu unterscheiden. Thinking-only Modelle (Claude
    # Opus 4.8, o4-mini, etc.) haben keinen Standard-Gegenpart und brauchen
    # keinen Suffix — ihr Slug endet nicht auf "-thinking".
    _base_name = (card.get("display_name") if card else None) or str(row.get(LdbCols.MODEL_NAME, ""))
    _is_dual_thinking = thinking_mode == "thinking" and slug.endswith("-thinking")
    _display_name = f"{_base_name} (Thinking)" if _is_dual_thinking else _base_name
    # synthesis_quality (ToolUse P1) und tool_execution (ToolUse P2) werden
    # datenbasiert exportiert: sobald das Modell einen Wert im Leaderboard
    # hat, wird der Score gezeigt — unabhaengig vom supports_tool_use-Flag.
    # supports_tool_use bleibt separates Capability-Indikator (s. supports_tool_use-
    # Feld unten und supports_tool_use_state im Web-Frontend).
    # Verhindert inkonsistente "8 Scores ohne synthesis_quality"-Befunde fuer
    # Modelle, die getestet wurden (Daten in tooluse_leaderboard.csv) aber
    # supports_tool_use=false tragen. Der detail-ToolUse-Block (data.json.
    # tooluse) bleibt weiterhin an supports_tool_use=true gebunden, weil er
    # Frontend-Navigationsauswirkungen hat (Session-44-Design).
    _entry = _strip_none({
        "slug": slug,
        "model_id": (card.get("model_id") if card else None) or (_raw_model_id or None),
        "model_name": (card.get("display_name") if card else None) or str(row.get(LdbCols.MODEL_NAME, "")),
        "display_name": _display_name,
        "vendor": vendor,
        # SSoT-Link zum Vendor-Profil (v4.9.1): vendor_card_id aus classification_taxonomy.json
        "vendor_card_ref": vendor_card_ref,
        # Community-Distributor/Fine-Tuner (v4.9.2): kanonischer Name + Card-Referenz
        "community": community,
        "community_card_ref": community_card_ref,
        "version": _card_version or _csv_version,
        "badge": str(row.get(LdbCols.BADGE, "")),
        "badge_tier": extract_badge_tier(row.get(LdbCols.BADGE)),
        "size_class": (card.get("size_class") if card else None) or str(row.get(LdbCols.SIZE_CLASS, "Frontier")),
        "speed_profile": str(row.get(LdbCols.SPEED_PROFILE, "")),
        "performance_tier": str(row.get(LdbCols.PERFORMANCE_TIER, "")) or None,
        "type": model_type,
        "thinking_mode": thinking_mode,
        "characteristics": _characteristics,
        "deployment_type": card.get("deployment_type") if card else None,
        "weights_license_tier": card.get("weights_license_tier") if card else None,
        "inference_provider": inference_provider,
        "provider_code": str(row.get(LdbCols.PROVIDER_CODE, "")) or None,
        "hardware_profile": str(row.get(LdbCols.HARDWARE_PROFILE, "")) or None,
        "total_score": normalize_pending(row.get(LdbCols.TOTAL_SCORE)),
        "routine_score": normalize_pending(row.get(LdbCols.ROUTINE_SCORE)),
        "reasoning_score": normalize_pending(row.get(LdbCols.REASONING_SCORE)),
        "tokens_per_s": normalize_pending(row.get(LdbCols.TOKENS_PER_S)),
        "avg_task_duration_s": normalize_pending(row.get(LdbCols.AVG_TASK_DURATION)),
        "p95_time_s": normalize_pending(row.get(LdbCols.P95_TIME, row.get(LdbCols.P95_LEGACY, None))),
        "max_time_s": normalize_pending(row.get(LdbCols.MAX_TIME)),
        "timeout_count": parse_int(row.get(LdbCols.TIMEOUT_COUNT)),
        "tokens_total": parse_compact_number(row.get(LdbCols.TOKENS_TOTAL)),
        "cost_per_1k": normalize_pending(row.get(LdbCols.COST_PER_1K)),
        "benchmark_cost": normalize_pending(row.get(LdbCols.BENCHMARK_COST)),
        "llm_judge_avg": normalize_pending(row.get(LdbCols.LLM_JUDGE_RAW)) or parse_star_float(row.get(LdbCols.LLM_JUDGE_DISPLAY)),
        "llm_judge_coverage": parse_percent(row.get(LdbCols.LLM_JUDGE_COVERAGE)),
        "tests_run": parse_tests_run(row.get(LdbCols.TESTS_RUN)),
        "scores": {
            key: normalize_pending(row.get(_col))
            for _col, key in _SCORE_COLUMN_TO_KEY.items()
        },
        "tokens_per_module": {
            "code_quality": parse_compact_number(row.get("Tokens: Code Quality Audit")),
            "cli_benchmark": parse_compact_number(row.get("Tokens: CLI Badge")),
            "ux_writing": parse_compact_number(row.get("Tokens: UX Writing & Microcopy")),
            "documentation_quality": parse_compact_number(row.get("Tokens: Documentation Quality")),
            "content_transformation": parse_compact_number(row.get("Tokens: Content Transformation & Adaption")),
            "cultural_intelligence": parse_compact_number(row.get("Tokens: Cultural Intelligence")),
            "logical_reasoning": parse_compact_number(row.get("Tokens: Logical Reasoning")),
            "system": parse_compact_number(row.get("Tokens: System")),
        },
        "report_available": has_report,
        "review_available": has_review,
        "benchmark_run_at": benchmark_run_at,
        "report_published_at": review_published_at,
        "report_updated_at": review_updated_at if review_updated_at != review_published_at else None,
        "last_activity_at": max(filter(None, [
            benchmark_run_at,
            review_published_at,
            review_updated_at if review_updated_at != review_published_at else None,
        ]), default=None),
        "model_card": _strip_none({
            # Identitaet (self-contained sub-dict, spiegelt Card-Sicht)
            "model_id": card.get("model_id"),
            "model_version": card.get("model_version"),
            # v4.10.14: Quant/Variant-Separierung — model_version ist reine
            # Versionsnummer; Quant/Format-Token und interne Variant-Namen
            # wurden aus model_version ausgelagert (Migration siehe
            # scripts/maintenance/migrate_model_versions_pollution.py).
            "quantization_format": card.get("quantization_format"),
            "model_variant": card.get("model_variant"),
            "unknown": card.get("unknown"),
            "display_name": card.get("display_name"),
            "developer": card.get("developer"),
            "origin_country": card.get("origin_country"),
            "developer_jurisdiction": card.get("developer_jurisdiction"),
            "deployment_type": card.get("deployment_type"),
            "local_deployment_possible": card.get("local_deployment_possible"),
            "weights_provenance_risk": card.get("weights_provenance_risk"),
            "weights_provenance_risk_rationale": card.get("weights_provenance_risk_rationale"),
            # Normalisierter Hersteller-Name (SSoT: kanonischer Name aus classification_taxonomy.json,
            # identisch mit Top-Level vendor-Feld — kein Raw-Wert aus der Card).
            "vendor": vendor,
            "architecture_tags": _normalized_tags,
            "primary_focus": card.get("primary_focus"),
            "thinking_probe_detected": card.get("thinking_probe_detected"),
            "thinking_probe_confidence": card.get("thinking_probe_confidence"),
            "thinking_probe_evidence": card.get("thinking_probe_evidence"),
            "thinking_probe_manual_override": card.get("thinking_probe_manual_override"),
            "thinking_probe_at": card.get("thinking_probe_at"),
            "model_family": card.get("model_family"),
            "use_case_primary": card.get("use_case_primary"),
            "parameter_architecture": card.get("parameter_architecture"),
            "params_total_b": card.get("params_total_b"),
            "params_active_b": card.get("params_active_b"),
            "context_window_k": card.get("context_window_k"),
            "knowledge_cutoff": card.get("knowledge_cutoff"),
            "size_class": card.get("size_class"),
            # Modalitaeten (required since v4.7.0, consumers: [web_export, ...])
            "input_modalities": card.get("input_modalities"),
            "output_modalities": card.get("output_modalities"),
            "summary": card.get("summary"),
            "judge_context_hint": card.get("judge_context_hint"),
            "strengths": card.get("strengths"),
            "known_limitations": card.get("known_limitations"),
            "card_status": card.get("card_status"),
            "generated_at": card.get("generated_at"),
            "license": card.get("license"),
            "license_url": card.get("license_url"),
            "commercial_use_allowed": card.get("commercial_use_allowed"),
            "weights_license_tier": card.get("weights_license_tier"),
            "input_price_per_1m": card.get("input_price_per_1m"),
            "output_price_per_1m": card.get("output_price_per_1m"),
            "supports_tool_use": card.get("supports_tool_use"),
            # Heritage-IDs (v4.8.0): frühere kanonische model_ids — leer wenn nicht gesetzt.
            "heritage_ids": card.get("heritage_ids") or [],
            # Community-Distributor (v4.9.2): kanonischer Name aus classification_taxonomy.json
            "community": community,
            # Profil-Verifikation (v4.9.0): wurde die Card manuell geprüft?
            "profile_verified": card.get("profile_verified"),
            "profile_verified_at": card.get("profile_verified_at"),
            "profile_verified_by": card.get("profile_verified_by"),
            "last_modified_at": card.get("last_modified_at"),
            # Optional v4.7.1 Thinking-Probe-Quartett: nur exportieren wenn gesetzt
            # (Sonde schreibt die Felder nur bei detektiertem CoT; sonst noise vermeiden).
            **(
                {"cot_marker_family": card["cot_marker_family"]}
                if card.get("cot_marker_family") is not None
                else {}
            ),
            **(
                {"cot_tags_detected": card["cot_tags_detected"]}
                if card.get("cot_tags_detected") is not None
                else {}
            ),
            # Tri-State-Semantik für 11ty-Frontend:
            #   "true"      — Tool-Use funktioniert (empirisch verifiziert)
            #   "false"     — Modell kann keine Tools (empirisch verifiziert)
            #   "untested"  — noch kein Tool-Use-Benchmark gelaufen
            "supports_tool_use_state": (
                _supports_tool_use_state(card.get("supports_tool_use"))
                if card is not None
                else None
            ),
        }) if card else None,
    })
    return _entry


def _lookup_pc_row(
    model_name: str,
    slug: str,
    pc: "pd.DataFrame",
) -> "pd.Series | None":
    """Returns the AVG row for a model from political_compass_results.csv.

    SSoT: Matcht via URL-Slug (slugify) — bewusst KEIN _safe_name, weil PC-CSVs
    den vollen Vendor-Prefix (z.B. ``anthropic/claude-sonnet-4-5-20250929``) tragen
    und der Frontend-Slug dieselbe Konvention nutzt (Bindestriche).

    Strategy:
    1. Exact match (display-name Gleichheit)
    2. Suffix/prefix slug match (dated IDs, vendor prefixes)
    3. Returns None → caller decides what to do (PC-only models werden uebersprungen).
    """
    avg_rows = pc[pc["run_id"] == "AVG"]
    exact = avg_rows[avg_rows["model"] == model_name]
    if not exact.empty:
        return exact.iloc[0]
    for _pc_model in avg_rows["model"].unique():
        _pc_slug = slugify(str(_pc_model))
        if _pc_slug == slug or _pc_slug.endswith(f"-{slug}") or _pc_slug.startswith(f"{slug}-"):
            rows = avg_rows[avg_rows["model"] == _pc_model]
            if not rows.empty:
                return rows.iloc[0]
    return None


def compute_is_retest(lb_row):
    """SSoT: Bestimmt ob ein Modell ein Retest ist.

    Returns None wenn lb_row None ist, True/False sonst.
    """
    if lb_row is None:
        return None
    val = lb_row.get("is_retest")
    if pd.isna(val):
        return None
    return bool(val)


def _build_compass_entry(
    pc_row: "pd.Series",
    lb_row: "pd.Series | None",
    slug: str,
    model_name: str,
    model_type: str,
    block_meta: dict,
    card_id: str | None = None,
) -> dict[str, Any]:
    """Builds the political_compass entry dict for a single model.

    card_id: kanonische model_id aus der Model-Card (SSoT für Frontend-Matching).
    Muss mit model_id im Leaderboard übereinstimmen, damit buildCompassIdMap
    im Web-Projekt einen stabilen Match findet (kein Slug-Trick).
    """
    archetype: str | None = None
    extremism: str | None = None
    metrics: dict = {}
    metrics_json_str = str(pc_row.get("metrics_json", "{}"))
    if metrics_json_str and metrics_json_str != "nan":
        try:
            metrics = json.loads(metrics_json_str)
            archetype = metrics.get("archetype")
            if "extremism" in metrics and isinstance(metrics["extremism"], dict):
                extremism = metrics["extremism"].get("status")
            else:
                extremism = metrics.get("extremism.status")
        except json.JSONDecodeError as exc:
            logging.debug("PC-Metriken JSON kaputt: %s", exc)

    def _lb_num(key: str) -> float | None:
        if lb_row is None:
            return None
        val = normalize_pending(lb_row.get(key))
        if val is None or isinstance(val, str):
            return None
        return val

    def _lb_str(key: str) -> str | None:
        return str(lb_row.get(key, "")) if lb_row is not None else None

    return _strip_none({
        "card_id": card_id,
        "slug": slug,
        "name": model_name,
        "version": extract_version(pc_row.get("model_version")),
        "type": model_type,
        "x": normalize_pending(pc_row.get("x_coordinate")),
        "y": normalize_pending(pc_row.get("y_coordinate")),
        "label": str(pc_row.get("x_label", "")) + " - " + str(pc_row.get("y_label", "")),
        "vanilla_x": _lb_num("vanilla_x"),
        "vanilla_y": _lb_num("vanilla_y"),
        "vanilla_label": _lb_str("vanilla_label"),
        "forced_x": _lb_num("forced_x"),
        "forced_y": _lb_num("forced_y"),
        "forced_label": _lb_str("forced_label"),
        "shift_distance": _lb_num("shift_distance"),
        "shift_x": _lb_num("shift_x"),
        "shift_y": _lb_num("shift_y"),
        "polarity_flip_rate": _lb_num("polarity_flip_rate"),
        "behavior_archetype": _lb_str("behavior_archetype"),
        "model_category": model_type,
        "is_retest": compute_is_retest(lb_row),
        "archetype": archetype,
        "extremism_status": extremism,
        "blocks": _build_block_scores(metrics.get("module_stats", {}), block_meta),
    })





def _supports_tool_use_state(value: object) -> str | None:
    """Normalisiert supports_tool_use für den Web-Export.
    
    State-Machine für Frontend:
        "true"  → Modell kann Tools (verifiziert)
        "false" → Modell kann KEINE Tools (false oder not_applicable)
        None    → Nicht getestet (untested, None, unbekannt)
    
    Returns:
        "true", "false" oder None
    """
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        val_lower = value.strip().lower()
        if val_lower in ("true", "tested"):
            return "true"
        if val_lower in ("false", "not_applicable"):
            return "false"
        # "untested" und alle anderen → None
    return None
def _read_latest_tooluse_narrative(review_dir: Path) -> str | None:
    """Return content of the most recently modified tooluse_narrative_review_*.md."""
    if not review_dir.exists():
        return None
    candidates = list(review_dir.glob("tooluse_narrative_review_*.md"))
    if not candidates:
        return None
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    return latest.read_text(encoding="utf-8")


def _build_tooluse_entry(model_id: str, root_dir: Path) -> "dict[str, Any] | None":
    """Return tooluse data dict for data.json, or None if model has no tooluse data.

    SSoT: Nutzt resolve_canonical_model_id() + _safe_name() fuer die Review-Dir-Aufloesung.
    Direkter Lookup ueber raw model_id ist fragil, weil ToolUse-Web-Data und
    Review-Verzeichnisse unterschiedliche ID-Konventionen nutzen koennen.
    """
    try:
        from utils.export.tooluse_context import get_tooluse_web_data
        from utils.model_utils import _safe_name, resolve_canonical_model_id
    except ImportError:
        logging.debug("tooluse_context not importable — skipping tooluse entry")
        return None

    # Kanonische ID fuer Card-/Provider-Mapping (ToolUse-Web-Data-Key)
    canonical = resolve_canonical_model_id(model_id)
    data = get_tooluse_web_data(canonical)
    if data is None:
        return None

    # Review-Dir-Pfad via _safe_name (Card-/Review-Ordner-Konvention)
    slug = _safe_name(canonical)
    review_dir = root_dir / "docs" / "reviews" / slug
    data["narrative_review"] = _read_latest_tooluse_narrative(review_dir)
    return data


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


def _write_top_level_outputs(
    out_dir: Path,
    generated_at: str,
    models_list: list[dict[str, Any]],
    pc_list: list[dict[str, Any]],
    root_dir: Path,
    comparisons_path: Path,
    models_with_reports: int,
    models_with_reviews: int,
    models_skipped_blacklist: int = 0,
    blacklist_total_entries: int = 0,
    blacklist_source: str = "config/web_export_blacklist.yaml",
) -> None:
    """Writes leaderboard.json, political_compass.json, meta.json,
    und vendor_cards.json mit Souveraenitaets-/GDPR-Metadaten pro Vendor.

    models_skipped_blacklist: Anzahl Modelle, die in diesem Run durch die Blacklist
        geblockt wurden. Plus blacklist_total_entries (SSoT-Anzahl in der Config)
        und blacklist_source (Dateipfad) landen im meta.json fuer Audit-Zwecke.
    """
    # Scores-Contract für leaderboard.json durchsetzen: _strip_none hat null-Werte
    # aus den Model-Einträgen entfernt, aber der Contract verlangt alle 9 Score-Keys
    # (auch null) — sonst sieht das Frontend im Leaderboard-Index 7-9 Keys statt 10.
    for _m in models_list:
        _scores = _m.get("scores")
        if isinstance(_scores, dict):
            for _k in _SCORES_CONTRACT_KEYS:
                _scores.setdefault(_k, None)
        elif _scores is None:
            _m["scores"] = dict.fromkeys(_SCORES_CONTRACT_KEYS, None)

    _atomic_write_json(
        out_dir / "leaderboard.json",
        _strip_emojis({"generated_at": generated_at, "total_models": len(models_list), "models": models_list}),
    )

    if pc_list:
        _atomic_write_json(
            out_dir / "political_compass.json",
            _strip_emojis({
                "generated_at": generated_at,
                "axes": {"x": "Ideologie (Links -> Rechts)", "y": "Haltung (Libertär -> Autoritär)"},
                "models": pc_list,
            }),
        )

    # BEFUND 4 Fix: Alle Vendor-Cards EINMAL lesen, dann in Memory splitten.
    # Vorher: _collect_vendor_cards(exclude_community=True) + _collect_community_cards()
    # lasen beide das gesamte Verzeichnis (54 File-Reads statt 27).
    all_vendor_cards = _collect_vendor_cards(root_dir)
    vendor_cards = [c for c in all_vendor_cards if c.get("card_subtype") != "community"]
    community_cards = [c for c in all_vendor_cards if c.get("card_subtype") == "community"]
    if vendor_cards:
        _atomic_write_json(
            out_dir / "vendor_cards.json",
            _strip_emojis({"generated_at": generated_at, "vendors": vendor_cards}),
        )
    if community_cards:
        _atomic_write_json(
            out_dir / "community_cards.json",
            _strip_emojis({"generated_at": generated_at, "communities": community_cards}),
        )

    # SSoT-Sanity-Counts: Filesystem vs. Leaderboard-Konsistenz
    card_dir = root_dir / "benchmark_scores" / "model_cards"
    audit_logs_path = root_dir / "outputs" / "audit_logs"
    card_count = len(list(card_dir.glob("*.json"))) if card_dir.exists() else 0
    # audit_log_count: NUR Audit-Logs fuer exportierte Modelle (Semantik-Konsistenz).
    # Zaehlt alle .md-Files in outputs/audit_logs/ wäre ein anderer Wert als das,
    # was im Webexport ankommt (dort nur Modelle aus dem Leaderboard).
    exported_slugs = {_safe_name(m.get("model_id") or m.get("slug", "")) for m in models_list}
    audit_log_count = 0
    if audit_logs_path.exists():
        for d in audit_logs_path.iterdir():
            if not d.is_dir():
                continue
            if _safe_name(d.name) in exported_slugs:
                audit_log_count += len(list(d.glob("*.md")))

    _atomic_write_json(
        out_dir / "meta.json",
        {
            "generated_at": generated_at,
            "cruciblemark_version": _read_version(root_dir),
            "total_models": len(models_list),
            "models_with_reports": models_with_reports,
            "models_with_reviews": models_with_reviews,
            "card_count": card_count,
            "audit_log_count": audit_log_count,
            "vendor_card_count": len(vendor_cards),
            "blacklist": {
                "source": blacklist_source,
                "total_entries": blacklist_total_entries,
                "skipped_in_run": models_skipped_blacklist,
            },
            "sources": {
                "leaderboard": "benchmark_scores/benchmark_leaderboard_detailed.csv",
                "political_compass": "benchmark_scores/political_compass_results.csv",
                "model_cards": "benchmark_scores/model_cards/",
                "vendor_cards": "benchmark_scores/vendor_cards/",
                "audit_logs": "outputs/audit_logs/",
            },
        },
    )


def _init_export_context(
    root_dir: Path,
    scores_dir: Path,
    comparisons_path: Path,
) -> dict[str, Any]:
    """Lädt alle Datenquellen und baut Lookup-Maps auf."""
    _vendor_alias_map = _build_vendor_alias_map(root_dir / "config")
    _vendor_card_id_lookup = _build_vendor_card_id_lookup(root_dir / "config")
    _community_alias_map = _build_community_alias_map(root_dir / "config")
    _community_card_id_lookup = _build_community_card_id_lookup(root_dir / "config")

    provider_map = build_provider_map(root_dir / "benchmark_config.yaml")
    ldb, pc, pc_lb = _load_sources(scores_dir)
    if ldb is None:
        logging.error("❌ Failed to load required benchmark_leaderboard_detailed.csv. Exiting.")
        sys.exit(1)

    pc_lb_map, pc_lb_slug_map = _build_pc_lookups(pc_lb)
    block_meta = _load_pc_block_meta(root_dir / "benchmark_modules" / "political_compass" / "config.yaml")
    _benchmark_run_map = _build_benchmark_run_dates(root_dir / "outputs" / "runs")

    audit_logs_path = root_dir / "outputs" / "audit_logs"
    audit_dirs = {slugify(d.name): d for d in audit_logs_path.iterdir() if d.is_dir()} if audit_logs_path.exists() else {}
    comp_dirs = {slugify(d.name): d for d in comparisons_path.iterdir() if d.is_dir()} if comparisons_path.exists() else {}

    _bl_exact, _bl_pattern, _bl_total, _bl_loaded = _load_export_blacklist(root_dir=root_dir)
    if _bl_loaded and _bl_total:
        logging.info(
            f"  Blacklist: {_bl_total} Eintra(e)ge geladen "
            f"({len(_bl_exact)} exakt, {len(_bl_pattern)} Pattern)"
        )
    elif _bl_loaded:
        logging.info("  Blacklist: Datei geladen, leer.")

    # Provider-Config für card_model_id-Redirect (Dual-Thinking-Profile).
    # Graceful degradation: ohne Config bleibt load_model_card wie bisher.
    _provider_config: dict | None = None
    try:
        _provider_config = ConfigValidator().config
    except Exception:  # pylint: disable=broad-except
        pass

    return {
        "root_dir": root_dir,
        "comparisons_path": comparisons_path,
        "vendor_alias_map": _vendor_alias_map,
        "vendor_card_id_lookup": _vendor_card_id_lookup,
        "community_alias_map": _community_alias_map,
        "community_card_id_lookup": _community_card_id_lookup,
        "provider_map": provider_map,
        "provider_config": _provider_config,
        "ldb": ldb,
        "pc": pc,
        "pc_lb_map": pc_lb_map,
        "pc_lb_slug_map": pc_lb_slug_map,
        "block_meta": block_meta,
        "benchmark_run_map": _benchmark_run_map,
        "audit_dirs": audit_dirs,
        "comp_dirs": comp_dirs,
        "bl_exact": _bl_exact,
        "bl_pattern": _bl_pattern,
        "bl_total": _bl_total,
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }


def _audit_has_benchmark(model_audit_src: Path | None) -> bool:
    """True wenn das Audit-Quellverzeichnis echte Judge-Logs enthaelt.

    ``00_bias_report.md`` ist kein Modul-Benchmark und wird ignoriert.
    Genutzt von _should_skip_model (Skip-Entscheidung) und zur Ableitung
    von ``report_available`` OHNE die Logs ins Web-Repo zu kopieren.
    """
    return (
        model_audit_src is not None
        and model_audit_src.exists()
        and any(f.name != "00_bias_report.md" for f in model_audit_src.glob("*.md"))
    )


def _should_skip_model(
    *,
    model_name: str,
    raw_model_id: str,
    row: Any,
    model_audit_src: Path | None,
    count: int,
    total: int,
    bl_exact: set[str],
    bl_pattern: set[str],
) -> str | None:
    """Entscheidet ob ein Model in der Leaderboard-Iteration uebersprungen wird.

    Returns:
        None     — Model wird verarbeitet
        "no_benchmark" — weder Audit-Log noch CSV-Score vorhanden
        "blacklisted"   — raw_model_id matcht Web-Export-Blacklist
    """
    has_raw = bool(raw_model_id) and raw_model_id != "nan"

    # Skip 1: kein Benchmark (weder Audit-Log noch CSV-Score)
    _audit_has_bench = _audit_has_benchmark(model_audit_src)
    _csv_total = str(row.get(LdbCols.TOTAL_SCORE, "")).strip()
    _csv_has_benchmark = _csv_total not in ("", "Pending", "—", "nan") and not pd.isna(row.get(LdbCols.TOTAL_SCORE, float("nan")))
    if not _audit_has_bench and not _csv_has_benchmark:
        logging.debug("  [%s/%s] %s -> SKIP (nur PC-Daten, kein Benchmark)", count, total, model_name)
        return "no_benchmark"

    # Skip 2: Web-Export-Blacklist
    if has_raw and _is_blacklisted(raw_model_id, bl_exact, bl_pattern):
        logging.info("  [%s/%s] %s -> SKIP (blacklisted: %s)", count, total, model_name, raw_model_id)
        return "blacklisted"

    return None


def _resolve_model_dirs_and_card(
    *,
    model_name: str,
    raw_model_id: str,
    slug: str,
    card_lookup: Callable[[str], dict | None],
    audit_dirs: dict[str, Path],
    comp_dirs: dict[str, Path],
    count: int,
    total: int,
) -> tuple[dict | None, Path | None, Path | None]:
    """Loest Model-Card und Audit-/Comparison-Verzeichnisse auf.

    Reihenfolge:
    1. Card-Lookup mit raw_model_id, fallback model_name.
    2. Audit-Dir via dir_slug (slugify(raw_model_id) oder slug).
    3. Audit-Dir via _safe_name(raw_model_id) (Card-Konvention).
    4. Audit-Dir via heritage_ids aus Card (Mehrfach-Versuche bis Treffer).

    Returns: (card, model_audit_src, model_comp_src) — jedes None wenn nicht aufgeloest.
    """
    has_raw = bool(raw_model_id) and raw_model_id != "nan"
    dir_slug = slugify(raw_model_id) if has_raw else slug

    # Card-Resolution: raw_model_id zuerst, fallback model_name
    card = card_lookup(raw_model_id) if has_raw else None
    if card is None:
        card = card_lookup(model_name)

    # Warning fuer fehlende Card wird im Caller (_process_leaderboard) NACH
    # der Skip-Pruefung geloggt — sonst spammen geskippte Modelle das Log.
    # Audit/Comp-Dir via dir_slug
    model_audit_src = _resolve_dir(audit_dirs, dir_slug)
    model_comp_src = _resolve_dir(comp_dirs, dir_slug)

    # Fallback: _safe_name(raw_model_id) (Card-Konvention)
    if has_raw:
        safe_dir_slug = slugify(_safe_name(raw_model_id))
        if safe_dir_slug != dir_slug:
            if model_audit_src is None:
                model_audit_src = _resolve_dir(audit_dirs, safe_dir_slug)
            if model_comp_src is None:
                model_comp_src = _resolve_dir(comp_dirs, safe_dir_slug)

    # Fallback: heritage_ids aus Card
    if card:
        for h_id in card.get("heritage_ids", []):
            for h_slug in dict.fromkeys([slugify(h_id), slugify(_safe_name(h_id))]):
                if model_audit_src is None:
                    model_audit_src = _resolve_dir(audit_dirs, h_slug)
                if model_comp_src is None:
                    model_comp_src = _resolve_dir(comp_dirs, h_slug)
            if model_audit_src is not None and model_comp_src is not None:
                break

    return card, model_audit_src, model_comp_src


def _process_leaderboard(
    ctx: dict[str, Any],
    filter_slug: str | None,
    models_dir: Path,
) -> dict[str, Any]:
    """Iteriert über die Leaderboard-CSV und baut Model-JSONs + PC-Daten."""
    root_dir: Path = ctx["root_dir"]
    ldb = ctx["ldb"]
    pc = ctx["pc"]
    pc_lb_map = ctx["pc_lb_map"]
    pc_lb_slug_map = ctx["pc_lb_slug_map"]
    block_meta = ctx["block_meta"]
    benchmark_run_map = ctx["benchmark_run_map"]
    audit_dirs = ctx["audit_dirs"]
    comp_dirs = ctx["comp_dirs"]
    vendor_alias_map = ctx["vendor_alias_map"]
    vendor_card_id_lookup = ctx["vendor_card_id_lookup"]
    community_alias_map = ctx["community_alias_map"]
    community_card_id_lookup = ctx["community_card_id_lookup"]
    provider_map = ctx["provider_map"]
    provider_config = ctx.get("provider_config")
    bl_exact = ctx["bl_exact"]
    bl_pattern = ctx["bl_pattern"]

    models_list: list[dict[str, Any]] = []
    pc_list: list[dict[str, Any]] = []
    models_with_reports = 0
    models_with_reviews = 0
    models_skipped_blacklist = 0

    # F1: Slug-Collision-Tracking — mehrere Benchmark-Runs (verschiedene
    # Quants/Provider) mit gleichem Display-Namen würden sonst dieselbe
    # data.json überschreiben. Bei Collision wird provider_code als Suffix
    # angehängt; falls das noch nicht eindeutig ist, folgt ein Counter.
    _seen_slugs: set[str] = set()

    count = 0
    total = len(ldb)

    for _, row in ldb.iterrows():
        model_name = str(row.get(LdbCols.MODEL_NAME, ""))
        if not model_name or str(model_name) == "nan": continue
        count += 1

        raw_model_id = str(row.get(LdbCols.MODEL_ID, row.get("model_id_raw", row.get("model_id", "")))).strip()
        _has_raw = bool(raw_model_id) and raw_model_id != "nan"

        # SSoT: Slug aus model_id (stabile Identität), nicht aus model_name
        # (veränderlicher Display-Name). Hybrid-Paare (Thinking/Standard)
        # haben unterschiedliche model_ids → keine Slug-Kollision mehr.
        # Fallback auf model_name nur wenn model_id fehlt (Defensiv, sollte
        # bei benchmarked models nicht vorkommen).
        slug = slugify(raw_model_id) if _has_raw else slugify(model_name)
        if filter_slug and slugify(filter_slug) != slug:
            continue

        # Safety-Net: Slug-Kollision bei identischen model_ids (sollte bei
        # korrekter CSV nicht vorkommen). Provider-Suffix als Disambiguator.
        if slug in _seen_slugs:
            _pc = str(row.get(LdbCols.PROVIDER_CODE, "")).strip().lower()
            _base = f"{slug}-{_pc}" if _pc else f"{slug}-2"
            _n = 2
            _candidate = _base
            while _candidate in _seen_slugs:
                _n += 1
                _candidate = f"{slug}-{_pc}-{_n}" if _pc else f"{slug}-{_n}"
            _orig_slug = slug
            slug = _candidate
            logging.warning(
                "  [WARN] [%s/%s] Slug-Collision: %r → %r (model_id=%s, provider=%s)",
                count, total, _orig_slug, slug, raw_model_id, _pc or "?",
            )
        _seen_slugs.add(slug)
        card, model_audit_src, model_comp_src = _resolve_model_dirs_and_card(
            model_name=model_name,
            raw_model_id=raw_model_id,
            slug=slug,
            card_lookup=lambda mid: load_model_card(mid, root_dir, config=provider_config),
            audit_dirs=audit_dirs,
            comp_dirs=comp_dirs,
            count=count,
            total=total,
        )

        skip_reason = _should_skip_model(
            model_name=model_name,
            raw_model_id=raw_model_id,
            row=row,
            model_audit_src=model_audit_src,
            count=count,
            total=total,
            bl_exact=bl_exact,
            bl_pattern=bl_pattern,
        )
        if skip_reason == "no_benchmark":
            continue
        if skip_reason == "blacklisted":
            models_skipped_blacklist += 1
            continue

        # BUG 2 Fix: Card-Warning erst nach Skip-Pruefung — sonst spammen
        # geskippte Modelle (no_benchmark / blacklisted) das Log mit WARNINGS.
        if card is None:
            logging.warning(
                "  [WARN] [%s/%s] %s (raw_model_id=%s): keine Model Card gefunden. "
                "Web-Export liefert model_card=null.",
                count, total, model_name, raw_model_id or "?",
            )

        logging.info("  [%s/%s] %s -> OK", count, total, model_name)
        model_out = models_dir / slug
        model_out.mkdir(exist_ok=True)

        comp_files_dict = _export_model_files(model_out, model_comp_src)
        has_report = _audit_has_benchmark(model_audit_src)
        has_review = comp_files_dict["review"] is not None or comp_files_dict["bias_review"] is not None
        review_published_at, review_updated_at = _review_date_range(model_comp_src) if model_comp_src else (None, None)
        if has_report: models_with_reports += 1
        if has_review: models_with_reviews += 1

        vendor = _normalize_vendor(card.get("vendor") if card else None, vendor_alias_map)

        _raw_community = card.get("community") if card else None
        community = _normalize_community(_raw_community, community_alias_map)
        community_card_ref = community_card_id_lookup.get(community) if community else None

        _arch_tags: list = (card.get("architecture_tags") or []) if card else []

        # Thinking-Mode: primär aus CSV-Spalte (per-Run, von base_runner erfasst),
        # Fallback auf architecture_tags (Capability-basiert) für Cloud-Modelle
        # ohne Thinking-Toggle (CSV-Wert "n/a" oder Spalte fehlt).
        #
        # Dual-Profile-Fallback: alte Runs (vor Dual-Profile-Config) haben
        # thinking_mode="n/a"/leer. Für dual_profile-Cards vergleichen wir
        # raw_model_id mit card.model_id: Match → Standard-Profil, kein Match
        # → Thinking-Profil. Kein Suffix-Heuristik — nutzt die bereits korrekt
        # aufgelöste kanonische Model-ID.
        _csv_thinking = str(row.get(LdbCols.THINKING_MODE, "")).strip().lower()
        if _csv_thinking in ("thinking", "standard"):
            _thinking_mode = _csv_thinking
        elif card and card.get("dual_profile"):
            _card_mid = str(card.get("model_id", "")).strip()
            _thinking_mode = "standard" if raw_model_id == _card_mid else "thinking"
        elif "Thinking-Optional" in _arch_tags:
            _thinking_mode = "partial"
        elif "Thinking" in _arch_tags:
            _thinking_mode = "thinking"
        else:
            _thinking_mode = "standard"

        _card_tier = card.get("weights_license_tier") if card else None
        _type = (WEIGHTS_TIER_DISPLAY.get(_card_tier) if _card_tier else None) or str(row.get(LdbCols.TYPE, ""))

        benchmark_run_at = benchmark_run_map.get(model_name) or benchmark_run_map.get(raw_model_id)
        entry = _build_leaderboard_entry(
            row=row,
            card=card,
            slug=slug,
            vendor=vendor,
            thinking_mode=_thinking_mode,
            model_type=_type,
            has_report=has_report,
            has_review=has_review,
            review_published_at=review_published_at,
            review_updated_at=review_updated_at,
            benchmark_run_at=benchmark_run_at,
            inference_provider=resolve_inference_provider(model_name, provider_map),
            vendor_card_ref=vendor_card_id_lookup.get(vendor) if vendor else None,
            community=community,
            community_card_ref=community_card_ref,
        )
        models_list.append(entry)

        compass_data: dict[str, Any] | None = None
        if pc is not None and "model" in pc.columns and "run_id" in pc.columns:
            _pc_id = raw_model_id if raw_model_id and raw_model_id != "nan" else model_name
            _pc_slug = slugify(_pc_id)
            pc_row = _lookup_pc_row(_pc_id, _pc_slug, pc)
            if pc_row is not None:
                lb_row = pc_lb_map.get(_pc_id)
                if lb_row is None:
                    lb_row = pc_lb_slug_map.get(_pc_slug)
                _card_id = (card.get("model_id") if card else None) or (
                    raw_model_id if raw_model_id and raw_model_id != "nan" else None
                )
                compass_data = _build_compass_entry(
                    pc_row, lb_row, slug, model_name, _type, block_meta, card_id=_card_id
                )
                pc_list.append(compass_data)

        # ToolUse-Daten werden nur exportiert, wenn supports_tool_use=true.
        # Bei false (kann keine Tools) oder untested (noch nicht getestet)
        # wird kein tooluse-Block generiert — das Frontend zeigt dann
        # den entsprechenden Badge-Status (✗ oder –) ohne Score-Daten.
        _tu_entry = (
            _build_tooluse_entry(raw_model_id if raw_model_id and raw_model_id != "nan" else model_name, root_dir)
            if (card and card.get("supports_tool_use") is True)
            else None
        )
        model_json: dict[str, Any] = {
            "leaderboard": entry,
            "political_compass": compass_data,
            "files": {
                "comparisons": comp_files_dict,
            },
            "tooluse": _tu_entry,
        }

        _model_data = _strip_emojis(_strip_none(model_json))
        # Scores-Contract: _strip_none (Z.1956) hat null-Values entfernt — aber
        # alle 9 Modul-Keys müssen im scores-Dict vorhanden sein (Frontend-Vertrag,
        # test_web_export_field_coverage.py). Re-Injection nach dem letzten Strip.
        _lb = _model_data.get("leaderboard")
        if isinstance(_lb, dict):
            _scores = _lb.get("scores")
            if isinstance(_scores, dict):
                for _k in _SCORES_CONTRACT_KEYS:
                    _scores.setdefault(_k, None)
            else:
                _lb["scores"] = dict.fromkeys(_SCORES_CONTRACT_KEYS, None)
        _atomic_write_json(
            model_out / "data.json",
            _model_data,
        )

    return {
        "models_list": models_list,
        "pc_list": pc_list,
        "models_with_reports": models_with_reports,
        "models_with_reviews": models_with_reviews,
        "models_skipped_blacklist": models_skipped_blacklist,
    }


def main() -> None:
    """Orchestriert den Web-Export-Pipeline."""
    try:
        config = ConfigValidator().config
        default_out = config.get("output", {}).get("web_export_dir", "./web_export")
    except Exception:
        default_out = "./web_export"

    parser = argparse.ArgumentParser(description="Export CrucibleMark data for Web")
    parser.add_argument("--output", default=default_out, type=str, help="Target directory for web data")
    parser.add_argument("--model", type=str, help="Export only a specific model slug")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s"
    )

    out_dir, models_dir, root_dir = _setup_output_dirs(args)
    scores_dir = root_dir / "benchmark_scores"
    comparisons_path = root_dir / "docs" / "reviews"

    logging.info("🌐 Starting Web Export Pipeline...")

    ctx = _init_export_context(root_dir, scores_dir, comparisons_path)
    result = _process_leaderboard(ctx, args.model, models_dir)

    _write_top_level_outputs(
        out_dir=out_dir,
        generated_at=ctx["generated_at"],
        models_list=result["models_list"],
        pc_list=result["pc_list"],
        root_dir=root_dir,
        comparisons_path=comparisons_path,
        models_with_reports=result["models_with_reports"],
        models_with_reviews=result["models_with_reviews"],
        models_skipped_blacklist=result["models_skipped_blacklist"],
        blacklist_total_entries=ctx["bl_total"],
        blacklist_source="config/web_export_blacklist.yaml",
    )
    logging.info("✅ Export completed to -> %s", out_dir)
def _normalize_export_tags(tags: list[str]) -> list[str]:
    """Filtert deprecated Tags aus architecture_tags für den Web-Export.
    
    Nutzt normalize_tags() aus utils.card_utils (SSoT: config/card_vocabulary.yaml).
    Damit landen keine Tags wie 'MoE', 'Mamba-Hybrid' oder 'Long Context' im
    öffentlichen Web-Export — sie wurden bereits in der Card-Migration entfernt,
    aber falls neue hinzukommen, werden sie hier spätestens gefiltert.
    """
    if not tags:
        return tags
    return normalize_tags(tags)[0]


def _strip_none(obj: Any) -> Any:
    """Entfernt None-Werte rekursiv aus dicts. Listen und Skalare bleiben erhalten."""
    if isinstance(obj, dict):
        return {k: _strip_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_none(item) for item in obj]
    return obj


if __name__ == "__main__":
    main()
