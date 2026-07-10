"""SSoT-Guardrail: _extract_reasoning_tokens darf nur in cohere.py override-definiert sein.

Die Base-Methode in ``utils/providers/base.py`` prueft bereits alle 3 Pfade
(OpenAI ``completion_tokens_details``, Anthropic ``output_tokens_details``,
Mistral ``reasoning_tokens``). Provider-spezifische Overrides sind nur fuer
genuin abweichende Formate erlaubt — aktuell nur Cohere
(``tokens.reasoning_tokens``).

Dieser AST-Sweep stellt sicher, dass keine dead no-op Stubs
(``return super()._extract_reasoning_tokens(usage)``) wieder eingefuehrt
werden. Dead Stubs verdecken, dass die Base-Methode bereits alles abdeckt,
und erzeugen Wartungslast ohne Funktionsgewinn.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_DIR = ROOT / "utils" / "providers"

# base.py definiert die SSoT-Methode; cohere.py hat die einzige genuine Override.
_ALLOWED_OVERRIDE_FILES: frozenset[str] = frozenset({"base.py", "cohere.py"})


def _find_method_defs(tree: ast.Module, method_name: str) -> list[ast.FunctionDef]:
    """Findet alle Methoden-Definitionen mit dem gegebenen Namen im AST."""
    results: list[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            results.append(node)
    return results


def test_no_dead_noop_stubs_in_providers() -> None:
    """Kein Provider darf einen dead no-op Stub fuer _extract_reasoning_tokens definieren.

    Ein dead no-op Stub ist eine Methode, die nur ``return super()._extract_reasoning_tokens(usage)``
    enthaelt. Die Base-Methode macht genau das schon — der Stub ist redundant.
    """
    dead_stubs: list[str] = []

    for py_file in sorted(PROVIDERS_DIR.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for method in _find_method_defs(tree, "_extract_reasoning_tokens"):
            # Pruefe ob der Body nur aus einem return super()._extract_reasoning_tokens(usage) besteht
            body = method.body
            if len(body) != 1:
                continue
            stmt = body[0]
            if not isinstance(stmt, ast.Return):
                continue
            val = stmt.value
            if not isinstance(val, ast.Call):
                continue
            func = val.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr != "_extract_reasoning_tokens":
                continue
            if not isinstance(func.value, ast.Call):
                continue
            super_func = func.value.func
            if isinstance(super_func, ast.Name) and super_func.id == "super":
                dead_stubs.append(py_file.name)

    assert not dead_stubs, (
        f"Dead no-op _extract_reasoning_tokens Stubs gefunden in: {dead_stubs}. "
        "Die Base-Methode in base.py prueft bereits alle Pfade (OpenAI/Anthropic/Mistral). "
        "Diese Stubs sind redundant und sollen geloescht werden."
    )


def test_only_cohere_defines_override() -> None:
    """Nur cohere.py darf _extract_reasoning_tokens definieren (genuine Override).

    Alle anderen Provider nutzen die Base-Methode aus base.py.
    """
    override_files: list[str] = []

    for py_file in sorted(PROVIDERS_DIR.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        methods = _find_method_defs(tree, "_extract_reasoning_tokens")
        if methods:
            override_files.append(py_file.name)

    unexpected = set(override_files) - _ALLOWED_OVERRIDE_FILES
    assert not unexpected, (
        f"Unerwartete Provider definieren _extract_reasoning_tokens: {sorted(unexpected)}. "
        f"Nur {_ALLOWED_OVERRIDE_FILES} darf eine Override haben. "
        "Wenn ein neuer Provider ein genuin abweichendes Usage-Format hat, "
        "fuege ihn zu _ALLOWED_OVERRIDE_FILES hinzu und dokumentiere warum."
    )


@pytest.mark.parametrize("provider_file", sorted(PROVIDERS_DIR.glob("*.py")))
def test_base_method_exists(provider_file: Path) -> None:
    """Stellt sicher, dass base.py die SSoT-Methode definiert."""
    if provider_file.name != "base.py":
        pytest.skip("Nur base.py wird auf die SSoT-Methode geprueft")

    tree = ast.parse(provider_file.read_text(encoding="utf-8"))
    methods = _find_method_defs(tree, "_extract_reasoning_tokens")
    assert len(methods) == 1, (
        f"base.py muss genau EINE _extract_reasoning_tokens-Methode definieren, "
        f"gefunden: {len(methods)}"
    )
