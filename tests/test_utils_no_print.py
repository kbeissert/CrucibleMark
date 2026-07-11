"""SSoT-Guardrail: Keine print()-Calls in utils/ Framework-Utils (außer logging_config.py).

Framework-Utils nutzen logging statt print(). CLI-Skripte (scripts/) dürfen
print() für User-Facing-Output behalten. Provider-Connectors (utils/providers/)
und Scoring (utils/scoring/) sind von diesem Test ausgenommen (separate Sektion).
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
UTILS_DIR = REPO_ROOT / "utils"

# logging_config.py: konfiguriert das Logging selbst (braucht print für Test-Output).
# benchmark_ui.py: Terminal-UI-Komponente — print(end='\r') für Live-Progress
#   ist ein legitimer UI-Anwendungsfall, den logging nicht abbilden kann
#   (logging unterstützt kein Carriage-Return-Zeilenüberschreiben).
EXCLUDED_FILES = {"logging_config.py", "benchmark_ui.py"}


def _collect_top_level_utils_py() -> list[Path]:
    """Top-Level utils/*.py — keine Subdirectories."""
    return sorted(
        p for p in UTILS_DIR.glob("*.py")
        if p.is_file() and p.name != "__init__.py"
    )


def _find_print_calls(py_file: Path) -> list[tuple[int, str]]:
    """Liefert (Zeilennummer, Quelltext-Zeile) für jeden print()-Call."""
    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(py_file))
    results: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            line_text = source.splitlines()[node.lineno - 1].strip()
            results.append((node.lineno, line_text))
    return results


@pytest.mark.parametrize("py_file", _collect_top_level_utils_py(), ids=lambda p: p.name)
def test_no_print_calls_in_framework_utils(py_file: Path) -> None:
    """Framework-Utils (außer logging_config.py) dürfen kein print() enthalten."""
    if py_file.name in EXCLUDED_FILES:
        pytest.skip(f"{py_file.name} ist ausgenommen (Logging-Setup)")

    offenders = _find_print_calls(py_file)
    if offenders:
        formatted = "\n".join(f"  L{ln}: {txt}" for ln, txt in offenders)
        pytest.fail(
            f"{py_file.relative_to(REPO_ROOT)} enthält {len(offenders)} print()-Call(s):\n"
            f"{formatted}\n"
            f"→ Ersetze durch logger.info/warning/error (logging statt print)."
        )
