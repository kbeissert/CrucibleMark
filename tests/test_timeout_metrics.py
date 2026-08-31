"""Tests für die Timeout-/Fehlerraten-Metrik des Audit-Reports.

Regression 2026-09-01 (User-Entscheidung): Die „Timeout-Rate" zählt
ausschließlich echte Fehler/Abbrüche (``status == "error"``). Die reine
Antwortdauer fließt NICHT ein — sie ist über P95-Antwortzeit, Tokens/s und
den Speed-Badge abgebildet. Vorher zählte ``execution_time >
TIMEOUT_DEFAULT`` (120 s) als Timeout und stufte erfolgreiche lokale Läufe
(122 s, 160 s) fälschlich als „❌ Nicht einsetzbar" ein.
"""
import pytest

from utils.benchmark_utils import calculate_timeout_metrics
from scripts.core.unified_runner import UnifiedBenchmarkRunner


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

def _make_runner() -> UnifiedBenchmarkRunner:
    """Lightweight Runner ohne Konstruktor-Nebenwirkungen (nur Metrik-Test)."""
    runner = UnifiedBenchmarkRunner.__new__(UnifiedBenchmarkRunner)
    runner.audit_mode = True
    return runner


@pytest.fixture
def captured(monkeypatch):
    """Fängt append_global_run_metrics-Aufrufe ab (kein Datei-IO)."""
    calls = []
    import scripts.core.unified_runner as ur
    monkeypatch.setattr(
        ur, "append_global_run_metrics",
        lambda model, asset_ids, times, count, total, name="Unknown": calls.append(
            {"model": model, "asset_ids": list(asset_ids), "times": list(times),
             "count": count, "total": total, "name": name}
        ),
    )
    return calls


def _result(asset_id: str, status: str = "success", t_exe: float = 10.0) -> dict:
    return {"asset_id": asset_id, "status": status, "execution_time": t_exe}


# ---------------------------------------------------------------------------
# Zähllogik in _record_global_metrics
# ---------------------------------------------------------------------------

class TestRecordGlobalMetricsCounting:
    """Kern-Regression: Dauer erzeugt keinen Timeout, Fehler schon."""

    def test_slow_success_is_not_counted(self, captured):
        """160-s-Erfolg (früher fälschlich Timeout) → count 0."""
        results = [_result("a1", "success", 160.7), _result("a2", "success", 122.4)]
        _make_runner()._record_global_metrics("m", results, {"name": "X"})
        assert captured[0]["count"] == 0
        assert captured[0]["total"] == 2

    def test_error_status_is_counted(self, captured):
        results = [_result("a1", "success", 10.0), _result("a2", "error", 5.0)]
        _make_runner()._record_global_metrics("m", results, {"name": "X"})
        assert captured[0]["count"] == 1

    def test_system_rows_excluded(self, captured):
        results = [
            _result("a1", "success", 10.0),
            {"type": "system", "asset_id": "sys", "status": "error", "execution_time": 1.0},
        ]
        _make_runner()._record_global_metrics("m", results, {"name": "X"})
        assert captured[0]["asset_ids"] == ["a1"]
        assert captured[0]["total"] == 1
        assert captured[0]["count"] == 0

    def test_audit_mode_disabled_skips(self, captured):
        runner = _make_runner()
        runner.audit_mode = False
        runner._record_global_metrics("m", [_result("a1")], {"name": "X"})
        assert captured == []


# ---------------------------------------------------------------------------
# Kategorisierung in calculate_timeout_metrics
# ---------------------------------------------------------------------------

class TestTimeoutCategories:
    def test_zero_is_stabil(self):
        m = calculate_timeout_metrics([10.0, 20.0], 0, 5)
        assert m["timeout_count"] == 0 and "Stabil" in m["ratio_category"]

    def test_low_rate_is_sporadisch(self):
        m = calculate_timeout_metrics([10.0] * 20, 1, 20)
        assert "Sporadisch" in m["ratio_category"]

    def test_mid_rate_is_unzuverlaessig(self):
        m = calculate_timeout_metrics([10.0] * 10, 2, 10)
        assert "Unzuverlässig" in m["ratio_category"]

    def test_high_rate_is_nicht_einsetzbar(self):
        m = calculate_timeout_metrics([10.0] * 5, 3, 5)
        assert "Nicht einsetzbar" in m["ratio_category"]

    def test_p95_single_value(self):
        m = calculate_timeout_metrics([42.0], 0, 1)
        assert m["p95"] == 42.0

    def test_p95_empty_list(self):
        m = calculate_timeout_metrics([], 0, 0)
        assert m["p95"] == 0.0
