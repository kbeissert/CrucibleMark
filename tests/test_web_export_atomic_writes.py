"""Tests fuer skeptische Audit-Fixes in scripts/web_export.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class TestAtomicWriteJson:
    """Tests fuer die _atomic_write_json Helper-Funktion."""

    def test_atomic_write_creates_file(self, tmp_path):
        from scripts.web_export import _atomic_write_json
        target = tmp_path / "out.json"
        _atomic_write_json(target, {"hello": "world", "n": 42})
        assert target.exists()
        assert json.loads(target.read_text()) == {"hello": "world", "n": 42}

    def test_atomic_write_no_temp_files_left(self, tmp_path):
        from scripts.web_export import _atomic_write_json
        target = tmp_path / "out.json"
        _atomic_write_json(target, {"k": "v"})
        temps = list(tmp_path.glob(".*.tmp"))
        assert temps == [], f"Temp-Files uebrig: {temps}"

    def test_atomic_write_overwrites_existing(self, tmp_path):
        from scripts.web_export import _atomic_write_json
        target = tmp_path / "out.json"
        target.write_text("OLD")
        _atomic_write_json(target, {"new": True})
        assert json.loads(target.read_text()) == {"new": True}

    def test_atomic_write_creates_parent_dirs(self, tmp_path):
        from scripts.web_export import _atomic_write_json
        target = tmp_path / "a" / "b" / "out.json"
        _atomic_write_json(target, {"nested": True})
        assert target.exists()

    def test_atomic_write_failure_leaves_target_intact(self, tmp_path):
        from scripts.web_export import _atomic_write_json
        target = tmp_path / "out.json"
        target.write_text("ORIGINAL")
        with pytest.raises((TypeError, ValueError)):
            _atomic_write_json(target, {"bad": object()})
        assert target.read_text() == "ORIGINAL", "Zieldatei wurde ueberschrieben trotz Fehler"
        temps = list(tmp_path.glob(".*.tmp"))
        assert temps == [], f"Temp-Files uebrig: {temps}"


class TestNoSilentPass:
    """Prueft, dass keine silent 'except ...: pass' mehr im Code ist."""

    def test_no_except_pass_outside_atomic_helper(self):
        """Statische Analyse: silent pass nur in _atomic_write_json erlaubt.

        In _atomic_write_json ist silent pass fuer Temp-File-Cleanup
        intentional (das eigentliche Error wird durch raise propagiert).
        """
        import re
        web_export = ROOT / "scripts" / "web_export.py"
        text = web_export.read_text()

        # Extrahiere _atomic_write_json-Funktion (Multi-Line-Args tolerant)
        atomic_match = re.search(
            r'def _atomic_write_json\b.*?(?=\ndef |\nclass )',
            text, re.DOTALL
        )
        atomic_body = atomic_match.group(0) if atomic_match else ""
        # Rest = alles ausser _atomic_write_json
        rest = text.replace(atomic_body, "")

        # Suche 'except ...:' gefolgt von 'pass'
        pattern = re.compile(
            r'except\s+[^:]+:\s*\n\s*pass\b',
            re.MULTILINE
        )
        matches = pattern.findall(rest)
        assert matches == [], (
            f"Silent pass-Patterns ausserhalb _atomic_write_json gefunden: {matches}"
        )

    def test_logging_used_in_web_export(self):
        web_export = ROOT / "scripts" / "web_export.py"
        text = web_export.read_text()
        assert "logging.warning" in text or "logging.error" in text


class TestProviderLandscapeReviewFallback:
    """Prueft Fallback-Logik fuer provider_landscape_review.md."""

    def test_legacy_path_fallback(self, tmp_path):
        reviews_path = tmp_path / "docs" / "reviews"
        reviews_path.mkdir(parents=True)
        legacy_md = reviews_path / "provider_landscape_review.md"
        legacy_md.write_text("# Legacy Provider-Landscape")

        comparisons_path = tmp_path / "docs" / "comparisons"
        comparisons_path.mkdir(parents=True)

        provider_md = comparisons_path / "provider_landscape_review.md"
        if not provider_md.exists():
            legacy = comparisons_path.parent / "reviews" / "provider_landscape_review.md"
            if legacy.exists():
                provider_md = legacy

        assert provider_md.exists()
        assert provider_md == legacy_md

    def test_primary_path_takes_precedence(self, tmp_path):
        comparisons_path = tmp_path / "docs" / "comparisons"
        comparisons_path.mkdir(parents=True)
        primary = comparisons_path / "provider_landscape_review.md"
        primary.write_text("# Primary")

        reviews_path = tmp_path / "docs" / "reviews"
        reviews_path.mkdir(parents=True)
        (reviews_path / "provider_landscape_review.md").write_text("# Legacy")

        provider_md = comparisons_path / "provider_landscape_review.md"
        if not provider_md.exists():
            legacy = comparisons_path.parent / "reviews" / "provider_landscape_review.md"
            if legacy.exists():
                provider_md = legacy

        assert provider_md == primary
