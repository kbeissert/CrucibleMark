from __future__ import annotations

import argparse
import json
from pathlib import Path

import openai

from utils.card_template import CardTemplate
from utils.model_utils import _card_path, _find_card
from .common import (
    _CHECK_SYSTEM_INSTRUCTION,
    _MAKE_SYSTEM_INSTRUCTION,
    _apply_check_fixes,
    _build_check_user_prompt,
    _build_make_user_prompt,
    _glob_model_cards,
    _parse_check_response,
    _parse_make_response,
    _preserve_operator_fields,
    _validate_against_template,
    logger,
)
from .models import CardCheckReport, CardFinding, CardMakeReport, LLMSession, LLMSpec, RunSummary

def _discover_targets(
    args: argparse.Namespace,
) -> list[tuple[str, Path]]:
    if args.card:
        if args.mode == "check":
            path = _find_card(args.card)
            if not path.exists():
                raise SystemExit(f"❌ Card nicht gefunden: {args.card}")
            return [(args.card, path)]
        path = _card_path(args.card, for_write=True)
        if not path.exists():
            logger.info("ℹ️  Card existiert nicht: %s — wird im 'make'-Modus erzeugt.", args.card)
        return [(args.card, path)]

    return _glob_model_cards(args.force)


def _render_markdown_report(
    reports: list[CardCheckReport], today: str, *, mode_label: str = "check (dry-run)"
) -> str:
    lines: list[str] = [
        f"# Model Card Check Report — {today}",
        "",
        f"**Modus:** {mode_label}",
        f"**Verarbeitet:** {sum(1 for r in reports if not r.error and r.parse_error is None)}"
        f" · **Übersprungen:** 0"
        f" · **Fehler:** {sum(1 for r in reports if r.error or r.parse_error)}",
        "",
    ]
    for r in reports:
        lines.append(f"## {r.model_id}")
        lines.append("")
        if r.error:
            lines.append(f"- ❌ Fehler: {r.error}")
        elif r.parse_error:
            lines.append(f"- ⚠️ Parse-Fehler: {r.parse_error}")
        elif not r.findings:
            lines.append("- ✅ keine Findings")
        else:
            errors = sum(1 for f in r.findings if f.severity == "error")
            warnings = sum(1 for f in r.findings if f.severity == "warning")
            infos = sum(1 for f in r.findings if f.severity == "info")
            lines.append(
                f"- 🔍 {len(r.findings)} Findings "
                f"({errors} errors, {warnings} warnings, {infos} info)"
            )
            for f in r.findings:
                icon = {"error": "🔴", "warning": "🟡", "info": "ℹ️"}.get(f.severity, "•")
                lines.append(f"  - {icon} `{f.field}` — {f.message}")
        if r.summary:
            lines.append(f"  - _{r.summary}_")
        lines.append("")
    return "\n".join(lines)


class CardManager:
    def __init__(
        self,
        args: argparse.Namespace,
        session: LLMSession,
        template: CardTemplate,
        editor_prompt: str,
        llm_spec: LLMSpec,
    ) -> None:
        self.args = args
        self.session = session
        self.template = template
        self.editor_prompt = editor_prompt
        self.llm_spec = llm_spec
        self.summary = RunSummary()

    def run(self) -> RunSummary:
        targets = _discover_targets(self.args)
        if not targets:
            logger.info("⚠️  Keine Ziel-Cards gefunden.")
            return self.summary

        logger.info(
            "🔧 Card-Manager LLM: %s/%s (base_url=%s)",
            self.llm_spec.provider_name, self.llm_spec.model, self.llm_spec.base_url,
        )
        logger.info("📦 %d Card(s) zu verarbeiten.", len(targets))

        for idx, (mid, path) in enumerate(targets, 1):
            print(f"\n[{idx}/{len(targets)}] {mid}")
            logger.info("[%d/%d] %s — %s", idx, len(targets), mid, path.name)
            if self.args.mode == "check":
                self._check_one(mid, path, idx, len(targets))
            else:
                self._make_one(mid, path, idx, len(targets))
        return self.summary

    def _check_one(
        self, mid: str, path: Path, idx: int, total: int
    ) -> CardCheckReport:
        report = CardCheckReport(model_id=mid, card_path=path)
        try:
            card = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report.error = f"Card nicht lesbar: {exc}"
            self.summary.errors += 1
            self.summary.check_reports.append(report)
            return report

        user_prompt = _build_check_user_prompt(card, self.editor_prompt)
        try:
            response = self.session.query(
                system=_CHECK_SYSTEM_INSTRUCTION,
                user=user_prompt,
                temperature=self.llm_spec.temperature,
            )
        except (openai.APIError, ValueError) as exc:  # noqa: BLE001
            report.error = str(exc)
            self.summary.errors += 1
            self.summary.check_reports.append(report)
            return report

        report.raw_response = response
        findings, summary, parse_err = _parse_check_response(response)
        report.findings = findings
        report.summary = summary
        report.parse_error = parse_err
        if parse_err:
            self.summary.errors += 1
        else:
            self.summary.processed += 1
            if findings:
                err_n = sum(1 for f in findings if f.severity == "error")
                warn_n = sum(1 for f in findings if f.severity == "warning")
                print(f"  ⚠  {len(findings)} Findings ({err_n} errors, {warn_n} warnings)")

        if self.args.fix and report.parse_error is None and not report.error:
            merged = _apply_check_fixes(card, report)
            merged = _preserve_operator_fields(card, merged)
            cleaned, warnings = _validate_against_template(merged, self.template)
            for w in warnings:
                logger.info("    · %s", w)
                report.findings.append(CardFinding(
                    field=w.split(":")[0].strip() if ":" in w else w,
                    severity="warning",
                    message=w,
                    current=None,
                    suggested=None,
                ))
            report.would_write = True
            if self.args.dry_run:
                logger.info("    [DRY-RUN] Würde %s aktualisieren.", path.name)
            else:
                path.write_text(
                    json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                logger.info("    ✅ %s aktualisiert.", path.name)
        elif self.args.fix and (report.parse_error or report.error):
            logger.info("    [FIX übersprungen] %s", report.parse_error or report.error)

        self.summary.check_reports.append(report)
        return report

    def _make_one(
        self, mid: str, path: Path, idx: int, total: int
    ) -> CardMakeReport:
        report = CardMakeReport(model_id=mid, card_path=path)
        existing: dict = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Bestehende Card nicht lesbar (%s) — neu aufbauen.", exc)

        user_prompt = _build_make_user_prompt(
            self.template, existing, self.editor_prompt,
        )
        try:
            response = self.session.query(
                system=_MAKE_SYSTEM_INSTRUCTION,
                user=user_prompt,
                temperature=self.llm_spec.temperature,
            )
        except (openai.APIError, ValueError, json.JSONDecodeError) as exc:  # noqa: BLE001
            report.error = str(exc)
            self.summary.errors += 1
            self.summary.make_reports.append(report)
            return report

        report.raw_response = response
        new_card, parse_err = _parse_make_response(response)
        if parse_err or new_card is None:
            report.parse_error = parse_err
            self.summary.errors += 1
            self.summary.make_reports.append(report)
            return report

        new_card = _preserve_operator_fields(existing or {}, new_card)
        cleaned, warnings = _validate_against_template(new_card, self.template)
        report.warnings = warnings
        report.new_card = cleaned
        self.summary.processed += 1

        report.would_write = True
        if self.args.dry_run:
            logger.info("    [DRY-RUN] Würde %s neu schreiben (%d Felder).", path.name, len(cleaned))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report.wrote = True
            logger.info("    ✅ %s geschrieben.", path.name)
        for w in warnings:
            logger.info("    · %s", w)

        self.summary.make_reports.append(report)
        return report

