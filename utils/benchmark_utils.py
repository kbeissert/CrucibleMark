"""
Shared utilities for benchmark runners.
Contains common logic for interactive selection and asset discovery.
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TypeVar

import yaml

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
    title: Optional[str] = None,
) -> Optional[T]:
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

    try:
        import yaml
        from pathlib import Path as _Path
        _config_path = _Path(__file__).resolve().parent.parent / "benchmark_config.yaml"
        with open(_config_path, "r", encoding="utf-8") as f:
            _cfg = yaml.safe_load(f)
        budget = _cfg.get("token_budgets", {}).get(module_key)
        return module_key, budget
    except Exception:
        return module_key, None


def save_audit_log(
    model: str,
    asset_id: str,
    prompt: str,
    response: str,
    judge_response: str,
    base_dir: Path = Path("outputs/audit_logs"),
    token_limit_cutoff: bool = False,
    token_limit_fallback: bool = False,
    execution_time: float = None,
    tokens_used: int = None,
    tokens_per_second: float = None,
    cost: float = None,
    provider: str = None,
    reasoning_tokens: int = None,
    **kwargs
) -> None:
    """
    Saves a comprehensive audit log for every test, containing prompt, response, and judge feedback.
    """
    try:
        # Create subdirectories for the model
        safe_model = str(model).replace(":", "_").replace("/", "_")
        model_dir = base_dir / safe_model
        model_dir.mkdir(exist_ok=True, parents=True)

        filename = f"{asset_id}.md"
        filepath = model_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Audit Log: {asset_id}\n")
            f.write(f"> **Erstellt am:** {datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}\n")
            f.write(f"**Model:** {model}\n")
            if provider:
                f.write(f"**Provider:** {provider}\n")
            if execution_time is not None:
                f.write(f"**Execution Time:** {execution_time:.2f} s\n")
            if tokens_used is not None:
                f.write(f"**Tokens Used:** {tokens_used}")
                if reasoning_tokens:
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
            if token_limit_fallback:
                f.write("> [!WARNING]\n> Das Modell (bzw. die API) hat das initial angeforderte Token-Limit abgelehnt (zu groß für die Architektur). Das System ist dynamisch auf ein kleineres 4096-Token-Fallback gewechselt. Dies zeigt, dass dieses Modell mit großen Token-Anfragen oder Kontexten Probleme hat!\n\n")

            # Reasoning-Token-Budget-Block: Reasoning-Tokens haben Output verdrängt
            if reasoning_tokens and reasoning_tokens > 0 and token_limit_cutoff:
                output_tokens = (tokens_used or 0) - reasoning_tokens
                f.write(
                    f"> [!WARNING]\n"
                    f"> **Reasoning-Tokens haben Output-Budget verdrängt:** Dieses Reasoning-Modell hat {reasoning_tokens} Tokens intern "
                    f"für Denk-/Chain-of-Thought-Prozesse verbraucht, die nicht im Output erscheinen. "
                    f"Verbleibende Output-Tokens: {max(0, output_tokens)}. "
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


            import re

            def demote_headers_safe(text: str) -> str:
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
            f.write("## 1. Prompt / Fragestellung\n\n")
            safe_prompt = demote_headers_safe(str(prompt))
            formatted_prompt = "\n".join([f"> {line}" for line in safe_prompt.split("\n")])
            f.write(f"{formatted_prompt}\n\n")

            f.write("## 2. Model Response / Antwort\n\n")
            if token_limit_cutoff:
                f.write("> [!CAUTION]\n> Das Modell hat das maximale Token-Limit erreicht und die Antwort abgebrochen. Die folgende Antwort ist INKOMPLETT und zeigt an, dass das Modell für diese Aufgabe zu gesprächig (verbose) war.\n\n")

            safe_response = demote_headers_safe(str(response))
            f.write(f"{safe_response}\n\n")

            f.write("## 3. Evaluation / LLM-Judge / Scorer\n\n")
            safe_judge = demote_headers_safe(str(judge_response))
            f.write(f"{safe_judge}\n")
    except OSError as e:
        logger.warning("Failed to save audit log for %s: %s", asset_id, e)

def calculate_timeout_metrics(execution_times: list[float], timeout_count: int, total_tests: int) -> dict:
    """Berechnet globale P95-Antwortzeiten und kategorisiert die Timeout-Rate des aktuellen Modul-Durchlaufs."""
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

def append_global_run_metrics(model: str, asset_ids: list[str],
                              execution_times: list[float],
                              timeout_count: int,
                              total_tests: int,
                              module_name: str = "Unknown") -> None:
    """Hängt die berechneten globalen Metriken an alle erzeugten Markdown-Logs eines Modul-Laufs an."""
    from pathlib import Path
    import re

    model_safe = str(model).replace(":", "_").replace("/", "_")
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
                # Execution Time anpassen, sodass P95 mit im Header steht
                content = re.sub(
                    r"(\*\*Execution Time:\*\* [\d.]+ s)",
                    fr"\1 (Modul-P95: {metrics['p95']} s)",
                    content,
                    count=1
                )
                if append_text not in content:
                    content += append_text

                f.seek(0)
                f.write(content)
                f.truncate()
