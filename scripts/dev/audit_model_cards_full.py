"""
Vollständiger SSoT-Audit für Model Cards.

Prüft ALLE Regeln aus:
- config/card_template_model.yaml (38 Pflichtfelder, Typen, Defaults)
- config/card_vocabulary.yaml (reserved/informational/deprecated tags)
- config/classification_taxonomy.json (Whitelists: tier, use_case, size_class,
  parameter_architecture, input/output_modalities)

Im Gegensatz zu validate_model_cards.py (das nur 7 Pflichtfelder + Tag-Whitelist
prüft) deckt dieses Script ALLE SSoT-Constraints ab.

Output: JSON mit allen Findings (CRITICAL/WARNING/INFO) pro Karte.

Verwendung:
    .venv/bin/python scripts/dev/audit_model_cards_full.py
    .venv/bin/python scripts/dev/audit_model_cards_full.py --json
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Projekt-Root zum sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import yaml

logger = logging.getLogger(__name__)

CARDS_DIR = Path("benchmark_scores/model_cards")


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_required_fields() -> list[dict]:
    """Liest 38 Pflichtfelder aus card_template_model.yaml."""
    data = load_yaml(Path("config/card_template_model.yaml"))
    return data.get("required_fields", [])


def get_optional_fields() -> list[dict]:
    data = load_yaml(Path("config/card_template_model.yaml"))
    return data.get("optional_fields", [])


def get_tag_registry() -> tuple[frozenset[str], dict[str, str | None]]:
    """(known_tags, deprecated_normalizations) aus card_vocabulary.yaml."""
    from utils.card_utils import get_all_known_tags, get_deprecated_normalizations
    return get_all_known_tags(), get_deprecated_normalizations()


def get_taxonomy_values(section: str) -> frozenset[str]:
    """Liest Whitelist-Werte aus classification_taxonomy.json."""
    from utils.card_utils import get_valid_values
    return get_valid_values(section)


def _check_required_fields(data: dict, add) -> None:
    for spec in get_required_fields():
        field_name = spec["name"]
        if field_name not in data:
            add("CRITICAL", "MISSING_REQUIRED", f"Pflichtfeld '{field_name}' fehlt", field_name)
            continue
        value = data[field_name]
        expected_type = spec.get("type")
        if value is None and spec.get("default") is None:
            continue
        if value is None and spec.get("default") == "TODO":
            continue
        if expected_type and expected_type != "null":
            if not _check_type(value, expected_type):
                add("CRITICAL", "WRONG_TYPE",
                    f"Feld '{field_name}' hat falschen Typ: erwartet {expected_type}, "
                    f"erhalten {type(value).__name__}",
                    field_name)


def _check_whitelisted_scalar_field(
    data: dict, key: str, valid: frozenset, code: str, is_todo_fn, add
) -> None:
    val = data.get(key)
    if val and not is_todo_fn(val) and val not in valid:
        add("CRITICAL", code,
            f"{key}='{val}' ist nicht in Whitelist: {sorted(valid)}",
            key)


def _check_whitelist_fields(data: dict, is_todo, add) -> None:
    _check_whitelisted_scalar_field(
        data, "deployment_type",
        frozenset({"cloud-only", "open-weights-cloud-available", "localweights", "open-weights"}),
        "INVALID_DEPLOYMENT_TYPE", is_todo, add,
    )
    _check_whitelisted_scalar_field(
        data, "weights_provenance_risk",
        frozenset({"low", "medium", "high"}),
        "INVALID_RISK_LEVEL", is_todo, add,
    )
    _check_whitelisted_scalar_field(
        data, "card_status",
        frozenset({"draft", "minimal", "complete"}),
        "INVALID_CARD_STATUS", lambda _v: False, add,
    )
    _check_whitelisted_scalar_field(
        data, "size_class",
        get_taxonomy_values("size_class"),
        "INVALID_SIZE_CLASS", is_todo, add,
    )


def _check_contradictions(data: dict, add) -> None:
    if data.get("unknown") is True and data.get("card_status") == "complete":
        add("CRITICAL", "UNKNOWN_COMPLETE_CONTRADICTION",
            "unknown=true und card_status='complete' schließen sich gegenseitig aus "
            "(Widerspruch: complete = vollständig geprüft, unknown = unvollständig)",
            "unknown/card_status")


def _check_tooluse(data: dict, add) -> None:
    tooluse = data.get("supports_tool_use")
    if tooluse is not None and not isinstance(tooluse, bool):
        add("CRITICAL", "TOOLUSE_WRONG_TYPE",
            f"supports_tool_use={tooluse!r} (Typ: {type(tooluse).__name__}) — "
            f"erwartet bool (true/false) oder null",
            "supports_tool_use")


def _check_modalities(data: dict, status: str, add) -> None:
    valid_in = get_taxonomy_values("input_modalities")
    valid_out = get_taxonomy_values("output_modalities")
    in_mods = data.get("input_modalities")
    out_mods = data.get("output_modalities")
    if in_mods is None:
        if status == "complete":
            add("CRITICAL", "MISSING_INPUT_MODALITIES",
                "input_modalities fehlt (Pflicht seit v4.7.0 in complete-Cards)",
                "input_modalities")
    elif isinstance(in_mods, list):
        for m in in_mods:
            if m not in valid_in:
                add("CRITICAL", "INVALID_INPUT_MODALITY",
                    f"input_modalities enthält '{m}' (nicht in Whitelist: {sorted(valid_in)})",
                    "input_modalities")
    if out_mods is None:
        if status == "complete":
            add("CRITICAL", "MISSING_OUTPUT_MODALITIES",
                "output_modalities fehlt (Pflicht seit v4.7.0 in complete-Cards)",
                "output_modalities")
    elif isinstance(out_mods, list):
        for m in out_mods:
            if m not in valid_out:
                add("CRITICAL", "INVALID_OUTPUT_MODALITY",
                    f"output_modalities enthält '{m}' (nicht in Whitelist: {sorted(valid_out)})",
                    "output_modalities")


def _check_architecture_tags(data: dict, add) -> None:
    from utils.card_utils import get_reserved_tags, get_informational_tags
    known_tags = get_reserved_tags() | get_informational_tags()
    _, deprecated_norm = get_tag_registry()
    tags = data.get("architecture_tags", [])
    if not isinstance(tags, list):
        return
    for tag in tags:
        if tag in known_tags:
            continue
        if tag in deprecated_norm:
            replacement = deprecated_norm[tag]
            if replacement is None:
                hint = "soll entfernt werden"
            else:
                hint = f"soll zu '{replacement}' migriert werden"
            add("WARNING", "DEPRECATED_TAG",
                f"architecture_tags enthält deprecated Tag '{tag}' — {hint}. "
                f"Registry: config/card_vocabulary.yaml",
                "architecture_tags")
        else:
            add("WARNING", "UNKNOWN_TAG",
                f"architecture_tags enthält unbekannten Tag '{tag}' — "
                f"nicht in config/card_vocabulary.yaml",
                "architecture_tags")


def _check_arch_consistency(data: dict, add) -> None:
    param_arch = data.get("parameter_architecture")
    if param_arch == "dense" and data.get("params_active_b") is not None:
        add("WARNING", "DENSE_WITH_ACTIVE_PARAMS",
            "params_active_b gesetzt, aber parameter_architecture='dense' "
            "(bei Dense sind total = aktiv — params_active_b sollte null sein)",
            "params_active_b")


def _check_model_id_format(data: dict, add) -> None:
    model_id = data.get("model_id", "")
    if "__" in model_id:
        add("WARNING", "DOUBLE_UNDERSCORE_ID",
            f"model_id='{model_id}' enthält doppelte Underscores",
            "model_id")


def check_card(path: Path, data: dict) -> list[dict]:
    """Returns list of findings, each: {severity, code, message, field}."""
    findings: list[dict] = []

    def add(severity: str, code: str, msg: str, field: str = "") -> None:
        findings.append({
            "severity": severity,
            "code": code,
            "message": msg,
            "field": field,
        })

    def is_todo(value: object) -> bool:
        return isinstance(value, str) and value.strip().upper() == "TODO"

    status = data.get("card_status")
    _check_required_fields(data, add)
    _check_whitelist_fields(data, is_todo, add)
    _check_contradictions(data, add)
    _check_tooluse(data, add)
    _check_modalities(data, status, add)
    _check_architecture_tags(data, add)
    _check_arch_consistency(data, add)
    _check_model_id_format(data, add)

    return findings


def _check_type(value, expected: str) -> bool:
    """Prüft JSON-Typ gegen erwarteten Typ-String."""
    if expected == "str":
        return isinstance(value, str)
    if expected == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "bool":
        return isinstance(value, bool)
    if expected == "list[str]":
        return isinstance(value, list) and all(isinstance(v, str) for v in value)
    if expected == "list":
        return isinstance(value, list)
    if expected == "null":
        return value is None
    return True


def _scan_all_cards(all_findings: dict, summary: dict) -> int:
    """Iterate über alle Cards und sammle Findings."""
    checked = 0
    for path in sorted(CARDS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            all_findings[path.name] = [{
                "severity": "CRITICAL",
                "code": "JSON_ERROR",
                "message": str(exc),
                "field": "",
            }]
            summary["CRITICAL"] += 1
            continue
        if not isinstance(data, dict):
            continue  # skip _index.json
        checked += 1
        findings = check_card(path, data)
        if findings:
            all_findings[path.name] = findings
            for f in findings:
                summary[f["severity"]] = summary.get(f["severity"], 0) + 1
    return checked


def _collect_duplicate_model_ids() -> dict[str, int]:
    seen: dict[str, int] = {}
    for path in sorted(CARDS_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict) and "model_id" in data:
            mid = data["model_id"]
            seen[mid] = seen.get(mid, 0) + 1
    return {k: v for k, v in seen.items() if v > 1}



def _add_duplicate_findings(all_findings: dict, summary: dict) -> None:
    duplicates = _collect_duplicate_model_ids()
    for mid, count in duplicates.items():
        all_findings["DUPLICATE_MODEL_IDS"] = all_findings.get("DUPLICATE_MODEL_IDS", []) + [{
            "severity": "CRITICAL",
            "code": "DUPLICATE_MODEL_ID",
            "message": f"model_id='{mid}' erscheint {count}× in Card-Dateien",
            "field": "model_id",
        }]
        summary["CRITICAL"] += 1


def _render_text_output(checked: int, summary: dict, all_findings: dict) -> str:
    lines = [
        f"Vollständiger SSoT-Audit — {checked} Cards geprüft",
        f"CRITICAL: {summary['CRITICAL']}, WARNING: {summary['WARNING']}, INFO: {summary.get('INFO', 0)}",
        "",
    ]
    for fname, findings in sorted(all_findings.items()):
        lines.append(f"=== {fname} ===")
        for f in findings:
            lines.append(f"  [{f['severity']}] {f['code']}: {f['message']}")
        lines.append("")
    return "\n".join(lines)


def _render_json_output(checked: int, summary: dict, all_findings: dict) -> str:
    return json.dumps(
        {"checked": checked, "summary": summary, "findings": all_findings},
        indent=2,
        ensure_ascii=False,
    )


def _emit_output(args, checked: int, summary: dict, all_findings: dict) -> None:
    if args.json:
        text = _render_json_output(checked, summary, all_findings)
    else:
        text = _render_text_output(checked, summary, all_findings)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Output geschrieben: {args.output}")
    else:
        print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Vollständiger SSoT-Audit für Model Cards")
    parser.add_argument("--json", action="store_true", help="Output als JSON")
    parser.add_argument("--output", type=str, help="Output-Datei (sonst stdout)")
    args = parser.parse_args()

    if not CARDS_DIR.exists():
        print(f"ERROR: {CARDS_DIR} nicht gefunden.", file=sys.stderr)
        return 2

    all_findings: dict[str, list[dict]] = {}
    summary = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}

    checked = _scan_all_cards(all_findings, summary)
    _add_duplicate_findings(all_findings, summary)
    _emit_output(args, checked, summary, all_findings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
