import os
import re
import argparse


def _collect_target_files() -> tuple[list[str], list[str]]:
    files_to_check_md: list[str] = []
    files_to_check_yaml: list[str] = []

    for root, _dirs, files in os.walk('.'):
        if '.venv' in root or '.git' in root or 'node_modules' in root:
            continue
        for f in files:
            path = os.path.join(root, f)
            if f.endswith('.md'):
                if root.startswith('./memory-bank') or root.startswith('./docs') or root.startswith('./.github') or (root == '.' and f in ['README.md', 'CHANGELOG.md']):
                    files_to_check_md.append(path)
            elif (f.endswith('.yaml') or f.endswith('.yml')) and ('config' in f or 'asset' in f or 'prompt' in f):
                files_to_check_yaml.append(path)

    files_to_check_md.sort()
    files_to_check_yaml.sort()
    return files_to_check_md, files_to_check_yaml


def _read_text_lines(path: str) -> list[str] | None:
    try:
        with open(path, encoding='utf-8') as file:
            return file.read().split('\n')
    except Exception:
        return None


def _read_file_lines(path: str) -> list[str] | None:
    try:
        with open(path, encoding='utf-8') as file:
            return file.readlines()
    except Exception:
        return None


def _check_github_prompt_frontmatter(path: str, content: str, add_finding) -> None:
    if not path.startswith('./.github/prompts/'):
        return
    if not content.startswith('---'):
        add_finding(path, "FRONTMATTER", 1, "Fehlendes YAML-Frontmatter")
        return
    parts = content.split('---', 2)
    if len(parts) > 1:
        fm = parts[1]
        if 'mode:' not in fm:
            add_finding(path, "FRONTMATTER", 1, "mode-Feld fehlt")
        if 'description:' not in fm:
            add_finding(path, "FRONTMATTER", 1, "description-Feld fehlt")


def _check_progress_checkboxes(path: str, lines: list[str], add_finding) -> None:
    if 'memory-bank/progress.md' not in path:
        return
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('- [') and not (s.startswith('- [ ]') or s.startswith('- [DONE]')):
            add_finding(path, "CONSISTENCY", i+1, f"Falsches Status-Feld Format: {s[:10]}...")


def _check_activecontext_required_fields(path: str, content: str, add_finding) -> None:
    if 'memory-bank/activeContext.md' not in path:
        return
    has_done = re.search(r'(?i)abgeschlossen', content)
    has_next = re.search(r'(?i)nächster schritt', content)
    has_risk = re.search(r'(?i)(offen|risiko|baustelle|risiken|blocker)', content)
    if not (has_done and has_next and has_risk):
        add_finding(path, "CONSISTENCY", 1, "Fehlende Pflichtfelder in activeContext.md")


def _check_inline_links(path: str, line: str, line_no: int, add_finding) -> None:
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
        link = m.group(2)
        if link.startswith('http') or link.startswith('mailto') or link.startswith('#') or link == '.':
            continue
        link = link.split('#')[0]
        if not link:
            continue
        base_dir = os.path.dirname(path)
        target = os.path.normpath(os.path.join(base_dir, link))
        if not os.path.exists(target):
            add_finding(path, "LINKS", line_no, f"Kaputter Link: {link}")


def _check_heading_hierarchy(path: str, line: str, line_no: int, i: int, lines: list[str], last_lvl: list, add_finding) -> None:
    hm = re.match(r'^(#+)\s+', line)
    if not hm:
        return
    lvl = len(hm.group(1))
    if i > 0 and lines[i-1].strip() != '':
        add_finding(path, "FORMATIERUNG", line_no, "Fehlende Leerzeile vor Heading")
    if lvl > last_lvl[0] + 1 and last_lvl[0] > 0:
        add_finding(path, "FORMATIERUNG", line_no, f"Falsche Hierarchie (H{last_lvl[0]} -> H{lvl})")
    last_lvl[0] = lvl


def _scan_md_code_and_links(path: str, lines: list[str], add_finding) -> bool:
    in_code_block = False
    last_lvl = [0]
    for i, line in enumerate(lines):
        line_no = i + 1
        if line.startswith('```'):
            if not in_code_block:
                in_code_block = True
                lang = line[3:].strip()
                if not lang:
                    add_finding(path, "FORMATIERUNG", line_no, "Code-Block ohne Sprach-Tag")
            else:
                in_code_block = False
        if in_code_block:
            continue

        _check_heading_hierarchy(path, line, line_no, i, lines, last_lvl, add_finding)

        if (line.endswith(' ') or line.endswith('\t')) and line.strip() != '' and not line.endswith('  '):
            add_finding(path, "FORMATIERUNG", line_no, "Trailing Whitespace")

        if "konfiguartion" in line.lower():
            add_finding(path, "TYPO", line_no, "Rechtschreibfehler: Konfiguartion")

        _check_inline_links(path, line, line_no, add_finding)
    return in_code_block


def _audit_md_file(path: str, add_finding) -> None:
    lines = _read_text_lines(path)
    if lines is None:
        return
    content = "\n".join(lines)
    _check_github_prompt_frontmatter(path, content, add_finding)
    _check_progress_checkboxes(path, lines, add_finding)
    _check_activecontext_required_fields(path, content, add_finding)
    still_open = _scan_md_code_and_links(path, lines, add_finding)
    if still_open:
        add_finding(path, "FORMATIERUNG", len(lines), "Ungeschlossener Code-Fence")





def _check_target_field_line(
    path: str, line: str, lines: list[str], i: int, indent: int, key: str,
    scalar_token: str | None, line_no: int, add_finding,
) -> None:
    """Prueft Folded-Scalar (>) auf enthaltene Listen in den Folgezeilen."""
    if not (scalar_token and scalar_token.startswith('>')):
        return
    has_lists = False
    for j in range(i+1, min(i+15, len(lines))):
        nline = lines[j]
        if not nline.strip():
            continue
        nindent = len(nline) - len(nline.lstrip())
        if nindent <= indent:
            break
        if re.match(r'^\s*[-*]\s', nline):
            has_lists = True
    if has_lists:
        add_finding(path, "YAML-SCALAR", line_no, f"Folded-Scalar (>) zerstört Listen in '{key}' → auf | wechseln", is_yaml=True)


def _scan_target_scalar_body(
    path: str, line: str, line_no: int, current_field: str,
    state: dict, apply_fixes: bool, new_lines: list[str], add_finding,
) -> None:
    """Prueft eine einzelne Zeile innerhalb des Target-Scalar-Blocks."""
    trimmed = line.strip()
    if trimmed.startswith('```'):
        state["in_code_block_yaml"] = not state["in_code_block_yaml"]
        if len(new_lines) > 0 and new_lines[-1].strip() != '':
            add_finding(path, "FORMATIERUNG", line_no, f"Fehlende Leerzeile vor Code-Block in '{current_field}'", is_yaml=True)
            if apply_fixes:
                new_lines.append('\n')
                state["needs_fix"] = True

    if not state["in_code_block_yaml"] and re.match(r'^\s*#{1,3}\s', line) and len(new_lines) > 0 and new_lines[-1].strip() != '':
        add_finding(path, "FORMATIERUNG", line_no, f"Fehlende Leerzeile vor Heading in '{current_field}'", is_yaml=True)


def _scan_yaml_scalar_block(
    path: str,
    lines: list[str],
    apply_fixes: bool,
    add_finding,
) -> tuple[list[str], bool]:
    TARGET_FIELDS = ['prompt', 'prompts', 'system_prompt', 'judge_prompt', 'judge_system_prompt']
    new_lines: list[str] = []
    state = {
        "is_in_target_scalar": False,
        "scalar_indent": 0,
        "current_field": "",
        "in_code_block_yaml": False,
        "needs_fix": False,
    }

    for i, line in enumerate(lines):
        line_no = i + 1
        field_match = re.match(r'^(\s*)([a-zA-Z0-9_]+):\s+([>|].*)?$', line)

        if field_match:
            indent = len(field_match.group(1))
            key = field_match.group(2)
            scalar_token = field_match.group(3)

            if key in TARGET_FIELDS:
                _check_target_field_line(
                    path, line, lines, i, indent, key, scalar_token, line_no, add_finding,
                )
                state["is_in_target_scalar"] = True
                state["scalar_indent"] = indent
                state["current_field"] = key
                state["in_code_block_yaml"] = False
                new_lines.append(line)
                continue

        if state["is_in_target_scalar"]:
            curr_indent = len(line) - len(line.lstrip())
            if line.strip() and curr_indent <= state["scalar_indent"]:
                state["is_in_target_scalar"] = False
            else:
                _scan_target_scalar_body(
                    path, line, line_no, state["current_field"],
                    state, apply_fixes, new_lines, add_finding,
                )

        new_lines.append(line)
    return new_lines, state["needs_fix"]


def _audit_yaml_file(path: str, apply_fixes: bool, add_finding) -> None:
    lines = _read_file_lines(path)
    if lines is None:
        return
    new_lines, needs_fix = _scan_yaml_scalar_block(path, lines, apply_fixes, add_finding)
    if apply_fixes and needs_fix:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Fixed formatting in {path}")


def _print_report(findings: dict[str, list[tuple[str, int, str]]], total_findings: int, yaml_findings_count: int, md_count: int, yaml_count: int) -> None:
    print("MARKDOWN AUDIT — CrucibleMark")
    print("==============================")
    printed_findings = 0
    for f, file_findings in sorted(findings.items()):
        display_path = f.replace('./', '')
        if len(file_findings) == 0:
            continue
        print(f"\nDatei: {display_path}")
        for cat, line, msg in file_findings:
            if "Kaputter Link: ." in msg:
                continue
            print(f"  [{cat}] Zeile {line}: {msg}")
            printed_findings += 1

    checked_total = md_count + yaml_count
    print(f"\nGesamt: {checked_total} Dateien geprüft, {total_findings} Befunde (davon {yaml_findings_count} in YAML-Prompt-Feldern)")


def audit_markdown_files(apply_fixes=False):
    files_to_check_md, files_to_check_yaml = _collect_target_files()

    findings: dict[str, list[tuple[str, int, str]]] = {}
    total_findings = 0
    yaml_findings_count = 0

    def add_finding(f, cat, line, msg, is_yaml=False):
        nonlocal total_findings, yaml_findings_count
        if f not in findings:
            findings[f] = []
        findings[f].append((cat, line, msg))
        total_findings += 1
        if is_yaml:
            yaml_findings_count += 1

    for path in files_to_check_md:
        _audit_md_file(path, add_finding)

    for path in files_to_check_yaml:
        _audit_yaml_file(path, apply_fixes, add_finding)

    _print_report(findings, total_findings, yaml_findings_count, len(files_to_check_md), len(files_to_check_yaml))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit and fix Markdown/YAML files")
    parser.add_argument("--fix", action="store_true", help="Apply auto-fixes for YAML formatting issues")
    args = parser.parse_args()

    audit_markdown_files(apply_fixes=args.fix)
