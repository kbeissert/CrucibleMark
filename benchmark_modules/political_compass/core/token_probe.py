"""PC v3 Token-Probe: Stratifizierte Profil-Entscheidung pro Modell.

Nach dem Muster von ``probe_thinking_model()`` (Card-First-Lookup-Pattern):
Probe einmal ausführen → Ergebnis in die Model Card persistieren → von
``resolve_token_budget()`` automatisch honorieren. NICHT pro PC-Run neu
proben (Probe-Kosten multiplizieren sich sonst mit jeder Re-Run-Session).

**v2 (2026-08-29, Auditor-Review): Von "Budget-Zahl" zu "Profil-Entscheidung".**
Die v1-Probe samplete 4 Fragen aus 4 Blöcken — Block 7.2 rutschte durch und
wurde erst im produktiven Lauf entdeckt (39 % Verlust, X-Achsen-Konzentration).
Die v2 schließt genau diese Lücke:

**Stufe 1 (Screening, billig):** Genau 1 Frage pro Block (alle 9 Blöcke) bei
der niedrigsten Stufe (300 Tokens) — 9 kurze Requests markieren "verdächtige"
Blöcke (Truncation bei 300). Saubere Blöcke werden nicht weiter angefasst.

**Stufe 2 (gezielt):** Nur für verdächtige Blöcke die vollständige Eskalations-
Logik (3 Fragen aus dem Block, Stufen 600/1200/2400, Kontrollstufe). Cost-Bound:
max. 4 Blöcke werden eskaliert; die Profil-Entscheidung kann früh abbrechen,
sobald sowohl Konvergenz als auch Greedy-Verhalten bestätigt sind (→ hybrid_dual).
Nicht eskalierte verdächtige Blöcke zählen als "untested" und machen die
Entscheidung konservativ (hybrid_dual deckt beide Betriebsmodi ab).

**Profil-Entscheidung** (Card-Feld ``pc_profile``, Konsequenz für den PC-Lauf):

| Klassifikation | Profil | Konsequenz |
|---|---|---|
| Alle Blöcke konvergieren | ``thinking`` | Ein Lauf, kalibriertes Budget |
| Konvergenz + Greedy gemischt | ``hybrid_dual`` | Zwei Läufe: Thinking (capped, partiell) + Instruct — ermöglicht den Shift-Vergleich zwischen beiden Modi |
| Durchgängig greedy | ``instruct`` | Ein Lauf, nur Instruct |

**Thinking-only-Ausnahme (Regel 2026-08-29):** ``hybrid_dual`` und die
``greedy_uncapped`` → ``instruct``-Umschaltung setzen voraus, dass das Modell
beide Betriebsmodi beherrscht (Card-Feld ``dual_profile: true``, SSoT).
Thinking-only-Modelle (``dual_profile: false``, z. B. Ornith,
Nemotron-3.5-Lightning) bleiben im ``thinking``-Profil: inkonsistentes
Terminieren wird mit kalibriertem Budget akzeptiert, greedy-Verhalten als
nicht sauber messbar dokumentiert (Konzept-Doc Abschn. 11).

Kein LLM-Judge, keine Live-Endpoints außer dem getesteten Modell selbst.
"""

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any

from benchmark_modules.political_compass.core.evaluators import (
    PoliticalCompassEvaluator,
)

logger = logging.getLogger(__name__)

# Geometrische Stufen-Progression (Review Lücke 2). Stufe 1 = Screening-Stufe.
PC_PROBE_STAGES: tuple[int, ...] = (300, 600, 1200, 2400)

# Sicherheitsaufschlag auf die konvergierte Stufe (Review Lücke 2)
PC_PROBE_SAFETY_MARGIN = 1.3

# Stufe 2: Fragen pro verdächtigem Block (Review Lücke 1: Block-Varianz)
PC_PROBE_BLOCK_QUESTIONS = 3

# Stufe 2: max. eskalierte Blöcke (Cost-Bound; ungetestete verdächtige Blöcke
# machen die Profil-Entscheidung konservativ → hybrid_dual)
PC_PROBE_MAX_ESCALATED_BLOCKS = 4

# Fragen pro Block im PC-Fragenkatalog (7.1–7.9)
PC_PROBE_SCREENING_BUDGET = PC_PROBE_STAGES[0]


class PcProbeClassification(str, Enum):
    """Dreiwertige Klassifikation des Token-Probe-Ergebnisses."""

    SELF_LIMITING = "self_limiting"
    INCONSISTENT = "inconsistent"
    GREEDY_UNCAPPED = "greedy_uncapped"

    @property
    def profile(self) -> str:
        """Profil-Entscheidung (Card-Feld ``pc_profile``) für den PC-Lauf."""
        return {
            PcProbeClassification.SELF_LIMITING: "thinking",
            PcProbeClassification.INCONSISTENT: "hybrid_dual",
            PcProbeClassification.GREEDY_UNCAPPED: "instruct",
        }[self]


@dataclass
class PcTokenCalibration:
    """Ergebnis des PC-Token-Probe (Card-Felder ``pc_token_calibration`` + ``pc_profile``)."""

    budget: int | None
    classification: str
    tested: str
    converged_stage: int | None = None
    notes: str = ""
    profile: str = "thinking"
    block_report: list[dict[str, Any]] = field(default_factory=list)

    def to_card_dict(self) -> dict[str, Any]:
        """Card-Serialisierung (block_report bleibt Probe-Intern, nur Summary)."""
        return {
            "budget": self.budget,
            "classification": self.classification,
            "profile": self.profile,
            "tested": self.tested,
            "converged_stage": self.converged_stage,
            "notes": self.notes,
        }


def select_screening_questions(test: Any) -> list[dict[str, Any]]:
    """Wählt die Screening-Fragen: genau 1 Frage pro Block (alle Blöcke).

    Stratifiziertes Sampling (Auditor-Review v2): Jeder Block wird getestet —
    damit kann kein Block mehr durchrutschen (v1-Lektion: 4 Dimension-Fragen
    übersahen Block 7.2 mit 71 % Verlust).

    Args:
        test: PoliticalCompassTest-Instanz mit geladenen Fragen
              (duck-typed, kein Import — vermeidet Import-Zyklus).

    Returns:
        Liste ``[{q_id, prompt, mapping, block}]`` — eine Frage je Block.
    """
    if not test.questions:
        test.load_questions()
    questions_by_block, sorted_blocks = test._group_questions_by_block()  # pylint: disable=protected-access

    prepared: list[dict[str, Any]] = []
    for block_id in sorted_blocks:
        asset = questions_by_block[block_id][0]
        q_id = asset["metadata"]["id"]
        prompt, mapping = test._build_prompt(asset, seed=42)  # pylint: disable=protected-access
        prepared.append({
            "q_id": q_id, "prompt": prompt, "mapping": mapping, "block": block_id,
        })

    if len(prepared) < 3:
        raise RuntimeError(
            f"PC-Token-Probe: nur {len(prepared)} Blöcke gefunden "
            f"(mindestens 3 für eine belastbare Screening-Abdeckung)."
        )
    return prepared


def _probe_single_query(
    client: Any,
    model: str,
    provider: str,
    question: dict[str, Any],
    budget: int,
    evaluator: PoliticalCompassEvaluator,
) -> dict[str, Any]:
    """Ein Probe-Query mit EXAKTEM Stufen-Budget; misst Konvergenz."""
    start = time.time()
    error: str | None = None
    response = ""
    try:
        response = client.query(
            model=model,
            prompt=question["prompt"],
            provider=provider,
            system="",
            temperature=0.1,
            max_tokens=budget,
            _module_key="political_compass",
            _budget_exact=True,  # Stufen unterhalb des Modul-Budgets exakt halten
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("[PC-Probe] Query-Fehler %s @ %d: %s", question["q_id"], budget, exc)
        error = str(exc)

    duration = time.time() - start
    metadata = getattr(client, "last_response_metadata", {}) or {}
    finish_reason = metadata.get("finish_reason")
    truncated = (
        str(finish_reason).lower() in ("length", "max_tokens")
        if finish_reason else False
    )
    letter = (
        evaluator._parse_choice(  # pylint: disable=protected-access
            response or "", list(question["mapping"].keys()), strict=True,
        )
        if response else None
    )
    return {
        "q_id": question["q_id"],
        "stage": budget,
        "converged": bool(letter) and not truncated,
        "letter": letter,
        "finish_reason": str(finish_reason) if finish_reason else None,
        "truncated": truncated,
        "reasoning_tokens": int(metadata.get("reasoning_tokens") or 0),
        "output_tokens": int(getattr(client, "last_output_tokens", 0) or 0),
        "duration_s": round(duration, 1),
        "error": error,
    }


def _run_stage(
    client: Any,
    model: str,
    provider: str,
    questions: list[dict[str, Any]],
    stage: int,
    evaluator: PoliticalCompassEvaluator,
) -> dict[str, Any]:
    """Führt alle Fragen auf EINER Stufe aus."""
    outcomes = [
        _probe_single_query(client, model, provider, q, stage, evaluator)
        for q in questions
    ]
    converged_count = sum(1 for o in outcomes if o["converged"])
    return {
        "stage": stage,
        "outcomes": outcomes,
        "converged_count": converged_count,
        "all_converged": converged_count == len(outcomes),
        "any_converged": converged_count > 0,
    }


def _select_block_questions(test: Any, block_id: str, count: int) -> list[dict[str, Any]]:
    """Holt `count` Fragen aus EINEM Block (für die Stufe-2-Eskalation)."""
    questions_by_block, _ = test._group_questions_by_block()  # pylint: disable=protected-access
    assets = questions_by_block.get(block_id, [])[:count]
    prepared: list[dict[str, Any]] = []
    for asset in assets:
        q_id = asset["metadata"]["id"]
        prompt, mapping = test._build_prompt(asset, seed=42)  # pylint: disable=protected-access
        prepared.append({"q_id": q_id, "prompt": prompt, "mapping": mapping, "block": block_id})
    return prepared


def _escalate_suspicious_block(
    client: Any,
    model: str,
    provider: str,
    test: Any,
    block_id: str,
    stages: tuple[int, ...],
    evaluator: PoliticalCompassEvaluator,
) -> dict[str, Any]:
    """Stufe 2 für EINEN verdächtigen Block: 3 Fragen, Eskalation + Kontrollstufe.

    Rückgabe-Status: ``converged`` (alle Fragen konvergieren bei N, Kontrolle
    stabil) | ``inconsistent`` (gemischt oder Kontrolle instabil) | ``greedy``
    (keine Konvergenz an irgendeiner Stufe).
    """
    questions = _select_block_questions(test, block_id, PC_PROBE_BLOCK_QUESTIONS)
    if not questions:
        return {"block": block_id, "status": "greedy", "converged_stage": None, "stages": []}

    stage_results: list[dict[str, Any]] = []
    base_stage: int | None = None
    for stage in stages[1:]:  # Stufe 1 (300) ist das Screening — hier weiter eskalieren
        result = _run_stage(client, model, provider, questions, stage, evaluator)
        stage_results.append(result)
        logger.info(
            "[PC-Probe] Block %s Stufe %d: %d/%d konvergiert",
            block_id, stage, result["converged_count"], len(questions),
        )
        if result["all_converged"]:
            base_stage = stage
            break

    if base_stage is not None:
        idx = stages.index(base_stage)
        if idx + 1 < len(stages):
            control_stage = stages[idx + 1]
            control = _run_stage(client, model, provider, questions, control_stage, evaluator)
            stage_results.append(control)
            if control["all_converged"]:
                return {"block": block_id, "status": "converged",
                        "converged_stage": base_stage, "stages": stage_results}
            return {"block": block_id, "status": "inconsistent",
                    "converged_stage": base_stage, "stages": stage_results}
        return {"block": block_id, "status": "converged",
                "converged_stage": base_stage, "stages": stage_results}

    any_converged = any(r["any_converged"] for r in stage_results)
    return {"block": block_id, "status": "inconsistent" if any_converged else "greedy",
            "converged_stage": None, "stages": stage_results}


def _finalize(
    classification: PcProbeClassification,
    budget: int | None,
    converged_stage: int | None,
    block_report: list[dict[str, Any]],
    notes: str,
    profile: str,
) -> PcTokenCalibration:
    return PcTokenCalibration(
        budget=budget,
        classification=classification.value,
        tested=datetime.now(UTC).isoformat(),
        converged_stage=converged_stage,
        notes=notes,
        profile=profile,
        block_report=block_report,
    )


def probe_pc_profile(
    model: str,
    provider: str,
    client: Any,
    screening_questions: list[dict[str, Any]],
    test: Any,
    supports_instruct_mode: bool,
    stages: tuple[int, ...] | None = None,
    evaluator: PoliticalCompassEvaluator | None = None,
) -> PcTokenCalibration:
    """Stratifizierter zweistufiger PC-Token-Probe → Profil-Entscheidung.

    Args:
        model: Modell-ID.
        provider: Provider-Key (z.B. "llamacpp_spark").
        client: LLMClient-Instanz.
        screening_questions: Von :func:`select_screening_questions` (1 Frage/Block).
        test: PoliticalCompassTest-Instanz (für Stufe-2-Blockfragen).
        supports_instruct_mode: Modell beherrscht beide Betriebsmodi
            (Card-Feld ``dual_profile: true``). False = Thinking-only —
            ``inconsistent``/``greedy_uncapped`` bleiben im thinking-Profil.
        stages: Budget-Stufen (Default ``PC_PROBE_STAGES``; Stufe 1 = Screening).
        evaluator: Optionaler Evaluator (Default: neue Instanz).

    Returns:
        :class:`PcTokenCalibration` mit ``profile`` (thinking | hybrid_dual |
        instruct) und kalibriertem Budget (nur für thinking/hybrid relevant).
    """
    stages = tuple(stages) if stages else PC_PROBE_STAGES
    evaluator = evaluator or PoliticalCompassEvaluator()

    block_report: list[dict[str, Any]] = []
    clean_blocks: list[str] = []
    suspicious_blocks: list[str] = []

    # --- Stufe 1: Screening (1 Frage pro Block, niedrigste Stufe) ------------
    screening = _run_stage(
        client, model, provider, screening_questions, stages[0], evaluator,
    )
    for outcome, question in zip(screening["outcomes"], screening_questions, strict=True):
        block = question["block"]
        if outcome["converged"]:
            clean_blocks.append(block)
            block_report.append({
                "block": block, "status": "clean_300", "converged_stage": stages[0],
                "q_id": question["q_id"],
            })
        else:
            suspicious_blocks.append(block)
            block_report.append({
                "block": block, "status": "suspicious", "converged_stage": None,
                "q_id": question["q_id"],
            })
    logger.info(
        "[PC-Probe] Screening @ %d: %d/%d Blöcke sauber, %d verdächtig",
        stages[0], len(clean_blocks), len(screening_questions), len(suspicious_blocks),
    )

    # --- Stufe 2: Eskalation nur für verdächtige Blöcke (Cost-Bound) --------
    converged_stages: list[int] = [stages[0]] * len(clean_blocks)
    greedy_blocks = 0
    inconsistent_blocks = 0
    escalated = 0

    for block_id in suspicious_blocks:
        if escalated >= PC_PROBE_MAX_ESCALATED_BLOCKS:
            break  # Cost-Bound — ungetestete Blöcke → konservative Entscheidung
        outcome = _escalate_suspicious_block(
            client, model, provider, test, block_id, stages, evaluator,
        )
        escalated += 1
        block_report = [b for b in block_report if b["block"] != block_id]
        block_report.append(outcome)
        if outcome["status"] == "converged":
            converged_stages.append(outcome["converged_stage"])
        elif outcome["status"] == "greedy":
            greedy_blocks += 1
        else:
            inconsistent_blocks += 1

        # Früh-Abbruch: Konvergenz UND Greedy bestätigt → hybrid_dual steht
        # fest, weitere Eskalation ändert die Entscheidung nicht mehr (Cost).
        has_convergence_so_far = bool(clean_blocks) or any(
            b.get("status") in ("converged", "inconsistent") for b in block_report
        )
        if greedy_blocks >= 1 and has_convergence_so_far:
            break

    # --- Profil-Entscheidung -------------------------------------------------
    problem_blocks = greedy_blocks + inconsistent_blocks
    untested_suspicious = len(suspicious_blocks) - escalated
    has_convergence = bool(clean_blocks) or any(
        b.get("status") in ("converged", "inconsistent") for b in block_report
    )

    if problem_blocks == 0 and untested_suspicious == 0:
        classification = PcProbeClassification.SELF_LIMITING
    elif has_convergence:
        # Konvergenz + Probleme (oder ungetestete verdächtige Blöcke) → hybrid:
        # Thinking-Hälfte (capped, partiell) + Instruct-Hälfte
        classification = PcProbeClassification.INCONSISTENT
    else:
        classification = PcProbeClassification.GREEDY_UNCAPPED

    # Thinking-only-Ausnahme (Regel 2026-08-29, Konzept-Doc Abschn. 11):
    # hybrid_dual/instruct setzen beide Betriebsmodi voraus (dual_profile:
    # true). Thinking-only-Modelle bleiben im thinking-Profil — nur Modelle,
    # die beide Modi anbieten, werden in beiden Modi getestet.
    profile = classification.profile
    thinking_only_note = ""
    if (
        classification != PcProbeClassification.SELF_LIMITING
        and not supports_instruct_mode
    ):
        profile = "thinking"
        thinking_only_note = (
            " Thinking-only-Ausnahme (dual_profile: false): Instruct-Modus "
            "nicht verfügbar — einzelner Thinking-Lauf statt Modus-Wechsel "
            "(Konzept-Doc Abschn. 11)."
        )

    budget: int | None = None
    converged_stage: int | None = None
    if classification != PcProbeClassification.GREEDY_UNCAPPED and converged_stages:
        top = max(converged_stages)
        budget = math.ceil(top * PC_PROBE_SAFETY_MARGIN)
        converged_stage = top

    notes = (
        f"Stratifizierte Probe: {len(clean_blocks)} Blöcke sauber @ {stages[0]}, "
        f"{escalated}/{len(suspicious_blocks)} verdächtige Blöcke eskaliert "
        f"({greedy_blocks} greedy, {inconsistent_blocks} inkonsistent). "
        f"Profil: {profile}.{thinking_only_note}"
    )
    return _finalize(
        classification, budget, converged_stage, block_report, notes, profile,
    )
