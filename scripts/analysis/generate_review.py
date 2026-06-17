#!/usr/bin/env python3
"""Meta-Reviewer für den Audit-Modus.

Generiert einen detaillierten redaktionellen Artikel über die Stärken und Schwächen
pro Modell, oder – bei --type bias – einen fokussierten Bias-Review basierend auf
dem Political Compass, oder – bei --type tooluse – einen narrativen Tool-Use-Review.

Orchestration only: all context-building logic lives in scripts/analysis/review/.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.llm_client import LLMClient
from utils.model_utils import (
    _find_card,
    _safe_name,
    find_card_by_heritage_id,
    get_model_identity,
    get_model_size_class,
    get_model_specialization,
    get_use_case_primary,
)
from utils.vendor_card_template import _safe_id
from scripts.analysis.review import (
    build_constraint_violations_summary,
    build_empty_response_context,
    build_non_success_context,
    build_token_efficiency_context,
    detect_provider,
    format_classification_context,
    get_model_card_context,
    get_model_metrics,
    get_vendor_card_context,
)

# Maximum characters of audit-log data fed to the LLM reviewer.
_MAX_LOG_CHARS = 30_000


def load_config() -> dict:
    config_path = ROOT_DIR / "benchmark_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_webexport_blacklist() -> set[str]:
    """Load web export blacklist model IDs.
    
    Returns set of blacklisted model_ids that should be skipped in auto-review.
    """
    blacklist_path = ROOT_DIR / "config" / "web_export_blacklist.yaml"
    try:
        with open(blacklist_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            blacklist = data.get("blacklist", [])
            # Return as set for fast O(1) lookup
            return set(blacklist) if blacklist else set()
    except Exception as e:
        print(f"⚠️ Konnte Webexport-Blacklist nicht laden: {e}")
        return set()


def _load_classification_taxonomy() -> dict:
    """Load classification_taxonomy.json; returns empty dict on failure."""
    path = ROOT_DIR / "config" / "classification_taxonomy.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _get_card_field(model_id: str, field: str, default: str = "") -> str:
    """Read a single string field from the model card."""
    try:
        card_path = _find_card(model_id)
        if card_path.exists():
            card = json.loads(card_path.read_text(encoding="utf-8"))
            val = card.get(field)
            if isinstance(val, str) and val:
                return val
    except Exception:
        pass
    return default


def _get_hardware_profile_for_model(model_id: str, config: dict) -> str:
    """Liest hardware_profile aus provider_config.yaml für ein lokales Modell.

    Durchsucht alle Provider-Sektionen (nicht nur 'commercial') nach der model_id
    und gibt den zugehörigen hardware_profile-Key zurück. Dieser Key wird in
    benchmark_config.yaml unter runner_environment.profiles aufgelöst — SSOT für
    die Frage, auf welcher Hardware das Modell getestet wurde.
    """
    safe_target = _safe_name(model_id)
    for section in config.get("providers", {}).values():
        if not isinstance(section, dict):
            continue
        for prov_cfg in section.values():
            if not isinstance(prov_cfg, dict):
                continue
            hw = prov_cfg.get("hardware_profile", "")
            if not hw:
                continue
            for m in prov_cfg.get("models", []):
                if not isinstance(m, dict):
                    continue
                raw_id = m.get("id", "")
                if raw_id == model_id or _safe_name(raw_id) == safe_target:
                    return hw
    return ""


def get_latest_audit_dir(base_dir: Path) -> Optional[Path]:
    """Find the most recently modified audit sub-directory."""
    subdirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name != ".DS_Store"]
    if not subdirs:
        return None
    return max(subdirs, key=os.path.getmtime)


def collect_data() -> str:
    """Read the main leaderboard CSV."""
    csv_path = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard.csv"
    if not csv_path.exists():
        return "Keine Leaderboard-Daten gefunden."
    with open(csv_path, "r", encoding="utf-8") as f:
        return f.read()


def _load_card_module(script_name: str) -> object:
    """Load a card-generator module by file path (avoids namespace collisions)."""
    import importlib.util
    path = ROOT_DIR / "scripts" / "analysis" / f"{script_name}.py"
    module_name = f"scripts_analysis_{script_name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Modul {script_name}.py nicht unter {path} gefunden.")
    module = importlib.util.module_from_spec(spec)
    # Modul in sys.modules registrieren, BEVOR exec_module läuft.
    # Hintergrund: @dataclass (Python 3.14) ruft sys.modules[cls.__module__].__dict__
    # auf, um KW_ONLY-Detection zu machen. Ohne Registrierung gibt es ein NoneType
    # statt des Modul-Dicts → AttributeError → Crash beim ersten @dataclass.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _ensure_model_card(
    model_id: str,
    client: LLMClient,
    card_provider: str,
    card_model: str,
    auto_mode: bool,
    dry_run: bool,
) -> dict | None:
    """Load or generate a model card.

    Returns dict (may be empty in dry_run), or None to signal the model should be skipped.
    """
    card_path = _find_card(model_id)
    if card_path.exists():
        try:
            return json.loads(card_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    if dry_run:
        print(f"  [FEHLEND] Model Card: {model_id}")
        return {}

    if not auto_mode:
        if not sys.stdin.isatty():
            print(f"  [WARNUNG] Model Card fehlt: {model_id} — kein interaktives Terminal, überspringe.")
            return None
        answer = input(f"  [FEHLEND] Model Card für '{model_id}' nicht gefunden. Jetzt generieren? [j/N] ").strip().lower()
        if answer not in ("j", "ja", "y", "yes"):
            print(f"  Überspringe {model_id}.")
            return None

    print(f"  Generiere Model Card für {model_id} ...")
    from utils.card_utils import ensure_card
    from utils.model_utils import _card_path
    mc_gen = _load_card_module("generate_model_cards")
    card_path_out = _card_path(model_id, for_write=True)
    result_path = ensure_card(model_id, card_path=card_path_out)
    mc_gen._rebuild_index()  # type: ignore[attr-defined]
    print(f"  Model Card erstellt: {result_path}")
    try:
        return json.loads(result_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _ensure_vendor_card(
    developer: str | None,
    client: LLMClient,
    card_provider: str,
    card_model: str,
    auto_mode: bool,
    dry_run: bool,
) -> dict | None:
    """Load or generate a provider card. Returns {} for local models (no provider)."""
    if not developer:
        return {}

    # SSoT-Pfad: SSoT-Lookup via load_vendor_card().
    from utils.vendor_card_template import CARDS_DIR, load_vendor_card
    card_path = CARDS_DIR / f"{_safe_id(developer)}.json"
    if card_path.exists():
        existing = load_vendor_card(developer)
        if existing:
            return existing

    if dry_run:
        print(f"  [FEHLEND] Provider Card: {developer}")
        return {}

    if not auto_mode:
        if not sys.stdin.isatty():
            print(f"  [WARNUNG] Provider Card fehlt: {developer} — kein interaktives Terminal, überspringe.")
            return None
        answer = input(f"  [FEHLEND] Provider Card für '{developer}' nicht gefunden. Jetzt generieren? [j/N] ").strip().lower()
        if answer not in ("j", "ja", "y", "yes"):
            print(f"  Überspringe Provider Card für {developer}.")
            return None

    print(f"  Generiere Provider Card für {developer} ...")
    # Direkter Aufruf statt Reflection: generate_vendor_cards_full() iteriert
    # die Provider-Liste und ruft _generate_card/_write_card intern.
    # Hier filtern wir auf den einen Provider via force-Logik im Caller-Pfad.
    from scripts.analysis.generate_vendor_cards import (
        _load_stats_from_csv,
        _generate_card,
        _write_card,
    )
    from utils.vendor_card_template import rebuild_provider_index
    all_stats: dict = _load_stats_from_csv()
    stats = all_stats.get(developer, {})
    provider_id = _safe_id(developer)
    card = _generate_card(developer, provider_id, stats, client, card_provider, card_model)
    _write_card(card)
    rebuild_provider_index()
    print(f"  Provider Card erstellt: {developer}")
    return card


def _ensure_dependencies(
    model_id: str,
    client: LLMClient,
    card_provider: str,
    card_model: str,
    auto_mode: bool = False,
    dry_run: bool = False,
) -> dict | None:
    """Ensure model card and provider card exist before generating a review.

    Returns dict (proceed) or None (skip this model).
    """
    model_card = _ensure_model_card(model_id, client, card_provider, card_model, auto_mode, dry_run)
    if model_card is None:
        return None

    developer: str | None = model_card.get("developer") if model_card else None
    if not developer:
        developer = detect_provider(model_id)

    if _ensure_vendor_card(developer, client, card_provider, card_model, auto_mode, dry_run) is None:
        return None

    return {}


def process_model_review(
    model_dir: Path,
    csv_data: str,
    client: LLMClient,
    provider: str,
    model_id: str,
    review_type: str = "benchmark",
    max_tokens: int = 8192,
    canonical_model_id: str | None = None,
) -> None:
    """Read audit logs for a tested LLM and generate a review.

    Args:
        canonical_model_id: Wenn gesetzt, wird dieser Wert statt ``model_dir.name``
            für Card-/Metriken-Lookups und den Output-Pfad verwendet. Wird vom
            Heritage-ID-Fallback in ``_run_audit_reviews`` gesetzt, wenn eine
            umbenannte Card über ``find_card_by_heritage_id`` gefunden wurde.
            Die Audit-Log-Dateien werden weiterhin aus ``model_dir`` gelesen.
    """
    # Heritage-ID-Fallback: wenn canonical_model_id gesetzt, nutzen wir sie
    # für Card-/Metriken-Lookups und den Output-Pfad. model_dir.name bleibt
    # für die tatsächlichen Audit-Log-Dateien (die liegen noch unter dem alten Namen).
    tested_model_name = canonical_model_id or model_dir.name
    _log_label = (
        f"{model_dir.name} → {canonical_model_id}"
        if canonical_model_id and canonical_model_id != model_dir.name
        else model_dir.name
    )
    print(f"\n📥 Sammle Logs für Modell: {_log_label} (Typ: {review_type})...")

    extracted_logs = []
    for md_file in model_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            is_bias_file = md_file.name in ("00_bias_report.md", "pol_comp_report.md")

            if review_type == "bias" and not is_bias_file:
                continue
            if review_type == "benchmark" and is_bias_file:
                continue

            judge_section_match = re.search(r"## 3\. Evaluation.*", content, re.DOTALL)
            system_info_match = re.search(r"> \[!(?:WARNING|CAUTION|ERROR)\].*?(?=\n\n|$)", content, re.DOTALL)
            system_info_text = f"\n\n{system_info_match.group(0)}" if system_info_match else ""

            safety_filter_match = re.search(r"## 2\. Model.*?Error: Content blocked by safety filters\.", content, re.DOTALL)
            if safety_filter_match:
                system_info_text += "\n\n> ⚠️ **[SAFETY FILTER TRIGGERED]** The model refused to answer due to extreme safety filters."

            if is_bias_file:
                extracted_logs.append(f"--- Datei: {md_file.name} ---\n{content}")
            elif judge_section_match:
                extracted = judge_section_match.group(0).strip()
                extracted_logs.append(f"--- Datei: {md_file.name} ---{system_info_text}\n{extracted}")
            else:
                extracted_logs.append(f"--- Datei: {md_file.name} ---{system_info_text}\n{content[-1500:]}")
        except Exception:
            continue

    if not extracted_logs:
        print(f"⚠️ Keine zutreffenden Logs gefunden für {tested_model_name} im Modus {review_type}, überspringe.")
        return

    if review_type == "bias":
        bias_card_path = _find_card(tested_model_name)
        if not bias_card_path.exists():
            print(f"⚠️ Keine Model Card für {tested_model_name} — Bias-Review wird übersprungen.")
            return
        try:
            bias_card = json.loads(bias_card_path.read_text(encoding="utf-8"))
            missing = {k for k in ("developer", "origin_country", "developer_jurisdiction") if not bias_card.get(k)}
            if missing:
                print(f"⚠️ Model Card für {tested_model_name} fehlt Felder {missing} — Bias-Review wird übersprungen.")
                return
        except Exception:
            print(f"⚠️ Model Card für {tested_model_name} nicht lesbar — Bias-Review wird übersprungen.")
            return

    log_data = "\n\n".join(extracted_logs)
    if len(log_data) > _MAX_LOG_CHARS:
        log_data = log_data[:_MAX_LOG_CHARS] if review_type == "bias" else log_data[-_MAX_LOG_CHARS:]

    try:
        from utils.config_validator import ConfigValidator
        from utils.constants import MODEL_TYPE_OPEN_WEIGHTS_CLOUD
        from utils.system_context import SystemContextManager

        # Auflösung über ConfigValidator, damit benchmark_config.yaml UND
        # config/provider_config.yaml (OpenRouter, Groq) gemerged berücksichtigt werden.
        validator = ConfigValidator()
        commercial_providers = validator.config.get("providers", {}).get("commercial", {})

        resolved_provider_key: str | None = None
        resolved_model_type: str = ""
        # `tested_model_name` ist hier bereits der safe_name (kommt aus model_dir.name),
        # z.B. "minimax_minimax-m3" für die Config-ID "minimax/minimax-m3".
        # Wir vergleichen deshalb beide Seiten safe-normalisiert.
        target_safe = _safe_name(tested_model_name)

        for prov_key, prov_cfg in commercial_providers.items():
            if not isinstance(prov_cfg, dict) or not prov_cfg.get("enabled", False):
                continue
            for m in prov_cfg.get("models", []):
                if not isinstance(m, dict):
                    continue
                raw_id = m.get("id")
                if not raw_id:
                    continue
                if _safe_name(raw_id) == target_safe:
                    resolved_provider_key = prov_key
                    # Per-Model-Override schlägt Provider-Default.
                    resolved_model_type = m.get("model_type") or prov_cfg.get("model_type", "")
                    break
            if resolved_provider_key:
                break

        if resolved_provider_key and resolved_model_type == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
            run_type = "cloud_open_weights"
        elif resolved_provider_key:
            # Jeder andere aktive commercial-Eintrag ist proprietäre API oder
            # als proprietary_api markierter OpenRouter-Endpoint (z.B. GLM, Kimi, DeepSeek via OR).
            run_type = "commercial"
        else:
            # Modell ist in keinem commercial-Provider gelistet → lokales Deployment.
            run_type = "local"

        context_manager = SystemContextManager()
        # SSOT: hardware_profile aus provider_config.yaml für lokale Modelle lesen.
        # Damit wird das Testsystem des Modells beschrieben, nicht der Review-Rechner.
        hw_profile_key = (
            _get_hardware_profile_for_model(tested_model_name, validator.config)
            if run_type == "local"
            else ""
        )
        hardware_context = context_manager.get_editor_prompt_injection(
            run_type, hardware_profile_key=hw_profile_key
        )
    except Exception:
        hardware_context = "Achte auf Performance und Effizienz bezüglich Token-Kosten."

    tier_metaphor_rules = ""
    try:
        _config = load_config()
        _tiers = _config.get("scoring_tiers", {})
        sorted_tiers = sorted(_tiers.items(), key=lambda item: item[1].get("threshold", 0.0), reverse=True)
        tier_lines = []
        for i, (_, data) in enumerate(sorted_tiers):
            threshold = data.get("threshold", 0.0)
            desc = data.get("prompt_description", "")
            next_threshold = sorted_tiers[i - 1][1].get("threshold", 100.0) if i > 0 else 100.0
            desc = desc.replace("{threshold}", str(threshold)).replace("{next_threshold}", str(next_threshold))
            tier_lines.append(desc)
        tier_metaphor_rules = "\n".join(tier_lines)
    except Exception:
        tier_metaphor_rules = "- **Ab 95%:** Platin\n- **Ab 80% bis unter 95%:** Gold\n- **Ab 65% bis unter 80%:** Silber\n- **Ab 50% bis unter 65%:** Bronze\n- **Unter 50%:** Standard"

    prompt_key = "bias_reviewer" if review_type == "bias" else "meta_reviewer"
    try:
        with open(ROOT_DIR / "config" / "meta_reviewer_prompt.yaml", "r", encoding="utf-8") as f:
            prompt_yaml = yaml.safe_load(f)
        prompt_template = prompt_yaml.get(prompt_key, {}).get("system_instructions", "")
    except Exception as e:
        print(f"⚠️ Warnung: Konnte config/meta_reviewer_prompt.yaml nicht laden: {e}")
        prompt_template = "Fehler beim Laden des Prompts."

    model_metrics = get_model_metrics(tested_model_name)
    if not model_metrics:
        alias_card = _find_card(tested_model_name)
        if alias_card.exists():
            try:
                alias_data = json.loads(alias_card.read_text(encoding="utf-8"))
                alias_id = alias_data.get("model_id")
                if alias_id and alias_id != tested_model_name:
                    model_metrics = get_model_metrics(alias_id)
                    if model_metrics:
                        print(f"ℹ️ Alias-Auflösung: {tested_model_name} → {alias_id}")
            except Exception:
                pass
    if not model_metrics:
        print(f"👻 Ghost Model erkannt oder keine Metriken für {tested_model_name} gefunden, überspringe.")
        return

    def safe_round(val: object) -> str:
        try:
            return str(round(float(val), 2))  # type: ignore[arg-type]
        except (ValueError, TypeError):
            return "n/a"

    timeout_count = model_metrics.get("Timeout Count", "n/a")
    tests_run = model_metrics.get("Tests Run", "n/a")
    if tests_run != "n/a" and "/" in tests_run:
        tests_run = tests_run.split("/")[-1]
    timeout_rate_str = f"{timeout_count}/{tests_run}" if timeout_count != "n/a" else "n/a"

    original_model_name = model_metrics.get("Model Name", tested_model_name)
    identity = get_model_identity(original_model_name)

    card_path = _find_card(tested_model_name)
    if card_path.exists():
        try:
            card_data = json.loads(card_path.read_text(encoding="utf-8"))
            card_tags = card_data.get("architecture_tags")
            if card_tags and isinstance(card_tags, list) and len(card_tags) > 0:
                identity = {**identity, "tags": card_tags}
            card_display_name = card_data.get("display_name")
            if card_display_name:
                identity = {**identity, "display_name": card_display_name}
        except Exception:
            pass

    _config = load_config()
    token_efficiency_context = build_token_efficiency_context(
        tested_model_name, _config.get("token_budgets", {})
    )
    constraint_violations_context = build_constraint_violations_summary(model_dir) if review_type == "benchmark" else ""
    empty_response_context = build_empty_response_context(tested_model_name) if review_type == "benchmark" else ""
    non_success_context = build_non_success_context(tested_model_name) if review_type == "benchmark" else ""

    if review_type == "bias":
        import csv as _csv
        pc_csv_path = ROOT_DIR / "benchmark_scores" / "political_compass_leaderboard.csv"
        if pc_csv_path.exists():
            with open(pc_csv_path, "r", encoding="utf-8") as _f:
                for _row in _csv.DictReader(_f):
                    _safe = _safe_name(_row.get("model", ""))
                    if _safe == tested_model_name or _row.get("model") == tested_model_name:
                        csv_data = (
                            f"- Vanilla X (Ökonomisch): {_row.get('vanilla_x', 'n/a')}\n"
                            f"- Vanilla Y (Gesellschaftlich): {_row.get('vanilla_y', 'n/a')}\n"
                            f"- Vanilla Label: {_row.get('vanilla_label', 'n/a')}\n"
                            f"- Forced X (Ökonomisch): {_row.get('forced_x', 'n/a')}\n"
                            f"- Forced Y (Gesellschaftlich): {_row.get('forced_y', 'n/a')}\n"
                            f"- Forced Label: {_row.get('forced_label', 'n/a')}\n"
                            f"- Shift X: {_row.get('shift_x', 'n/a')}, Shift Y: {_row.get('shift_y', 'n/a')}\n"
                            f"- Shift Distance (euklidisch): {_row.get('shift_distance', 'n/a')}\n"
                            f"- Polarity Flip Rate: {_row.get('polarity_flip_rate', 'n/a')}%\n"
                            f"- Verhaltens-Archetyp: {_row.get('behavior_archetype', 'n/a')}\n"
                            f"- Extremismus-Status: {_row.get('extremism_status', 'n/a')}"
                        )
                        break

    _taxonomy = _load_classification_taxonomy()
    _use_case = get_use_case_primary(tested_model_name)
    _size_class = model_metrics.get("Size Class") or get_model_size_class(tested_model_name)
    _param_arch = _get_card_field(tested_model_name, "parameter_architecture", "dense")

    template_vars = {
        "tested_model_name": tested_model_name,
        "display_model_name": identity["display_name"],
        "model_tags": ", ".join(identity["tags"]),
        "hardware_context": hardware_context,
        "csv_data": csv_data,
        "log_data": log_data,
        "tier_metaphor_rules": tier_metaphor_rules,
        "model_specialization": get_model_specialization(tested_model_name),
        "model_p95_time": safe_round(model_metrics.get("P95 Time (s)")),
        "model_tokens_per_s": safe_round(model_metrics.get("Tokens/s")),
        "model_timeout_rate": timeout_rate_str,
        "model_provider_type": model_metrics.get("Type", "n/a"),
        "model_size_class": _size_class,
        "model_card_context": get_model_card_context(tested_model_name),
        "vendor_card_context": get_vendor_card_context(tested_model_name),
        "token_efficiency_context": token_efficiency_context,
        "constraint_violations_context": constraint_violations_context,
        "empty_response_context": empty_response_context,
        "non_success_context": non_success_context,
        "use_case_classification_context": format_classification_context(_use_case, _size_class, _param_arch, _taxonomy),
    }

    try:
        prompt = prompt_template.format(**template_vars)
    except KeyError as e:
        print(f"⚠️ Warnung im Prompt-Template: Fehlende Variable {e}")
        template_vars[e.args[0]] = "n/a"
        prompt = prompt_template.format(**template_vars)

    print(f"🤖 Generiere {review_type.capitalize()}-Review für {tested_model_name} mit {provider}/{model_id}...")

    try:
        response = client.query(
            model=model_id,
            prompt=prompt,
            provider=provider,
            temperature=0.7,
            max_tokens=max_tokens,
        )
    except Exception as e:
        print(f"❌ Fehler bei der Generierung für {tested_model_name}: {e}")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT_DIR / "docs" / "reviews" / _safe_name(tested_model_name)
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix = "bias_review" if review_type == "bias" else "review"
    out_file = out_dir / f"{prefix}_{timestamp}.md"

    display_time = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
    lines = response.splitlines()
    if lines:
        lines.insert(1, f"\n> **Erstellt am:** {display_time}\n")
    else:
        lines.append(f"\n> **Erstellt am:** {display_time}\n")

    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Review gespeichert unter: {out_file.relative_to(ROOT_DIR)}")


def _run_tooluse_reviews(
    args: argparse.Namespace,
    client: LLMClient,
    provider: str,
    model_id: str,
    max_tokens: int,
) -> None:
    """Tooluse-Narrative-Reviews für alle (oder ein) Modell(e) generieren."""
    from utils.export.tooluse_context import (
        build_tooluse_context,
        get_all_tooluse_model_ids,
        get_tooluse_leaderboard_row,
    )

    try:
        with open(ROOT_DIR / "config" / "meta_reviewer_prompt.yaml", "r", encoding="utf-8") as f:
            prompt_yaml = yaml.safe_load(f)
        prompt_template = prompt_yaml.get("tooluse_reviewer", {}).get("system_instructions", "")
    except Exception as e:
        print(f"❌ Fehler beim Laden des tooluse_reviewer-Prompts: {e}")
        return
    if not prompt_template:
        print("❌ 'tooluse_reviewer' nicht in config/meta_reviewer_prompt.yaml gefunden.")
        return

    leaderboard_csv = ROOT_DIR / "benchmark_scores" / "tooluse_leaderboard.csv"
    if not leaderboard_csv.exists():
        print("❌ tooluse_leaderboard.csv nicht gefunden. Bitte erst Benchmark ausführen.")
        return

    model_ids = [args.model] if args.model else get_all_tooluse_model_ids()
    if not model_ids:
        print("⚠️ Keine Modelle in tooluse_leaderboard.csv gefunden.")
        return

    _taxonomy = _load_classification_taxonomy()
    # Blacklist vorab laden — Matching erfolgt über model_id aus der Model Card (SSOT)
    blacklist = _load_webexport_blacklist() if args.auto else set()

    for mid in model_ids:
        slug = _safe_name(mid)
        out_dir = ROOT_DIR / "docs" / "reviews" / slug

        if args.auto and not args.force:
            existing_reviews = sorted(out_dir.glob("tooluse_narrative_review_*.md")) if out_dir.exists() else []
            if existing_reviews:
                latest_review_mtime = existing_reviews[-1].stat().st_mtime
                # audit_dir verwendet slug (_safe_name), weil audit_logs-Verzeichnisse
                # per SSoT mit _safe_name angelegt werden (Punkte/Slashes → Underscores).
                # Rohe mid (z.B. "xiaomi/mimo-v2.5") würde einen verschachtelten Pfad
                # erzeugen, der nie existiert → Recency-Check wäre immer False.
                audit_dir = ROOT_DIR / "outputs" / "audit_logs" / slug
                tooluse_audit_files = list(audit_dir.glob("tooluse*.md")) if audit_dir.exists() else []
                latest_audit_mtime = max((f.stat().st_mtime for f in tooluse_audit_files), default=0)
                if latest_review_mtime >= latest_audit_mtime:
                    print(f"⏩ Tool-Use-Review für {mid} aktuell – überspringe.")
                    continue

        # Guard 1: model must have data in tooluse_leaderboard.csv
        if not get_tooluse_leaderboard_row(mid):
            print(f"⏩ {mid}: Kein Eintrag in tooluse_leaderboard.csv — Benchmark zuerst ausführen.")
            continue

        # Guard 2: Card laden — model_id daraus ist SSOT für Blacklist + supports_tool_use
        _card = _find_card(mid)
        _card_data: dict = {}
        if _card.exists():
            try:
                _card_data = json.loads(_card.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Blacklist-Check: SSOT ist die model_id aus der Card (nicht der Tooluse-Leaderboard-Key)
        if args.auto and blacklist:
            _bl_id = _card_data.get("model_id") or slug
            if _bl_id in blacklist:
                print(f"⏩ {mid}: Auf Webexport-Blacklist ({_bl_id}) → Tool-Use-Review wird übersprungen.")
                continue

        # supports_tool_use prüfen (Tri-State):
        #   true       → Tool-Use-Review wird generiert
        #   false      → Modell kann keine Tools — Review übersprungen (gewollt)
        #   "untested" → noch kein Benchmark gelaufen — Review übersprungen
        #   null/fehlt → wie "untested" behandelt
        if _card_data:
            stu = _card_data.get("supports_tool_use")
            if stu is False:
                print(f"⏩ {mid}: supports_tool_use=false in Model Card — überspringe.")
                continue
            if stu is not True:  # None, "untested", oder sonstiger Wert
                print(
                    f"⏩ {mid}: supports_tool_use={stu!r} (nicht getestet) "
                    f"— Tool-Use-Benchmark zuerst ausführen."
                )
                continue

        ctx = build_tooluse_context(mid)
        if not ctx:
            print(f"⚠️ Keine Leaderboard-Daten für {mid} — überspringe.")
            continue

        identity = get_model_identity(mid)
        card_path = _find_card(mid)
        if card_path.exists():
            try:
                card_data = json.loads(card_path.read_text(encoding="utf-8"))
                card_tags = card_data.get("architecture_tags")
                if card_tags and isinstance(card_tags, list):
                    identity = {**identity, "tags": card_tags}
                card_display = card_data.get("display_name")
                if card_display:
                    identity = {**identity, "display_name": card_display}
            except Exception:
                pass

        _use_case = get_use_case_primary(mid)
        _size_class = get_model_size_class(mid)
        _param_arch = _get_card_field(mid, "parameter_architecture", "dense")

        ctx["model_tags"] = ", ".join(identity["tags"])
        ctx["display_model_name"] = identity["display_name"]
        ctx["model_card_context"] = get_model_card_context(mid)
        ctx["use_case_classification_context"] = format_classification_context(
            _use_case, _size_class, _param_arch, _taxonomy
        )

        try:
            prompt = prompt_template.format(**ctx)
        except KeyError as e:
            print(f"⚠️ Fehlende Template-Variable {e} für {mid} — setze 'n/a'.")
            ctx[e.args[0]] = "n/a"
            prompt = prompt_template.format(**ctx)

        if getattr(args, "dry_run", False):
            print(f"  [DRY-RUN] Würde Tool-Use-Review für {mid} generieren.")
            continue

        print(f"🤖 Generiere Tool-Use-Review für {mid} mit {provider}/{model_id}...")
        try:
            response = client.query(
                model=model_id,
                prompt=prompt,
                provider=provider,
                temperature=0.7,
                max_tokens=max_tokens,
            )
        except Exception as e:
            print(f"❌ Fehler bei der Generierung für {mid}: {e}")
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = out_dir / f"tooluse_narrative_review_{timestamp}.md"
        display_time = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
        lines = response.splitlines()
        if lines:
            lines.insert(1, f"\n> **Erstellt am:** {display_time}\n")
        out_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"✅ Tool-Use-Review gespeichert unter: {out_file.relative_to(ROOT_DIR)}")


def _is_valid_audit_dir(path: Path) -> bool:
    """Prüft, ob ein Verzeichnis ein gültiges Audit-Log-Verzeichnis ist.

    Ein Verzeichnis zählt als Audit-Dir wenn EINES erfüllt ist:
      A) Es enthält mindestens eine Datei mit bekanntem Audit-Slug-Pattern:
         00_bias_report.md, cli\\d+\\.md, code_quality_\\d+\\.md,
         tooluse\\d+\\.md, documentation_quality_\\d+\\.md
      B) Der Ordnername sieht aus wie ein Modellname (slug-konform):
         länger als 4 Zeichen, enthält Bindestrich ODER Underscore,
         keine Punkte (Punkte werden in safe_name zu Underscores konvertiert).
         Schließt Stub-/Test-Ordner wie z.B. outputs/audit_logs/test/ aus.

    Pfad (B) ist nötig, damit Test-Fixtures mit leeren Audit-Dirs
    (z.B. model-a, model-b, gpt-5_4) durchlaufen ohne pro Modell eine
    dummy-Audit-Datei anlegen zu müssen.
    """
    if not path.is_dir():
        return False
    name = path.name
    # Heuristik B: Modellname-Pattern
    if (
        len(name) > 4
        and ("-" in name or "_" in name)
        and "." not in name
        and not name.startswith(".")
    ):
        return True
    # Heuristik A: bekannte Audit-Slug-Files
    audit_pattern = re.compile(
        r"^(00_bias_report|cli\d+|code_quality_\d+|tooluse\d+|documentation_quality_\d+)\.md$"
    )
    try:
        for f in path.iterdir():
            if f.is_file() and audit_pattern.match(f.name):
                return True
    except OSError:
        return False
    return False


def _run_per_model_all_reviews(
    args: argparse.Namespace,
    client: LLMClient,
    provider: str,
    model_id: str,
    max_tokens: int,
    csv_data: str,
) -> None:
    """Per-Model Iterationsmodus: für jedes Modell benchmark → bias → tooluse,
    erst dann nächstes Modell. Skip-Logik pro Review-Typ beibehalten.

    Verwendet die bestehenden _run_audit_reviews / _run_tooluse_reviews-Helfer
    mit einem überschriebenen args.model-Filter (safe_target_model dort).
    """
    audit_base_dir = ROOT_DIR / "outputs" / "audit_logs"
    if not audit_base_dir.exists():
        print("❌ Keine Audit-Logs gefunden.")
        return

    # Die Ordnernamen in outputs/audit_logs/ sind nach _safe_name normalisiert
    # (Punkt -> Underscore), identisch zu model_cards/ und docs/reviews/.
    # Wir verwenden sie hier sowohl als Slug (fuer out_dir-Pfade) als auch
    # als model_id (fuer audit_dir und Sub-Calls).
    slugs = sorted(
        d.name for d in audit_base_dir.iterdir()
        if _is_valid_audit_dir(d)
    )
    if not slugs:
        print("⚠️ Keine Modell-Verzeichnisse in outputs/audit_logs/ gefunden.")
        return

    if args.model:
        target_safe = _safe_name(args.model)
        if target_safe in slugs:
            slugs = [target_safe]
        else:
            print(f"⚠️ Modell '{args.model}' (slug: {target_safe}) nicht in outputs/audit_logs/ gefunden.")
            return

    print(f"📦 {len(slugs)} Modelle gefunden. Iteriere per Modell: Benchmark → PC-Bias → Tool-Use …\n")

    # Lade Webexport-Blacklist für Auto-Review-Skip
    blacklist = _load_webexport_blacklist() if args.auto else set()

    for idx, slug in enumerate(slugs, 1):
        # Webexport-Blacklist-Check: Modelle auf der Blacklist im Auto-Modus überspringen
        if args.auto and slug in blacklist:
            print(f"⏩ [{idx}/{len(slugs)}] {slug}: Auf Webexport-Blacklist → Review wird übersprungen.")
            continue

        print(f"\n{'=' * 64}")
        print(f"📦 MODELL [{idx}/{len(slugs)}]: {slug}")
        print(f"{'=' * 64}")

        # Unabhängige Namespace-Kopie mit überschriebenem --model,
        # damit _run_audit_reviews / _run_tooluse_reviews nur diesen Slug
        # verarbeiten (safe_target_model-Filter).
        model_args = argparse.Namespace(**vars(args))
        model_args.model = slug

        print(f"\n── {slug}: Schritt 1/2: Benchmark-Review ──")
        _run_audit_reviews(
            model_args, client, provider, model_id, max_tokens, csv_data,
            effective_type="benchmark",
        )

        print(f"\n── {slug}: Schritt 2/2: PC-Bias-Review ──")
        _run_audit_reviews(
            model_args, client, provider, model_id, max_tokens, "",
            effective_type="bias",
        )

    # Tooluse-Reviews werden NACH dem per-model-Loop generiert, weil tooluse_leaderboard.csv
    # Ollama-Format-IDs enthält (z.B. "gemma3:12b"), die nicht mit den audit_log-Slug-Namen
    # übereinstimmen (z.B. "gemma-3-12b-it"). Ein pro-Modell-Lookup würde immer fehlschlagen.
    # Mit model=None iteriert _run_tooluse_reviews über get_all_tooluse_model_ids() → korrekte IDs.
    print(f"\n── Tool-Use-Reviews (alle ausstehenden Einträge aus tooluse_leaderboard.csv) ──")
    tooluse_args = argparse.Namespace(**vars(args))
    tooluse_args.model = None  # Kein Slug-Filter — IDs kommen aus tooluse_leaderboard.csv
    _run_tooluse_reviews(tooluse_args, client, provider, model_id, max_tokens)

    print("\n✅ Per-Model-Reviews abgeschlossen.")


def _run_audit_reviews(
    args: argparse.Namespace,
    client: LLMClient,
    provider: str,
    model_id: str,
    max_tokens: int,
    csv_data: str,
    effective_type: str,
) -> None:
    """Benchmark- oder Bias-Reviews durch Iteration über outputs/audit_logs/ generieren."""
    audit_base_dir = ROOT_DIR / "outputs" / "audit_logs"
    if not audit_base_dir.exists():
        print("❌ Keine Audit-Logs gefunden.")
        return

    print(f"📁 Durchsuche Audit-Logs nach Modellen ({effective_type.upper()})...")
    found_models = False

    safe_target_model = _safe_name(args.model) if args.model else None
    
    # Lade Webexport-Blacklist für Auto-Review-Skip
    blacklist = _load_webexport_blacklist() if args.auto else set()

    _configured_safe_ids: set[str] = set()
    try:
        _cfg = load_config()
        for _p in list(_cfg.get("providers", {}).get("commercial", {}).values()) + list(_cfg.get("providers", {}).get("local", {}).values()):
            for _m in _p.get("models", []):
                _configured_safe_ids.add(_safe_name(_m["id"]))
    except Exception:
        pass

    for subdir in audit_base_dir.iterdir():
        if not _is_valid_audit_dir(subdir):
            continue
        # Defense in depth: vergleiche safe_name-normalisiert, damit auch
        # Audit-Dirs mit roher Schreibweise (z.B. "gpt-5.4" statt "gpt-5_4")
        # korrekt gematcht werden.
        if safe_target_model and _safe_name(subdir.name) != safe_target_model:
            continue
        
        # Webexport-Blacklist-Check: Modelle auf der Blacklist im Auto-Modus überspringen
        if args.auto and subdir.name in blacklist:
            print(f"⏩ {subdir.name}: Auf Webexport-Blacklist → Review wird übersprungen.")
            continue
        
        found_models = True

        # Heritage-ID-Fallback: prüfe ob subdir.name eine veraltete ID ist,
        # für die eine umbenannte Card mit heritage_ids existiert.
        # In diesem Fall wird die kanonische ID aus der neuen Card für alle
        # nachgelagerten Lookups (Card, Metriken, Output-Pfad) genutzt,
        # während die Audit-Log-Dateien weiterhin aus subdir gelesen werden.
        effective_model_id: str = subdir.name
        if not _find_card(subdir.name).exists():
            _heritage_path = find_card_by_heritage_id(subdir.name)
            if _heritage_path is not None:
                try:
                    _h_data = json.loads(_heritage_path.read_text(encoding="utf-8"))
                    _h_canonical = _h_data.get("model_id")
                    if isinstance(_h_canonical, str) and _h_canonical:
                        print(f"ℹ️ Heritage-ID: {subdir.name} → {_h_canonical}")
                        effective_model_id = _h_canonical
                except Exception:
                    pass

        # Nur warnen wenn kein Heritage-Fund — sonst wäre das ein False-Positive,
        # denn die alte Audit-Dir ist intentional unter dem veralteten Namen.
        if _configured_safe_ids and subdir.name not in _configured_safe_ids:
            if effective_model_id == subdir.name:  # kein Heritage-Fund
                if not re.search(r"-\d{8}$|-\d{6}$", subdir.name):
                    print(f"⚠️  Verzeichnis '{subdir.name}' entspricht keiner konfigurierten Modell-ID — mögliches Duplikat.")

        if effective_type == "benchmark":
            bench_files = [
                f for f in subdir.iterdir()
                if f.is_file() and f.name != "00_bias_report.md" and not f.name.startswith("tooluse")
            ]
            if not bench_files:
                print(f"⏩ {subdir.name}: Nur PC-Bias-Report vorhanden, keine Benchmark-Logs – überspringe.")
                continue

        if args.auto and not getattr(args, "force", False):
            review_prefix = "bias_review" if effective_type == "bias" else "review"
            review_out_dir = ROOT_DIR / "docs" / "reviews" / _safe_name(subdir.name)
            existing_reviews = sorted(review_out_dir.glob(f"{review_prefix}_*.md")) if review_out_dir.exists() else []
            if existing_reviews:
                latest_review_mtime = existing_reviews[-1].stat().st_mtime
                if effective_type == "benchmark":
                    # Nur Modul-Reports: kein 00_bias_report.md, kein tooluse*.md
                    audit_files = [
                        f for f in subdir.iterdir()
                        if f.is_file() and f.name != "00_bias_report.md" and not f.name.startswith("tooluse")
                    ]
                else:
                    # bias: nur 00_bias_report.md
                    audit_files = [f for f in subdir.iterdir() if f.is_file() and f.name == "00_bias_report.md"]
                latest_audit_mtime = max((f.stat().st_mtime for f in audit_files), default=0)
                if latest_review_mtime >= latest_audit_mtime:
                    print(f"⏩ Review für {subdir.name} aktuell – überspringe.")
                    continue

        if effective_type == "benchmark":
            dep_context = _ensure_dependencies(
                model_id=effective_model_id,
                client=client,
                card_provider=provider,
                card_model=model_id,
                auto_mode=args.auto,
                dry_run=args.dry_run,
            )
            if dep_context is None:
                continue
            if args.dry_run:
                continue

        if getattr(args, "dry_run", False):
            print(f"  [DRY-RUN] Würde {effective_type}-Review für {subdir.name} generieren.")
            continue

        process_model_review(
            subdir, csv_data, client, provider, model_id, effective_type, max_tokens,
            canonical_model_id=effective_model_id if effective_model_id != subdir.name else None,
        )

    if not found_models:
        print("⚠️ Keine Audit-Logs für das spezifizierte Modell gefunden.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generiert qualitative LLM-Reviews basierend auf den Audit-Logs.")
    parser.add_argument("-m", "--model", type=str, help="Nur dieses Modell reviewen")
    parser.add_argument("-a", "--all", action="store_true", help="Alle Modelle reviewen")
    parser.add_argument(
        "-t", "--type",
        type=str,
        choices=["benchmark", "bias", "provider", "tooluse", "all"],
        default="benchmark",
        help="Review-Typ: benchmark (Standard), bias (PC), tooluse, provider oder all (benchmark+bias+tooluse).",
    )
    parser.add_argument("--auto", action="store_true", help="Fehlende Cards automatisch generieren")
    parser.add_argument("--force", action="store_true", help="Neugenerierung erzwingen")
    parser.add_argument("--dry-run", action="store_true", help="Nur fehlende Cards anzeigen, nichts generieren")
    parser.add_argument(
        "--per-model",
        action="store_true",
        help="Nur mit --type all: pro Modell benchmark → bias → tooluse sequenziell, "
             "erst dann nächstes Modell (Default: batch-by-type).",
    )
    args = parser.parse_args()

    if not args.model and not args.all and args.type not in ("provider", "all"):
        print("❌ Bitte gib ein Modell an (-m <modell>) oder nutze --all für alle Modelle.")
        sys.exit(1)

    if args.per_model and args.type != "all":
        print("❌ --per-model ist nur mit --type all erlaubt.")
        sys.exit(1)

    if args.per_model and not (args.all or args.model):
        print("❌ --per-model benötigt --all oder --model.")
        sys.exit(1)

    print(f"📰 Starte Meta-Reviewer Auswertung ({args.type.upper()}-Modus)...")

    config = load_config()
    client = LLMClient(config=config)
    review_config = config.get("llm_review", {}).get("provider", {})
    provider = review_config.get("name", "google")
    model_id = review_config.get("model", "gemini-2.5-pro")
    review_max_tokens = review_config.get("max_tokens", 8192)

    if not provider or not model_id:
        print("⚠️ Warnung: 'llm_review' Konfiguration fehlt in benchmark_config.yaml, nutze Google Gemini als Fallback.")
        provider = "google"
        model_id = "gemini-2.5-pro"

    print(f"🔧 Konfigurierter Reviewer: {provider}/{model_id}")

    if args.type == "provider":
        print("📊 Lade Provider Leaderboard...")
        csv_path = ROOT_DIR / "benchmark_scores" / "provider_leaderboard.csv"
        if not csv_path.exists():
            print("❌ provider_leaderboard.csv nicht gefunden. Bitte erst generate_vendor_stats.py ausführen.")
            return

        csv_data = csv_path.read_text(encoding="utf-8")
        with open(ROOT_DIR / "config" / "meta_reviewer_prompt.yaml", "r", encoding="utf-8") as f:
            prompt_config = yaml.safe_load(f)

        prompt = prompt_config.get("provider_reviewer", {}).get("system_instructions", "")
        if not prompt:
            prompt = prompt_config.get("meta_reviewer", {}).get("provider_reviewer", {}).get("system_instructions", "")

        if not prompt:
            print("❌ Fehler: 'provider_reviewer' Prompt in config/meta_reviewer_prompt.yaml nicht gefunden.")
            return

        prompt = prompt.replace("{csv_data}", csv_data)
        print("🧠 Generiere Provider Landscape Report...")
        try:
            response = client.query(model=model_id, prompt=prompt, provider=provider, temperature=0.7)
            out_file = ROOT_DIR / "docs" / "reviews" / "provider_landscape_review.md"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(response, encoding="utf-8")
            print(f"✅ Provider Review gespeichert unter: {out_file.relative_to(ROOT_DIR)}")
        except Exception as e:
            print(f"❌ Fehler bei der Generierung: {e}")
        return

    if args.type == "tooluse":
        _run_tooluse_reviews(args, client, provider, model_id, review_max_tokens)
        print("\n✅ Tool-Use-Reviews abgeschlossen.")
        return

    if args.type == "all":
        if args.per_model:
            _run_per_model_all_reviews(
                args, client, provider, model_id, review_max_tokens, collect_data()
            )
            return
        print("\n── Schritt 1/3: Benchmark-Reviews ──")
        _run_audit_reviews(args, client, provider, model_id, review_max_tokens, collect_data(), effective_type="benchmark")
        print("\n── Schritt 2/3: PC-Bias-Reviews ──")
        _run_audit_reviews(args, client, provider, model_id, review_max_tokens, "", effective_type="bias")
        print("\n── Schritt 3/3: Tool-Use-Reviews ──")
        _run_tooluse_reviews(args, client, provider, model_id, review_max_tokens)
        print("\n✅ Alle Reviews abgeschlossen.")
        return

    # benchmark oder bias
    csv_data = collect_data() if args.type == "benchmark" else ""
    _run_audit_reviews(args, client, provider, model_id, review_max_tokens, csv_data, effective_type=args.type)
    print("\n✅ Reviews abgeschlossen.")


if __name__ == "__main__":
    main()
