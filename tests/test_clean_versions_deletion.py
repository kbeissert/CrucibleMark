"""Phase 28: Schutz vor Re-Introduktion von scripts/maintenance/clean_versions.py.

Hintergrund: Das alte Skript war toter Code (nicht im Makefile referenziert)
und enthielt eine hartkodierte Migration ``claude-opus-4-6`` ->
``claude-3-5-opus-latest`` (nicht-existente Modell-Variante). Es lief
bei jedem Import sofort los (kein ``__main__``-Guard).

Dieser Test stellt sicher, dass die Datei nicht versehentlich wieder
eingefuehrt wird. Sollte die Migration in Zukunft noetig werden,
muss sie als getesteter Helper in ``utils/model_utils.py`` landen
(nicht als Top-Level-Skript).
"""
from pathlib import Path


def test_clean_versions_file_does_not_exist():
    """Verhindert Re-Introduktion des toten Skripts."""
    target = Path("scripts/maintenance/clean_versions.py")
    assert not target.exists(), (
        f"Phase 28: {target} wurde geloescht (toter Code). "
        "Falls eine Legacy-Migration noetig wird, in utils/model_utils.py "
        "als getesteten Helper verschieben — nicht als Top-Level-Skript."
    )
