"""Globale Pytest-Fixtures fuer das CrucibleMark-Test-Set.

Sorgt dafuer, dass CARD_DIR-Schreibzugriffe waehrend Tests niemals
die echten Model-Cards in ``benchmark_scores/model_cards/`` treffen.

Hintergrund (2026-06-10):
- ``utils.model_utils.CARD_DIR`` zeigt per Default auf
  ``benchmark_scores/model_cards/`` (SSoT).
- Einige Worker-Tests (``test_run_score_benchmark``,
  ``test_run_political_compass_benchmark``) rufen ``worker.main()`` direkt
  auf und monkeypatchen ``CARD_DIR`` NICHT. Dadurch konnten Code-Pfade
  wie ``discover_models()`` oder Card-Lookups in
  ``UnifiedBenchmarkRunner`` echte Test-Cards (``m1.json``, ``m2.json``,
  ``True.json``) im Produktionsordner anlegen.
- Diese autouse-Fixture lenkt ``CARD_DIR`` fuer jeden Test auf
  ``tmp_path`` um. Konvention: ``CARD_DIR = tmp_path`` — identisch zu
  den bestehenden Fixtures in ``test_enforce_card_first.py``,
  ``test_id_ssot_invariants.py`` und
  ``test_benchmark_auto_untested_tooluse.py``, daher kein Konflikt
  (monkeypatch restauriert am Ende alle setattrs auf den Originalwert).
- Lokale ``CARD_DIR``-Konstanten in anderen Modulen (z.B.
  ``scripts.core.benchmark_auto.CARD_DIR``) sind separate Modul-Attribute
  und werden NICHT beeinflusst.

Opt-Out:
- Tests, die explizit echte Cards brauchen (z.B. Lookup-Tests in
  ``test_resolve_canonical_model_id.py``), koennen mit
  ``@pytest.mark.uses_real_cards`` markiert werden. Die autouse-Fixture
  wird fuer diese Tests uebersprungen.
"""
from __future__ import annotations

from pathlib import Path

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Registriert Custom-Marker, damit ``--strict-markers``-Setups keine
    ``PytestUnknownMarkWarning`` werfen.
    """
    config.addinivalue_line(
        "markers",
        "uses_real_cards: Test verlasst sich auf die echten Model-Cards "
        "in benchmark_scores/model_cards/ und ueberspringt die globale "
        "CARD_DIR-Isolation.",
    )


@pytest.fixture(autouse=True)
def _isolate_card_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, request: pytest.FixtureRequest):
    """CARD_DIR fuer jeden Test auf tmp_path umlenken.

    Verhindert, dass Tests versehentlich echte Cards in
    ``benchmark_scores/model_cards/`` anlegen oder vorhandene
    ueberschreiben.

    Skip mit ``@pytest.mark.uses_real_cards`` fuer Tests, die explizit
    die echten Model-Cards brauchen (z.B. Resolution-Tests mit
    glob-fallback Card-Alias).
    """
    if request.node.get_closest_marker("uses_real_cards"):
        yield
        return
    monkeypatch.setattr("utils.model_utils.CARD_DIR", tmp_path)
    # CARD_DIR lives in utils.model_card_io after the Sektion-A refactor;
    # _find_card/_card_path/read CARD_DIR from there at call-time.
    monkeypatch.setattr("utils.model_card_io.CARD_DIR", tmp_path)
    yield
