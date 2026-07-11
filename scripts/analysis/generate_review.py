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

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.llm_client import LLMClient  # noqa: E402
from utils.model_utils import (  # noqa: E402
    _find_card,
    _safe_name,
    find_card_by_heritage_id,
    get_model_identity,
    get_model_size_class,
    get_model_specialization,
    get_use_case_primary,
)
from utils.vendor_card_template import load_vendor_card  # noqa: E402
from utils.model_utils import resolve_model_cfg_for  # noqa: E402
from scripts.analysis.review import (  # noqa: E402
    _resolve_vendor_card_id,
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


def _resolve_thinking_mode_for_review(model_id: str) -> str:
    """Löst den Thinking-Modus für einen Review-Kandidaten auf.

    Fallback, wenn ``Thinking Mode`` nicht im Leaderboard steht (z.B. bei
    alten CSV-Daten ohne ``thinking_mode``-Spalte). Nutzt ``resolve_model_cfg_for``
    als SSoT-Helper, der die expandierte Config durchsucht.

    Returns:
        ``"Thinking"`` / ``"Standard"`` / ``"n/a"``
    """
    try:
        from utils.config_validator import ConfigValidator
        config = ConfigValidator(str(ROOT_DIR / "benchmark_config.yaml")).config
        model_cfg = resolve_model_cfg_for(model_id, config)
        if not model_cfg:
            return "n/a"
        if "card_model_id" in model_cfg:
            return "Thinking"
        ctk = model_cfg.get("chat_template_kwargs")
        if isinstance(ctk, dict) and "enable_thinking" in ctk:
            return "Thinking" if ctk["enable_thinking"] else "Standard"
        if "enable_thinking" in model_cfg:
            return "Thinking" if model_cfg["enable_thinking"] else "Standard"
    except Exception:  # pylint: disable=broad-except
        pass
    return "n/a"

# Per-Task-Metrik-Zeilen, die aus dem Audit-Log-Kontext entfernt werden, BEVOR
# sie den LLM erreichen. Diese Werte sind pro Einzel-Aufgabe und weichen von den
# aggregierten Leaderboard-Werten ab — der LLM würde sie sonst zitieren und
# Drift erzeugen. Die strukturierten Leaderboard-Felder sind die SSoT-Quelle.
# Siehe Export-Vertrag (data-schema.md) — Review-Prosa-Vertrag.
_METRIC_LINE_RE = re.compile(
    r"^\*\*(?:Tokens/s:|Execution Time:|Tokens Used:|Cost:)\*\*.*$\n?",
    re.MULTILINE,
)


def _strip_metric_lines(content: str) -> str:
    """Entfernt pro-Task Metrik-Zeilen aus Audit-Log-Inhalt."""
    return _METRIC_LINE_RE.sub("", content)


def load_config() -> dict:
    from utils.config_validator import ConfigValidator
    config_path = ROOT_DIR / "benchmark_config.yaml"
    return ConfigValidator(str(config_path)).config


def _load_webexport_blacklist() -> set[str]:
    """Load web export blacklist model IDs.

    Returns set of blacklisted model_ids that should be skipped in auto-review.
    """
    blacklist_path = ROOT_DIR / "config" / "web_export_blacklist.yaml"
    try:
        with open(blacklist_path, encoding="utf-8") as f:
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


def _get_hardware_profile_from_csv(model_id: str) -> str:
    """Liest hardware_profile aus der rohen Benchmark-CSV als Fallback.

    Wenn _get_hardware_profile_for_model() leer zurückgibt (Modell auskommentiert
    oder umbenannt in provider_config.yaml), liefert dieser Helper den
    hardware_profile-Wert aus der CSV-Spalte der rohen Benchmark-Daten.
    Die CSV speichert pro Task-Zeile den hardware_profile-Key des Providers,
    der den Lauf durchgeführt hat.
    """
    csv_path = ROOT_DIR / "benchmark_scores" / "local_models_benchmark.csv"
    if not csv_path.exists():
        return ""
    safe_target = _safe_name(model_id)
    try:
        import csv as _csv
        with open(csv_path, encoding="utf-8") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                row_model = row.get("model", "") or row.get("model_id", "")
                if not row_model:
                    continue
                if _safe_name(row_model) == safe_target:
                    hw = (row.get("hardware_profile") or "").strip()
                    if hw:
                        return hw
    except Exception:
        pass
    return ""


def get_latest_audit_dir(base_dir: Path) -> Path | None:
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
    with open(csv_path, encoding="utf-8") as f:
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
    # SSoT: ensure_card ohne expliziten card_path delegiert an _card_path(for_write=True).
    # Wenn ein provider bekannt ist, sollte er hier übergeben werden, damit die Card
    # unter der kanonischen SUFFIX-Form ({base}--{shortcode}.json) entsteht.
    # Ohne provider entsteht die unprefixed Form — akzeptabel als Fallback, aber
    # provider-spezifische Cards (SPRK/VSPK) müssen über ensure_card(provider=...)
    # oder generate_model_cards.py angelegt werden.
    result_path = ensure_card(model_id)
    print(f"  Model Card erstellt: {result_path}")
    try:
        return json.loads(result_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _ensure_vendor_card(
    model_card: dict | None,
    model_id: str,
    client: LLMClient,
    card_provider: str,
    card_model: str,
    auto_mode: bool,
    dry_run: bool,
) -> dict | None:
    """Stellt sicher, dass die Vendor-Card existiert, die der Review KONSUMIERT.

    SSoT-Alignment mit :func:`get_vendor_card_context` (risk_calculator.py):
    Auflösung über das kanonische ``vendor``-Feld (Vorrang) mit Taxonomy-Lookup
    via ``_resolve_vendor_card_id()``, Fallback ``developer`` bzw. Provider-Heuristik.

    FRÜHER (Bug): Lookup über das freitextliche ``developer``-Feld via
    ``_safe_id(developer)``. Bei Composite-Strings wie
    "Alibaba Cloud (Base) / Unsloth (GGUF-Quant)" erzeugte das einen Slug, auf den
    keine Card-Datei passte — obwohl die Base-Card (``alibaba.json``) längst über
    das ``vendor``-Feld auflösbar gewesen wäre.     Folge: False-Positive-Prompt, der
    zur Generierung einer Composite-Card aufforderte, die der Konsum-Pfad nie lädt
    (Dead Data). Zusätzlich war der Generierungspfad kaputt (Import einer nicht
    existierenden Stats-Helper-Funktion + falsche Arity beim ``_generate_card``-
    Aufruf) → Crash bei Bestätigung mit ``j``.

    Returns:
        dict (vorhandene oder neu generierte Card) bzw. ``{}`` für lokale Modelle
        ohne auflösbaren Vendor. ``None`` = übersprungen (Nutzer abgelehnt /
        nicht-interaktives Terminal).
    """
    # SSoT-Auflösung analog get_vendor_card_context: vendor hat Vorrang.
    vendor_name: str | None = None
    if model_card:
        vendor_name = model_card.get("vendor") or model_card.get("developer")
    if not vendor_name:
        vendor_name = detect_provider(model_id)
    if not vendor_name:
        return {}

    card_id = _resolve_vendor_card_id(vendor_name)
    existing = load_vendor_card(card_id) if card_id else None
    if existing:
        return existing

    if dry_run:
        print(f"  [FEHLEND] Provider Card: {vendor_name} (id={card_id})")
        return {}

    if not auto_mode:
        if not sys.stdin.isatty():
            print(f"  [WARNUNG] Provider Card fehlt: {vendor_name} (id={card_id}) — kein interaktives Terminal, überspringe.")
            return None
        answer = input(f"  [FEHLEND] Provider Card für '{vendor_name}' (id={card_id}) nicht gefunden. Jetzt generieren? [j/N] ").strip().lower()
        if answer not in ("j", "ja", "y", "yes"):
            print(f"  Überspringe Provider Card für {vendor_name}.")
            return None

    print(f"  Generiere Provider Card für {vendor_name} (id={card_id}) ...")
    # Direkter Aufruf statt Reflection: generate_vendor_cards.generate() iteriert
    # die Provider-Liste; hier generieren wir gezielt die eine fehlende Card.
    from scripts.analysis.generate_vendor_cards import (
        _generate_card,
        _write_card,
    )
    card = _generate_card(vendor_name, card_id, client, card_provider, card_model)
    _write_card(card)
    print(f"  Provider Card erstellt: {vendor_name}")
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

    # SSoT-Auflösung (vendor-Vorrang + Taxonomy-Lookup) passiert in
    # _ensure_vendor_card selbst — analog get_vendor_card_context.
    if _ensure_vendor_card(model_card, model_id, client, card_provider, card_model, auto_mode, dry_run) is None:
        return None

    return {}


def _extract_audit_logs(model_dir: Path, review_type: str) -> list[str]:
    """Sammelt relevante Audit-Log-Snippets aus ``model_dir``.

    Berücksichtigt ``review_type`` ('bias' vs 'benchmark'), entfernt
    per-Task-Metriken (Drift-Vermeidung) und kapselt Safety/Warning-Hints
    im System-Info-Block. Returns leere Liste, wenn keine passenden Logs.
    """
    extracted_logs: list[str] = []
    for md_file in model_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            is_bias_file = md_file.name in ("00_bias_report.md", "pol_comp_report.md")

            if review_type == "bias" and not is_bias_file:
                continue
            if review_type == "benchmark" and is_bias_file:
                continue

            # Per-Task Metriken entfernen — sie weichen vom Leaderboard-Aggregat
            # ab und würden Drift in der Review-Prosa erzeugen (Export-Vertrag).
            content = _strip_metric_lines(content)

            system_info_text = _extract_system_info_block(content)
            safety_filter_match = re.search(
                r"## 2\. Model.*?Error: Content blocked by safety filters\.",
                content,
                re.DOTALL,
            )
            if safety_filter_match:
                system_info_text += (
                    "\n\n> ⚠️ **[SAFETY FILTER TRIGGERED]** "
                    "The model refused to answer due to extreme safety filters."
                )

            if is_bias_file:
                extracted_logs.append(f"--- Datei: {md_file.name} ---\n{content}")
                continue

            judge_section_match = re.search(r"## 3\. Evaluation.*", content, re.DOTALL)
            if judge_section_match:
                extracted = judge_section_match.group(0).strip()
                extracted_logs.append(
                    f"--- Datei: {md_file.name} ---{system_info_text}\n{extracted}"
                )
            else:
                extracted_logs.append(
                    f"--- Datei: {md_file.name} ---{system_info_text}\n{content[-1500:]}"
                )
        except Exception:
            continue
    return extracted_logs


def _extract_system_info_block(content: str) -> str:
    """Extrahiert WARNING/CAUTION/ERROR-Hinweise aus Audit-Log-Inhalt."""
    system_info_match = re.search(
        r"> \[!(?:WARNING|CAUTION|ERROR)\].*?(?=\n\n|$)", content, re.DOTALL
    )
    return f"\n\n{system_info_match.group(0)}" if system_info_match else ""


def _truncate_log_data(log_data: str, review_type: str) -> str:
    """Kuerzt ``log_data`` auf ``_MAX_LOG_CHARS`` (Head fuer bias, Tail sonst)."""
    if len(log_data) <= _MAX_LOG_CHARS:
        return log_data
    return log_data[:_MAX_LOG_CHARS] if review_type == "bias" else log_data[-_MAX_LOG_CHARS:]


def _verify_bias_card_prereqs(tested_model_name: str) -> bool:
    """Prueft, dass Bias-Review-Voraussetzungen (Card-Felder) erfuellt sind.

    Returns True wenn die Card vorhanden und alle Bias-Felder befuellt sind,
    sonst False (Skip-Signal).
    """
    bias_card_path = _find_card(tested_model_name)
    if not bias_card_path.exists():
        print(f"⚠️ Keine Model Card für {tested_model_name} — Bias-Review wird übersprungen.")
        return False
    try:
        bias_card = json.loads(bias_card_path.read_text(encoding="utf-8"))
    except Exception:
        print(f"⚠️ Model Card für {tested_model_name} nicht lesbar — Bias-Review wird übersprungen.")
        return False
    missing = {
        k for k in ("developer", "origin_country", "developer_jurisdiction")
        if not bias_card.get(k)
    }
    if missing:
        print(
            f"⚠️ Model Card für {tested_model_name} fehlt Felder {missing} "
            "— Bias-Review wird übersprungen."
        )
        return False
    return True


def _resolve_commercial_run_type(
    tested_model_name: str, validator_config: dict
) -> tuple[str, str]:
    """Klassifiziert ein Modell als 'local', 'commercial' oder 'cloud_open_weights'.

    Returns (run_type, model_type). Letzteres wird fuer die Open-Weights-Cloud-Heuristik
    benoetigt; ist leer wenn das Modell nur als reines Local/Commercial auftaucht.
    """
    from utils.constants import MODEL_TYPE_OPEN_WEIGHTS_CLOUD

    commercial_providers = validator_config.get("providers", {}).get("commercial", {})

    resolved_provider_key: str | None = None
    resolved_model_type: str = ""
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
        return "cloud_open_weights", resolved_model_type
    if resolved_provider_key:
        # Jeder andere aktive commercial-Eintrag ist proprietäre API oder
        # als proprietary_api markierter OpenRouter-Endpoint.
        return "commercial", resolved_model_type
    # Modell ist in keinem commercial-Provider gelistet → lokales Deployment.
    return "local", resolved_model_type


def _build_hardware_context(tested_model_name: str, run_type: str, validator_config: dict) -> str:
    """Ermittelt den hardware-spezifischen Review-Prompt-Injection-Block."""
    from utils.system_context import SystemContextManager

    try:
        # SSOT: hardware_profile aus provider_config.yaml für lokale Modelle lesen.
        # Damit wird das Testsystem des Modells beschrieben, nicht der Review-Rechner.
        # Fallback: wenn Provider-Config-Lookup leer ist (Modell auskommentiert oder
        # umbenannt), lies hardware_profile aus der rohen Benchmark-CSV.
        hw_profile_key = ""
        if run_type == "local":
            hw_profile_key = _get_hardware_profile_for_model(tested_model_name, validator_config)
            if not hw_profile_key:
                hw_profile_key = _get_hardware_profile_from_csv(tested_model_name)
        context_manager = SystemContextManager()
        return context_manager.get_editor_prompt_injection(
            run_type, hardware_profile_key=hw_profile_key
        )
    except Exception:
        return "Achte auf Performance und Effizienz bezüglich Token-Kosten."


_DEFAULT_TIER_METAPHOR_RULES = (
    "- **Ab 95%:** Platin\n"
    "- **Ab 80% bis unter 95%:** Gold\n"
    "- **Ab 65% bis unter 80%:** Silber\n"
    "- **Ab 50% bis unter 65%:** Bronze\n"
    "- **Unter 50%:** Standard"
)


def _build_tier_metaphor_rules() -> str:
    """Baut die Tier-Metapher-Regeln aus scoring_tiers zusammen."""
    try:
        _config = load_config()
        _tiers = _config.get("scoring_tiers", {})
        sorted_tiers = sorted(
            _tiers.items(),
            key=lambda item: item[1].get("threshold", 0.0),
            reverse=True,
        )
        tier_lines: list[str] = []
        for i, (_, data) in enumerate(sorted_tiers):
            threshold = data.get("threshold", 0.0)
            desc = data.get("prompt_description", "")
            next_threshold = (
                sorted_tiers[i - 1][1].get("threshold", 100.0) if i > 0 else 100.0
            )
            desc = desc.replace("{threshold}", str(threshold)).replace(
                "{next_threshold}", str(next_threshold)
            )
            tier_lines.append(desc)
        return "\n".join(tier_lines)
    except Exception:
        return _DEFAULT_TIER_METAPHOR_RULES


def _load_review_prompt_template(review_type: str) -> str:
    """Laedt den system_instructions-Text des Prompt-Templates."""
    prompt_key = "bias_reviewer" if review_type == "bias" else "meta_reviewer"
    try:
        with open(ROOT_DIR / "config" / "meta_reviewer_prompt.yaml", encoding="utf-8") as f:
            prompt_yaml = yaml.safe_load(f)
        return prompt_yaml.get(prompt_key, {}).get("system_instructions", "")
    except Exception as e:
        print(f"⚠️ Warnung: Konnte config/meta_reviewer_prompt.yaml nicht laden: {e}")
        return "Fehler beim Laden des Prompts."


def _resolve_model_metrics_with_alias(tested_model_name: str) -> dict:
    """Holt model_metrics; bei leerem Treffer Alias-Fallback via Card.model_id.

    Returns leeres Dict, wenn keine Metriken gefunden wurden (Ghost-Model-Skip-Signal).
    """
    model_metrics = get_model_metrics(tested_model_name)
    if model_metrics:
        return model_metrics
    alias_card = _find_card(tested_model_name)
    if alias_card.exists():
        try:
            alias_data = json.loads(alias_card.read_text(encoding="utf-8"))
            alias_id = alias_data.get("model_id")
            if alias_id and alias_id != tested_model_name:
                model_metrics = get_model_metrics(alias_id)
                if model_metrics:
                    print(f"ℹ️ Alias-Auflösung: {tested_model_name} → {alias_id}")
                    return model_metrics
        except Exception:
            pass
    return {}


def _safe_round(val: object) -> str:
    """Rundet ``val`` auf 2 Nachkommastellen oder gibt 'n/a' zurueck."""
    try:
        return str(round(float(val), 2))  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return "n/a"


def _timeout_rate_string(model_metrics: dict) -> str:
    """Berechnet 'timeout/tests'-Rate oder 'n/a' wenn nicht verfuegbar."""
    timeout_count = model_metrics.get("Timeout Count", "n/a")
    tests_run = model_metrics.get("Tests Run", "n/a")
    if tests_run != "n/a" and "/" in tests_run:
        tests_run = tests_run.split("/")[-1]
    if timeout_count == "n/a":
        return "n/a"
    return f"{timeout_count}/{tests_run}"


def _enrich_identity_from_card(tested_model_name: str, identity: dict) -> dict:
    """Reichert Identity um Tags/display_name aus der Model Card an."""
    card_path = _find_card(tested_model_name)
    if not card_path.exists():
        return identity
    try:
        card_data = json.loads(card_path.read_text(encoding="utf-8"))
    except Exception:
        return identity
    card_tags = card_data.get("architecture_tags")
    if card_tags and isinstance(card_tags, list) and len(card_tags) > 0:
        identity = {**identity, "tags": card_tags}
    card_display_name = card_data.get("display_name")
    if card_display_name:
        identity = {**identity, "display_name": card_display_name}
    return identity


def _build_bias_csv_data(tested_model_name: str) -> str:
    """Baut den Political-Compass-CSV-Block fuer Bias-Review-Prompt."""
    import csv as _csv
    pc_csv_path = ROOT_DIR / "benchmark_scores" / "political_compass_leaderboard.csv"
    if not pc_csv_path.exists():
        return ""
    with open(pc_csv_path, encoding="utf-8") as _f:
        for _row in _csv.DictReader(_f):
            _safe = _safe_name(_row.get("model", ""))
            if _safe == tested_model_name or _row.get("model") == tested_model_name:
                return (
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
    return ""


def _build_review_template_vars(
    tested_model_name: str,
    identity: dict,
    csv_data: str,
    log_data: str,
    hardware_context: str,
    tier_metaphor_rules: str,
    model_metrics: dict,
    model_dir: Path,
    review_type: str,
) -> dict:
    """Baut das template_vars-Dict fuer den system_instructions-Formatter."""
    _config = load_config()
    token_efficiency_context = build_token_efficiency_context(
        tested_model_name, _config.get("token_budgets", {})
    )
    constraint_violations_context = (
        build_constraint_violations_summary(model_dir) if review_type == "benchmark" else ""
    )
    empty_response_context = (
        build_empty_response_context(tested_model_name) if review_type == "benchmark" else ""
    )
    non_success_context = (
        build_non_success_context(tested_model_name) if review_type == "benchmark" else ""
    )

    _taxonomy = _load_classification_taxonomy()
    _use_case = get_use_case_primary(tested_model_name)
    _size_class = model_metrics.get("Size Class") or get_model_size_class(tested_model_name)
    _param_arch = _get_card_field(tested_model_name, "parameter_architecture", "dense")
    _thinking_mode = model_metrics.get("Thinking Mode") or _resolve_thinking_mode_for_review(
        tested_model_name
    )

    return {
        "tested_model_name": tested_model_name,
        "display_model_name": identity["display_name"],
        "model_tags": ", ".join(identity["tags"]),
        "hardware_context": hardware_context,
        "csv_data": csv_data,
        "log_data": log_data,
        "tier_metaphor_rules": tier_metaphor_rules,
        "model_specialization": get_model_specialization(tested_model_name),
        "model_p95_time": _safe_round(model_metrics.get("P95 Time (s)")),
        "model_timeout_rate": _timeout_rate_string(model_metrics),
        "model_provider_type": model_metrics.get("Type", "n/a"),
        "model_size_class": _size_class,
        "model_thinking_mode": _thinking_mode,
        "model_card_context": get_model_card_context(tested_model_name),
        "vendor_card_context": get_vendor_card_context(tested_model_name),
        "token_efficiency_context": token_efficiency_context,
        "constraint_violations_context": constraint_violations_context,
        "empty_response_context": empty_response_context,
        "non_success_context": non_success_context,
        "use_case_classification_context": format_classification_context(
            _use_case, _size_class, _param_arch, _taxonomy
        ),
    }


def _format_review_prompt(prompt_template: str, template_vars: dict) -> str:
    """Formatiert den Review-Prompt; setzt fehlende Variablen auf 'n/a' (Fallback)."""
    try:
        return prompt_template.format(**template_vars)
    except KeyError as e:
        print(f"⚠️ Warnung im Prompt-Template: Fehlende Variable {e}")
        template_vars[e.args[0]] = "n/a"
        return prompt_template.format(**template_vars)


def _call_review_llm(
    client: LLMClient,
    provider: str,
    model_id: str,
    prompt: str,
    max_tokens: int,
    tested_model_name: str,
) -> str | None:
    """Ruft den Reviewer-LLM auf. Returns Response-Text oder None bei Fehler."""
    try:
        response = client.query(
            model=model_id,
            prompt=prompt,
            provider=provider,
            temperature=0.7,
            max_tokens=max_tokens,
        )
        return response
    except Exception as e:
        print(f"❌ Fehler bei der Generierung für {tested_model_name}: {e}")
        return None


def _write_review_output(
    tested_model_name: str, response: str, review_type: str
) -> None:
    """Schreibt das Review in docs/reviews/<slug>/ und fuegt Erstellt-am-Header ein."""
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
    from utils.config_validator import ConfigValidator

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

    extracted_logs = _extract_audit_logs(model_dir, review_type)
    if not extracted_logs:
        print(
            f"⚠️ Keine zutreffenden Logs gefunden für {tested_model_name} "
            f"im Modus {review_type}, überspringe."
        )
        return

    if review_type == "bias" and not _verify_bias_card_prereqs(tested_model_name):
        return

    log_data = _truncate_log_data("\n\n".join(extracted_logs), review_type)

    try:
        validator = ConfigValidator()
        run_type, _ = _resolve_commercial_run_type(tested_model_name, validator.config)
        hardware_context = _build_hardware_context(tested_model_name, run_type, validator.config)
    except Exception:
        hardware_context = "Achte auf Performance und Effizienz bezüglich Token-Kosten."

    tier_metaphor_rules = _build_tier_metaphor_rules()
    prompt_template = _load_review_prompt_template(review_type)

    model_metrics = _resolve_model_metrics_with_alias(tested_model_name)
    if not model_metrics:
        print(f"👻 Ghost Model erkannt oder keine Metriken für {tested_model_name} gefunden, überspringe.")
        return

    original_model_name = model_metrics.get("Model Name", tested_model_name)
    identity = _enrich_identity_from_card(
        tested_model_name, get_model_identity(original_model_name)
    )

    if review_type == "bias":
        csv_data = _build_bias_csv_data(tested_model_name)

    template_vars = _build_review_template_vars(
        tested_model_name,
        identity,
        csv_data,
        log_data,
        hardware_context,
        tier_metaphor_rules,
        model_metrics,
        model_dir,
        review_type,
    )
    prompt = _format_review_prompt(prompt_template, template_vars)

    print(f"🤖 Generiere {review_type.capitalize()}-Review für {tested_model_name} mit {provider}/{model_id}...")
    response = _call_review_llm(
        client, provider, model_id, prompt, max_tokens, tested_model_name
    )
    if response is None:
        return
    _write_review_output(tested_model_name, response, review_type)


def _load_tooluse_prompt_template() -> str:
    """Laedt den system_instructions-Text fuer tooluse_reviewer. '' wenn fehlend."""
    try:
        with open(ROOT_DIR / "config" / "meta_reviewer_prompt.yaml", encoding="utf-8") as f:
            prompt_yaml = yaml.safe_load(f)
        return prompt_yaml.get("tooluse_reviewer", {}).get("system_instructions", "")
    except Exception as e:
        print(f"❌ Fehler beim Laden des tooluse_reviewer-Prompts: {e}")
        return ""


def _is_tooluse_review_current(slug: str, mid: str) -> bool:
    """Prueft, ob die Tool-Use-Review unter ``slug`` aktueller als die Audit-Logs ist.

    audit_dir verwendet slug (_safe_name), weil audit_logs-Verzeichnisse
    per SSoT mit _safe_name angelegt werden (Punkte/Slashes → Underscores).
    Rohe mid (z.B. "xiaomi/mimo-v2.5") würde einen verschachtelten Pfad
    erzeugen, der nie existiert → Recency-Check wäre immer False.
    """
    out_dir = ROOT_DIR / "docs" / "reviews" / slug
    existing_reviews = (
        sorted(out_dir.glob("tooluse_narrative_review_*.md"))
        if out_dir.exists()
        else []
    )
    if not existing_reviews:
        return False
    latest_review_mtime = existing_reviews[-1].stat().st_mtime
    audit_dir = ROOT_DIR / "outputs" / "audit_logs" / slug
    tooluse_audit_files = (
        list(audit_dir.glob("tooluse*.md")) if audit_dir.exists() else []
    )
    latest_audit_mtime = max(
        (f.stat().st_mtime for f in tooluse_audit_files), default=0
    )
    if latest_review_mtime >= latest_audit_mtime:
        print(f"⏩ Tool-Use-Review für {mid} aktuell – überspringe.")
        return True
    return False


def _load_card_data_for_model(mid: str) -> dict:
    """Laedt Model-Card-JSON fuer ``mid``; leeres Dict, wenn keine oder fehlerhaft."""
    card = _find_card(mid)
    if not card.exists():
        return {}
    try:
        return json.loads(card.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _should_skip_tooluse_for_supports_flag(mid: str, card_data: dict) -> bool:
    """Prueft supports_tool_use Tri-State und gibt Skip-Signal zurueck.

      true       → skip=False (Review wird generiert)
      false      → skip=True (Modell kann keine Tools — gewollt)
      "untested"/None/sonst → skip=True (Benchmark erst ausfuehren)
    """
    if not card_data:
        return False
    stu = card_data.get("supports_tool_use")
    if stu is False:
        print(f"⏩ {mid}: supports_tool_use=false in Model Card — überspringe.")
        return True
    if stu is not True:  # None, "untested", oder sonstiger Wert
        print(
            f"⏩ {mid}: supports_tool_use={stu!r} (nicht getestet) "
            f"— Tool-Use-Benchmark zuerst ausführen."
        )
        return True
    return False


def _enrich_tooluse_identity(mid: str, identity: dict) -> dict:
    """Reichert Tool-Use-Identity um Tags/display_name aus Card an."""
    card_data = _load_card_data_for_model(mid)
    if not card_data:
        return identity
    card_tags = card_data.get("architecture_tags")
    if card_tags and isinstance(card_tags, list):
        identity = {**identity, "tags": card_tags}
    card_display = card_data.get("display_name")
    if card_display:
        identity = {**identity, "display_name": card_display}
    return identity


def _enrich_tooluse_context(mid: str, ctx: dict, taxonomy: dict) -> None:
    """Reichert Tool-Use-Context-Dict um Prompt-Variablen an (in-place)."""
    identity = _enrich_tooluse_identity(mid, get_model_identity(mid))
    _use_case = get_use_case_primary(mid)
    _size_class = get_model_size_class(mid)
    _param_arch = _get_card_field(mid, "parameter_architecture", "dense")

    ctx["model_tags"] = ", ".join(identity["tags"])
    ctx["display_model_name"] = identity["display_name"]
    ctx["model_thinking_mode"] = _resolve_thinking_mode_for_review(mid)
    ctx["model_card_context"] = get_model_card_context(mid)
    ctx["use_case_classification_context"] = format_classification_context(
        _use_case, _size_class, _param_arch, taxonomy
    )


def _format_tooluse_prompt(prompt_template: str, mid: str, ctx: dict) -> str:
    """Formatiert Tool-Use-Prompt; setzt fehlende Variablen auf 'n/a'."""
    try:
        return prompt_template.format(**ctx)
    except KeyError as e:
        print(f"⚠️ Fehlende Template-Variable {e} für {mid} — setze 'n/a'.")
        ctx[e.args[0]] = "n/a"
        return prompt_template.format(**ctx)


def _write_tooluse_review_output(slug: str, response: str) -> None:
    """Schreibt Tool-Use-Review in docs/reviews/<slug>/."""
    out_dir = ROOT_DIR / "docs" / "reviews" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"tooluse_narrative_review_{timestamp}.md"
    display_time = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
    lines = response.splitlines()
    if lines:
        lines.insert(1, f"\n> **Erstellt am:** {display_time}\n")
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Tool-Use-Review gespeichert unter: {out_file.relative_to(ROOT_DIR)}")


def _should_skip_tooluse_for_blacklist(mid: str, card_data: dict, slug: str, args, blacklist: set[str]) -> bool:
    """Prueft Webexport-Blacklist per SSOT (Card.model_id || slug)."""
    if not (args.auto and blacklist):
        return False
    bl_id = card_data.get("model_id") or slug
    if bl_id in blacklist:
        print(f"⏩ {mid}: Auf Webexport-Blacklist ({bl_id}) → Tool-Use-Review wird übersprungen.")
        return True
    return False


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

    prompt_template = _load_tooluse_prompt_template()
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

        if args.auto and not args.force and _is_tooluse_review_current(slug, mid):
            continue

        # Guard 1: model must have data in tooluse_leaderboard.csv
        if not get_tooluse_leaderboard_row(mid):
            print(f"⏩ {mid}: Kein Eintrag in tooluse_leaderboard.csv — Benchmark zuerst ausführen.")
            continue

        # Guard 2: Card laden — model_id daraus ist SSOT für Blacklist + supports_tool_use
        card_data = _load_card_data_for_model(mid)

        # Blacklist-Check: SSOT ist die model_id aus der Card (nicht der Tooluse-Leaderboard-Key)
        if _should_skip_tooluse_for_blacklist(mid, card_data, slug, args, blacklist):
            continue

        # supports_tool_use Tri-State pruefen
        if _should_skip_tooluse_for_supports_flag(mid, card_data):
            continue

        ctx = build_tooluse_context(mid)
        if not ctx:
            print(f"⚠️ Keine Leaderboard-Daten für {mid} — überspringe.")
            continue

        _enrich_tooluse_context(mid, ctx, _taxonomy)
        prompt = _format_tooluse_prompt(prompt_template, mid, ctx)

        if getattr(args, "dry_run", False):
            print(f"  [DRY-RUN] Würde Tool-Use-Review für {mid} generieren.")
            continue

        print(f"🤖 Generiere Tool-Use-Review für {mid} mit {provider}/{model_id}...")
        response = _call_review_llm(
            client, provider, model_id, prompt, max_tokens, mid
        )
        if response is None:
            continue
        _write_tooluse_review_output(slug, response)


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
    print("\n── Tool-Use-Reviews (alle ausstehenden Einträge aus tooluse_leaderboard.csv) ──")
    tooluse_args = argparse.Namespace(**vars(args))
    tooluse_args.model = None  # Kein Slug-Filter — IDs kommen aus tooluse_leaderboard.csv
    _run_tooluse_reviews(tooluse_args, client, provider, model_id, max_tokens)

    print("\n✅ Per-Model-Reviews abgeschlossen.")


def _collect_configured_model_ids() -> set[str]:
    """Sammelt alle safe-normalisierten Modell-IDs aus commercial+local Providers."""
    out: set[str] = set()
    try:
        cfg = load_config()
        providers = cfg.get("providers", {})
        for section in (providers.get("commercial"), providers.get("local")):
            if not isinstance(section, dict):
                continue
            for prov in section.values():
                if not isinstance(prov, dict):
                    continue
                for m in prov.get("models", []):
                    if isinstance(m, dict) and "id" in m:
                        out.add(_safe_name(m["id"]))
    except Exception:
        pass
    return out


def _resolve_effective_model_id(subdir_name: str) -> str:
    """Heritage-ID-Fallback: gibt canonical model_id zurueck falls umbenannt.

    Sonst ``subdir_name``. In diesem Fall nutzt der nachgelagerte Code die
    raw-Form fuer Card-/Metriken-Lookups, waehrend die Audit-Log-Dateien
    weiterhin aus subdir gelesen werden.
    """
    if _find_card(subdir_name).exists():
        return subdir_name
    heritage_path = find_card_by_heritage_id(subdir_name)
    if heritage_path is None:
        return subdir_name
    try:
        h_data = json.loads(heritage_path.read_text(encoding="utf-8"))
        h_canonical = h_data.get("model_id")
    except Exception:
        return subdir_name
    if isinstance(h_canonical, str) and h_canonical:
        print(f"ℹ️ Heritage-ID: {subdir_name} → {h_canonical}")
        return h_canonical
    return subdir_name


def _warn_if_orphaned_dir(
    subdir_name: str, effective_model_id: str, configured_safe_ids: set[str]
) -> None:
    """Warnt, wenn das Audit-Dir zu keiner konfigurierten Modell-ID passt.

    Ueberspringt date-suffixed Stubs und Faelle mit Heritage-Fund.
    """
    if not configured_safe_ids or subdir_name in configured_safe_ids:
        return
    if effective_model_id != subdir_name:
        return  # Heritage-Fund — alter Name intentional
    if re.search(r"-\d{8}$|-\d{6}$", subdir_name):
        return  # date-suffix stub ist kein Duplikat
    print(
        f"⚠️  Verzeichnis '{subdir_name}' entspricht keiner konfigurierten "
        "Modell-ID — mögliches Duplikat."
    )


def _audit_files_for_type(subdir: Path, effective_type: str) -> list[Path]:
    """Filtert Audit-Files fuer den Review-Typ (Modul-Reports vs PC-Bias-Report)."""
    if effective_type == "benchmark":
        # Nur Modul-Reports: kein 00_bias_report.md, kein tooluse*.md
        return [
            f for f in subdir.iterdir()
            if f.is_file() and f.name != "00_bias_report.md"
            and not f.name.startswith("tooluse")
        ]
    # bias: nur 00_bias_report.md
    return [f for f in subdir.iterdir() if f.is_file() and f.name == "00_bias_report.md"]


def _is_audit_review_current(
    subdir: Path, effective_type: str, args: argparse.Namespace
) -> bool:
    """Prueft, ob die bestehende Review aktueller als die Audit-Files ist.

    Returns True wenn skip (Review aktuell), False wenn Neugenerierung noetig.
    """
    if not (args.auto and not getattr(args, "force", False)):
        return False
    review_prefix = "bias_review" if effective_type == "bias" else "review"
    review_out_dir = ROOT_DIR / "docs" / "reviews" / _safe_name(subdir.name)
    existing = (
        sorted(review_out_dir.glob(f"{review_prefix}_*.md"))
        if review_out_dir.exists()
        else []
    )
    if not existing:
        return False
    latest_review_mtime = existing[-1].stat().st_mtime
    audit_files = _audit_files_for_type(subdir, effective_type)
    latest_audit_mtime = max((f.stat().st_mtime for f in audit_files), default=0)
    if latest_review_mtime >= latest_audit_mtime:
        print(f"⏩ Review für {subdir.name} aktuell – überspringe.")
        return True
    return False


def _ensure_benchmark_deps_or_skip(
    effective_model_id: str,
    args: argparse.Namespace,
    client: LLMClient,
    provider: str,
    model_id: str,
) -> bool:
    """Stellt sicher, dass Cards/Dependencies fuer Benchmark-Review vorhanden sind.

    Returns True wenn das Modell uebersprungen werden soll (Nutzer-Ablehnung
    oder Dry-Run nach Dep-Check). Sonst False (weitermachen).
    """
    dep_context = _ensure_dependencies(
        model_id=effective_model_id,
        client=client,
        card_provider=provider,
        card_model=model_id,
        auto_mode=args.auto,
        dry_run=args.dry_run,
    )
    if dep_context is None:
        return True
    return bool(args.dry_run)


def _process_audit_subdir(
    subdir: Path,
    args: argparse.Namespace,
    client: LLMClient,
    provider: str,
    model_id: str,
    max_tokens: int,
    csv_data: str,
    effective_type: str,
    safe_target_model: str | None,
    blacklist: set[str],
    configured_safe_ids: set[str],
) -> bool:
    """Verarbeitet ein einzelnes Audit-Subdir. Returns True wenn es uebersprungen wurde."""
    # Defense in depth: vergleiche safe_name-normalisiert, damit auch
    # Audit-Dirs mit roher Schreibweise (z.B. "gpt-5.4" statt "gpt-5_4")
    # korrekt gematcht werden.
    if safe_target_model and _safe_name(subdir.name) != safe_target_model:
        return True

    if args.auto and subdir.name in blacklist:
        print(f"⏩ {subdir.name}: Auf Webexport-Blacklist → Review wird übersprungen.")
        return True

    effective_model_id = _resolve_effective_model_id(subdir.name)
    _warn_if_orphaned_dir(subdir.name, effective_model_id, configured_safe_ids)

    if effective_type == "benchmark":
        bench_files = _audit_files_for_type(subdir, "benchmark")
        if not bench_files:
            print(
                f"⏩ {subdir.name}: Nur PC-Bias-Report vorhanden, "
                "keine Benchmark-Logs – überspringe."
            )
            return True

    if _is_audit_review_current(subdir, effective_type, args):
        return True

    if effective_type == "benchmark" and _ensure_benchmark_deps_or_skip(
        effective_model_id, args, client, provider, model_id
    ):
        return True

    if getattr(args, "dry_run", False):
        print(f"  [DRY-RUN] Würde {effective_type}-Review für {subdir.name} generieren.")
        return True

    canonical = effective_model_id if effective_model_id != subdir.name else None
    process_model_review(
        subdir, csv_data, client, provider, model_id, effective_type, max_tokens,
        canonical_model_id=canonical,
    )
    return False


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
    safe_target_model = _safe_name(args.model) if args.model else None
    blacklist = _load_webexport_blacklist() if args.auto else set()
    configured_safe_ids = _collect_configured_model_ids()

    found_models = False
    for subdir in audit_base_dir.iterdir():
        if not _is_valid_audit_dir(subdir):
            continue
        skipped = _process_audit_subdir(
            subdir, args, client, provider, model_id, max_tokens, csv_data,
            effective_type, safe_target_model, blacklist, configured_safe_ids,
        )
        if not skipped:
            found_models = True

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
        # DEPRECATED (v4.10.12): Provider-Vergleichs-Reviews wurden in Session 44
        # stillgelegt — das Konzept "Provider-Speed-Vergleich" wird nicht mehr
        # verfolgt. Stattdessen provider_cards.json (per LLM generierte
        # redaktionelle Karten) + stats aus den einzelnen Modul-Reviews.
        print("❌ --type provider ist deprecated (seit v4.10.12).")
        print("   Stattdessen: vendor_cards.json via 'make vendor-cards' erzeugen.")
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
