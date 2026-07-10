import os
import re
import argparse

def audit_markdown_files(apply_fixes=False):
    files_to_check_md = []
    files_to_check_yaml = []

    for root, dirs, files in os.walk('.'):
        if '.venv' in root or '.git' in root or 'node_modules' in root:
            continue
        for f in files:
            path = os.path.join(root, f)
            if f.endswith('.md'):
                if root.startswith('./memory-bank') or root.startswith('./docs') or root.startswith('./.github') or (root == '.' and f in ['README.md', 'CHANGELOG.md']):
                    files_to_check_md.append(path)
            elif f.endswith('.yaml') or f.endswith('.yml'):
                if 'config' in f or 'asset' in f or 'prompt' in f:
                    files_to_check_yaml.append(path)

    files_to_check_md.sort()
    files_to_check_yaml.sort()

    findings = {}
    total_findings = 0
    yaml_findings_count = 0

    def add_finding(f, cat, line, msg, is_yaml=False):
        nonlocal total_findings, yaml_findings_count
        if f not in findings: findings[f] = []
        findings[f].append((cat, line, msg))
        total_findings += 1
        if is_yaml:
            yaml_findings_count += 1

    # 1. Check MD files (Read-only as before)
    for path in files_to_check_md:
        try:
            with open(path, encoding='utf-8') as file:
                content = file.read()
                lines = content.split('\n')
        except Exception: continue

        in_code_block = False

        if path.startswith('./.github/prompts/'):
            if not content.startswith('---'): add_finding(path, "FRONTMATTER", 1, "Fehlendes YAML-Frontmatter")
            else:
                parts = content.split('---', 2)
                if len(parts) > 1:
                    fm = parts[1]
                    if 'mode:' not in fm: add_finding(path, "FRONTMATTER", 1, "mode-Feld fehlt")
                    if 'description:' not in fm: add_finding(path, "FRONTMATTER", 1, "description-Feld fehlt")

        if 'memory-bank/progress.md' in path:
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith('- [') and not (s.startswith('- [ ]') or s.startswith('- [DONE]')):
                    add_finding(path, "CONSISTENCY", i+1, f"Falsches Status-Feld Format: {s[:10]}...")

        if 'memory-bank/activeContext.md' in path:
            if not (re.search(r'(?i)abgeschlossen', content) and re.search(r'(?i)nächster schritt', content) and re.search(r'(?i)(offen|risiko|baustelle|risiken|blocker)', content)):
                add_finding(path, "CONSISTENCY", 1, "Fehlende Pflichtfelder in activeContext.md")

        last_lvl = 0
        for i, line in enumerate(lines):
            line_no = i + 1
            if line.startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    lang = line[3:].strip()
                    if not lang: add_finding(path, "FORMATIERUNG", line_no, "Code-Block ohne Sprach-Tag")
                else:
                    in_code_block = False
            if in_code_block: continue

            hm = re.match(r'^(#+)\s+', line)
            if hm:
                lvl = len(hm.group(1))
                if i > 0 and lines[i-1].strip() != '': add_finding(path, "FORMATIERUNG", line_no, "Fehlende Leerzeile vor Heading")
                if lvl > last_lvl + 1 and last_lvl > 0: add_finding(path, "FORMATIERUNG", line_no, f"Falsche Hierarchie (H{last_lvl} -> H{lvl})")
                last_lvl = lvl

            if line.endswith(' ') or line.endswith('\t'):
                if line.strip() != '' and not line.endswith('  '): add_finding(path, "FORMATIERUNG", line_no, "Trailing Whitespace")

            if "konfiguartion" in line.lower(): add_finding(path, "TYPO", line_no, "Rechtschreibfehler: Konfiguartion")

            for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
                link = m.group(2)
                if not link.startswith('http') and not link.startswith('mailto') and not link.startswith('#') and link != '.':
                    link = link.split('#')[0]
                    if link:
                        base_dir = os.path.dirname(path)
                        target = os.path.normpath(os.path.join(base_dir, link))
                        if not os.path.exists(target): add_finding(path, "LINKS", line_no, f"Kaputter Link: {link}")

        if in_code_block: add_finding(path, "FORMATIERUNG", len(lines), "Ungeschlossener Code-Fence")

    # 2. Check YAML files
    TARGET_FIELDS = ['prompt', 'prompts', 'system_prompt', 'judge_prompt', 'judge_system_prompt']

    for path in files_to_check_yaml:
        try:
            with open(path, encoding='utf-8') as file:
                lines = file.readlines()
        except Exception: continue

        new_lines = []
        is_in_target_scalar = False
        scalar_indent = 0
        current_field = ""
        in_code_block_yaml = False
        needs_fix = False

        for i, line in enumerate(lines):
            line_no = i + 1
            field_match = re.match(r'^(\s*)([a-zA-Z0-9_]+):\s+([>|].*)?$', line)

            if field_match:
                indent = len(field_match.group(1))
                key = field_match.group(2)
                scalar_token = field_match.group(3)

                if key in TARGET_FIELDS:
                    if scalar_token and scalar_token.startswith('>'):
                        has_lists = False
                        for j in range(i+1, min(i+15, len(lines))):
                            nline = lines[j]
                            if not nline.strip(): continue
                            nindent = len(nline) - len(nline.lstrip())
                            if nindent <= indent: break
                            if re.match(r'^\s*[-*]\s', nline): has_lists = True
                        if has_lists:
                            add_finding(path, "YAML-SCALAR", line_no, f"Folded-Scalar (>) zerstört Listen in '{key}' → auf | wechseln", is_yaml=True)

                    is_in_target_scalar = True
                    scalar_indent = indent
                    current_field = key
                    in_code_block_yaml = False
                    new_lines.append(line)
                    continue

            if is_in_target_scalar:
                curr_indent = len(line) - len(line.lstrip())
                if line.strip() and curr_indent <= scalar_indent:
                    is_in_target_scalar = False
                else:
                    trimmed = line.strip()
                    if trimmed.startswith('```'):
                        in_code_block_yaml = not in_code_block_yaml
                        if len(new_lines) > 0 and new_lines[-1].strip() != '':
                            add_finding(path, "FORMATIERUNG", line_no, f"Fehlende Leerzeile vor Code-Block in '{current_field}'", is_yaml=True)
                            if apply_fixes:
                                new_lines.append('\n')
                                needs_fix = True

                    if not in_code_block_yaml and re.match(r'^\s*#{1,3}\s', line):
                        if len(new_lines) > 0 and new_lines[-1].strip() != '':
                            add_finding(path, "FORMATIERUNG", line_no, f"Fehlende Leerzeile vor Heading in '{current_field}'", is_yaml=True)

            new_lines.append(line)

        if apply_fixes and needs_fix:
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"Fixed formatting in {path}")

    # 3. Print Report
    print("MARKDOWN AUDIT — CrucibleMark")
    print("==============================")
    printed_findings = 0
    for f, file_findings in sorted(findings.items()):
        display_path = f.replace('./', '')
        if len(file_findings) == 0: continue
        print(f"\nDatei: {display_path}")
        for cat, line, msg in file_findings:
            if "Kaputter Link: ." in msg: continue
            print(f"  [{cat}] Zeile {line}: {msg}")
            printed_findings += 1

    checked_total = len(files_to_check_md) + len(files_to_check_yaml)
    print(f"\nGesamt: {checked_total} Dateien geprüft, {total_findings} Befunde (davon {yaml_findings_count} in YAML-Prompt-Feldern)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit and fix Markdown/YAML files")
    parser.add_argument("--fix", action="store_true", help="Apply auto-fixes for YAML formatting issues")
    args = parser.parse_args()

    audit_markdown_files(apply_fixes=args.fix)
