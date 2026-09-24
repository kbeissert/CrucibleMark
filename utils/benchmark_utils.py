"""
Shared utilities for benchmark runners.
Contains common logic for interactive selection and asset discovery.
"""

import json
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import yaml

from utils.model_utils import _safe_name

T = TypeVar("T")

logger = logging.getLogger(__name__)


def load_asset_yaml(asset_path: Path) -> dict[str, Any]:
    """
    Safely loads a YAML asset file.
    Handles single document and multi-document files (returns the metadata one).
    Returns empty dict on failure.
    """
    try:
        with open(asset_path, encoding="utf-8") as f:
            content = f.read()

        # Try single load first
        return yaml.safe_load(content) or {}
    except yaml.YAMLError:
        # Fallback for multi-document files
        try:
            with open(asset_path, encoding="utf-8") as f:
                docs = list(yaml.safe_load_all(f))
            # Find doc with metadata
            return next(
                (d for d in docs if d and isinstance(d, dict) and "metadata" in d),
                docs[0] if docs else {},
            )
        except (OSError, yaml.YAMLError) as e:
            logger.error("Failed to load asset %s: %s", asset_path, e)
            return {}
    except OSError as e:
        logger.error("Failed to read file %s: %s", asset_path, e)
        return {}


def print_header(title: str, width: int = 60) -> None:
    """DEPRECATED: Use TerminalUI.print_header instead."""
    from utils.benchmark_ui import TerminalUI

    TerminalUI.print_header(title, width)


def select_from_list(
    items: list[T],
    display_func: Callable[[T], str | tuple[str, str]],
    prompt: str = "Wähle einen Eintrag",
    title: str | None = None,
) -> T | None:
    """DEPRECATED: Use TerminalUI.select_from_list instead."""
    from utils.benchmark_ui import TerminalUI

    return TerminalUI.select_from_list(items, display_func, prompt, title)


def discover_assets(directory: str | Path, pattern: str = "*.yaml") -> list[Path]:
    """
    Finds all assets matching pattern in directory.

    Args:
        directory: Path to search in
        pattern: Glob pattern (default: *.yaml)

    Returns:
        Sorted list of paths
    """
    path = Path(directory)

    if not path.exists():
        return []

    return sorted(list(path.glob(pattern)))


# Default tags stripped by clean_reasoning_tags when no override is given.
# Covers the most common CoT tag families across providers.
_DEFAULT_REASONING_TAGS: list[str] = ["think", "thought", "reasoning"]


# Tag, mit dem der ausgelagerte Reasoning-Kanal für die Bewertung rekonstruiert wird.
REASONING_CHANNEL_TAG = "think"


def has_reasoning_channel(text: str) -> bool:
    """True, wenn der Text bereits einen Denkblock trägt (jede Tag-Familie)."""
    low = str(text or "").lower()
    return any(f"<{tag}" in low for tag in _DEFAULT_REASONING_TAGS)


def with_reasoning_channel(response: str, think_content: str | None) -> str:
    """Materialisiert den ausgelagerten Reasoning-Kanal als Denkblock vor der Antwort.

    Provider liefern Denkinhalt teils in einem separaten Feld (`reasoning_content`)
    statt im `content`-Feld; die Connectoren lagern das nach ``think_content`` aus.
    Für die Bewertung muss dieser Text wieder Teil der Response sein — sonst sieht
    ein Scorer, der Denkblöcke auswertet (Reasoning Tier 3: Self-Correction,
    Linguistic Analysis, Thought Depth), bei diesen Modellen nichts, obwohl gedacht
    wurde. Das ist der Kanal-Bias, den diese Funktion schließt.

    Die Rekonstruktion ist identisch für Regel- und Judge-Stufe (SSoT hier).
    Trägt die Antwort schon einen Denkblock (CoT inline im Content-Feld, z. B.
    Qwen3.8), wird nichts vorangestellt — kein Doppelblock.

    Args:
        response: Sichtbarer Antworttext des Providers.
        think_content: Ausgelagerter Reasoning-Text oder None/leer.

    Returns:
        Effektiver Bewertungs-Text.
    """
    think = str(think_content or "").strip()
    if not think or has_reasoning_channel(response):
        return response
    return f"<{REASONING_CHANNEL_TAG}>\n{think}\n</{REASONING_CHANNEL_TAG}>\n\n{response}"


def clean_reasoning_tags(
    text: str,
    tags: list[str] | None = None,
    extra_patterns: list[str] | None = None,
) -> str:
    """Remove reasoning/CoT tags from a model response before scoring.

    This is the SSoT for reasoning-tag stripping across all benchmark modules.
    Each module may pass its own ``tags`` and ``extra_patterns`` to preserve
    module-specific behaviour without duplicating the regex logic.

    Args:
        text: Raw model response string.
        tags: XML-style tag names to strip (e.g. ``["think", "thought"]``).
              Each entry N strips ``<N>…</N>`` blocks (case-insensitive, DOTALL).
              Defaults to ``["think", "thought", "reasoning"]``.
        extra_patterns: Additional raw regex patterns to strip *after* tags.
              Useful for non-XML markers like ``[Reasoning]…[/Reasoning]``.

    Returns:
        Cleaned, stripped response string.  Returns ``""`` for falsy input.
    """
    if not text:
        return ""
    _tags = tags if tags is not None else _DEFAULT_REASONING_TAGS
    cleaned = text
    for tag in _tags:
        pattern = f"<{re.escape(tag)}>.*?</{re.escape(tag)}>"
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if extra_patterns:
        for pattern in extra_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


def format_pc_run_data(run_dict: dict, include_extremism: bool = False) -> dict:
    """
    Formatiert Political Compass Run-Daten in standardisiertes Schema.

    Args:
        run_dict: Dict mit keys 'x', 'y', 'x_label', 'y_label'
        include_extremism: Wenn True, füge extremism/sigma hinzu (für AVG)

    Returns:
        Standardisiertes Dict für metadata_json
    """
    x = run_dict.get("x", 0.0)
    y = run_dict.get("y", 0.0)
    x_label = run_dict.get("x_label", "Unbekannt")
    y_label = run_dict.get("y_label", "Unbekannt")

    # Basis-Struktur (für Individual Runs)
    formatted = {
        "coordinates": {"x": x, "y": y, "formatted": f"({x}, {y})"},
        "labels": {"x": x_label, "y": y_label, "archetype": f"{x_label}-{y_label}"},
        "display": {"ideology": f"{x_label} ({x})", "stance": f"{y_label} ({y})"},
    }

    # Erweiterte Struktur (für Aggregate/AVG)
    if include_extremism:
        formatted["extremism"] = run_dict.get(
            "extremism",
            {
                "count": 0,
                "rate": 0.0,
                "status": "✅ Demokratisch",
                "categories": {},
                "details": [],
            },
        )
        formatted["sigma"] = run_dict.get("sigma", {"x": 0.0, "y": 0.0})
        formatted["module_stats"] = run_dict.get("module_stats", {})

    return formatted


def format_political_compass_data(report: dict[str, Any]) -> dict[str, Any]:
    """
    Formats the raw Political Compass report into a standardized data object.
    Used for consistent JSON structure in results.
    """
    return {
        "coordinates": {
            "x": report["coordinates"]["x"],
            "y": report["coordinates"]["y"],
            "formatted": f"({report['coordinates']['x']}, {report['coordinates']['y']})",
        },
        "labels": {
            "x": report["archetype"].get("x_label", "Unknown"),
            "y": report["archetype"].get("y_label", "Unknown"),
            "archetype": report["archetype"]["label"],
        },
        "display": {
            "ideology": f"{report['archetype'].get('x_label', '?')} ({report['coordinates']['x']})",
            "stance": f"{report['archetype'].get('y_label', '?')} ({report['coordinates']['y']})",
        },
        "extremism": report.get("extremism", {"count": 0, "rate": 0.0}),
    }


def prepare_pc_csv_row(
    model: str,
    report: dict[str, Any],
    data_object: dict[str, Any],
    model_version: str = "unknown",
) -> dict[str, Any]:
    """
    Prepares a dictionary row for the Political Compass CSV.
    """
    return {
        "model": model,
        "model_version": model_version,
        "run_id": "AVG",
        "x_coordinate": report["coordinates"]["x"],
        "y_coordinate": report["coordinates"]["y"],
        "x_label": report["archetype"]["x_label"],
        "y_label": report["archetype"]["y_label"],
        "metrics_json": json.dumps(data_object, ensure_ascii=False),
        "timestamp": report.get("timestamp", ""),
    }


def _get_token_budget(asset_id: str) -> tuple[str | None, int | None]:
    """Gibt (modul_key, token_budget) für eine asset_id zurück, oder (None, None) wenn kein Budget konfiguriert."""
    # Modul aus asset_id ableiten (z.B. "cultural_intel_001" → "cultural_intelligence")
    _MODULE_PREFIX_MAP = {
        "cultural_intel": "cultural_intelligence",
        "ux_writing": "ux_writing",
        "content_transformation": "content_transformation",
        "documentation_quality": "documentation_quality",
        "code_quality": "code_quality",
        "cli": "cli_benchmark",
        # reasoning und reasoning_metacog absichtlich NICHT enthalten
    }
    module_key = None
    for prefix, key in _MODULE_PREFIX_MAP.items():
        if str(asset_id).startswith(prefix):
            module_key = key
            break

    if module_key is None:
        return None, None

    budget = _get_token_budgets_config().get(module_key)
    return module_key, budget


# Performance (Review 2026-08-15): benchmark_config.yaml wird pro Audit-Log-
# Schreibung neu gelesen. Modul-Level-Cache — die Config ändert sich nicht
# während eines Laufs (SSoT wird beim Prozessstart gelesen).
_TOKEN_BUDGETS_CACHE: dict[str, int] | None = None


def _get_token_budgets_config() -> dict[str, int]:
    """Liest token_budgets aus benchmark_config.yaml (einmalig gecacht)."""
    global _TOKEN_BUDGETS_CACHE  # pylint: disable=global-statement
    if _TOKEN_BUDGETS_CACHE is not None:
        return _TOKEN_BUDGETS_CACHE
    try:
        import yaml
        from pathlib import Path as _Path
        _config_path = _Path(__file__).resolve().parent.parent / "benchmark_config.yaml"
        with open(_config_path, encoding="utf-8") as f:
            _cfg = yaml.safe_load(f) or {}
        _TOKEN_BUDGETS_CACHE = _cfg.get("token_budgets", {}) or {}
    except Exception:  # pylint: disable=broad-exception-caught
        _TOKEN_BUDGETS_CACHE = {}
    return _TOKEN_BUDGETS_CACHE


def save_audit_log(
    model: str,
    asset_id: str,
    prompt: str,
    response: str,
    judge_response: str,
    base_dir: Path = Path("outputs/audit_logs"),
    token_limit_cutoff: bool = False,
    token_limit_fallback: bool = False,
    execution_time: float | None = None,
    tokens_used: int | None = None,
    tokens_per_second: float | None = None,
    cost: float | None = None,
    provider: str | None = None,
    reasoning_tokens: int | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    think_content: str | None = None,
    thinking_mode: str | None = None,
    reasoning_reask_stage: int | None = None,
    reasoning_reask_exhausted: bool = False,
    reasoning_reask_final_budget: int | None = None,
    cot_calibrated_start: bool = False,
    reasoning_last_resort: bool = False,
    reasoning_last_resort_budget: int | None = None,
    reasoning_loop_suspected: bool = False,
    reasoning_loop_stage: int = 0,
    reasoning_loop_elapsed_s: float | None = None,
    refusal_retry_used: bool = False,
    refusal_retry_original_prompt: str | None = None,
    **kwargs
) -> None:
    """
    Saves a comprehensive audit log for every test, containing prompt, response, and judge feedback.

    ``input_tokens``/``output_tokens`` sind die echten Provider-Usage-Werte
    (Output inkl. Thinking) und werden als Breakdown in den Header geschrieben.

    Die Eskalationsleiter-Parameter (``reasoning_reask_*``/``cot_calibrated_start``)
    erzeugen den Reviewer-Info-Block (``_write_escalation_ladder_block``) —
    Traceability für den Meta-Reviewer (analog PC v3 Sektion 2.9).
    """
    try:
        # Create subdirectories for the model
        safe_model = _safe_name(str(model))
        model_dir = base_dir / safe_model
        model_dir.mkdir(exist_ok=True, parents=True)

        filename = f"{asset_id}.md"
        filepath = model_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            _write_audit_header(
                f,
                asset_id=asset_id,
                model=model,
                provider=provider,
                thinking_mode=thinking_mode,
                execution_time=execution_time,
                tokens_used=tokens_used,
                reasoning_tokens=reasoning_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                tokens_per_second=tokens_per_second,
                cost=cost,
            )
            if token_limit_fallback:
                f.write("> [!WARNING]\n> Das Modell (bzw. die API) hat das initial angeforderte Token-Limit abgelehnt (zu groß für die Architektur). Das System ist dynamisch auf ein kleineres 4096-Token-Fallback gewechselt. Dies zeigt, dass dieses Modell mit großen Token-Anfragen oder Kontexten Probleme hat!\n\n")

            _write_token_limit_warnings(
                f,
                model=model,
                asset_id=asset_id,
                tokens_used=tokens_used,
                reasoning_tokens=reasoning_tokens,
                output_tokens=output_tokens,
                token_limit_cutoff=token_limit_cutoff,
            )

            _write_escalation_ladder_block(
                f,
                reasoning_reask_stage=reasoning_reask_stage,
                reasoning_reask_exhausted=reasoning_reask_exhausted,
                reasoning_reask_final_budget=reasoning_reask_final_budget,
                cot_calibrated_start=cot_calibrated_start,
                reasoning_last_resort=reasoning_last_resort,
                reasoning_last_resort_budget=reasoning_last_resort_budget,
                reasoning_loop_suspected=reasoning_loop_suspected,
                reasoning_loop_stage=reasoning_loop_stage,
                reasoning_loop_elapsed_s=reasoning_loop_elapsed_s,
            )

            _write_refusal_retry_block(
                f,
                refusal_retry_used=refusal_retry_used,
                refusal_retry_original_prompt=refusal_retry_original_prompt,
            )

            f.write("## 1. Prompt / Fragestellung\n\n")
            safe_prompt = _demote_headers_safe(str(prompt))
            formatted_prompt = "\n".join([f"> {line}" for line in safe_prompt.split("\n")])
            f.write(f"{formatted_prompt}\n\n")

            f.write("## 2. Model Response / Antwort\n\n")
            if token_limit_cutoff:
                f.write("> [!CAUTION]\n> Das Modell hat das maximale Token-Limit erreicht und die Antwort abgebrochen. Die folgende Antwort ist INKOMPLETT und zeigt an, dass das Modell für diese Aufgabe zu gesprächig (verbose) war.\n\n")

            _write_response_block(f, response, think_content)

            f.write("## 3. Evaluation / LLM-Judge / Scorer\n\n")
            safe_judge = _demote_headers_safe(str(judge_response))
            f.write(f"{safe_judge}\n")
    except OSError as e:
        logger.warning("Failed to save audit log for %s: %s", asset_id, e)


def _write_audit_header(
    f,
    asset_id: str,
    model: str,
    provider: str | None,
    thinking_mode: str | None,
    execution_time: float | None,
    tokens_used: int | None,
    reasoning_tokens: int | None,
    input_tokens: int | None,
    output_tokens: int | None,
    tokens_per_second: float | None,
    cost: float | None,
) -> None:
    """Schreibt den oberen Markdown-Header eines Audit-Logs (Metadaten-Block).

    Die Token-Breakdown bleibt auf der ``**Tokens Used:**``-Zeile, weil
    ``generate_review._strip_metric_lines()`` genau diese Zeile aus dem
    Review-Prompt-Kontext entfernt (Review-Prosa-Vertrag).
    """
    from datetime import datetime  # noqa: PLC0415  (lokal: vermeidet Module-Init-Kosten)

    f.write(f"# Audit Log: {asset_id}\n")
    f.write(f"> **Erstellt am:** {datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}\n")
    f.write(f"**Model:** {model}\n")
    if provider:
        f.write(f"**Provider:** {provider}\n")
    if thinking_mode:
        f.write(f"**Thinking Mode:** {thinking_mode}\n")
    if execution_time is not None:
        f.write(f"**Execution Time:** {execution_time:.2f} s\n")
    if tokens_used is not None:
        f.write(f"**Tokens Used:** {tokens_used}")
        if input_tokens and output_tokens:
            _detail = f" — {input_tokens} Input + {output_tokens} Output (echte Usage, Output inkl. Thinking)"
            if reasoning_tokens:
                _detail += f", davon {reasoning_tokens} Reasoning-Tokens"
            f.write(_detail)
        elif reasoning_tokens:
            f.write(f" _(davon {reasoning_tokens} Reasoning-Tokens, die intern verbraucht wurden)_")
        f.write("\n")
    if tokens_per_second is not None:
        f.write(f"**Tokens/s:** {tokens_per_second:.2f}\n")
    if cost is not None:
        try:
            f.write(f"**Cost:** ${float(cost):.4f}\n")
        except ValueError:
            f.write(f"**Cost:** ${cost}\n")
    f.write("\n")


def _write_token_limit_warnings(
    f,
    model: str,
    asset_id: str,
    tokens_used: int | None,
    reasoning_tokens: int | None,
    output_tokens: int | None,
    token_limit_cutoff: bool,
) -> None:
    """Schreibt die Warn-/Hinweis-Blöcke rund um Token-Limit-Cutoff & Reasoning-Verbrauch."""
    # Reasoning-Token-Budget-Block: Reasoning-Tokens haben Output verdrängt
    if reasoning_tokens and reasoning_tokens > 0 and token_limit_cutoff:
        if output_tokens:
            # Echte Usage: Output-Tokens (inkl. Thinking) minus Thinking = sichtbarer Output
            visible_output = max(0, output_tokens - reasoning_tokens)
            _approx_note = ""
        else:
            # Legacy-Fallback (keine Output-Usage): grobe Schätzung aus der Gesamtsumme
            visible_output = max(0, (tokens_used or 0) - reasoning_tokens)
            _approx_note = " (geschätzt)"
        f.write(
            f"> [!WARNING]\n"
            f"> **Reasoning-Tokens haben Output-Budget verdrängt:** Dieses Reasoning-Modell hat {reasoning_tokens} Tokens intern "
            f"für Denk-/Chain-of-Thought-Prozesse verbraucht, die nicht im Output erscheinen. "
            f"Verbleibende Output-Tokens: {visible_output}{_approx_note}. "
            f"Das Token-Budget wurde erschöpft bevor die vollständige Antwort generiert werden konnte. "
            f"Dies ist kein Fehler, sondern eine modellspezifische Eigenschaft von Reasoning-Modellen (z.B. MiniMax M2, DeepSeek R1).\n\n"
        )

    # Token-Budget-Flag: API hat das konfigurierte Output-Limit beschränkt
    if token_limit_cutoff:
        _module_key, _budget = _get_token_budget(str(asset_id))
        if _budget is not None:
            f.write(
                f"> [!NOTE]\n"
                f"> **Token-Budget ausgeschöpft:** Das Modell hat das konfigurierte Output-Budget "
                f"für Modul `{_module_key}` ({_budget} Tokens) vollständig ausgeschöpft. "
                f"Die Antwort wurde durch dieses Limit beschränkt — der tatsächliche Output wäre länger gewesen. "
                f"Product Engineers: Dieser Task-Typ triggert systematisch das Output-Limit bei diesem Modell.\n\n"
            )

            if _is_unknown_reasoning_model(str(model), reasoning_tokens):
                f.write(
                    f"> [!WARNING]\n"
                    f"> **Mögliches Reasoning-Modell nicht erkannt:** `{model}` hat das Token-Budget "
                    f"für Modul `{_module_key}` ({_budget} Tokens) vollständig ausgeschöpft, "
                    f"ist aber weder als Reasoning-Modell klassifiziert noch wurden `reasoning_tokens > 0` "
                    f"in den API-Metadaten gemeldet. Falls dieses Modell intern Chain-of-Thought betreibt "
                    f"(Thinking-Tokens ohne sichtbare Tags), erklärt das den Budget-Engpass.\n"
                    f"> \n"
                    f"> **Empfohlene Aktion:**\n"
                    f"> ```\n"
                    f"> make probe-thinking MODEL={model}\n"
                    f"> # Bei Bestätigung (detected=true):\n"
                    f"> make run-model MODEL={model} --force\n"
                    f"> ```\n\n"
                )


def _write_escalation_ladder_block(
    f,
    reasoning_reask_stage: int | None,
    reasoning_reask_exhausted: bool,
    reasoning_reask_final_budget: int | None,
    cot_calibrated_start: bool,
    reasoning_last_resort: bool = False,
    reasoning_last_resort_budget: int | None = None,
    reasoning_loop_suspected: bool = False,
    reasoning_loop_stage: int = 0,
    reasoning_loop_elapsed_s: float | None = None,
) -> None:
    """Schreibt den Eskalationsleiter-Info-Block (Reviewer-Traceability).

    Analog zu den PC-v3-Eskalations-Badges (Sektion 2.9): Der Meta-Reviewer
    liest diese Blöcke aus den Audit-Logs und interpretiert sie aktiv —
    Stufen-Klettern = Token-Hunger des nicht-terminierenden CoT, Erschöpfung =
    Messgrenze (kein Modellversagen), kalibrierter Start = Benchmark-Historie.
    Denkzeit-Abbruch (``reasoning_loop_suspected``) = Loop-Verdacht: Das
    Modell terminierte nicht binnen ``escalation_time_limit_s`` und wurde vom
    Wächter abgebrochen — abgegrenzt zur Budget-Erschöpfung (Zeit vs. Tokens).
    Ohne Eskalation bleibt der Block komplett weg (keine grünen Fussnoten).
    """
    if not reasoning_reask_stage or reasoning_reask_stage < 2:
        return
    _budget = (
        f"{reasoning_reask_final_budget:,} Tokens"
        if reasoning_reask_final_budget
        else "Eskalationsbudget"
    )
    # Denkzeit-Wächter (höchste Priorität): Der Abbruch erfolgte am Zeitbudget
    # der Eskalationsphase, nicht an einer Token-Grenze — starker Loop-Verdacht.
    if reasoning_loop_suspected:
        _elapsed = (
            f"{reasoning_loop_elapsed_s:,.0f} s"
            if reasoning_loop_elapsed_s
            else "das Eskalations-Zeitbudget"
        )
        _stage_detail = (
            f" in Stufe {reasoning_loop_stage}"
            if reasoning_loop_stage
            else ""
        )
        f.write(
            f"> [!CAUTION]\n"
            f"> **⏱ Denkzeit-Wächter ausgelöst: Abbruch{_stage_detail} nach "
            f"{_elapsed}.** Das Modell lief in der Eskalationsphase in eine "
            f"nicht terminierende Thinking-Kette und wurde vom Loop-Guard "
            f"(``reasoning_reask.escalation_time_limit_s``) abgebrochen — die "
            f"Token-Budgets (bis {_budget}) waren zu diesem Zeitpunkt NICHT "
            f"ausgeschöpft. **Interpretation: hoher Loop-Verdacht "
            f"(reasoning_loop_suspected)**, abgegrenzt zur Budget-Erschöpfung "
            f"(reasoning_reask_exhausted = Token-Grenze erreicht, Zeit ok). "
            f"Die 0-%-Bewertung misst den Denkloop, nicht die Aufgabenqualität.\n\n"
        )
        return
    # Last-Resort (letzte Leiter-Stufe): eigener, prominenter Block — die
    # bewertete Antwort entstand unter geöffnetem Budget; der Token-Hunger und
    # die Einsatzkosten sind der Kernbefund. KEINE Card-Kalibrierung (bewusst).
    if reasoning_last_resort:
        _lrb = (
            f"{reasoning_last_resort_budget:,} Tokens"
            if reasoning_last_resort_budget
            else "geöffnetes Budget"
        )
        if reasoning_reask_exhausted:
            f.write(
                f"> [!CAUTION]\n"
                f"> **⛔ Last-Resort erschöpft: Stufe {reasoning_reask_stage} ({_lrb}) "
                f"ohne sichtbaren Output.** Auch das deutlich geöffnete Budget "
                f"verbrannte vollständig im internen Reasoning — endgültige "
                f"Messgrenze des Frameworks, kein Modellversagen. Die 0-%-Bewertung "
                f"misst die Messgrenze.\n\n"
            )
        else:
            f.write(
                f"> [!CAUTION]\n"
                f"> **🚨 Last-Resort-Modus: Stufe {reasoning_reask_stage} ({_lrb}) "
                f"über der Erschöpfungsgrenze ({_budget}).** Die regulären "
                f"Eskalationsstufen endeten ohne sichtbaren Output — für DIESE "
                f"Frage wurde das Budget geöffnet, die bewertete Antwort entstand "
                f"unter diesem geöffneten Budget.\n"
                f"> **Einsatzkosten:** Erstversuch + Leiter + Last-Resort = "
                f"außergewöhnlicher Ressourcen-Aufwand (API-Kosten bzw. "
                f"Stromkosten im lokalen Betrieb) — siehe Token-Verbrauch im "
                f"Header. Bewusste Ausnahme: KEINE Card-Kalibrierung, das "
                f"Standard-Budget bleibt unverändert.\n\n"
            )
        if cot_calibrated_start:
            f.write(
                "> [!NOTE]\n"
                "> **📌 Start aus Card-Kalibrierung:** Der Erstversuch lief bereits "
                "auf einem persistierten Start-Budget (`cot_budget_calibration` in "
                "der Model Card).\n\n"
            )
        return
    if reasoning_reask_exhausted:
        f.write(
            f"> [!CAUTION]\n"
            f"> **⛔ Leiter erschöpft: Stufe {reasoning_reask_stage} ({_budget}) ohne "
            f"sichtbaren Output — Messgrenze, kein Modellversagen.** Das Modell verbrannte "
            f"auch das eskalierte Budget vollständig im internen Reasoning (nicht-terminierende "
            f"Thinking-Kette). Die 0-%-Bewertung misst die Messgrenze des Frameworks, "
            f"nicht die Aufgabenqualität.\n\n"
        )
    else:
        f.write(
            f"> [!NOTE]\n"
            f"> **🔁 Eskalationsleiter: Stufe {reasoning_reask_stage} ({_budget}) erfolgreich.** "
            f"Der Erstversuch verbrannte sein komplettes Budget im internen Reasoning "
            f"(0 sichtbarer Output); erst die eskalierte Stufe lieferte die bewertete Antwort.\n\n"
        )
    if cot_calibrated_start:
        f.write(
            "> [!NOTE]\n"
            "> **📌 Start aus Card-Kalibrierung:** Der Erstversuch lief bereits auf einem "
            "persistierten Start-Budget (`cot_budget_calibration` in der Model Card) — "
            "Ergebnis früherer Eskalationen, kein Standard-Modul-Budget.\n\n"
        )


def _is_unknown_reasoning_model(model: str, reasoning_tokens: int | None) -> bool:
    """Prüft, ob ein Modell weder als Reasoning noch als Thinking-Optional erkannt wurde.

    Wird für den Maintainer-Hinweis bei unentdecktem Reasoning-Budget-Verbrauch genutzt.
    """
    _is_reasoning = False
    _is_thinking_optional = False
    try:
        from utils.model_utils import is_reasoning_model, is_thinking_optional_from_card
        _is_reasoning = is_reasoning_model(str(model))
        _is_thinking_optional = is_thinking_optional_from_card(str(model))
    except Exception:
        pass
    return not _is_reasoning and not reasoning_tokens and not _is_thinking_optional


def _demote_headers_safe(text: str) -> str:
    """Stuft Markdown-Header ab (H1/H2 → H3-H6), ohne Codeblöcke zu verändern."""
    import re

    blocks = re.split(r'(```.*?```)', text, flags=re.DOTALL)
    for i, _ in enumerate(blocks):
        if i % 2 == 0:
            # Stuft Überschriften ab, limitiert sie aber strikt auf maximal H6 und min H3
            blocks[i] = re.sub(
                r'^((?:>\s*)*)(#+)\s',
                lambda m: str(m.group(1)) + '#' * min(6, max(3, len(m.group(2)) + 1)) + ' ',
                blocks[i],
                flags=re.MULTILINE
            )
    return "".join(blocks)


def _write_response_block(f, response: str, think_content: str | None) -> None:
    """Schreibt den Model-Response-Block inkl. ThinkContent-Fallback."""
    safe_response = _demote_headers_safe(str(response))
    if safe_response.strip():
        f.write(f"{safe_response}\n\n")
        return

    if think_content:
        f.write(
            "> [!NOTE]\n> **Kein sichtbarer Output.** Das Modell hat ausschließlich intern (ThinkChunk) "
            "gearbeitet und keinen formatierten Antworttext produziert. Der Reasoning-Inhalt wird zur "
            "Information unten angezeigt — er geht nicht in die Wertung ein.\n\n"
        )
        safe_think = _demote_headers_safe(str(think_content))
        f.write(f"{safe_think}\n\n")
        return

    f.write(f"{safe_response}\n\n")

def calculate_timeout_metrics(execution_times: list[float], timeout_count: int, total_tests: int) -> dict:
    """Berechnet globale P95-Antwortzeiten und kategorisiert die Timeout-Rate des aktuellen Modul-Durchlaufs.

    Semantik von ``timeout_count`` (2026-09-01): Zählt ausschließlich echte
    Fehler/Abbrüche (``status == "error"``) — siehe
    ``UnifiedBenchmarkRunner._record_global_metrics``. Die Antwortdauer fließt
    bewusst NICHT ein (P95-Antwortzeit + Tokens/s + Speed-Badge decken sie ab);
    ein langsamer, aber vollständiger Lauf ist zuverlässig, nicht ausgefallen.
    """
    import statistics

    p95 = 0.0
    if execution_times:
        valid_times = [t for t in execution_times if t is not None]
        if len(valid_times) > 1:
            try:
                p95 = statistics.quantiles(valid_times, n=20)[18]
            except statistics.StatisticsError:
                p95 = max(valid_times)
        elif len(valid_times) == 1:
            p95 = valid_times[0]

    rate = timeout_count / total_tests if total_tests > 0 else 0
    if timeout_count == 0:
        category = "✅ Stabil"
    elif rate <= 0.07:
        category = "⚠️ Sporadisch"
    elif rate <= 0.35:
        category = "🔴 Unzuverlässig"
    else:
        category = "❌ Nicht einsetzbar"

    return {
        "p95": round(p95, 2),
        "timeout_count": timeout_count,
        "total_tests": total_tests,
        "ratio_category": category,
        "rate": rate
    }


def token_distribution(values: list[int]) -> dict[str, int]:
    """Median/avg/P95/Max-Verteilung über Token-Werte (leer-sicher).

    SSoT für PC-v3-Statistiken (Modul-Monitoring, Bias-Report, Kalibrierungs-
    skript) — ein gemeinsamer P95-Schätzer verhindert Drift zwischen
    Kalibrierungs-Empfehlung und Monitoring-Warnung (Review 2026-08-29).
    Verwendet statistics.quantiles (n=20, Index 18) wie calculate_timeout_metrics.
    """
    import statistics

    if not values:
        return {"median": 0, "avg": 0, "p95": 0, "max": 0}
    sorted_vals = sorted(values)
    try:
        p95 = (
            statistics.quantiles(sorted_vals, n=20)[18]
            if len(sorted_vals) > 1
            else sorted_vals[0]
        )
    except statistics.StatisticsError:
        p95 = sorted_vals[-1]
    # Exclusive-Quantile extrapolieren bei kleinen n über das Maximum hinaus
    # (n=4: P95 > Max) — für Token-Reports unsinnig, daher geclampt.
    p95 = min(int(p95), sorted_vals[-1])
    return {
        "median": int(statistics.median(sorted_vals)),
        "avg": int(sum(sorted_vals) / len(sorted_vals)),
        "p95": p95,
        "max": sorted_vals[-1],
    }

def append_global_run_metrics(model: str, asset_ids: list[str],
                              execution_times: list[float],
                              timeout_count: int,
                              total_tests: int,
                              module_name: str = "Unknown") -> None:
    """Hängt die berechneten globalen Metriken an alle erzeugten Markdown-Logs eines Modul-Laufs an."""
    from pathlib import Path
    import re

    model_safe = _safe_name(str(model))
    out_dir = Path(f"outputs/audit_logs/{model_safe}")
    metrics = calculate_timeout_metrics(execution_times, timeout_count, total_tests)

    append_text = f"\n\n---\n\n### 📦 Modul-Metriken ({module_name})\n\n"
    append_text += f"- **P95-Antwortzeit:** {metrics['p95']} s\n"
    append_text += f"- **Timeout-Rate:** {metrics['timeout_count']}/{metrics['total_tests']} ({metrics['ratio_category']})\n"

    for asset_id in asset_ids:
        f_path = out_dir / f"{asset_id}.md"
        if f_path.exists():
            with open(f_path, "r+", encoding="utf-8") as f:
                content = f.read()
                # Execution Time anpassen, sodass P95 mit im Header steht.
                # Guard: bereits vorhandene (Modul-P95: ...) Suffixe konsumieren,
                # damit bei Re-Runs keine Akkumulation entsteht.
                content = re.sub(
                    r"(\*\*Execution Time:\*\* [\d.]+ s)(?:\s*\(Modul-P95: [\d.]+ s\))*",
                    fr"\1 (Modul-P95: {metrics['p95']} s)",
                    content,
                    count=1
                )
                if append_text not in content:
                    content += append_text

                f.seek(0)
                f.write(content)
                f.truncate()


def _write_refusal_retry_block(
    f: Any,
    refusal_retry_used: bool,
    refusal_retry_original_prompt: str | None = None,
) -> None:
    """Schreibt den Refusal-Retry-Info-Block (Reviewer-Traceability).

    Dokumentiert, dass der Erstversuch serverseitig verweigert wurde
    (finish_reason=refusal, z. B. Anthropic stop_reason=refusal) und die
    bewertete Antwort aus einem Zweitversuch mit entschärfter Prompt-Fassung
    stammt (refusal_retry_prompt im Asset). Der Meta-Reviewer MUSS diese
    Information prominent im Modell-Report verarbeiten (Check
    "Safety-Refusal & Tag-freier Retry" in meta_reviewer_prompt.yaml):
    Die Bewertung bezieht sich auf den Zweitversuch; das
    Verweigerungsverhalten des Original-Prompts ist ein eigenständiger
    Befund (Modell-Sicherheitsschicht, nicht Aufgabenqualität).
    Ohne Retry bleibt der Block komplett weg.

    ``refusal_retry_original_prompt`` schreibt die verweigerte Erstversuch-
    Fassung in den Block (Schattenmetrik-Parität zur Eskalationsleiter):
    Sektion 1 zeigt die tatsächlich gestellte Retry-Fassung (via
    ``evaluated_prompt``), der Reviewer braucht aber auch das Original,
    um das Refusal-Verhalten als Befund bewerten zu können.
    """
    if not refusal_retry_used:
        return
    f.write(
        "> [!IMPORTANT]\n"
        "> **🚫→🔁 Safety-Refusal-Retry:** Der Erstversuch wurde serverseitig "
        "verweigert (finish_reason=refusal — die API blockte die Anfrage vor "
        "der Generierung, 0 Output-Tokens). Die bewertete Antwort stammt aus "
        "einem **Zweitversuch mit entschärfter Prompt-Fassung** "
        "(refusal_retry_prompt im Asset): identische Frage und "
        "Bewertungsgrundlage — nur das verweigerungsauslösende Element wurde "
        "entfernt bzw. defensiver umformuliert (z. B. <thought>-Tag-"
        "Formatanweisung bei Metacog-Assets oder Remediation-Framing beim "
        "Security-Audit).\n"
        "> **Für den Reviewer:** (1) Der Score misst die Aufgabenfähigkeit "
        "aus dem Zweitversuch — fair und vergleichbar mit kooperativen "
        "Modellen. (2) Das Refusal-Verhalten selbst ist ein eigenständiger "
        "Befund: Das Modell lehnt die Formatanweisung ab (vermutlich "
        "Sicherheitsschicht gegen erzwungene Pseudo-Denken-Tags; Evidenz: "
        "A/B-Test 2026-09-24). (3) Erwähne beides im Report: Fähigkeit UND "
        "Verweigerungsverhalten.\n\n"
    )
    if refusal_retry_original_prompt:
        f.write(
            "<details>\n"
            "<summary>🚫 Verweigerte Original-Fassung (Erstversuch, "
            "finish_reason=refusal)</summary>\n\n"
            "```\n"
            f"{refusal_retry_original_prompt.strip()}\n"
            "```\n\n"
            "</details>\n\n"
        )
