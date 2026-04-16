from typing import Optional
#!/usr/bin/env python3
"""
Meta-Reviewer für den Audit-Modus
Generiert einen detaillierten redaktionellen Artikel über die Stärken und Schwächen pro Modell,
oder, falls als bias spezifiziert, einen fokussierten Bias-Review basierend auf dem Political Compass.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
import yaml

# Setup import path to allow imports from root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.llm_client import LLMClient
from utils.model_utils import get_model_specialization, get_model_identity

def load_config() -> dict:
    config_path = ROOT_DIR / "benchmark_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_model_metrics(model_name: str) -> dict:
    import csv
    detailed_csv = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard_detailed.csv"
    if not detailed_csv.exists():
        return {}

    def normalize(s):
        return s.replace(":", "_").replace("-", "_").replace("/", "_").lower()

    norm_target = normalize(model_name)
    try:
        with open(detailed_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_model = row.get("Model Name", "")
                norm_csv = normalize(csv_model)
                if norm_target == norm_csv or norm_target.startswith(f"{norm_csv}_") or norm_target.endswith(f"_{norm_csv}"):
                    return row
    except Exception:
        pass
    return {}

def get_latest_audit_dir(base_dir: Path) -> Optional[Path]:
    """Findet das zuletzt aktualisierte Audit-Verzeichnis."""
    subdirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name != ".DS_Store"]
    if not subdirs:
        return None
    return max(subdirs, key=os.path.getmtime)

def collect_data() -> str:
    """Liest die Leaderboard.csv."""
    csv_path = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard.csv"
    if not csv_path.exists():
        return "Keine Leaderboard-Daten gefunden."

    with open(csv_path, "r", encoding="utf-8") as f:
        return f.read()

def get_model_card_context(model_id: str) -> str:
    """Liest die JSON-Karte eines Modells und gibt einen formatierten Kontext-String zurück."""
    import json
    import re

    cards_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
    safe = re.sub(r"[:/.\\ ]", "_", model_id)
    card_path = cards_dir / f"{safe}.json"

    if not card_path.exists():
        return ""

    try:
        with open(card_path, "r", encoding="utf-8") as f:
            card = json.load(f)
    except Exception:
        return ""

    if card.get("unknown"):
        return ""

    strengths = ", ".join(card.get("strengths", []))
    limitations = ", ".join(card.get("known_limitations", []))
    hint = card.get("judge_context_hint", "")

    lines = [
        f"### Model Card: {card.get('display_name', model_id)}",
        f"- **Entwickler:** {card.get('developer', 'n/a')} ({card.get('origin_country', 'n/a')})",
        f"- **Fokus:** {card.get('primary_focus', 'n/a')} | **Familie:** {card.get('model_family', 'n/a')}",
        f"- **Zusammenfassung:** {card.get('summary', '')}",
    ]
    if strengths:
        lines.append(f"- **Stärken:** {strengths}")
    if limitations:
        lines.append(f"- **Einschränkungen:** {limitations}")
    if hint:
        lines.append(f"- **Bewertungshinweis:** {hint}")

    return "\n".join(lines)


def compute_sovereign_risk(model_card: dict, provider_card: dict | None) -> tuple[str, str]:
    """Berechnet das kombinierte Sovereign-Risk zur Render-Zeit (Worst-Case-Prinzip).
    Gibt (risk_level, rationale) zurück — niemals statisch gespeichert."""
    RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
    risks: list[tuple[str, str]] = []

    # Weights-Risiko aus Model Card
    wprov = (model_card.get("weights_provenance_risk") or "").lower()
    wprov_rationale = model_card.get("weights_provenance_risk_rationale", "")
    if wprov in RISK_ORDER:
        risks.append((wprov, f"Weights-Provenienz: {wprov_rationale or wprov}"))

    if provider_card:
        dep = provider_card.get("deployment", {})
        cloud_act = dep.get("cloud_act_exposure", False)
        applicable_law = dep.get("applicable_law", "Unknown")
        nsl = (dep.get("chinese_nsl_risk") or "none").lower()

        if nsl == "high":
            risks.append(("high", f"Provider unterliegt chinesischem NSL ({provider_card.get('display_name', '')})"))
        elif cloud_act:
            eu_adequacy = dep.get("eu_adequacy_decision", False)
            level = "medium" if eu_adequacy else "high"
            risks.append((level, f"US CLOUD Act anwendbar via {provider_card.get('display_name', '')} ({'mit SCCs/DPA' if eu_adequacy else 'ohne EU-Absicherung'})"))
        elif applicable_law == "EU (GDPR)":
            risks.append(("low", f"EU-Jurisdiktion via {provider_card.get('display_name', '')} (DSGVO)"))
        elif applicable_law == "N/A (lokal only)":
            # Lokaler Betrieb: nur Weights-Risiko zählt
            if wprov == "high":
                risks.append(("medium", "Lokal betrieben – kein Datentransfer, aber Weights stammen von riskantem Entwickler"))
            else:
                risks.append(("low", "Vollständig lokal, kein Datentransfer"))
    else:
        # Kein Provider bekannt = Annahme lokal
        if wprov == "high":
            risks.append(("medium", "Kein Provider zugeordnet (vermutlich lokal) – Weights-Risiko bleibt"))
        else:
            risks.append(("low", "Kein Cloud-Provider zugeordnet"))

    if not risks:
        return ("medium", "Unbekannte Risikokombination")

    best = max(risks, key=lambda r: RISK_ORDER.get(r[0], 0))
    return best


def get_provider_card_context(model_id: str) -> str:
    """Ermittelt den Provider aus der Model Card, berechnet das kombinierte Sovereign Risk
    zur Render-Zeit und gibt einen formatierten Kontext-String zurück."""
    import json
    import re

    def safe_id(name: str) -> str:
        s = name.lower()
        s = re.sub(r"[^a-z0-9]+", "_", s)
        return s.strip("_")

    # Model Card laden
    cards_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
    safe = re.sub(r"[:/.\\ ]", "_", model_id)
    model_card_path = cards_dir / f"{safe}.json"

    model_card: dict = {}
    developer = None
    if model_card_path.exists():
        try:
            with open(model_card_path, "r", encoding="utf-8") as f:
                model_card = json.load(f)
            developer = model_card.get("developer")
        except Exception:
            pass

    # Provider Card laden (optional)
    provider_card: dict | None = None
    if developer:
        provider_cards_dir = ROOT_DIR / "benchmark_scores" / "provider_cards"
        provider_card_path = provider_cards_dir / f"{safe_id(developer)}.json"
        if provider_card_path.exists():
            try:
                with open(provider_card_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if not loaded.get("unknown"):
                    provider_card = loaded
            except Exception:
                pass

    if not model_card and not provider_card:
        return ""

    # Sovereign Risk zur Render-Zeit berechnen
    risk_level, risk_rationale = compute_sovereign_risk(model_card, provider_card)

    lines: list[str] = []

    if provider_card:
        dep = provider_card.get("deployment", {})
        lines += [
            f"### Provider Card: {provider_card.get('display_name', developer)}",
            f"- **Unternehmen:** {provider_card.get('company', 'n/a')} | **Sitz:** {provider_card.get('headquarters', 'n/a')}",
            f"- **Anwendbares Recht:** {dep.get('applicable_law', 'n/a')} | **Datenstandort:** {dep.get('data_residency', 'n/a')}",
            f"- **GDPR DPA:** {dep.get('gdpr_dpa_available', 'unknown')} | **Datenspeicherung:** {dep.get('data_retention_days', 'unknown')} Tage",
        ]
        privacy_note = provider_card.get("privacy_note", "")
        if privacy_note:
            lines.append(f"- **Deployment-Datenschutz:** {privacy_note}")

    # Kombiniertes Risiko (immer ausgeben, auch ohne Provider Card)
    lines.append(f"- **Berechnetes Sovereign Risk (Model × Provider):** `{risk_level.upper()}` — {risk_rationale}")

    if model_card:
        wprov = model_card.get("weights_provenance_risk", "")
        if wprov:
            lines.append(f"- **Weights-Provenienz-Risiko:** `{wprov}` — {model_card.get('weights_provenance_risk_rationale', '')}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dependency pre-check: automatische Erzeugung fehlender Cards
# ---------------------------------------------------------------------------

# Bekannte Cloud-Provider-Präfixe (normalized, lowercase) → Provider-Anzeigename
_CLOUD_PREFIX_TO_PROVIDER: dict[str, str] = {
    "gpt-": "OpenAI",
    "o1": "OpenAI",
    "o3": "OpenAI",
    "o4": "OpenAI",
    "claude-": "Anthropic",
    "gemini-": "Google",
    "gemma": "Google",
    "mistral": "Mistral AI",
    "codestral": "Mistral AI",
    "ministral": "Mistral AI",
    "pixtral": "Mistral AI",
    "grok-": "xAI",
    "deepseek-": "DeepSeek",
    "qwen": "Alibaba Cloud",
    "kimi": "Moonshot AI",
    "minimax": "MiniMax",
    "llama": "Meta",
}


def _detect_provider(model_id: str) -> str | None:
    """Schätzt den Cloud-Provider anhand des Modell-ID-Präfixes.

    Gibt den Provider-Anzeigenamen zurück oder None wenn das Modell
    wahrscheinlich lokal betrieben wird (kein bekanntes Cloud-Präfix).
    """
    normalized = model_id.lower()
    for prefix, provider_name in _CLOUD_PREFIX_TO_PROVIDER.items():
        stripped = prefix.rstrip("-")
        if normalized.startswith(stripped):
            return provider_name
    return None


def _load_card_module(script_name: str) -> object:
    """Lädt ein Card-Generator-Modul sicher per Dateipfad (verhindert Namespace-Kollisionen)."""
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
    client: "LLMClient",
    card_provider: str,
    card_model: str,
    auto_mode: bool,
    dry_run: bool,
) -> "dict | None":
    """Lädt die Model Card oder generiert sie bei Bedarf.

    Rückgabewerte:
        dict  — Mit Inhalt: vorhandene/neue Karte. Leer ({}): fehlend, aber dry_run-Modus.
        None  — Benutzer hat übersprungen → Review-Schleife soll dieses Modell skippen.
    """
    import json
    import re

    cards_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
    safe = re.sub(r"[:/.\\ ]", "_", model_id)
    card_path = cards_dir / f"{safe}.json"

    if card_path.exists():
        try:
            with open(card_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Karte fehlt
    if dry_run:
        print(f"  [FEHLEND] Model Card: {model_id}")
        return {}  # leer, aber kein Skip-Signal

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
    developer: "str | None",
    client: "LLMClient",
    card_provider: str,
    card_model: str,
    auto_mode: bool,
    dry_run: bool,
) -> "dict | None":
    """Lädt die Provider Card oder generiert sie bei Bedarf.

    Wenn developer None ist (lokales Modell ohne Cloud-Provider), wird sofort
    ein leeres Dict zurückgegeben — das ist kein Fehlerfall.
    Rückgabewerte: analog zu _ensure_model_card.
    """
    import json
    import re

    if not developer:
        return {}  # kein Provider (lokales Modell) — ok

    def safe_id(name: str) -> str:
        s = name.lower()
        s = re.sub(r"[^a-z0-9]+", "_", s)
        return s.strip("_")

    provider_id = safe_id(developer)
    cards_dir = ROOT_DIR / "benchmark_scores" / "provider_cards"
    card_path = cards_dir / f"{provider_id}.json"

    if card_path.exists():
        try:
            with open(card_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Karte fehlt
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
    card = pc_gen._generate_card(developer, provider_id, stats, client, card_provider, card_model)  # type: ignore[attr-defined]
    pc_gen._write_card(card)  # type: ignore[attr-defined]
    pc_gen._rebuild_index()  # type: ignore[attr-defined]
    print(f"  Provider Card erstellt: {developer}")
    return card


def _ensure_dependencies(
    model_id: str,
    client: "LLMClient",
    card_provider: str,
    card_model: str,
    auto_mode: bool = False,
    dry_run: bool = False,
) -> "dict | None":
    """Stellt sicher, dass Model Card und Provider Card vor der Review-Generierung vorhanden sind.

    Rückgabewerte:
        dict  — Fortfahren (kann leer sein, Inhalt wird aktuell nicht genutzt).
        None  — Modell überspringen (Benutzer hat abgebrochen oder kein Terminal verfügbar).
    """
    model_card = _ensure_model_card(model_id, client, card_provider, card_model, auto_mode, dry_run)
    if model_card is None:
        return None

    # Entwickler aus Karte lesen oder per Präfix schätzen (Fallback für dry_run / leere Karte)
    developer: str | None = model_card.get("developer") if model_card else None
    if not developer:
        developer = _detect_provider(model_id)

    provider_result = _ensure_provider_card(developer, client, card_provider, card_model, auto_mode, dry_run)
    if provider_result is None:
        return None

    return {}  # Signal: Abhängigkeiten OK, Review kann starten


def _build_token_efficiency_context(tested_model_name: str) -> str:
    """Berechnet pro-Modul Token-Overhead dieses Modells vs. Fleet-Median.
    Gibt einen formatierten Markdown-Block zurück, oder einen Hinweis wenn keine Daten vorliegen.
    Module ohne Budget-Konfiguration (Reasoning, Metacog) werden explizit als 'exempt' markiert.
    """
    import csv
    import statistics
    from collections import defaultdict

    cfg = load_config()
    token_budgets: dict[str, int] = cfg.get("token_budgets", {})

    # Modul aus asset_id ableiten
    _MODULE_PREFIX_MAP: dict[str, str] = {
        "cultural_intel": "cultural_intelligence",
        "ux_writing": "ux_writing",
        "content_transf": "content_transformation",
        "documentation_quality": "documentation_quality",
        "code_quality": "code_quality",
        "cli": "cli_benchmark",
        "reasoning_metacog": "__exempt__",
        "reasoning": "__exempt__",
    }

    def _asset_to_module(asset_id: str) -> str | None:
        for prefix, key in _MODULE_PREFIX_MAP.items():
            if asset_id.startswith(prefix):
                return key
        return None

    # Alle drei CSV-Quellen durchsuchen
    csv_sources = [
        ROOT_DIR / "benchmark_scores" / "local_models_benchmark.csv",
        ROOT_DIR / "benchmark_scores" / "commercial_models_benchmark.csv",
        ROOT_DIR / "benchmark_scores" / "cloud_models_benchmark.csv",
    ]

    def norm(s: str) -> str:
        return s.replace(":", "_").replace("-", "_").replace("/", "_").lower()

    norm_target = norm(tested_model_name)

    # fleet_tokens[module_key] = list of avg_tokens per model
    fleet_per_model: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for src in csv_sources:
        if not src.exists():
            continue
        try:
            with open(src, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    asset_id = row.get("asset_id", "")
                    model_name = row.get("model", "")
                    try:
                        tokens = float(row.get("tokens_used", "") or 0)
                    except (ValueError, TypeError):
                        tokens = 0.0
                    if not asset_id or tokens <= 0:
                        continue
                    module_key = _asset_to_module(asset_id)
                    if module_key is None:
                        continue
                    fleet_per_model[norm(model_name)][module_key].append(tokens)
        except Exception:
            continue

    if not fleet_per_model:
        return "*Keine Token-Daten in den Benchmark-CSVs vorhanden.*"

    # Ziel-Modell finden
    target_key: str | None = None
    for key in fleet_per_model:
        if key == norm_target or key.startswith(norm_target) or norm_target.startswith(key):
            target_key = key
            break

    if target_key is None:
        return f"*Kein CSV-Eintrag für `{tested_model_name}` gefunden — Token-Effizienz nicht berechenbar.*"

    # Fleet-Median pro Modul berechnen
    all_modules: set[str] = set()
    for model_data in fleet_per_model.values():
        all_modules.update(model_data.keys())

    lines = ["### Token-Effizienz pro Modul\n"]
    lines.append("| Modul | Dieses Modell (Ø) | Fleet-Median | Overhead | Budget | Status |")
    lines.append("|-------|:---:|:---:|:---:|:---:|:---:|")

    has_data = False
    for module_key in sorted(all_modules):
        target_vals = fleet_per_model[target_key].get(module_key, [])
        if not target_vals:
            continue
        target_avg = round(statistics.mean(target_vals), 0)

        fleet_all: list[float] = []
        for model_data in fleet_per_model.values():
            model_module_vals = model_data.get(module_key, [])
            if model_module_vals:
                fleet_all.append(statistics.mean(model_module_vals))

        fleet_median = round(statistics.median(fleet_all), 0) if len(fleet_all) >= 2 else None

        if module_key == "__exempt__":
            status = "⚪ Exempt"
            budget_str = "Exempt"
            overhead_str = "–"
        else:
            budget = token_budgets.get(module_key)
            budget_str = str(budget) if budget else "–"
            if fleet_median and fleet_median > 0:
                overhead = round(target_avg / fleet_median, 2)
                overhead_str = f"{overhead}×"
            else:
                overhead_str = "n/a"
                overhead = None

            if budget is not None and target_avg > budget * 1.5:
                ratio = round(target_avg / budget, 1)
                status = f"🔴 Verbos ({ratio}× Budget)"
            elif budget is not None and target_avg > budget:
                status = "🟡 Erhöht"
            else:
                status = "🟢 OK"

        fleet_str = str(int(fleet_median)) if fleet_median else "n/a"
        display_name = module_key.replace("_", " ").replace("__", "").title() if module_key != "__exempt__" else "Reasoning / Metacog"
        lines.append(f"| {display_name} | {int(target_avg)} | {fleet_str} | {overhead_str} | {budget_str} | {status} |")
        has_data = True

    if not has_data:
        return f"*Keine Modul-Token-Daten für `{tested_model_name}` gefunden.*"

    return "\n".join(lines)


def process_model_review(model_dir: Path, csv_data: str, client: LLMClient, provider: str, model_id: str, review_type: str = "benchmark"):
    """Liest Audit-Logs für ein spezifisch getestetes LLM und generiert eine Review."""
    tested_model_name = model_dir.name
    print(f"\n📥 Sammle Logs für Modell: {tested_model_name} (Typ: {review_type})...")

    extracted_logs = []
    for md_file in model_dir.rglob("*.md"):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            is_bias_file = md_file.name in ['00_bias_report.md', 'pol_comp_report.md']

            # Filter logic based on review type
            if review_type == "bias" and not is_bias_file:
                continue
            if review_type == "benchmark" and is_bias_file:
                continue

            # Simple Extraktion via Regex (suche nach Judge Evaluation Blöcken unten)
            judge_section_match = re.search(r'## 3\. Evaluation.*', content, re.DOTALL)

            # Suche nach System-Infos und Warnungen
            system_info_match = re.search(r'> \[!(?:WARNING|CAUTION|ERROR)\].*?(?=\n\n|$)', content, re.DOTALL)
            system_info_text = f"\n\n{system_info_match.group(0)}" if system_info_match else ""

            # Suche explizit nach harten Safety-Filter Blöcken, die in "2. Model Response" auftauchen
            safety_filter_match = re.search(r'## 2\. Model.*?Error: Content blocked by safety filters\.', content, re.DOTALL)
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

    log_data = "\n\n".join(extracted_logs)

    max_log_chars = 30000
    if len(log_data) > max_log_chars:
        if review_type == "bias":
            log_data = log_data[:max_log_chars]
        else:
            log_data = log_data[-max_log_chars:]


    try:
        from utils.system_context import SystemContextManager
        from utils.model_utils import get_model_category

        context_manager = SystemContextManager()

        _config = load_config()
        # Single Source of Truth
        # Zuerst prüfen, ob es in der kommerziellen Liste ist
        commercial_models = []
        for p_config in _config.get("providers", {}).get("commercial", {}).values():
            if p_config.get("enabled", False):
                commercial_models.extend([m["id"] for m in p_config.get("models", [])])

        source_context = "commercial" if tested_model_name in commercial_models else "local"

        category = get_model_category(tested_model_name, source_context)

        if category == "Proprietär":
            run_type = "commercial"
        elif category in ["Local Cloud", "Open Weights (Cloud)", "Cloud (Open-Weights)"]:
            run_type = "cloud_open_weights"
        else:
            run_type = "local"

        hardware_context = context_manager.get_editor_prompt_injection(run_type)
    except Exception as e:
        hardware_context = "Achte auf Performance und Effizienz bezüglich Token-Kosten."

    # Load tier definitions from config
    tier_metaphor_rules = ""
    try:
        import yaml
        with open(ROOT_DIR / "benchmark_config.yaml", "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f)
            _tiers = _config.get("scoring_tiers", {})
            _tier_lines = []

            # Create a sorted list based on thresholds
            sorted_tiers = sorted(_tiers.items(), key=lambda item: item[1].get('threshold', 0.0), reverse=True)

            for i, (key, data) in enumerate(sorted_tiers):
                threshold = data.get('threshold', 0.0)
                desc = data.get('prompt_description', '')
                next_threshold = sorted_tiers[i-1][1].get('threshold', 100.0) if i > 0 else 100.0

                # Format exactly as configured
                desc = desc.replace('{threshold}', str(threshold)).replace('{next_threshold}', str(next_threshold))
                _tier_lines.append(desc)

            tier_metaphor_rules = "\n".join(_tier_lines)
    except Exception:
        tier_metaphor_rules = "- **Ab 95%:** Platin\n- **Ab 80% bis unter 95%:** Gold\n- **Ab 65% bis unter 80%:** Silber\n- **Ab 50% bis unter 65%:** Bronze\n- **Unter 50%:** Standard"


    if review_type == "benchmark":
        try:
            import yaml
            with open(ROOT_DIR / "config" / "meta_reviewer_prompt.yaml", "r", encoding="utf-8") as f:
                prompt_yaml = yaml.safe_load(f)
                prompt_template = prompt_yaml.get("meta_reviewer", {}).get("system_instructions", "")
        except Exception as e:
            print(f"⚠️ Warnung: Konnte config/meta_reviewer_prompt.yaml nicht laden: {e}")
            prompt_template = """Fehler beim Laden des Prompts."""
    else:
        try:
            import yaml
            with open(ROOT_DIR / "config" / "meta_reviewer_prompt.yaml", "r", encoding="utf-8") as f:
                prompt_yaml = yaml.safe_load(f)
                prompt_template = prompt_yaml.get("bias_reviewer", {}).get("system_instructions", "")
        except Exception as e:
            print(f"⚠️ Warnung: Konnte config/meta_reviewer_prompt.yaml nicht laden: {e}")
            prompt_template = """Fehler beim Laden des Prompts."""

    model_metrics = get_model_metrics(tested_model_name)
    if not model_metrics:
        print(f"👻 Ghost Model erkannt oder keine Metriken für {tested_model_name} in 'benchmark_leaderboard_detailed.csv' gefunden, überspringe Review-Generierung.")
        return

    def safe_round(val):
        try:
            return str(round(float(val), 2))
        except (ValueError, TypeError):
            return "n/a"

    timeout_count = model_metrics.get("Timeout Count", "n/a")
    tests_run = model_metrics.get("Tests Run", "n/a")
    if tests_run != "n/a" and "/" in tests_run:
        tests_run = tests_run.split("/")[-1]

    timeout_rate_str = f"{timeout_count}/{tests_run}" if timeout_count != "n/a" else "n/a"

    # Extract model identity for display (display_name and tags for human-friendly output)
    original_model_name = model_metrics.get("Model Name", tested_model_name)
    identity = get_model_identity(original_model_name)

    # --- Token-Effizienz-Kontext berechnen ---
    token_efficiency_context = _build_token_efficiency_context(tested_model_name)

    template_vars = {
        "tested_model_name": tested_model_name,  # raw ID für Audit-Trail
        "display_model_name": identity["display_name"],  # "kimi-k2-instruct" (ohne Präfixe)
        "model_tags": ", ".join(identity["tags"]),  # "Instruction, Abliterated"
        "hardware_context": hardware_context,
        "csv_data": csv_data,
        "log_data": log_data,
        "tier_metaphor_rules": tier_metaphor_rules,
        "model_specialization": get_model_specialization(tested_model_name),
        "model_p95_time": safe_round(model_metrics.get("P95 Time (s)")),
        "model_tokens_per_s": safe_round(model_metrics.get("Tokens/s")),
        "model_timeout_rate": timeout_rate_str,
        "model_provider_type": model_metrics.get("Type", "n/a"),
        "model_card_context": get_model_card_context(tested_model_name),
        "model_card_json": get_model_card_context(tested_model_name),
        "provider_card_context": get_provider_card_context(tested_model_name),
        "token_efficiency_context": token_efficiency_context,
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
            temperature=0.7 # Ein bisschen Kreativität für einen Artikel
        )
    except Exception as e:
        print(f"❌ Fehler bei der Generierung für {tested_model_name}: {e}")
        return

    # Speichern in docs/reviews/ (öffentlich versioniert)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT_DIR / "docs" / "reviews" / tested_model_name
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix = "bias_review" if review_type == "bias" else "review"
    out_file = out_dir / f"{prefix}_{timestamp}.md"

    # Zeitstempel in Bericht einfügen, am besten in der zweiten Zeile
    display_time = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
    lines = response.splitlines()
    if lines:
        lines.insert(1, f"\n> **Erstellt am:** {display_time}\n")
    else:
        lines.append(f"\n> **Erstellt am:** {display_time}\n")
    response_with_timestamp = "\n".join(lines)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(response_with_timestamp)

    print(f"✅ Review gespeichert unter: {out_file.relative_to(ROOT_DIR)}")


def main():
    parser = argparse.ArgumentParser(description="Generiert qualitative LLM-Reviews basierend auf den Audit-Logs.")
    parser.add_argument("-m", "--model", type=str, help="Generiere den Review nur für dieses spezifische Modell (z.B. claude-haiku-4-5-20251001)")
    parser.add_argument("-a", "--all", action="store_true", help="Generiere Reviews für alle Modelle mit gefundenen Audit-Logs")
    parser.add_argument("-t", "--type", type=str, choices=["benchmark", "bias", "provider"], default="benchmark", help="Art des Reviews: 'benchmark' (standard), 'bias' oder 'provider'")
    parser.add_argument("--auto", action="store_true", help="Unbeaufsichtigt: fehlende Cards automatisch generieren ohne Rückfrage")
    parser.add_argument("--dry-run", action="store_true", help="Zeigt fehlende Cards an, generiert aber nichts und erstellt keinen Review")
    args = parser.parse_args()

    if not args.model and not args.all and args.type != "provider":
        print("❌ Bitte gib ein Modell an (-m <modell>) oder nutze --all für alle Modelle.")
        sys.exit(1)

    print(f"📰 Starte Meta-Reviewer Auswertung ({args.type.upper()}-Modus)...")

    # Init config and client
    config = load_config()
    client = LLMClient(config=config)

    # Lade die neue llm_review Config anstelle der Judge-Config!
    review_config = config.get("llm_review", {}).get("provider", {})
    provider = review_config.get("name", "google")
    model_id = review_config.get("model", "gemini-2.5-pro")

    # Falls die neue Config block fälschlicherweise nicht gefunden wird (Fallback)
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

        with open(csv_path, "r", encoding="utf-8") as f:
            csv_data = f.read()

        with open(ROOT_DIR / "config/meta_reviewer_prompt.yaml", "r", encoding="utf-8") as f:
            import yaml
            prompt_config = yaml.safe_load(f)

        prompt = prompt_config.get("provider_reviewer", {}).get("system_instructions", "")
        if not prompt:
            prompt = prompt_config.get("meta_reviewer", {}).get("provider_reviewer", {}).get("system_instructions", "")

        if not prompt:
            print("❌ Fehler: 'provider_reviewer' Prompt in config/meta_reviewer_prompt.yaml nicht gefunden.")
            return

        prompt = prompt.replace("{csv_data}", csv_data)

        print("🧠 Generiere Provider Landscape Report (dies kann einen Moment dauern)...")
        try:
            response = client.query(
                model=model_id,
                prompt=prompt,
                provider=provider,
                temperature=0.7
            )

            out_file = ROOT_DIR / "docs" / "reviews" / "provider_landscape_review.md"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(response)

            print(f"✅ Provider Review gespeichert unter: {out_file.relative_to(ROOT_DIR)}")
            return
        except Exception as e:
            print(f"❌ Fehler bei der Generierung: {e}")
            return

    audit_base_dir = ROOT_DIR / "outputs" / "audit_logs"

    if not audit_base_dir.exists():
        print("❌ Keine Audit-Logs gefunden.")
        return

    print("📁 Durchsuche Audit-Logs nach Modellen...")

    found_models = False

    # Safe model name for comparison (matching benchmark_utils.py)
    safe_target_model = args.model.replace(":", "_").replace("/", "_") if args.model else None

    # Iteriere über die Modell-Ordner (z.B. mistral-medium-latest) im Audit-Root
    for subdir in audit_base_dir.iterdir():
        if subdir.is_dir() and subdir.name != ".DS_Store":
            if safe_target_model and subdir.name != safe_target_model:
                continue
            found_models = True
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
                    continue  # Benutzer hat übersprungen
                if args.dry_run:
                    continue  # Nur Bericht, kein Review
            process_model_review(subdir, csv_data, client, provider, model_id, args.type)

    if not found_models:
        print("⚠️ Keine Audit-Logs für das spezifizierte Modell gefunden.")


if __name__ == "__main__":
    main()
