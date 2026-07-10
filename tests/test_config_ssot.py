"""SSoT-Guardrail: Keine raw yaml.safe_load auf benchmark_config/provider_config.

Skripte muessen ConfigValidator nutzen, um Config-Hierarchie (Global -> Modul -> Runtime)
korrekt zu mergen. Raw-loads umgehen Caching und Merge-Logik.

Modul-Configs (benchmark_modules/*/config.yaml) und andere YAMLs duerfen weiterhin
direkt geladen werden - sie sind nicht Teil des ConfigValidator-Merge.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Skripte in scripts/legacy sind einmalige Migrationen (nicht aktiv gepflegt).
# utils/ ist Framework-Code und nutzt ConfigValidator bereits (Implementierung
# in utils/config_validator.py darf yaml.safe_load aufrufen).
IGNORED_DIRS = {"legacy", "__pycache__"}
IGNORED_FILES = {
    "utils/config_validator.py",
    "utils/__init__.py",
    "scripts/__init__.py",
}

# String-Argumente, die wir als "ok" betrachten - sie verweisen NICHT auf
# die zentralen Config-Dateien (benchmark_config.yaml oder provider_config.yaml).
# Alles andere muss gegen die SSoT migriert sein.
CONFIG_PATH_NEEDLES = ("benchmark_config", "provider_config")


def _iter_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(REPO_ROOT)
        parts = rel.parts
        if any(p in IGNORED_DIRS for p in parts):
            continue
        rel_str = rel.as_posix()
        if rel_str in IGNORED_FILES:
            continue
        files.append(path)
    return files


def _find_yaml_safe_load_calls(tree: ast.AST) -> list[ast.Call]:
    """Sammelt alle ``yaml.safe_load(...)`` Call-Nodes."""
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if func.attr != "safe_load":
            continue
        value = func.value
        if not isinstance(value, ast.Name):
            continue
        if value.id != "yaml":
            continue
        calls.append(node)
    return calls


def _arg_looks_like_central_config(arg: ast.AST) -> bool:
    """Prueft ein einzelnes Call-Argument auf benchmark_config/provider_config-Hinweise."""
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return any(needle in arg.value for needle in CONFIG_PATH_NEEDLES)
    if isinstance(arg, ast.JoinedStr):
        for value in arg.values:
            if (
                isinstance(value, ast.Constant)
                and isinstance(value.value, str)
                and any(needle in value.value for needle in CONFIG_PATH_NEEDLES)
            ):
                return True
        return False
    if isinstance(arg, ast.Call):
        # Annahme: Path() / "benchmark_config.yaml" o.ae. - heuristik: walk
        for sub in ast.walk(arg):
            if (
                isinstance(sub, ast.Constant)
                and isinstance(sub.value, str)
                and any(needle in sub.value for needle in CONFIG_PATH_NEEDLES)
            ):
                return True
        return False
    return False


def _scan_file(path: Path) -> list[tuple[int, str]]:
    """Liefert (line_no, snippet)-Treffer, wenn yaml.safe_load auf zentrale Config zeigt."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    hits: list[tuple[int, str]] = []
    for call in _find_yaml_safe_load_calls(tree):
        for arg in call.args:
            if _arg_looks_like_central_config(arg):
                hits.append((call.lineno, ast.unparse(arg)))
                break
    return hits


def _ripgrep_fallback() -> list[tuple[str, int, str]]:
    """Fallback: rg-Pattern fuer Faelle mit Variablen, die auf zentrale Config verweisen.

    AST verliert variable-name-Aufloesung. Hier suchen wir File+Line, wo im
    YAML-Block + benchmark_config/provider_config in der Naehe auftaucht.

    Nur Code-Zeilen werden geprueft (keine Kommentare), um False Positives zu
    vermeiden - Kommentare, die ``yaml.safe_load`` nur erwaehnen, sind erlaubt.
    """
    import re

    pattern = re.compile(r"benchmark_config|provider_config")
    results: list[tuple[str, int, str]] = []
    for py in _iter_python_files(SCRIPTS_DIR):
        rel = py.relative_to(REPO_ROOT).as_posix()
        try:
            text = py.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "yaml.safe_load" not in text:
            continue
        # Tokenisiere und entferne Kommentare, damit wir nur Code-Zeilen matchen.
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        lines = text.splitlines()
        # Map ast.Call-Nodes (nur yaml.safe_load) auf Line-Numbers.
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "safe_load":
                continue
            if not isinstance(node.func.value, ast.Name):
                continue
            if node.func.value.id != "yaml":
                continue
            lineno = node.lineno
            # Suche die Config-Referenz in den 8 umliegenden Code-Zeilen.
            lo = max(0, lineno - 3)
            hi = min(len(lines), lineno + 8)
            window = "\n".join(lines[lo:hi])
            if pattern.search(window):
                results.append((rel, lineno, lines[lineno - 1].strip()))
    return results


def test_no_raw_yaml_load_on_central_config() -> None:
    """Keine Skripte laden benchmark_config.yaml/provider_config.yaml via yaml.safe_load."""
    bad: list[str] = []
    for path in _iter_python_files(SCRIPTS_DIR):
        rel = path.relative_to(REPO_ROOT)
        for line_no, snippet in _scan_file(path):
            bad.append(f"{rel}:{line_no}: {snippet}")

    if bad:
        msg = "\n".join(bad)
        pytest.fail(
            "Folgende raw yaml.safe_load verweisen auf benchmark_config/"
            "provider_config. Diese muessen ConfigValidator nutzen:\n"
            f"{msg}"
        )


def test_no_ripgrep_fallback_matches() -> None:
    """AST kann Variablen nicht verfolgen - text-basierter Check als Defense in Depth.

    Falls der AST-Test oben zu wenig findet (z.B. Variable haelt den Config-Pfad),
    soll dieser zweite Test zumindest Datei+Line reported.
    """
    hits = _ripgrep_fallback()
    if hits:
        msg = "\n".join(f"{f}:{ln}: {snippet}" for f, ln, snippet in hits)
        pytest.fail(
            "Text-basierter Fallback findet yaml.safe_load + Config-Referenz in der Naehe. "
            "Bitte auf ConfigValidator migrieren:\n"
            f"{msg}"
        )
