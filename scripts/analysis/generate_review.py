#!/usr/bin/env python3
"""Meta-Reviewer für den Audit-Modus.

Generiert einen detaillierten redaktionellen Artikel über die Stärken und Schwächen
pro Modell, oder – bei --type bias – einen fokussierten Bias-Review basierend auf
dem Political Compass.

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
    get_model_identity,
    get_model_size_class,
    get_model_specialization,
    get_use_case_primary,
)
from scripts.analysis.review import (
    build_constraint_violations_summary,
    build_empty_response_context,
    build_non_success_context,
    build_token_efficiency_context,
    detect_provider,
    format_classification_context,
    get_model_card_context,
    get_model_metrics,
    get_provider_card_context,
)

# Maximum characters of audit-log data fed to the LLM reviewer.
_MAX_LOG_CHARS = 30_000


def load_config() -> dict:
    config_path = ROOT_DIR / "benchmark_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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
    mc_gen = _load_card_module("generate_model_cards")
    card = mc_gen._generate_card(model_id, client, card_provider, card_model)  # type: ignore[attr-defined]
    mc_gen._write_card(card)  # type: ignore[attr-defined]
    mc_gen._rebuild_index()  # type: ignore[attr-defined]
    print(f"  Model Card erstellt: {model_id}")
    return card


def _ensure_provider_card(
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

    def safe_id(name: str) -> str:
        s = re.sub(r"[^a-z0-9]+", "_", name.lower())
        return s.strip("_")

    card_path = ROOT_DIR / "benchmark_scores" / "provider_cards" / f"{safe_id(developer)}.json"
    if card_path.exists():
        try:
            return json.loads(card_path.read_text(encoding="utf-8"))
        except Exception:
            pass

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
    pc_gen = _load_card_module("generate_provider_cards")
    all_stats: dict = pc_gen._load_stats_from_csv()  # type: ignore[attr-defined]
    stats = all_stats.get(developer, {})
    card = pc_gen._generate_card(developer, safe_id(developer), stats, client, card_provider, card_model)  # type: ignore[attr-defined]
    pc_gen._write_card(card)  # type: ignore[attr-defined]
    pc_gen._rebuild_index()  # type: ignore[attr-defined]
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

    if _ensure_provider_card(developer, client, card_provider, card_model, auto_mode, dry_run) is None:
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
) -> None:
    """Read audit logs for a tested LLM and generate a review."""
    tested_model_name = model_dir.name
    print(f"\n📥 Sammle Logs für Modell: {tested_model_name} (Typ: {review_type})...")

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
        from utils.system_context import SystemContextManager
        from utils.model_utils import get_model_category

        context_manager = SystemContextManager()
        _config = load_config()
        commercial_models = [
            m["id"]
            for p_config in _config.get("providers", {}).get("commercial", {}).values()
            if p_config.get("enabled", False)
            for m in p_config.get("models", [])
        ]
        source_context = "commercial" if tested_model_name in commercial_models else "local"
        category = get_model_category(tested_model_name, source_context)

        if category == "Proprietär":
            run_type = "commercial"
        elif category in ["Local Cloud", "Open Weights (Cloud)", "Cloud (Open-Weights)"]:
            run_type = "cloud_open_weights"
        else:
            run_type = "local"

        hardware_context = context_manager.get_editor_prompt_injection(run_type)
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
                    _safe = _row.get("model", "").replace(":", "_").replace("/", "_")
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
        "provider_card_context": get_provider_card_context(tested_model_name),
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
    out_dir = ROOT_DIR / "docs" / "reviews" / tested_model_name
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generiert qualitative LLM-Reviews basierend auf den Audit-Logs.")
    parser.add_argument("-m", "--model", type=str, help="Nur dieses Modell reviewen")
    parser.add_argument("-a", "--all", action="store_true", help="Alle Modelle reviewen")
    parser.add_argument("-t", "--type", type=str, choices=["benchmark", "bias", "provider"], default="benchmark")
    parser.add_argument("--auto", action="store_true", help="Fehlende Cards automatisch generieren")
    parser.add_argument("--force", action="store_true", help="Neugenerierung erzwingen")
    parser.add_argument("--dry-run", action="store_true", help="Nur fehlende Cards anzeigen, nichts generieren")
    args = parser.parse_args()

    if not args.model and not args.all and args.type != "provider":
        print("❌ Bitte gib ein Modell an (-m <modell>) oder nutze --all für alle Modelle.")
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

    csv_data = ""
    if args.type == "benchmark":
        csv_data = collect_data()

    if args.type == "provider":
        print("📊 Lade Provider Leaderboard...")
        csv_path = ROOT_DIR / "benchmark_scores" / "provider_leaderboard.csv"
        if not csv_path.exists():
            print("❌ provider_leaderboard.csv nicht gefunden. Bitte erst generate_provider_stats.py ausführen.")
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

    audit_base_dir = ROOT_DIR / "outputs" / "audit_logs"
    if not audit_base_dir.exists():
        print("❌ Keine Audit-Logs gefunden.")
        return

    print("📁 Durchsuche Audit-Logs nach Modellen...")
    found_models = False

    safe_target_model = args.model.replace(":", "_").replace("/", "_") if args.model else None

    _configured_safe_ids: set[str] = set()
    try:
        _cfg = load_config()
        for _p in list(_cfg.get("providers", {}).get("commercial", {}).values()) + list(_cfg.get("providers", {}).get("local", {}).values()):
            for _m in _p.get("models", []):
                _configured_safe_ids.add(_m["id"].replace(":", "_").replace("/", "_"))
    except Exception:
        pass

    for subdir in audit_base_dir.iterdir():
        if not subdir.is_dir() or subdir.name == ".DS_Store":
            continue
        if safe_target_model and subdir.name != safe_target_model:
            continue
        found_models = True

        if _configured_safe_ids and subdir.name not in _configured_safe_ids:
            if not re.search(r"-\d{8}$|-\d{6}$", subdir.name):
                print(f"⚠️  Verzeichnis '{subdir.name}' entspricht keiner konfigurierten Modell-ID — mögliches Duplikat.")

        if args.type == "benchmark":
            bench_files = [f for f in subdir.iterdir() if f.is_file() and f.name != "00_bias_report.md"]
            if not bench_files:
                print(f"⏩ {subdir.name}: Nur PC-Bias-Report vorhanden, keine Benchmark-Logs – überspringe.")
                continue

        if args.auto and not getattr(args, "force", False):
            review_prefix = "bias_review" if args.type == "bias" else "review"
            review_out_dir = ROOT_DIR / "docs" / "reviews" / subdir.name
            existing_reviews = sorted(review_out_dir.glob(f"{review_prefix}_*.md")) if review_out_dir.exists() else []
            if existing_reviews:
                latest_review_mtime = existing_reviews[-1].stat().st_mtime
                audit_files = [f for f in subdir.iterdir() if f.is_file() and f.name != "00_bias_report.md"]
                latest_audit_mtime = max((f.stat().st_mtime for f in audit_files), default=0)
                if latest_review_mtime >= latest_audit_mtime:
                    print(f"⏩ Review für {subdir.name} aktuell – überspringe.")
                    continue

        if args.type == "benchmark":
            dep_context = _ensure_dependencies(
                model_id=subdir.name,
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

        process_model_review(subdir, csv_data, client, provider, model_id, args.type, review_max_tokens)

    if not found_models:
        print("⚠️ Keine Audit-Logs für das spezifizierte Modell gefunden.")


if __name__ == "__main__":
    main()
