"""PC-Token-Probe: Card-First-Hook (Pattern: Thinking-Probe).

Analog zu ``unified_runner._ensure_model_card`` (Thinking-Probe vor dem
Standard-Benchmark): Hat die Model Card keinen PC-Token-Probe-Eintrag
(``pc_profile`` fehlt oder ist null), wird die Probe vor dem PC-Benchmark
ausgeführt und das Ergebnis persistiert (``pc_token_calibration`` +
``pc_profile``). Nachfolgende Läufe überspringen die Probe (Card-First;
``resolve_token_budget()`` honoriert das kalibrierte Budget automatisch).

Die Probe-Algorithmik selbst lebt in :mod:`token_probe` (stratifizierter
zweistufiger Sampling). Dieses Modul ist nur für Card-State,
Orchestrierung und Card-Write verantwortlich — gemeinsame SSoT für den
Runner-Hook (``utils/base_runner.py``) und das CLI-Tool
``scripts/tools/pc_calibrate.py`` (kein Duplikat).

**Fast-Fail-Guard (Incident 2026-09-02):** Bei ``PcProbeError``
(systematische Provider-Fehler) wird bewusst NICHT in die Card geschrieben
— der nächste Lauf wiederholt die Probe. Der Runner lässt den Benchmark
weiterlaufen (analog Thinking-Probe-Skip bei 429/403).
"""

import json
import logging
from pathlib import Path
from typing import Any

from benchmark_modules.political_compass.core.token_probe import (
    PcTokenCalibration,
    probe_pc_profile,
    select_screening_questions,
)
from utils.io_helpers import atomic_write_json
from utils.model_card_io import _find_card, read_dual_profile

logger = logging.getLogger(__name__)


def read_pc_probe_state(model: str) -> tuple[bool, dict[str, Any] | None]:
    """Liest die Card und prüft, ob ein PC-Token-Probe fehlt.

    Returns:
        ``(needs_probe, card_data)``. Card fehlt, ist unlesbar oder
        ``pc_profile`` fehlt/null (Draft-Cards) → ``needs_probe=True``.
        Semantik identisch zur Thinking-Probe: nur None/fehlt triggert,
        ein gesetzter Wert (thinking | hybrid_dual | instruct) nicht.
    """
    card_path = _find_card(model)
    if not card_path.exists():
        return True, None
    try:
        card: dict[str, Any] = json.loads(card_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "[PC-Probe-Hook] Card für '%s' unlesbar: %s — Probe wird nachgeholt.",
            model, exc,
        )
        return True, None
    if card.get("pc_profile") is None:
        return True, card
    return False, card


def run_pc_token_probe(
    model: str,
    provider: str,
    client: Any,
) -> PcTokenCalibration:
    """Führt den stratifizierten zweistufigen Token-Probe aus.

    Args:
        model: Modell-ID (kanonisch).
        provider: Provider-Key (z.B. "anthropic", "llamacpp_spark").
        client: LLMClient-Instanz.

    Raises:
        PcProbeError: Fast-Fail-Guard — mehr als 50 % der Queries sind
            fehlgeschlagen (systematischer Provider-Fehler). Kein Card-Write.
    """
    from benchmark_modules.political_compass.test import PoliticalCompassTest

    test = PoliticalCompassTest()
    screening = select_screening_questions(test)
    print(
        f"[PC-Probe] {model} · Screening: 1 Frage/Block ({len(screening)} Blöcke) "
        f"@ 300 Tokens, Stufe 2 nur für verdächtige Blöcke …",
        flush=True,
    )
    # Thinking-only-Ausnahme (Regel 2026-08-29): dual_profile aus der Card ist
    # die SSoT für die Modi-Fähigkeit — nur Modelle mit beiden Betriebsmodi
    # dürfen hybrid_dual/instruct-Profile bekommen (Konzept-Doc Abschn. 11).
    supports_instruct = read_dual_profile(model)
    if not supports_instruct:
        print(
            f"[PC-Probe] {model}: Thinking-only (dual_profile != true) — "
            f"kein Instruct-Gegenlauf möglich.",
            flush=True,
        )
    return probe_pc_profile(
        model, provider, client, screening, test,
        supports_instruct_mode=supports_instruct,
    )


def write_pc_calibration_to_card(
    model: str,
    calibration: PcTokenCalibration,
    provider: str | None = None,
) -> Path:
    """Persistiert das Probe-Ergebnis in die Card (Pattern: probe_thinking.py).

    Schreibt ``pc_token_calibration`` (Budget + Klassifikation) UND das
    Top-Level-Feld ``pc_profile`` (thinking | hybrid_dual | instruct).
    """
    from utils.card_utils import ensure_card

    existing_path = _find_card(model)
    if existing_path.exists():
        card_path = ensure_card(model, card_path=existing_path)
    else:
        card_path = ensure_card(model, provider=provider)

    card: dict[str, Any] = json.loads(card_path.read_text(encoding="utf-8"))
    card["pc_token_calibration"] = calibration.to_card_dict()
    card["pc_profile"] = calibration.profile
    atomic_write_json(card_path, card, indent=2, ensure_ascii=False)
    return card_path


def ensure_pc_token_probe(
    model: str,
    provider: str,
    client: Any,
) -> PcTokenCalibration | None:
    """Card-First-Hook: Probe nur ausführen, wenn die Card keinen Eintrag hat.

    Returns:
        Kalibrierungs-Ergebnis nach Probe + Card-Write, oder None wenn
        übersprungen (Card hat bereits ``pc_profile``).

    Raises:
        PcProbeError: Fast-Fail-Guard — propagiert bewusst an den Aufrufer
            (kein Card-Write; der Runner lässt den Benchmark weiterlaufen).
    """
    needs_probe, card = read_pc_probe_state(model)
    if not needs_probe:
        print(
            f"   ✓ Card vorhanden mit pc_profile={card['pc_profile']} — "
            f"PC-Token-Probe übersprungen.",
            flush=True,
        )
        logger.info(
            "[PC-Probe-Hook] '%s' hat pc_profile=%s → Probe übersprungen.",
            model, card["pc_profile"],
        )
        return None

    reason = "Keine Card gefunden" if card is None else "Card vorhanden, aber pc_profile fehlt (null)"
    print(f"   ⏳ {reason} — starte PC-Token-Probe ...", flush=True)
    logger.info("[PC-Probe-Hook] '%s' → PC-Token-Probe vor dem Benchmark.", model)

    calibration = run_pc_token_probe(model, provider, client)
    card_path = write_pc_calibration_to_card(model, calibration, provider=provider)
    print(
        f"   ✓ PC-Token-Probe: profile={calibration.profile} "
        f"budget={calibration.budget} → {card_path}",
        flush=True,
    )
    return calibration
