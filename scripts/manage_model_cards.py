#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.card_research.common import (  # noqa: E402
    _load_benchmark_config,
    _load_editor_prompt,
    _resolve_llm_spec,
    _setup_logging,
)
from scripts.card_research.manager import CardManager, _render_markdown_report  # noqa: E402
from scripts.card_research.models import (  # noqa: E402
    LLMSession,
    LLMSpec,
    MAX_RETRIES,
    PER_CALL_TIMEOUT_S,
    RunSummary,
)
from scripts.card_research.researcher import Researcher, _render_research_markdown_report  # noqa: E402
from utils.card_template import load_card_template  # noqa: E402
from utils.model_utils import _find_card  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LLM-gestütztes Model-Card-Management. Prüft (check) oder ergänzt (make) Cards via LLM.",
    )
    parser.add_argument("--mode", required=True, choices=["check", "make", "research"], help="check: Findings-Report (optional mit --fix). make: Card regenerieren. research: LLM-Recherche mit profile_verified-Lock.")
    parser.add_argument("--card", type=str, help="Nur diese eine Card verarbeiten.")
    parser.add_argument("--force", action="store_true", help="Auch verifizierte Cards einbeziehen.")
    parser.add_argument("--fix", action="store_true", help="(check) Vorgeschlagene Korrekturen direkt anwenden.")
    parser.add_argument("--write", action="store_true", help="(make) Card tatsächlich schreiben — sonst Dry-Run.")
    parser.add_argument("--dry-run", action="store_true", help="Explizit kein Schreibvorgang (Standard für make).")
    parser.add_argument("--model", type=str, help="LLM-Modell (überschreibt Config).")
    parser.add_argument("--base-url", type=str, help="OpenAI-kompatibler Endpoint (z.B. http://localhost:1234/v1).")
    parser.add_argument("--api-key-env", type=str, default=None, help="Name der Env-Variable mit dem API-Key (Default: aus Config oder OPENAI_API_KEY).")
    parser.add_argument("--provider", type=str, help="Provider-Label (informational).")
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES)
    parser.add_argument("--timeout-s", type=int, default=PER_CALL_TIMEOUT_S)
    parser.add_argument("--pause", type=float, default=1.0, help="Pause in Sekunden zwischen jeder Card (Default: 1.0).")
    parser.add_argument("--max-cards", type=int, default=0, help="Max. Cards pro Run (0=alle). Bei llama.cpp-Speicherproblemen nutzen.")
    parser.add_argument("--tooluse", action="store_true", help="Tool-Use-Modus: LLM recherchiert via MCP (web_search/fetch).")
    parser.add_argument("--mcp-url", type=str, default="http://localhost:8765", help="MCP-Server URL (Default: http://localhost:8765).")
    return parser


def _validate_args(args: argparse.Namespace) -> None:
    if args.fix and args.mode != "check":
        raise SystemExit("❌ --fix ist nur mit --mode check erlaubt.")
    if args.card and args.mode == "check" and not _find_card(args.card).exists():
        raise SystemExit(f"❌ Card nicht gefunden: {args.card}")
    if args.card and args.mode == "research" and args.card.lower() != "all" and not _find_card(args.card).exists():
        raise SystemExit(f"❌ Card nicht gefunden: {args.card}")
    if args.write and args.dry_run:
        raise SystemExit("❌ --write und --dry-run sind nicht kombinierbar.")
    if getattr(args, "tooluse", False) and args.mode != "research":
        raise SystemExit("❌ --tooluse ist nur mit --mode research erlaubt.")
    if args.mode == "make" and not args.write:
        args.dry_run = True


def _build_session(args: argparse.Namespace) -> tuple[LLMSession, LLMSpec]:
    config = _load_benchmark_config()
    llm_spec = _resolve_llm_spec(args, config)
    if not llm_spec.api_key:
        raise SystemExit(f"❌ Kein API-Key gefunden. Setze die Env-Variable {args.api_key_env!r} (oder via --api-key-env überschreiben).")
    session = LLMSession(
        model=llm_spec.model,
        base_url=llm_spec.base_url,
        api_key=llm_spec.api_key,
        max_retries=args.max_retries,
        timeout_s=args.timeout_s,
    )
    return session, llm_spec


def _run(args: argparse.Namespace, session: LLMSession, llm_spec: LLMSpec) -> RunSummary:
    template = load_card_template("model")
    editor_prompt = _load_editor_prompt()
    if args.mode == "research":
        return Researcher(args, session, template, editor_prompt, llm_spec).run()
    return CardManager(args, session, template, editor_prompt, llm_spec).run()


def _print_report(args: argparse.Namespace, summary: RunSummary) -> None:
    print()
    if args.mode == "check" and not args.fix:
        print(_render_markdown_report(summary.check_reports, date.today().isoformat()))
    elif args.mode == "check" and args.fix:
        print(_render_markdown_report(summary.check_reports, date.today().isoformat(), mode_label="check (fix)"))
    elif args.mode == "research":
        print(_render_research_markdown_report(summary.research_reports, date.today().isoformat()))
    print(f"✅ Fertig: {summary.processed} verarbeitet, {summary.errors} Fehler.")


def main() -> int:
    args = _build_parser().parse_args()
    _setup_logging()
    _validate_args(args)
    session, llm_spec = _build_session(args)
    summary = _run(args, session, llm_spec)
    _print_report(args, summary)
    return 0 if summary.errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
