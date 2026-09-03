"""Tests für den PC-Token-Probe Card-First-Hook (``pc_probe_hook``).

Entscheidung 2026-09-03: Hat die Model Card keinen PC-Token-Probe-Eintrag
(``pc_profile`` fehlt/null), muss die Probe VOR dem PC-Benchmark laufen —
analog zur Thinking-Probe vor dem Standard-Benchmark
(``unified_runner._ensure_model_card``). Die Probe läuft einmalig;
nachfolgende Läufe überspringen sie (Card-First). Bei ``PcProbeError``
(Fast-Fail-Guard) läuft der Benchmark weiter ohne Card-Write.
"""
import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark_modules.political_compass.core import pc_probe_hook  # noqa: E402
from benchmark_modules.political_compass.core.pc_probe_hook import (  # noqa: E402
    ensure_pc_token_probe,
    read_pc_probe_state,
    run_pc_token_probe,
    write_pc_calibration_to_card,
)
from benchmark_modules.political_compass.core.token_probe import (  # noqa: E402
    PcProbeError,
    PcTokenCalibration,
)
from utils.base_runner import BaseBenchmarkRunner  # noqa: E402


# --- Test-Helpers ----------------------------------------------------------


def _calibration(profile: str = "thinking", budget: int | None = 1200) -> PcTokenCalibration:
    """Deterministisches Probe-Ergebnis für die Tests."""
    return PcTokenCalibration(
        budget=budget,
        classification="self_limiting",
        tested="2026-09-03T00:00:00+00:00",
        converged_stage=600,
        notes="test",
        profile=profile,
        block_report=[{"block": "7.1", "status": "converged", "converged_stage": 600}],
    )


def _write_card(card_dir: Path, model_id: str, payload: dict) -> Path:
    """Schreibt eine Test-Card in ``card_dir`` und gibt den Pfad zurück."""
    card_path = card_dir / f"{model_id}.json"
    card_path.write_text(
        json.dumps({"model_id": model_id, **payload}),
        encoding="utf-8",
    )
    return card_path


# --- read_pc_probe_state Tests ---------------------------------------------


class TestReadPcProbeState:
    """read_pc_probe_state triggert Probe bei null/missing/defekter Card."""

    def test_missing_card_triggers_probe(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            pc_probe_hook, "_find_card", lambda model_id: tmp_path / f"{model_id}.json",
        )
        needs_probe, card = read_pc_probe_state("test-model")
        assert needs_probe is True
        assert card is None

    def test_null_pc_profile_triggers_probe(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Draft-Card mit ``pc_profile: null`` MUSS Probe triggern.

        Semantik identisch zur Thinking-Probe (Pitfall 2026-06-10):
        explizit null = "Probe noch nicht gelaufen".
        """
        card_path = _write_card(tmp_path, "test-model", {"pc_profile": None, "card_status": "draft"})
        monkeypatch.setattr(pc_probe_hook, "_find_card", lambda model_id: card_path)
        needs_probe, card = read_pc_probe_state("test-model")
        assert needs_probe is True
        assert card is not None and card["model_id"] == "test-model"

    def test_missing_pc_profile_key_triggers_probe(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        card_path = _write_card(tmp_path, "test-model", {"card_status": "draft"})
        data = json.loads(card_path.read_text(encoding="utf-8"))
        assert "pc_profile" not in data
        monkeypatch.setattr(pc_probe_hook, "_find_card", lambda model_id: card_path)
        needs_probe, _ = read_pc_probe_state("test-model")
        assert needs_probe is True

    def test_set_pc_profile_skips_probe(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Card mit gesetztem ``pc_profile`` → KEIN Re-Probe (Endlos-Probe-Schutz)."""
        card_path = _write_card(tmp_path, "test-model", {"pc_profile": "hybrid_dual"})
        monkeypatch.setattr(pc_probe_hook, "_find_card", lambda model_id: card_path)
        needs_probe, card = read_pc_probe_state("test-model")
        assert needs_probe is False
        assert card["pc_profile"] == "hybrid_dual"

    def test_corrupt_card_triggers_probe(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Defekte Card crascht nicht — Probe wird sicher nachgeholt."""
        corrupt = tmp_path / "corrupt.json"
        corrupt.write_text("{ not valid json", encoding="utf-8")
        monkeypatch.setattr(pc_probe_hook, "_find_card", lambda model_id: corrupt)
        needs_probe, card = read_pc_probe_state("corrupt-model")
        assert needs_probe is True
        assert card is None


# --- ensure_pc_token_probe Tests -------------------------------------------


class TestEnsurePcTokenProbe:
    """ensure_pc_token_probe: Skip bei Card-Eintrag, sonst Probe + Card-Write."""

    def test_skip_when_card_has_pc_profile(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        card_path = _write_card(tmp_path, "test-model", {"pc_profile": "hybrid_dual"})
        monkeypatch.setattr(pc_probe_hook, "_find_card", lambda model_id: card_path)
        calls: list[Any] = []
        monkeypatch.setattr(
            pc_probe_hook, "run_pc_token_probe",
            lambda *args: calls.append(args) or _calibration(),
        )
        result = ensure_pc_token_probe("test-model", "anthropic", client=object())
        assert result is None
        assert not calls, "Probe darf bei bestehendem pc_profile NICHT laufen"

    def test_probe_and_card_write_when_no_card(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            pc_probe_hook, "_find_card", lambda model_id: tmp_path / f"{model_id}.json",
        )
        monkeypatch.setattr(
            pc_probe_hook, "run_pc_token_probe",
            lambda model, provider, client: _calibration(),
        )
        written: list[tuple[str, PcTokenCalibration, str | None]] = []

        def fake_write(model: str, calibration: PcTokenCalibration, provider: str | None = None) -> Path:
            written.append((model, calibration, provider))
            return tmp_path / f"{model}.json"

        monkeypatch.setattr(pc_probe_hook, "write_pc_calibration_to_card", fake_write)

        result = ensure_pc_token_probe("test-model", "anthropic", client=object())
        assert result is not None and result.profile == "thinking"
        assert len(written) == 1
        assert written[0][0] == "test-model"
        assert written[0][2] == "anthropic"

    def test_probe_error_propagates_without_card_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Fast-Fail-Guard: PcProbeError propagiert, bewusst KEIN Card-Write
        (nächster Lauf wiederholt die Probe)."""
        monkeypatch.setattr(
            pc_probe_hook, "_find_card", lambda model_id: tmp_path / f"{model_id}.json",
        )

        def boom(model: str, provider: str, client: Any) -> PcTokenCalibration:
            raise PcProbeError("Fast-Fail: 5/5 Queries fehlgeschlagen")

        monkeypatch.setattr(pc_probe_hook, "run_pc_token_probe", boom)
        written: list[Any] = []
        monkeypatch.setattr(
            pc_probe_hook, "write_pc_calibration_to_card",
            lambda *args, **kwargs: written.append(1),
        )

        with pytest.raises(PcProbeError):
            ensure_pc_token_probe("test-model", "anthropic", client=object())
        assert not written


# --- run_pc_token_probe Tests ----------------------------------------------


class TestRunPcTokenProbe:
    """run_pc_token_probe verdrahtet Test, Screening und dual_profile."""

    def test_passes_supports_instruct_and_screening(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(pc_probe_hook, "read_dual_profile", lambda model_id: True)
        captured: dict[str, Any] = {}

        def fake_probe(
            model: str, provider: str, client: Any,
            screening: list[dict[str, Any]], test: Any, supports_instruct_mode: bool,
        ) -> PcTokenCalibration:
            captured["supports_instruct"] = supports_instruct_mode
            captured["screening_count"] = len(screening)
            return _calibration()

        monkeypatch.setattr(pc_probe_hook, "probe_pc_profile", fake_probe)

        result = run_pc_token_probe("test-model", "anthropic", client=object())
        assert result.profile == "thinking"
        assert captured["supports_instruct"] is True
        # Stratifiziertes Sampling: genau 1 Frage pro Block (9 Blöcke)
        assert captured["screening_count"] == 9


# --- write_pc_calibration_to_card Tests ------------------------------------


class TestWritePcCalibrationToCard:
    """write_pc_calibration_to_card persistiert beide Card-Felder."""

    def test_writes_calibration_and_profile(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import utils.card_utils as card_utils

        target = tmp_path / "test-model.json"
        target.write_text(json.dumps({"model_id": "test-model"}), encoding="utf-8")

        def fake_ensure_card(model_id: str, *, card_path: Path | None = None, provider: str | None = None) -> Path:
            assert card_path == target
            return card_path

        monkeypatch.setattr(card_utils, "ensure_card", fake_ensure_card)
        monkeypatch.setattr(pc_probe_hook, "_find_card", lambda model_id: target)

        card_path = write_pc_calibration_to_card(
            "test-model", _calibration(profile="hybrid_dual"), provider="anthropic",
        )
        assert card_path == target
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["pc_profile"] == "hybrid_dual"
        assert data["pc_token_calibration"]["profile"] == "hybrid_dual"
        assert data["pc_token_calibration"]["budget"] == 1200
        assert data["pc_token_calibration"]["classification"] == "self_limiting"


# --- Runner-Integration ----------------------------------------------------


class TestRunnerHook:
    """BaseBenchmarkRunner._ensure_pc_token_probe: Durchreichung + Fehler-Toleranz."""

    def _make_runner(self) -> BaseBenchmarkRunner:
        runner = BaseBenchmarkRunner.__new__(BaseBenchmarkRunner)
        runner.client = object()
        return runner

    def test_calls_through_with_client(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        runner = self._make_runner()
        calls: list[Any] = []

        def fake_ensure(model: str, provider: str, client: Any) -> None:
            calls.append((model, provider, client))

        monkeypatch.setattr(pc_probe_hook, "ensure_pc_token_probe", fake_ensure)
        runner._ensure_pc_token_probe("test-model", "anthropic")
        assert calls == [("test-model", "anthropic", runner.client)]

    def test_error_does_not_abort_benchmark(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Probe-Fehler (Fast-Fail-Guard) dürfen den Benchmark NICHT abbrechen
        (analog Thinking-Probe-Skip bei 429/403)."""
        runner = self._make_runner()

        def boom(model: str, provider: str, client: Any) -> None:
            raise PcProbeError("Fast-Fail: 5/5 Queries fehlgeschlagen")

        monkeypatch.setattr(pc_probe_hook, "ensure_pc_token_probe", boom)
        runner._ensure_pc_token_probe("test-model", "anthropic")  # darf nicht werfen


def test_execute_batch_module_contains_hook() -> None:
    """Source-Level-Check: execute_batch_module MUSS _ensure_pc_token_probe
    aufrufen (nach den Skip-Checks, vor dem Test-Load) — sonst läuft die
    Probe nie für PC-Runs. (Stil: test_repair_pc_leaderboard.py)"""
    source = (
        Path(__file__).resolve().parents[1] / "utils" / "base_runner.py"
    ).read_text(encoding="utf-8")
    assert "self._ensure_pc_token_probe(model, provider)" in source, (
        "PC-Token-Probe-Hook fehlt in execute_batch_module — "
        "Probe läuft nie vor dem PC-Benchmark!"
    )
    assert source.index("self._check_pc_leaderboard_skip") < source.index(
        "self._ensure_pc_token_probe",
    ), "Hook muss NACH den Skip-Checks laufen (keine Probe für gescort-Modelle)"
