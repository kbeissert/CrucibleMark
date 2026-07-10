from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path
from typing import Any

import openai

from utils.card_template import CardTemplate
from .common import (
    TOOL_SCHEMAS,
    _LLM_TEXT_FIELDS,
    _RESEARCH_SYSTEM_INSTRUCTION,
    _build_research_user_prompt,
    _build_tooluse_system_instruction,
    _call_mcp_tool,
    _check_health,
    _collect_pre_findings,
    _discover_research_targets,
    _ensure_gguf_conventions,
    _ensure_license_consistency,
    _ensure_mcp_running,
    _extract_json_object,
    _extract_tool_content,
    _parse_tool_call,
    _prefill_template_fields,
    _preserve_operator_fields,
    _reset_llama_context,
    _server_root_url,
    _stop_mcp_server,
    _validate_against_template,
    _check_license_cascade,
    _check_license_consistency,
    _check_license_text_fields,
    _check_community,
    logger,
)
from .models import CardFinding, LLMSession, LLMSpec, ResearchReport, RunSummary

class Researcher:
    """Recherchiert Card-Inhalte via LLM mit profile_verified-Lock-Mechanismus.

    Lock-Phase: ``profile_verified`` wird auf ``False`` gesetzt (Resumption-Marker
    bei Abbruch). Bei Erfolg wird es wieder auf ``True`` gesetzt, inkl.
    ``profile_verified_at`` und ``profile_verified_by``.

    Backup: vor dem Schreiben wird ``<card>.pre-research.bak`` angelegt und
    bei Erfolg geloescht (Sicherheitsnetz fuer Diff-Inspektion).
    """

    BACKUP_SUFFIX = ".pre-research.bak"

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

    # ------------------------------------------------------------------
    # Shared helpers for lock / backup / commit / findings extraction
    # ------------------------------------------------------------------

    def _load_card(self, path: Path, report: ResearchReport) -> dict | None:
        """Load card JSON or set report.error and return None."""
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report.error = f"Card nicht lesbar: {exc}"
            self.summary.errors += 1
            self.summary.research_reports.append(report)
            return None

    def _apply_lock(
        self, original: dict, path: Path, report: ResearchReport
    ) -> bool:
        """Set profile_verified=False on disk. Returns False on failure."""
        if self.args.dry_run:
            return True
        locked = dict(original)
        locked["profile_verified"] = False
        locked["profile_verified_at"] = None
        locked["profile_verified_by"] = None
        locked["last_modified_at"] = date.today().isoformat()
        try:
            path.write_text(
                json.dumps(locked, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report.locked = True
            logger.info("    🔓 Lock geoeffnet: %s (profile_verified=false)", path.name)
            return True
        except OSError as exc:
            report.error = f"Lock fehlgeschlagen: {exc}"
            self.summary.errors += 1
            self.summary.research_reports.append(report)
            return False

    def _create_backup(
        self, path: Path, report: ResearchReport
    ) -> Path | None:
        """Create .pre-research.bak if not dry_run. Returns backup path."""
        if self.args.dry_run:
            return None
        backup_path = path.with_name(path.name + self.BACKUP_SUFFIX)
        try:
            backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            report.backup_path = backup_path
            return backup_path
        except OSError as exc:
            logger.warning("    ⚠️ Backup fehlgeschlagen: %s — weiter ohne.", exc)
            return None

    def _extract_findings(
        self, parsed: dict, report: ResearchReport, *, text_only: bool = True
    ) -> None:
        """Append LLM findings from parsed JSON to report.

        Args:
            text_only: If True, discard findings for structural fields
                (only keep _LLM_TEXT_FIELDS). Used in non-tooluse mode where
                the LLM cannot actually search the web.
        """
        findings_raw = parsed.get("findings", [])
        if not isinstance(findings_raw, list):
            return
        for item in findings_raw:
            if not isinstance(item, dict):
                continue
            field_name = str(item.get("field", ""))
            if text_only and field_name not in _LLM_TEXT_FIELDS:
                logger.debug("    🗑️ LLM-Finding verworfen (strukturelles Feld): %s", field_name)
                continue
            suggested = item.get("suggested")
            if suggested is None or (isinstance(suggested, str) and not suggested.strip()):
                logger.debug("    🗑️ LLM-Finding verworfen (kein suggested): %s", field_name)
                continue
            report.findings.append(CardFinding(
                field=field_name,
                severity=str(item.get("severity", "info")),
                message=str(item.get("message", "")),
                current=item.get("current"),
                suggested=suggested,
            ))
        report.summary = str(parsed.get("summary", ""))

    def _commit_card(
        self,
        original: dict,
        parsed: dict,
        path: Path,
        report: ResearchReport,
        backup_path: Path | None,
    ) -> None:
        """Merge, validate and write (or dry-run) the card. Unlocks on success."""
        merged = dict(original)
        for f in report.findings:
            if f.suggested is not None and f.field:
                merged[f.field] = f.suggested
        merged = _ensure_license_consistency(merged)
        merged = _ensure_gguf_conventions(merged)
        report.findings.extend(_check_license_cascade(merged))
        merged = _preserve_operator_fields(original, merged)
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
            logger.info(
                "    [DRY-RUN] Wuerde %s aktualisieren (%d Felder, %d Findings).",
                path.name, len(cleaned), len(report.findings),
            )
        else:
            final = dict(cleaned)
            final_checks: list[CardFinding] = []
            final_checks.extend(_check_license_consistency(dict(final)))
            final_checks.extend(_check_license_text_fields(dict(final)))
            final_checks.extend(_check_community(dict(final)))
            pflicht_warnings = [w for w in warnings if "Pflichtfeld" in w]
            has_remaining_errors = (
                any(f.severity == "error" for f in final_checks)
                or len(pflicht_warnings) > 0
            )
            if has_remaining_errors:
                err_count = len([f for f in final_checks if f.severity == "error"]) + len(pflicht_warnings)
                logger.warning("    ⚠️ profile_verified bleibt false — %d verbleibende Probleme.", err_count)
                final["profile_verified"] = False
                final["profile_verified_at"] = None
                final["profile_verified_by"] = None
            else:
                final["profile_verified"] = True
                final["profile_verified_at"] = date.today().isoformat()
                final["profile_verified_by"] = f"llm:{self.llm_spec.model}"
            final["last_modified_at"] = date.today().isoformat()
            path.write_text(
                json.dumps(final, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report.unlocked = True
            report.wrote = True
            report.profile_verified = bool(final.get("profile_verified", False))
            logger.info("    🔒 Lock geschlossen: %s (profile_verified=%s)", path.name, report.profile_verified)
            if backup_path and backup_path.exists():
                try:
                    backup_path.unlink()
                    report.backup_path = None
                except OSError as exc:
                    logger.warning("    ⚠️ Backup loeschen fehlgeschlagen: %s", exc)

        self.summary.processed += 1

    def _handle_research_error(
        self, exc: Exception, path: Path, report: ResearchReport
    ) -> None:
        """Common error handler for research exceptions."""
        report.error = str(exc)
        logger.error("    🔓 Lock bleibt offen: %s (Fehler: %s)", path.name, exc)
        self.summary.errors += 1
        self.summary.research_reports.append(report)

    def run(self) -> RunSummary:
        targets = _discover_research_targets(self.args)
        if not targets:
            logger.info("⚠️  Keine Ziel-Cards gefunden (alle bereits verifiziert?).")
            return self.summary

        tooluse = getattr(self.args, "tooluse", False)
        mcp_url = getattr(self.args, "mcp_url", "http://localhost:8765")
        mcp_started_by_us = False

        if tooluse:
            mcp_started_by_us = _ensure_mcp_running(mcp_url)
            if not mcp_started_by_us and not _check_health(f"{mcp_url}/health", "MCP"):
                logger.error("❌ MCP-Server nicht erreichbar — Abbruch.")
                return self.summary
            logger.info(
                "🔬 Card-Researcher Tool-Use: %s/%s (MCP=%s)",
                self.llm_spec.provider_name, self.llm_spec.model, mcp_url,
            )
        else:
            logger.info(
                "🔬 Card-Researcher LLM: %s/%s (base_url=%s)",
                self.llm_spec.provider_name, self.llm_spec.model, self.llm_spec.base_url,
            )
        logger.info("📦 %d Card(s) zu recherchieren.", len(targets))

        max_cards = getattr(self.args, "max_cards", 0)
        if max_cards > 0:
            targets = targets[:max_cards]
            logger.info("    🔢 Limitiert auf %d Cards pro Run.", max_cards)

        llm_root = _server_root_url(self.llm_spec.base_url)
        try:
            for idx, (mid, path) in enumerate(targets, 1):
                if idx > 1:
                    pause = getattr(self.args, 'pause', 1.0)
                    time.sleep(pause)
                    logger.info("    ⏸ Pause %.1fs vor nächster Card.", pause)

                if not _check_health(f"{llm_root}/health", "llama.cpp", timeout=5):
                    logger.error("    ❌ llama.cpp nicht erreichbar — überspringe %s.", mid)
                    self.summary.errors += 1
                    continue

                print(f"\n[{idx}/{len(targets)}] {mid}")
                logger.info("[%d/%d] %s — %s", idx, len(targets), mid, path.name)
                if tooluse:
                    self._research_tooluse_one(mid, path, idx, len(targets))
                else:
                    self._research_one(mid, path, idx, len(targets))

                _reset_llama_context(self.llm_spec.base_url)
        finally:
            if mcp_started_by_us:
                _stop_mcp_server()

        remaining = len(_discover_research_targets(self.args))
        if remaining > 0:
            logger.info(
                "📊 Fortschritt: %d verarbeitet, %d noch offen. "
                "Server neustarten und erneut laufen lassen.",
                self.summary.processed, remaining,
            )

        return self.summary

    def _research_one(self, mid: str, path: Path, idx: int, total: int) -> ResearchReport:
        report = ResearchReport(model_id=mid, card_path=path)

        original = self._load_card(path, report)
        if original is None:
            return report

        original = _prefill_template_fields(original, self.template)

        pre_findings = _collect_pre_findings(original)
        report.findings.extend(pre_findings)

        if not self._apply_lock(original, path, report):
            return report

        backup_path = self._create_backup(path, report)

        try:
            user_prompt = _build_research_user_prompt(original, self.editor_prompt, pre_findings)
            response = self.session.query(
                system=_RESEARCH_SYSTEM_INSTRUCTION,
                user=user_prompt,
                temperature=self.llm_spec.temperature,
            )
            report.raw_response = response

            parsed = _extract_json_object(response)
            if parsed is None:
                report.parse_error = f"Kein parsebares JSON: {response[:200]}…"
                logger.error("    ❌ Recherche fehlgeschlagen — Lock bleibt offen.")
                self.summary.errors += 1
                self.summary.research_reports.append(report)
                return report

            self._extract_findings(parsed, report)
            self._commit_card(original, parsed, path, report, backup_path)
        except (OSError, json.JSONDecodeError, openai.APIError, ValueError) as exc:  # noqa: BLE001
            self._handle_research_error(exc, path, report)
            return report

        self.summary.research_reports.append(report)
        return report

    def _build_tooluse_user_prompt(
        self,
        original: dict,
        pre_findings: list[CardFinding],
        tool_results: list[str],
    ) -> str:
        text_card = {k: v for k, v in original.items() if k in _LLM_TEXT_FIELDS}
        structural_card = {k: v for k, v in original.items() if k not in _LLM_TEXT_FIELDS}
        parts = [
            self.editor_prompt,
            "",
            "## Strukturelle Felder (vom Script validiert)",
            "```json",
            json.dumps(structural_card, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Zu pruefende Textfelder",
            "```json",
            json.dumps(text_card, ensure_ascii=False, indent=2),
            "```",
        ]
        if pre_findings:
            parts.append("")
            parts.append("## Heuristische Pre-Findings")
            for finding in pre_findings:
                parts.append(f"- `{finding.field}` [{finding.severity}]: {finding.message}")
        if tool_results:
            parts.append("")
            parts.append("## Tool-Ergebnisse bisher")
            for i, result in enumerate(tool_results, 1):
                parts.append(f"### Ergebnis {i}")
                parts.append(result)
        return "\n".join(parts)

    def _query_tooluse_round(
        self,
        system_prompt: str,
        user_prompt: str,
        round_num: int,
        report: ResearchReport,
    ) -> str | None:
        try:
            return self.session.query(
                system=system_prompt,
                user=user_prompt,
                temperature=self.llm_spec.temperature,
            )
        except Exception as exc:
            logger.error("    ❌ LLM-Call fehlgeschlagen (Runde %d): %s", round_num, exc)
            report.error = f"LLM-Call Runde {round_num}: {exc}"
            self.summary.errors += 1
            self.summary.research_reports.append(report)
            return None

    def _append_tool_result(
        self,
        tool_call: dict[str, Any],
        mcp_url: str,
        tool_results: list[str],
        round_num: int,
    ) -> None:
        tool_name = tool_call.get("name", "")
        tool_params = tool_call.get("parameters", {})
        logger.info(
            "    🔧 Runde %d: Tool-Call '%s' mit params=%s",
            round_num,
            tool_name,
            json.dumps(tool_params, ensure_ascii=False)[:200],
        )
        transcript = _call_mcp_tool(mcp_url, tool_name, tool_params)
        content = _extract_tool_content(transcript)
        tool_results.append(f"Tool: {tool_name}\n{content}")
        logger.info("    📥 Runde %d: Tool-Ergebnis (%d chars)", round_num, len(content))

    def _handle_tooluse_parse_error(
        self,
        parse_err: str,
        response: str,
        round_num: int,
        max_tool_rounds: int,
        report: ResearchReport,
    ) -> bool:
        if round_num < max_tool_rounds:
            logger.warning(
                "    ⚠️ Runde %d: Kein Tool-Call, kein findings-JSON — retry: %s | Response: %s",
                round_num,
                parse_err[:100],
                response[:300],
            )
            return True
        report.parse_error = f"Kein parsebares JSON nach {max_tool_rounds} Runden: {parse_err[:200]}"
        logger.error("    ❌ Keine finale Antwort nach %d Runden. Response: %s", round_num, response[:1500])
        self.summary.errors += 1
        self.summary.research_reports.append(report)
        return False

    def _run_tooluse_rounds(
        self,
        original: dict,
        pre_findings: list[CardFinding],
        report: ResearchReport,
        mcp_url: str,
    ) -> dict | None:
        system_prompt = _build_tooluse_system_instruction(TOOL_SCHEMAS)
        tool_results: list[str] = []
        max_tool_rounds = 3
        for round_num in range(1, max_tool_rounds + 1):
            user_prompt = self._build_tooluse_user_prompt(original, pre_findings, tool_results)
            response = self._query_tooluse_round(system_prompt, user_prompt, round_num, report)
            if response is None:
                return None
            if round_num == max_tool_rounds:
                report.raw_response = response
            tool_call, parse_err = _parse_tool_call(response)
            if tool_call is not None:
                self._append_tool_result(tool_call, mcp_url, tool_results, round_num)
                continue
            if parse_err and not self._handle_tooluse_parse_error(parse_err, response, round_num, max_tool_rounds, report):
                return None
            if parse_err:
                continue
            final_parsed = _extract_json_object(response)
            if final_parsed is None:
                report.parse_error = f"Kein parsebares JSON: {response[:200]}…"
                logger.error("    ❌ Runde %d: Kein parsebares JSON.", round_num)
                self.summary.errors += 1
                self.summary.research_reports.append(report)
                return None
            if "findings" in final_parsed:
                return final_parsed
        return {}

    def _research_tooluse_one(self, mid: str, path: Path, idx: int, total: int) -> ResearchReport:
        report = ResearchReport(model_id=mid, card_path=path)
        mcp_url = getattr(self.args, "mcp_url", "http://localhost:8765")
        original = self._load_card(path, report)
        if original is None:
            return report
        original = _prefill_template_fields(original, self.template)
        pre_findings = _collect_pre_findings(original)
        report.findings.extend(pre_findings)
        if not self._apply_lock(original, path, report):
            return report
        backup_path = self._create_backup(path, report)
        try:
            final_parsed = self._run_tooluse_rounds(original, pre_findings, report, mcp_url)
            if final_parsed is None:
                return report
            self._extract_findings(final_parsed, report, text_only=False)
            self._commit_card(original, final_parsed, path, report, backup_path)
        except (OSError, json.JSONDecodeError, openai.APIError, ValueError) as exc:
            self._handle_research_error(exc, path, report)
        self.summary.research_reports.append(report)
        return report


def _render_research_markdown_report(reports: list[ResearchReport], today: str) -> str:
    lines: list[str] = [
        f"# Model Card Research Report — {today}",
        "",
        "**Modus:** research",
        f"**Verarbeitet:** {sum(1 for r in reports if not r.error and r.parse_error is None)}"
        f" · **Recherche-Fehler:** {sum(1 for r in reports if r.error or r.parse_error)}"
        f" · **Murks-Findings:** "
        f"{sum(1 for r in reports for f in r.findings if f.severity == 'error')}",
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
        if r.locked and not r.unlocked:
            lines.append("  - _🔓 Lock offen (profile_verified=false) — bei naechstem Lauf Resumption_")
        elif r.unlocked:
            if r.profile_verified:
                lines.append("  - _🔒 Lock geschlossen (profile_verified=true)_")
            else:
                lines.append("  - _🔒 Lock geschlossen (profile_verified=false) — error-Findings vorhanden_")
        lines.append("")
    return "\n".join(lines)

