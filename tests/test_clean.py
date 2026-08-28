"""Phase 28: Tests fuer clean.py (Dispatcher, ohne Subprozess)."""
import contextlib
import sys
from unittest.mock import patch


from scripts.maintenance import clean as clean_module


# ---------------------------------------------------------------------------
# _run_clean_results: Direktaufruf statt Subprozess
# ---------------------------------------------------------------------------

def test_run_clean_results_does_not_call_subprocess(monkeypatch, capsys):
    """Phase 28: _run_clean_results ruft subprocess NICHT auf, sondern main_with_args."""
    called_with_args = []

    def fake_main_with_args(args):
        called_with_args.append(args)

    monkeypatch.setattr(
        "scripts.maintenance.clean_results.main_with_args",
        fake_main_with_args,
    )

    clean_module._run_clean_results(model="test-model", dry_run=True)

    assert len(called_with_args) == 1
    ns = called_with_args[0]
    assert ns.model == "test-model"
    assert ns.dry_run is True
    assert ns.prune_orphans is False
    assert ns.force is False


def test_run_clean_results_passes_dry_run_false(monkeypatch):
    """dry_run=False wird korrekt durchgereicht."""
    captured = []

    def fake_main_with_args(args):
        captured.append(args)

    monkeypatch.setattr(
        "scripts.maintenance.clean_results.main_with_args",
        fake_main_with_args,
    )
    clean_module._run_clean_results(model="x", module="y", dry_run=False)

    assert captured[0].module == "y"
    assert captured[0].dry_run is False


def test_clean_dispatcher_invokes_run_clean_results(monkeypatch):
    """main() mit --model x ruft _run_clean_results auf (kein Subprozess)."""
    called = []

    def fake_run(model=None, module=None, dry_run=False):
        called.append((model, module, dry_run))

    monkeypatch.setattr(clean_module, "_run_clean_results", fake_run)
    # Leaderboard-Update-Side-Effect neutralisieren
    monkeypatch.setattr(
        "scripts.maintenance.clean_results.main_with_args",
        lambda args: None,
    )

    test_argv = ["clean.py", "--model", "qwen2.5:14b"]
    # argparse kann sys.exit rufen, ist hier egal
    with (
        patch.object(sys, "argv", test_argv),
        contextlib.suppress(SystemExit),
    ):
        clean_module.main()
    # Wenn main() durchlaeuft, ist _run_clean_results aufgerufen worden
    assert len(called) == 1
    assert called[0][0] == "qwen2.5:14b"


def test_clean_dispatcher_handles_subprocess_deprecation(monkeypatch):
    """Stellt sicher, dass der alte subprocess.run-Aufruf weg ist."""
    import inspect
    source = inspect.getsource(clean_module._run_clean_results)
    assert "subprocess" not in source, (
        "Phase 28: _run_clean_results darf subprocess nicht mehr importieren"
    )
    assert "main_with_args" in source, (
        "Phase 28: _run_clean_results muss main_with_args aufrufen"
    )
