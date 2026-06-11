"""Tests fuer utils.model_utils._has_inline_cot() und probe_thinking_model() Signal C.

Hintergrund: Gemma 4 26B-A4B ignoriert llama.cpp --reasoning off und produziert
Chain-of-Thought inline im content-Feld (User-Log-Beweis vom Spark-Benchmark-Run,
9.6.2026). Die klassischen Signale A (<think>-Tags) und B (reasoning_tokens
provider metadata) schlagen daher nicht an. Signal C ist eine Heuristik, die
typische Reasoning-Marker + Berechnungs-Operatoren erkennt.

Siehe: utils/model_utils.py:_has_inline_cot() und probe_thinking_model() Signal C.
"""
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.model_utils import (
    _has_inline_cot,
    _INLINE_COT_LENGTH_THRESHOLD,
    _INLINE_COT_OPS,
    probe_thinking_model,
    ThinkingProbeResult,
)


# ---------------------------------------------------------------------------
# _has_inline_cot() — direkte Heuristik-Tests
# ---------------------------------------------------------------------------

def test_inline_cot_empty_text_returns_false():
    """Leere Antwort darf nicht als CoT erkannt werden."""
    assert _has_inline_cot("") is False
    assert _has_inline_cot(None) is False  # type: ignore[arg-type]


def test_inline_cot_short_direct_answer_returns_false():
    """Direkte Antwort unterhalb der Laengen-Schwelle → kein CoT-Signal.

    Realistisches Beispiel: 'v = s/t = 120/1.5 = 80 km/h' (28 Zeichen)
    """
    short = "v = s/t = 120/1.5 = 80 km/h"
    assert len(short) < _INLINE_COT_LENGTH_THRESHOLD
    assert _has_inline_cot(short) is False


def test_inline_cot_long_prose_without_ops_returns_false():
    """Langer Prosa-Text ohne Berechnungs-Operatoren → kein CoT-Signal.

    Reduziert False-Positives bei Erklaerungen / Code-Outputs.
    """
    prose = (
        "The train travels at constant speed. We assume no stops along the way. "
        "The distance is one hundred and twenty kilometres and the time is one and "
        "a half hours. A simple division yields the average velocity."
    )
    assert len(prose) > _INLINE_COT_LENGTH_THRESHOLD
    op_count = sum(prose.count(op) for op in _INLINE_COT_OPS)
    assert op_count < 2, f"Test-Vorbedingung: <2 Ops, aber {op_count} Ops gefunden"
    assert _has_inline_cot(prose) is False


# Hinweis: Ein "Code ohne genuegend Ops"-Test wurde verworfen, weil selbst
# minimales Python (z. B. 'result = fn(120, 1.5)') mind. 2 Ops enthaelt
# (1x ' = ' + 1x ' / ' im Funktionsbody). Die Heuristik triggert dann
# zu Recht. Prosa ohne Ops wird bereits durch
# test_inline_cot_long_prose_without_ops_returns_false abgedeckt.



def test_inline_cot_gemma_4_real_world_example_returns_true():
    """User-Log-Beweis: Gemma 4 26B-A4B mit --reasoning off produziert inline CoT.

    Dies ist der tatsaechlich beobachtete Output aus dem Spark-Benchmark-Run
    vom 9.6.2026 (Original ~1142 Zeichen, hier gekuerzt auf das Wesentliche).
    """
    gemma_response = (
        "OK, das ist eine einfache Geschwindigkeitsberechnung. "
        "v = s/t = 120/1.5 = 80. "
        "Die Formel fuer die Durchschnittsgeschwindigkeit lautet "
        "Geschwindigkeit = Strecke / Zeit. "
        "Wir setzen die gegebenen Werte ein: s = 120 km, t = 1.5 h. "
        "Die Berechnung ergibt 120 / 1.5 = 80 km/h. "
        "Die Antwort ist also 80 km/h. "
        "Optional koennen wir das in m/s umrechnen: 80 * 1000 / 3600 = 22.22 m/s. "
        "Aber die Frage war in km/h, also ist 80 km/h die finale Antwort."
    )
    assert len(gemma_response) > _INLINE_COT_LENGTH_THRESHOLD
    op_count = sum(gemma_response.count(op) for op in _INLINE_COT_OPS)
    assert op_count >= 2, f"Test-Vorbedingung: >=2 Ops, aber {op_count} gefunden"
    assert _has_inline_cot(gemma_response) is True


def test_inline_cot_minimum_length_boundary():
    """Exakt an der Schwellwert-Grenze: Schwelle ist '>' (strikt groesser)."""
    # 200 Zeichen ohne Berechnungen → False (exakt an Grenze, kein '>')
    text_no_ops = "a" * _INLINE_COT_LENGTH_THRESHOLD
    assert len(text_no_ops) == _INLINE_COT_LENGTH_THRESHOLD
    assert _has_inline_cot(text_no_ops) is False

    # 201 Zeichen ohne Berechnungen → immer noch False (kein Op)
    text_no_ops_over = "a" * (_INLINE_COT_LENGTH_THRESHOLD + 1)
    assert _has_inline_cot(text_no_ops_over) is False

    # 201 Zeichen mit 2x ' = ' → True (exakt 1 ueber Schwelle + 2 Ops)
    # Laengenrechnung: 99 + len(' = ') + 49 + len(' = ') + 45 = 99 + 3 + 49 + 3 + 45 = 199 → zu kurz
    # Korrekt: 99 + 3 + 50 + 3 + 46 = 201
    text_with_ops = ("a" * 99) + " = " + ("a" * 50) + " = " + ("a" * 46)
    assert len(text_with_ops) == _INLINE_COT_LENGTH_THRESHOLD + 1, (
        f"Test-Vorbedingung: Laenge 201, aber {len(text_with_ops)}"
    )
    assert text_with_ops.count(" = ") >= 2
    assert _has_inline_cot(text_with_ops) is True


# ---------------------------------------------------------------------------
# probe_thinking_model() — Integration Signal C mit gemocktem LLMClient
# ---------------------------------------------------------------------------

def _mock_llm_client(raw_response: str, reasoning_tokens: int = 0) -> MagicMock:
    """Baut einen Mock-LLMClient, der `raw_response` und `reasoning_tokens` liefert."""
    client = MagicMock()
    client.query.return_value = raw_response
    client.last_response_metadata = {"reasoning_tokens": reasoning_tokens}
    return client


def test_probe_signal_c_inline_cot_detected_with_medium_confidence():
    """probe_thinking_model() muss Signal C ausloesen, wenn _has_inline_cot() triggert."""
    gemma_response = (
        "OK, das ist eine einfache Geschwindigkeitsberechnung. "
        "v = s/t = 120/1.5 = 80. "
        "Die Formel fuer die Durchschnittsgeschwindigkeit lautet "
        "Geschwindigkeit = Strecke / Zeit. "
        "Wir setzen die gegebenen Werte ein: s = 120 km, t = 1.5 h. "
        "Die Berechnung ergibt 120 / 1.5 = 80 km/h. "
        "Die Antwort ist also 80 km/h."
    )
    client = _mock_llm_client(gemma_response, reasoning_tokens=0)

    # LLMClient wird in probe_thinking_model() per `from utils.llm_client import LLMClient`
    # lokal importiert — der Patch muss daher auf dem Quell-Modul ansetzen, nicht
    # auf utils.model_utils (das Attribut existiert dort nicht).
    with patch("utils.llm_client.LLMClient", return_value=client):
        result = probe_thinking_model("gemma-4-26b-a4b-q8", "llamacpp_spark", config={})

    assert isinstance(result, ThinkingProbeResult)
    assert result.detected is True
    assert result.confidence == "medium"
    assert "Inline CoT" in result.evidence
    assert f">{_INLINE_COT_LENGTH_THRESHOLD}" in result.evidence


def test_probe_signal_a_takes_precedence_over_signal_c():
    """<think>-Tag (Signal A) schlaegt Signal C — hoechste Konfidenz gewinnt."""
    response_with_tag = (
        "<think>\n"
        "OK, das ist eine einfache Geschwindigkeitsberechnung. "
        "v = s/t = 120/1.5 = 80. Die Antwort ist 80 km/h.\n"
        "</think>\n"
        "80 km/h"
    )
    client = _mock_llm_client(response_with_tag, reasoning_tokens=0)

    with patch("utils.llm_client.LLMClient", return_value=client):
        result = probe_thinking_model("test-model", "llamacpp_spark", config={})

    assert result.detected is True
    assert result.confidence == "high"
    assert "Think-tag" in result.evidence


def test_probe_signal_b_takes_precedence_over_signal_c():
    """reasoning_tokens > 0 (Signal B) schlaegt Signal C — frueher im Code-Pfad."""
    short_response = "v = s/t = 120/1.5 = 80 km/h"  # unter Schwellwert, kein Signal C
    client = _mock_llm_client(short_response, reasoning_tokens=42)

    with patch("utils.llm_client.LLMClient", return_value=client):
        result = probe_thinking_model("test-model", "llamacpp_spark", config={})

    assert result.detected is True
    assert result.confidence == "medium"
    assert "reasoning_tokens=42" in result.evidence


def test_probe_signal_b_cold_start_empty_output_not_detected():
    """Cold-Start-Guard: reasoning_tokens > 0 + leerer Output → detected=False.

    Hintergrund: llama.cpp-Modelle (z. B. Gemma 4 26B-A4B-QAT) liefern
    bei den ersten Anfragen reasoning_tokens=512, aber 0 chars Output.
    Das ist ein Kontext-Aufbau-Artefakt, kein echter Thinking-Nachweis.
    Ohne den Guard wuerde Signal B faelschlicherweise detected=True setzen.
    """
    client = _mock_llm_client("", reasoning_tokens=512)

    with patch("utils.llm_client.LLMClient", return_value=client):
        result = probe_thinking_model("gemma-4-26b-a4b-qat", "llamacpp_spark", config={})

    assert result.detected is False
    assert result.confidence == "low"
    assert "reasoning_tokens=512" in result.evidence
    assert "Cold-Start-Verdacht" in result.evidence


def test_probe_signal_b_cold_start_whitespace_only_not_detected():
    """Cold-Start-Guard greift auch bei Whitespace-only-Output (strip() == '')."""
    client = _mock_llm_client("   \n   ", reasoning_tokens=128)

    with patch("utils.llm_client.LLMClient", return_value=client):
        result = probe_thinking_model("test-model", "llamacpp_spark", config={})

    assert result.detected is False
    assert result.confidence == "low"
    assert "Cold-Start-Verdacht" in result.evidence


def test_probe_no_signals_returns_low_confidence():
    """Weder Tags noch reasoning_tokens noch inline CoT → low confidence."""
    short_direct = "80 km/h"
    client = _mock_llm_client(short_direct, reasoning_tokens=0)

    with patch("utils.llm_client.LLMClient", return_value=client):
        result = probe_thinking_model("test-model", "llamacpp_spark", config={})

    assert result.detected is False
    assert result.confidence == "low"
    assert "No CoT signals found" in result.evidence


def test_probe_long_prose_without_ops_returns_low_confidence():
    """Langer Prosa-Text ohne Berechnungen → kein Signal C → low confidence."""
    prose = (
        "This is a thoughtful and elaborate answer that contains many words "
        "and sentences but does not include any actual mathematical operations "
        "or formulas that would indicate chain-of-thought reasoning in the "
        "response. It is just explanatory text without computational content."
    ) * 2  # um die Schwellwert-Laenge sicher zu ueberschreiten
    client = _mock_llm_client(prose, reasoning_tokens=0)

    with patch("utils.llm_client.LLMClient", return_value=client):
        result = probe_thinking_model("test-model", "llamacpp_spark", config={})

    assert result.detected is False
    assert result.confidence == "low"


def test_probe_runtime_error_on_api_failure():
    """API-Fehler muss als RuntimeError propagiert werden (Card-First-Hook)."""
    client = MagicMock()
    client.query.side_effect = ConnectionError("server not reachable")

    with patch("utils.llm_client.LLMClient", return_value=client):
        try:
            probe_thinking_model("test-model", "llamacpp_spark", config={})
        except RuntimeError as exc:
            assert "ThinkingProbe" in str(exc)
            assert "test-model" in str(exc)
        else:
            raise AssertionError("RuntimeError expected, but no exception raised")
