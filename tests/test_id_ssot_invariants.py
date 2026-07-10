"""Phase 5: Härtet die ID-SSoT-Garantien ab.

Pruefungen:
  1. Bruecken-Aequivalenz: enforce_card_first() und resolve_canonical_model_id()
     liefern fuer jede Eingabe dieselbe kanonische Form.
  2. Slugify-Konsistenz: _safe_name() deckt alle Sonderzeichen ab, die in
     model_ids auftauchen.
  3. Idempotenz: enforce_card_first() darf beliebig oft aufgerufen werden
     ohne die kanonische Form zu aendern.
  4. Kein Inline-re.sub fuer ID-Transformation: ID-Transformationen duerfen
     nur in utils/model_utils.py und utils/card_utils.py definiert sein.
     Wird ueber statischen AST-Sweep erzwungen.
"""
import ast
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.model_utils import (  # noqa: E402
    _safe_name,
    enforce_card_first,
    resolve_canonical_model_id,
)


# ---------------------------------------------------------------------------
# 1. Bruecken-Aequivalenz
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw",
    [
        "claude-haiku-4-5",
        "claude-haiku-4-5-20251001",
        "qwen3.5-35b-a3b-q8",
        "qwen3_5-35b-a3b-q8",
        "hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M",
        "moonshotai/kimi-k2-0711",
        "gpt-5",
        "  leer-strip-test  ",
    ],
)
def test_enforce_card_first_matches_resolve_canonical(monkeypatch, tmp_path, raw):
    """enforce_card_first() liefert dieselbe kanonische Form wie resolve_canonical_model_id()."""
    monkeypatch.setattr("utils.model_utils.CARD_DIR", tmp_path)
    monkeypatch.setattr("utils.model_card_io.CARD_DIR", tmp_path)
    expected = resolve_canonical_model_id(raw)
    actual, _has_card = enforce_card_first(raw)
    assert actual == expected


# ---------------------------------------------------------------------------
# 2. Slugify-Konsistenz
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("foo/bar", "foo_bar"),
        ("foo:bar", "foo_bar"),
        ("foo.bar", "foo_bar"),
        ("foo bar", "foo_bar"),
        ("a/b.c:d e", "a_b_c_d_e"),
        # hf.co-Prefix wird zuerst gestrippt
        ("hf.co/x/y", "y"),
    ],
)
def test_safe_name_handles_all_separators(raw, expected):
    """_safe_name() deckt : / . Leerzeichen ab."""
    assert _safe_name(raw) == expected


# ---------------------------------------------------------------------------
# 3. Idempotenz
# ---------------------------------------------------------------------------

def test_enforce_card_first_idempotent(monkeypatch, tmp_path):
    """Auch nach 10 Aufrufen bleibt die kanonische Form stabil."""
    monkeypatch.setattr("utils.model_utils.CARD_DIR", tmp_path)
    monkeypatch.setattr("utils.model_card_io.CARD_DIR", tmp_path)
    raw = "wiederholungs-test-001"
    first, _ = enforce_card_first(raw)
    for _ in range(10):
        again, _ = enforce_card_first(first)
        assert again == first


# ---------------------------------------------------------------------------
# 4. Statischer Sweep: keine Inline-ID-Transformationen ausserhalb model_utils.py/card_utils.py
# ---------------------------------------------------------------------------

_ALLOWED_FILES = {
    Path("utils/model_utils.py").resolve(),
    Path("utils/model_id_base.py").resolve(),
    Path("utils/model_card_io.py").resolve(),
    Path("utils/card_utils.py").resolve(),
}

# AST-Visitor der re.sub-Aufrufe mit model_id-/safe_name-relevanter Regex findet.
# Heuristik: re.sub-Aufrufe, deren Pattern einen der Sonderzeichen : / . oder
# ein alphanumer-strip-Muster enthaelt.
_RE_SUB_AST_NAME = "re.sub"


def _is_id_transform_pattern(pattern: str) -> bool:
    """True wenn das re.sub-Pattern eine ID-/Slug-Transformation beschreibt."""
    if not pattern:
        return False
    # Zeichenklassen, die auf Slugify/ID-Normalisierung hindeuten
    markers = [r"[:/.\-]", r"[^a-z0-9]", r"[^a-zA-Z0-9]"]
    return any(m in pattern for m in markers)


# Marker fuer model_id-Use-Case: wenn eine Funktion diese Namen verwendet,
# ist der re.sub darin ein Kandidat fuer den Sweep.
_MODEL_ID_MARKERS = {"model_id", "model_card", 'r["model"]', "r['model']"}


def _enclosing_function_uses_model_id(node: ast.Call, tree: ast.Module) -> bool:
    """True wenn der naechste umschliessende FunctionDef model_id-Marker verwendet."""
    for parent in ast.walk(tree):
        if not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not (getattr(parent, "end_lineno", parent.lineno) >= node.lineno >= parent.lineno):
            continue
        source = ast.dump(parent)
        return any(marker in source for marker in _MODEL_ID_MARKERS)
    return False


def _scan_python_file(path: Path) -> list[tuple[int, str]]:
    """Findet re.sub-Aufrufe mit ID-Transform-Pattern in Funktionen,
    die model_id-Marker verwenden.
    """
    findings: list[tuple[int, str]] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return findings
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "sub"):
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "re"):
            continue
        if not (node.args and isinstance(node.args[0], ast.Constant)):
            continue
        pattern = node.args[0].value
        if not (isinstance(pattern, str) and _is_id_transform_pattern(pattern)):
            continue
        if not _enclosing_function_uses_model_id(node, tree):
            continue
        findings.append((node.lineno, pattern))
    return findings


def test_no_inline_id_transforms_outside_ssm_modules():
    """In utils/ und scripts/ darf kein Inline-re.sub fuer model_id-IDs liegen.

    Ausnahmen: utils/model_utils.py, utils/card_utils.py (SSoT-Module).
    Provider-Card-Slugifier (re.sub in Funktionen ohne model_id-Marker)
    zaehlen NICHT -- sie sind ein anderer Use-Case.
    """
    root = Path(__file__).resolve().parents[1]
    scan_roots = [root / "utils", root / "scripts"]
    violations: list[str] = []
    for scan_root in scan_roots:
        for py_file in scan_root.rglob("*.py"):
            if py_file.resolve() in _ALLOWED_FILES:
                continue
            for lineno, pattern in _scan_python_file(py_file):
                rel = py_file.relative_to(root)
                violations.append(f"{rel}:{lineno}: re.sub({pattern!r})")
    assert not violations, (
        "Inline-model_id-Transformationen gefunden. Diese Stellen muessen ueber "
        "utils.model_utils._safe_name/resolve_canonical_model_id laufen:\n"
        + "\n".join(violations)
    )


# ---------------------------------------------------------------------------
# Phase 12: Audit-Log-Ordner muessen _safe_name-konform sein.
#
# Vor Phase 12 hatten 29 von 83 audit_logs-Ordnern Punkte in der ID
# ("gpt-5.4/" statt "gpt-5_4/"). Die Review-Generierung hat deshalb
# fuer diese Modelle keine Reviews gefunden. Diese Invariante verhindert
# den Drift in Zukunft.
# ---------------------------------------------------------------------------

def test_audit_logs_dirs_use_safe_name():
    """Alle outputs/audit_logs/<X>/ MÜSSEN _safe_name(X) == X entsprechen.

    Ausnahme: ".DS_Store" (macOS-Artifact).
    """
    root = Path(__file__).resolve().parents[1]
    audit_dir = root / "outputs" / "audit_logs"
    if not audit_dir.exists():
        pytest.skip("outputs/audit_logs/ existiert nicht in dieser Umgebung")

    offenders: list[str] = []
    for d in audit_dir.iterdir():
        if not d.is_dir() or d.name == ".DS_Store":
            continue
        if _safe_name(d.name) != d.name:
            offenders.append(f"{d.name!r} -> _safe_name -> {_safe_name(d.name)!r}")

    assert not offenders, (
        "Audit-Log-Ordner sind nicht _safe_name-konform. Diese Ordner verhindern, "
        "dass die Review-Generierung Modelle mit Punkten/Slashes in der ID findet.\n"
        "Loesung: `mv outputs/audit_logs/<X> outputs/audit_logs/<_safe_name(X)>`\n"
        "Betroffene Ordner:\n" + "\n".join(offenders)
    )
