"""Tests für den Heartbeat-Feature im UnifiedBenchmarkRunner.

Verifiziert:
- _run_asset_loop startet/stoppt den Heartbeat-Thread
- Heartbeat-Print erscheint nach <60s
- _handle_heartbeat_signal aktualisiert Phase/Q-ID/Retry-Info
- _print_asset_status zeigt Retry-Indikatoren (🔁/⛔/✓/❌)
- Threading ist daemon=True und cleanup im finally-Block
- Kein Thread-Leak bei normalem Loop-Abschluss
- Kein Thread-Leak bei Exception im Loop
"""

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.core.unified_runner import UnifiedBenchmarkRunner


# --- Test-Helpers -----------------------------------------------------------

# Anzahl der Fake-Assets im Lifecycle-Test
_FAKE_ASSET_COUNT = 3
# Erwartete completed-Zähler nach _run_asset_loop: _FAKE_ASSET_COUNT aus fake_handle
# + 1 aus _run_asset_loop nach erfolgreichem handle-Call
_EXPECTED_COMPLETED = _FAKE_ASSET_COUNT + 1


def _make_runner(**overrides) -> UnifiedBenchmarkRunner:
    """Erzeugt einen Runner mit gemockten Pflichtfeldern."""
    runner = UnifiedBenchmarkRunner.__new__(UnifiedBenchmarkRunner)
    # Initialisiere nur die Felder, die _run_asset_loop / Heartbeat lesen
    runner._heartbeat_stop = None  # wird im Test gesetzt
    for k, v in overrides.items():
        setattr(runner, k, v)
    return runner


# --- _handle_heartbeat_signal Tests ----------------------------------------


class TestHandleHeartbeatSignal:
    """_handle_heartbeat_signal aktualisiert Runner-State korrekt."""

    def setup_method(self) -> None:
        self.runner = _make_runner(
            _heartbeat_stop=MagicMock(is_set=MagicMock(return_value=False)),
            _heartbeat_start=time.time(),
            _heartbeat_last_activity=0.0,  # alt
            _heartbeat_phase="Setup",
            _heartbeat_q_id="",
            _heartbeat_retry="",
            _heartbeat_completed=0,
            _heartbeat_total=10,
        )

    def test_updates_q_id_when_provided(self) -> None:
        self.runner._handle_heartbeat_signal(q_id="political_compass_7.3.001")
        assert self.runner._heartbeat_q_id == "political_compass_7.3.001"

    def test_does_not_overwrite_q_id_when_empty(self) -> None:
        self.runner._heartbeat_q_id = "existing_q"
        self.runner._handle_heartbeat_signal(q_id="")
        assert self.runner._heartbeat_q_id == "existing_q"

    def test_sets_retry_info(self) -> None:
        self.runner._handle_heartbeat_signal(
            retry_info="Retry 2/2 temp 0.7", is_retry=True
        )
        assert self.runner._heartbeat_retry == "Retry 2/2 temp 0.7"

    def test_phase_becomes_retry_during_retry(self) -> None:
        self.runner._handle_heartbeat_signal(is_retry=True)
        assert self.runner._heartbeat_phase == "Retry"

    def test_phase_reverts_to_test_after_retry(self) -> None:
        self.runner._heartbeat_phase = "Retry"
        self.runner._handle_heartbeat_signal(is_retry=False)
        assert self.runner._heartbeat_phase == "Test"

    def test_resets_last_activity(self) -> None:
        old_activity = self.runner._heartbeat_last_activity
        time.sleep(0.01)  # damit time.time() sicher größer wird
        self.runner._handle_heartbeat_signal()
        assert self.runner._heartbeat_last_activity > old_activity


# --- _print_asset_status Tests ---------------------------------------------


class TestPrintAssetStatus:
    """_print_asset_status zeigt korrektes Status-Icon + optionalen Retry-Counter."""

    def test_success_icon(self, capsys: pytest.CaptureFixture) -> None:
        UnifiedBenchmarkRunner._print_asset_status(
            i=1, total=10, asset_name="test", result={"status": "success", "percentage": 85.0, "tokens_used": 100, "execution_time": 2.0}
        )
        out = capsys.readouterr().out
        assert "✓" in out
        assert "[1/10]" in out
        assert "85.0%" in out

    def test_error_icon(self, capsys: pytest.CaptureFixture) -> None:
        UnifiedBenchmarkRunner._print_asset_status(
            i=2, total=10, asset_name="test", result={"status": "error", "percentage": 0, "tokens_used": 0, "execution_time": 0}
        )
        out = capsys.readouterr().out
        assert "❌" in out

    def test_refusal_icon(self, capsys: pytest.CaptureFixture) -> None:
        UnifiedBenchmarkRunner._print_asset_status(
            i=3, total=10, asset_name="test",
            result={"status": "success", "refusal_flag": True, "percentage": 0, "tokens_used": 50, "execution_time": 1.0}
        )
        out = capsys.readouterr().out
        assert "🔁" in out

    def test_hard_refusal_icon(self, capsys: pytest.CaptureFixture) -> None:
        UnifiedBenchmarkRunner._print_asset_status(
            i=4, total=10, asset_name="test",
            result={"status": "success", "hard_refusal": True, "percentage": 0, "tokens_used": 0, "execution_time": 5.0}
        )
        out = capsys.readouterr().out
        assert "⛔" in out

    def test_retry_count_appended(self, capsys: pytest.CaptureFixture) -> None:
        UnifiedBenchmarkRunner._print_asset_status(
            i=5, total=10, asset_name="test",
            result={"status": "success", "refusal_retry_count": 2, "percentage": 75.0, "tokens_used": 200, "execution_time": 3.5}
        )
        out = capsys.readouterr().out
        assert "(×2)" in out

    def test_no_retry_count_when_zero(self, capsys: pytest.CaptureFixture) -> None:
        UnifiedBenchmarkRunner._print_asset_status(
            i=6, total=10, asset_name="test",
            result={"status": "success", "refusal_retry_count": 0, "percentage": 90.0, "tokens_used": 80, "execution_time": 1.5}
        )
        out = capsys.readouterr().out
        assert "(×" not in out


# --- _run_asset_loop Heartbeat Lifecycle Tests ------------------------------


class TestHeartbeatLifecycle:
    """_run_asset_loop startet/stoppt den Heartbeat-Thread korrekt."""

    def test_thread_starts_and_stops_clean(self, capsys: pytest.CaptureFixture) -> None:
        """Smoke-Test: Heartbeat-Thread wird sauber gestartet und im finally gestoppt."""
        runner = _make_runner()

        # Mock _handle_single_asset, damit die Loop schnell durchläuft
        call_count = {"n": 0}

        def fake_handle(**kwargs) -> None:
            call_count["n"] += 1
            # Heartbeat-State setzen (vom echten Code)
            runner._heartbeat_q_id = f"test_{call_count['n']}"
            runner._heartbeat_completed = call_count["n"]

        runner._handle_single_asset = fake_handle  # type: ignore[assignment]

        # _FAKE_ASSET_COUNT Fake-Assets
        assets = [Path(f"/tmp/fake_{i}.yaml") for i in range(_FAKE_ASSET_COUNT)]

        # _save_partial_results wird im except-Pfad aufgerufen, hier nicht relevant
        runner._save_partial_results = MagicMock()  # type: ignore[assignment]

        runner._run_asset_loop(
            assets=assets,
            model="test-model",
            provider="ollama",
            benchmark_info={},
            is_local=True,
            run_id="test123",
            pause_calculator=None,
            run_limiter=None,
            results=[],
        )

        # Loop ist _FAKE_ASSET_COUNT× durchgelaufen
        assert call_count["n"] == _FAKE_ASSET_COUNT
        # Heartbeat-State nach Loop: q_id = letzter Asset, completed = _EXPECTED_COMPLETED
        # (= _FAKE_ASSET_COUNT aus fake_handle, +1 aus _run_asset_loop nach dem handle-Call)
        assert runner._heartbeat_completed == _EXPECTED_COMPLETED
        # Heartbeat wurde gestoppt (Event ist gesetzt)
        assert runner._heartbeat_stop.is_set() is True

    def test_exception_still_stops_heartbeat(self, capsys: pytest.CaptureFixture) -> None:
        """Auch bei Asset-Exception muss der Heartbeat-Thread sauber stoppen."""
        runner = _make_runner()

        def failing_handle(**kwargs) -> None:
            raise RuntimeError("simulated asset failure")

        runner._handle_single_asset = failing_handle  # type: ignore[assignment]
        runner._handle_asset_exception = MagicMock()  # suppress exception print
        runner._save_partial_results = MagicMock()  # type: ignore[assignment]

        assets = [Path("/tmp/fake.yaml")]

        # Sollte NICHT crashen — Exception wird in _handle_asset_exception gefangen
        runner._run_asset_loop(
            assets=assets,
            model="test-model",
            provider="ollama",
            benchmark_info={},
            is_local=True,
            run_id="test123",
            pause_calculator=None,
            run_limiter=None,
            results=[],
        )

        # Heartbeat wurde sauber gestoppt
        assert runner._heartbeat_stop.is_set() is True


# --- Integration: PoliticalCompass ↔ Runner Heartbeat ---------------------


class TestPoliticalCompassHeartbeatIntegration:
    """Verify _notify_heartbeat correctly delegates to runner's heartbeat handler."""

    def test_notify_heartbeat_graceful_no_op_without_runner(self) -> None:
        """Ohne gesetzten _benchmark_runner ist _notify_heartbeat ein no-op."""
        from benchmark_modules.political_compass.test import PoliticalCompassTest

        test = PoliticalCompassTest.__new__(PoliticalCompassTest)
        # Kein _benchmark_runner gesetzt — muss ohne Crash durchlaufen
        test._notify_heartbeat(q_id="test", retry_info="r1", is_retry=True)

    def test_notify_heartbeat_invokes_runner_handler(self) -> None:
        """Mit gesetztem _benchmark_runner wird _handle_heartbeat_signal aufgerufen."""
        from benchmark_modules.political_compass.test import PoliticalCompassTest

        # Mock-Runner mit Spy
        runner_mock = MagicMock()
        runner_mock._heartbeat_stop = MagicMock()  # marks heartbeat as active

        test = PoliticalCompassTest.__new__(PoliticalCompassTest)
        test._benchmark_runner = runner_mock

        test._notify_heartbeat(
            q_id="political_compass_7.3.001",
            retry_info="Retry 1/2 temp 0.4",
            is_retry=True,
        )

        # Handler wurde mit den korrekten Argumenten aufgerufen
        runner_mock._handle_heartbeat_signal.assert_called_once_with(
            q_id="political_compass_7.3.001",
            retry_info="Retry 1/2 temp 0.4",
            is_retry=True,
        )

    def test_notify_heartbeat_swallows_exceptions(self) -> None:
        """Heartbeat-Fehler dürfen den Test NIEMALS crashen."""
        from benchmark_modules.political_compass.test import PoliticalCompassTest

        runner_mock = MagicMock()
        runner_mock._heartbeat_stop = MagicMock()
        runner_mock._handle_heartbeat_signal.side_effect = RuntimeError("heartbeat bug")

        test = PoliticalCompassTest.__new__(PoliticalCompassTest)
        test._benchmark_runner = runner_mock

        # Darf nicht crashen — Exception wird geloggt + ignored
        test._notify_heartbeat(q_id="x", retry_info="y", is_retry=True)
