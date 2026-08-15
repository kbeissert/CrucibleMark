"""Textuelle provider_config.yaml-Block-Helfer (SSoT).

Diese drei Funktionen manipulieren die provider_config.yaml als Textdatei
(kommentarerhaltend, kein yaml.dump). Sie waren zuvor identisch in
scripts/maintenance/audit_markdown.py und scripts/dev/sync_cost_limits.py
dupliziert (Review 2026-08-15, DRY-Verstoß) und sind jetzt hier konsolidiert.
"""

from __future__ import annotations


def find_providers_block(lines: list[str]) -> tuple[int | None, int]:
    """Findet Zeilenbereich des Top-Level `providers:`-Blocks."""
    providers_start: int | None = None
    providers_end: int = len(lines)
    for i, line in enumerate(lines):
        if line.rstrip() == "providers:":
            providers_start = i
        elif (
            providers_start is not None
            and line
            and not line[0].isspace()
            and not line.startswith("#")
        ):
            providers_end = i
            break
    return providers_start, providers_end


def find_section_line(
    lines: list[str], section_header: str, start: int, end: int
) -> int | None:
    """Findet die Zeilennummer eines Section-Headers im Bereich [start, end)."""
    for i in range(start, end):
        if lines[i].rstrip() == section_header:
            return i
    return None


def find_insert_index(
    lines: list[str], section_line_idx: int, providers_end: int
) -> int:
    """Findet die Einfüge-Position: vor daily_budget: oder nächstem Sub-Key."""
    insert_before: int | None = None
    for i in range(section_line_idx + 1, providers_end):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.startswith("daily_budget:"):
            insert_before = i
            break
        if indent <= 2 and stripped and not stripped.startswith("#"):
            insert_before = i
            break
    return providers_end if insert_before is None else insert_before
