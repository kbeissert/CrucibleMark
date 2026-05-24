"""Methodology notes for the tooluse benchmark review.

Deterministic rule-based annotations triggered by leaderboard row data.
Each note explains a structural benchmark condition to human reviewers —
no LLM inference, no scoring changes.

Usage:
    from benchmark_modules.tooluse.core.methodology_notes import get_applicable_notes
    notes = get_applicable_notes(leaderboard_row_dict)
    for note in notes:
        print(note.render_markdown())
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MethodologyNote:
    tag: str
    title: str
    body: str
    severity: str  # "info" | "warning" | "context"

    def render_markdown(self) -> str:
        icon = {"info": "ℹ️", "warning": "⚠️", "context": "📋"}.get(self.severity, "📋")
        lines = [
            f"> **{icon} [{self.tag}] {self.title}**",
            ">",
        ]
        for line in self.body.strip().splitlines():
            lines.append(f"> {line}" if line.strip() else ">")
        return "\n".join(lines)

    def render_text(self) -> str:
        """Plain-text version for terminal output."""
        return f"[{self.tag}] {self.title}\n{self.body.strip()}"


# ---------------------------------------------------------------------------
# Note definitions
# ---------------------------------------------------------------------------

_NOTES: list[dict[str, Any]] = [
    {
        "tag": "MCP_FORMAT_MISMATCH",
        "title": "Custom-MCP-Format — Retry erforderlich",
        "severity": "context",
        "trigger": lambda r: _bool(r.get("retry_required")),
        "body": (
            "Dieses Modell benötigte auf allen Benchmark-Assets einen zweiten Versuch,\n"
            "um einen gültigen Tool-Call im CrucibleMark-Custom-JSON-Schema zu erzeugen\n"
            "(`retry_required: true`). Das ist kein Fehler bei der Tool-Use-Kompetenz.\n"
            "\n"
            "Hintergrund: Kommerzielle Modelle sind durch Fine-Tuning auf ihr natives\n"
            "API-Tool-Calling-Format optimiert (z.B. Anthropic `tool_use`, OpenAI\n"
            "`function_calling`). CrucibleMark verwendet ein uniformes Custom-JSON-Schema\n"
            "im System-Prompt, damit alle Modelle — einschließlich lokaler Ollama-Modelle\n"
            "ohne native API — unter gleichen Bedingungen getestet werden.\n"
            "\n"
            "Auswirkung auf den Score: P1 misst das Ergebnis nach erfolgtem Tool-Call,\n"
            "nicht die Anzahl der Versuche. Der Retry erhöht Token-Verbrauch und Latenz,\n"
            "beeinflusst aber P1 nicht direkt.\n"
            "\n"
            "Einschränkung für die Praxis: Bei Einsatz über die native API (z.B. Cline\n"
            "mit Anthropic SDK oder OpenAI SDK) entfällt dieses Verhalten vollständig.\n"
            "Der Retry ist ein Benchmark-Artefakt, kein Produktionsproblem."
        ),
    },
    {
        "tag": "LOCAL_NATIVE_MCP_FORMAT",
        "title": "Lokales Modell — MCP-Custom-Format nativ beherrscht",
        "severity": "info",
        "trigger": lambda r: (
            not _bool(r.get("retry_required"))
            and r.get("deployment_type", "") in (
                "open-weights", "open-weights-cloud-available"
            )
            and r.get("tool_call_attempts", "1") == "1"
        ),
        "body": (
            "Dieses Modell erzeugte den Tool-Call-JSON im ersten Versuch korrekt\n"
            "(`retry_required: false`, `tool_call_attempts: 1`). Das deutet darauf hin,\n"
            "dass es weniger auf ein proprietäres natives Tool-Format konditioniert ist\n"
            "und den Instruction-Following-Ansatz des Custom-Schemas direkt umsetzt.\n"
            "\n"
            "Im Kontext Ollama + MCP-Stack ist das ein relevanter Produktionsvorteil:\n"
            "Weniger API-Calls, geringere Latenz, niedrigerer Token-Verbrauch pro Task."
        ),
    },
    {
        "tag": "HALLUCINATION_DETECTED",
        "title": "Halluzination erkannt — Hard Fail",
        "severity": "warning",
        "trigger": lambda r: _bool(r.get("hallucination_flag")),
        "body": (
            "Das Modell hat auf mindestens einem Asset Inhalte generiert, die nicht\n"
            "aus dem abgerufenen Tool-Ergebnis stammen, sondern erfunden wurden\n"
            "(`hallucination_flag: true`). Dies löst einen Hard Fail in der Bewertung aus.\n"
            "\n"
            "Für produktiven Einsatz in content-kritischen Tasks (z.B. Recherche,\n"
            "Dokumentenzusammenfassung, faktenbasierte Berichte) ist dieses Verhalten\n"
            "ein disqualifizierendes Signal. Der Score unterschätzt möglicherweise das\n"
            "Risiko, da nur erkannte Muster-Halluzinationen gezählt werden."
        ),
    },
    {
        "tag": "TOOL_CALL_INVALID",
        "title": "Tool-Call ungültig oder fehlgeschlagen",
        "severity": "warning",
        "trigger": lambda r: not _bool(r.get("tool_call_valid", "true")),
        "body": (
            "Das Modell hat auf mindestens einem Asset keinen auswertbaren Tool-Call\n"
            "erzeugt (`tool_call_valid: false`). Mögliche Ursachen: Parse-Fehler nach\n"
            "zwei Versuchen, Whitelist-Verletzung (Sandbox-Block), oder generelles\n"
            "Ignorieren der Tool-Use-Instruktion.\n"
            "\n"
            "P2 wurde durch den Combined-Score-Guardrail auf max. 60 gedeckelt.\n"
            "Empfehlung: Vor produktivem Einsatz mit Tool-Use-Aufgaben vertiefte\n"
            "Evaluierung mit task-spezifischen Prompts."
        ),
    },
    {
        "tag": "SYNTHESIS_QUALITY_LOW",
        "title": "Synthesequalität unter Benchmark-Schwelle",
        "severity": "warning",
        "trigger": lambda r: (
            _float(r.get("p2_score")) < 40.0
            and _bool(r.get("tool_call_valid", "true"))
        ),
        "body": (
            "Die Synthesequalität (P2) liegt unter 40 Punkten, obwohl das Tool korrekt\n"
            "aufgerufen wurde. Das deutet auf eine der folgenden Situationen hin:\n"
            "\n"
            "- **State B2 (Parametrische Antwort):** Das Modell ignorierte den abgerufenen\n"
            "  Content und antwortete aus seinem Trainings-Wissen heraus. P2 wurde auf\n"
            "  cap_B2=35 gedeckelt.\n"
            "- **State B1 (Transparentes Scheitern):** Das Modell konnte den Content nicht\n"
            "  verarbeiten und kommunizierte das transparent. P2 wurde auf cap_B1=50\n"
            "  gedeckelt — der tatsächliche Score lag jedoch darunter.\n"
            "- **State C (Kein Tool-Call):** Das Modell hat das Tool nicht genutzt.\n"
            "  P2 wurde auf cap_C=20 gedeckelt.\n"
            "\n"
            "Die genaue Ursache ist im Asset-Audit-Log dokumentiert\n"
            "(Content-Verification-State je Asset)."
        ),
    },
    {
        "tag": "HIGH_LATENCY_LOCAL",
        "title": "Hohe Latenz — Lokale Deployment-Grenze",
        "severity": "info",
        "trigger": lambda r: (
            _float(r.get("total_time_s")) > 120.0
            and r.get("deployment_type", "") in (
                "open-weights", "open-weights-cloud-available"
            )
        ),
        "body": (
            "Die Gesamt-Laufzeit für 3 Assets überschreitet 120 Sekunden\n"
            f"(`total_time_s` im Leaderboard). Bei lokalem Deployment ist das ein\n"
            "Hardware-abhängiger Grenzwert, kein Modellproblem.\n"
            "\n"
            "Einschätzung: Für interaktive Cline/Hermes-Sessions mit einzelnen\n"
            "Tool-Calls (nicht Batch) ist die relevante Latenz pro Call zu messen,\n"
            "nicht über einen 3-Asset-Batch. Der Benchmark misst die akkumulierte\n"
            "Batch-Latenz — die Einzelcall-Latenz liegt entsprechend niedriger."
        ),
    },
    {
        "tag": "MOCK_MODE_BENCHMARK",
        "title": "Benchmark in Mock-MCP-Modus ausgeführt",
        "severity": "context",
        "trigger": lambda r: r.get("mcp_mode", "") == "mock",
        "body": (
            "Dieser Benchmark-Run wurde im Mock-MCP-Modus ausgeführt (`mcp_mode: mock`).\n"
            "Der MCP-Server lieferte deterministische Fixture-Daten statt echter\n"
            "Netzwerk-Responses. Das gewährleistet:\n"
            "\n"
            "- **Reproduzierbarkeit:** Identischer Content für alle Modelle, keine\n"
            "  Netzwerk-Varianz in P2-Scores\n"
            "- **Fairness:** Kein Modell profitiert von aktuellem Web-Content oder\n"
            "  unterschiedlichen Ladezeiten\n"
            "- **Einschränkung:** Echte Netzwerk-Fehler, Timeouts oder Content-Varianz\n"
            "  werden nicht getestet. Für Produktions-Validierung ist ein Live-Mode-Run\n"
            "  empfohlen."
        ),
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_applicable_notes(row: dict[str, Any]) -> list[MethodologyNote]:
    """Return all notes whose trigger condition is met for the given leaderboard row."""
    result = []
    for spec in _NOTES:
        try:
            if spec["trigger"](row):
                result.append(MethodologyNote(
                    tag=spec["tag"],
                    title=spec["title"],
                    body=spec["body"],
                    severity=spec["severity"],
                ))
        except Exception:  # noqa: BLE001
            pass
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _float(value: Any) -> float:
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0
