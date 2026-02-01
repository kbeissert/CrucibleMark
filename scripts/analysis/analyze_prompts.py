#!/usr/bin/env python3
"""
Prompt Analysis Script
======================

Analyzes the token length of all benchmark assets to identify potential cost drivers.
Detailed breakdown of System Prompt vs User Prompt vs Content.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

# Third-party imports
try:
    import tiktoken
    ENCODING = tiktoken.get_encoding("cl100k_base")  # GPT-4Tokenizer
except ImportError:
    ENCODING = None

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.benchmark_utils import load_asset_yaml  # noqa: E402
from utils.constants import Colors  # noqa: E402

# Configuration
MODULES_DIR = ROOT_DIR / "benchmark_modules"
WARN_THRESHOLD = 2000  # Tokens
CRITICAL_THRESHOLD = 4000  # Tokens


def count_tokens(text: str) -> int:
    """Returns accurate token count if tiktoken is available, else heuristic."""
    if not text:
        return 0
    if ENCODING:
        return len(ENCODING.encode(text))
    return len(text) // 4  # Rough estimate for english text


def analyze_module(module_path: Path) -> List[Dict[str, Any]]:
    """Scans a module directory for assets and analyzes them."""
    assets_dir = module_path / "assets"
    if not assets_dir.exists():
        return []

    results = []

    # Recursively find yaml files
    for asset_file in assets_dir.rglob("*.yaml"):
        if asset_file.name.startswith("config"):
            continue

        data = load_asset_yaml(asset_file)
        if not data:
            continue

        metadata = data.get("metadata", {})
        asset_id = metadata.get("id", asset_file.stem)

        # Extract Prompt Components
        prompt_data = data.get("prompt", {})
        context = data.get("context", "")

        if isinstance(prompt_data, str):
            system_prompt = ""
            user_prompt = prompt_data
        else:
            system_prompt = prompt_data.get("system", "")
            user_prompt = prompt_data.get("user", "")

        # Combine content (Context is often appended to user prompt)
        full_content = f"{context}\n{user_prompt}"

        sys_tokens = count_tokens(system_prompt)
        user_tokens = count_tokens(full_content)
        total_tokens = sys_tokens + user_tokens

        results.append({
            "id": asset_id,
            "file": asset_file.name,
            "sys_tokens": sys_tokens,
            "user_tokens": user_tokens,
            "total_tokens": total_tokens
        })

    return sorted(results, key=lambda x: x["total_tokens"], reverse=True)


def print_report(module_name: str, assets: List[Dict[str, Any]]):
    """Prints a formatted report for a module."""
    if not assets:
        return

    print(f"\n{Colors.HEADER}📦 Module: {module_name}{Colors.ENDC}")
    print(f"{'ASSET ID':<30} {'SYS':>6} {'USER':>6} {'TOTAL':>8}   {'STATUS'}")
    print("-" * 70)

    for a in assets:
        total = a["total_tokens"]

        if total > CRITICAL_THRESHOLD:
            color = Colors.FAIL
            status = "CRITICAL 🔴"
        elif total > WARN_THRESHOLD:
            color = Colors.WARNING
            status = "WARN ⚠️"
        else:
            color = Colors.GREEN
            status = "OK ✅"

        print(
            f"{a['id']:<30} {a['sys_tokens']:>6} {a['user_tokens']:>6} "
            f"{color}{total:>8}{Colors.ENDC}   {status}"
        )


def main():
    print(f"{Colors.BOLD}🔍 Prompt Token Analysis{Colors.ENDC}")
    if ENCODING:
        print(f"   Parser: {Colors.CYAN}tiktoken (cl100k_base){Colors.ENDC} - Accurate for GPT-4")
    else:
        print(f"   Parser: {Colors.WARNING}Heuristic (Char/4){Colors.ENDC} - Install 'tiktoken' for accuracy")

    print("-" * 70)

    total_project_tokens = 0
    modules = sorted([d for d in MODULES_DIR.iterdir() if d.is_dir() and not d.name.startswith("__")])

    for module_dir in modules:
        assets = analyze_module(module_dir)
        if assets:
            print_report(module_dir.name, assets)
            module_total = sum(a["total_tokens"] for a in assets)
            total_project_tokens += module_total

    print("\n" + "=" * 70)
    print(f"💰 Total Tokens (One Full Run): {Colors.BOLD}{total_project_tokens:,}{Colors.ENDC}")

    # Cost Estimate (avg price mix)
    # Assume $5/1M input tokens (GPT-4o)
    est_cost = (total_project_tokens / 1_000_000) * 5.00
    print(f"   Est. Cost (GPT-4o):      ${est_cost:.4f}")

    # Assume $3/1M input tokens (Claude 3.5 Sonnet)
    est_cost_claude = (total_project_tokens / 1_000_000) * 3.00
    print(f"   Est. Cost (Claude 3.5):  ${est_cost_claude:.4f}")


if __name__ == "__main__":
    main()
