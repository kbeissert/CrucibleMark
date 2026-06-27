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


class TestAtomicWriteText:
    """Tests fuer _atomic_write_text (BUG 3 Fix)."""

    def test_atomic_write_text_creates_file(self, tmp_path):
        from scripts.web_export import _atomic_write_text
        target = tmp_path / "audit_log.md"
        _atomic_write_text(target, "# Audit Log\nContent here")
        assert target.read_text(encoding="utf-8") == "# Audit Log\nContent here"

    def test_atomic_write_text_overwrites_existing(self, tmp_path):
        from scripts.web_export import _atomic_write_text
        target = tmp_path / "review.md"
        target.write_text("OLD", encoding="utf-8")
        _atomic_write_text(target, "NEW")
        assert target.read_text(encoding="utf-8") == "NEW"

    def test_atomic_write_text_no_temp_files_left(self, tmp_path):
        from scripts.web_export import _atomic_write_text
        target = tmp_path / "test.md"
        _atomic_write_text(target, "content")
        temps = list(tmp_path.glob(".*.tmp"))
        assert temps == []

    def test_atomic_write_text_failure_leaves_target_intact(self, tmp_path):
        from scripts.web_export import _atomic_write_text
        target = tmp_path / "existing.md"
        target.write_text("ORIGINAL", encoding="utf-8")
        # Simuliere Fehler durch nicht-schreibbares Verzeichnis
        import os
        os.chmod(tmp_path, 0o444)
        try:
            _atomic_write_text(tmp_path / "new.md", "content")
            assert False, "Sollte OSError werfen"
        except (OSError, PermissionError):
            pass
        finally:
            os.chmod(tmp_path, 0o755)
        # Original-Datei unversehrt
        assert target.read_text(encoding="utf-8") == "ORIGINAL"
        # Keine Temp-Files uebrig
        assert list(tmp_path.glob(".*.tmp")) == []


class TestAtomicCopy:
    """Tests fuer _atomic_copy (BUG 3 Fix)."""

    def test_atomic_copy_creates_file(self, tmp_path):
        from scripts.web_export import _atomic_copy
        src = tmp_path / "source.md"
        src.write_text("# Source Content", encoding="utf-8")
        dst = tmp_path / "out" / "dest.md"
        _atomic_copy(src, dst)
        assert dst.read_text(encoding="utf-8") == "# Source Content"

    def test_atomic_copy_overwrites_existing(self, tmp_path):
        from scripts.web_export import _atomic_copy
        src = tmp_path / "source.md"
        src.write_text("NEW CONTENT", encoding="utf-8")
        dst = tmp_path / "dest.md"
        dst.write_text("OLD", encoding="utf-8")
        _atomic_copy(src, dst)
        assert dst.read_text(encoding="utf-8") == "NEW CONTENT"

    def test_atomic_copy_no_temp_files_left(self, tmp_path):
        from scripts.web_export import _atomic_copy
        src = tmp_path / "source.md"
        src.write_text("content", encoding="utf-8")
        dst = tmp_path / "dest.md"
        _atomic_copy(src, dst)
        assert list(tmp_path.glob(".*.tmp")) == []

    def test_atomic_copy_preserves_permissions(self, tmp_path):
        import os
        from scripts.web_export import _atomic_copy
        src = tmp_path / "source.md"
        src.write_text("content", encoding="utf-8")
        os.chmod(src, 0o755)
        dst = tmp_path / "dest.md"
        _atomic_copy(src, dst)
        assert oct(os.stat(dst).st_mode)[-3:] == "755"


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

        # Extrahiere alle Atomic-Helper (BUG 3: 3 Helper mit silent pass fuer Temp-Cleanup)
        atomic_bodies = []
        for func_name in ("_atomic_write_json", "_atomic_write_text", "_atomic_copy"):
            m = re.search(
                r'def ' + func_name + r'\b.*?(?=\ndef |\nclass )',
                text, re.DOTALL
            )
            if m:
                atomic_bodies.append(m.group(0))
        # Rest = alles ausser den Atomic-Helpern
        rest = text
        for body in atomic_bodies:
            rest = rest.replace(body, "")

        # Suche 'except ...:' gefolgt von 'pass'
        pattern = re.compile(
            r'except\s+[^:]+:\s*\n\s*pass\b',
            re.MULTILINE
        )
        matches = pattern.findall(rest)
        assert matches == [], (
            f"Silent pass-Patterns ausserhalb Atomic-Helper gefunden: {matches}"
        )

    def test_logging_used_in_web_export(self):
        web_export = ROOT / "scripts" / "web_export.py"
        text = web_export.read_text()
        assert "logging.warning" in text or "logging.error" in text


class TestProviderLandscapeReviewFallback:
    """Prueft Fallback-Logik fuer provider_landscape_review.md.

    BUG 1 Fix (v4.10.11): Vorher war comparisons_path.parent / "reviews" / ...
    identisch zu comparisons_path / ... (weil comparisons_path = docs/reviews/).
    Jetzt werden beide Pfade unabhaengig von root_dir geprueft.
    """

    def _resolve_provider_md(self, root_dir: Path) -> Path | None:
        """Repliziert die korrigierte Logik aus _write_top_level_outputs."""
        primary = root_dir / "docs" / "comparisons" / "provider_landscape_review.md"
        legacy = root_dir / "docs" / "reviews" / "provider_landscape_review.md"
        return primary if primary.exists() else (legacy if legacy.exists() else None)

    def test_legacy_path_fallback(self, tmp_path):
        """Wenn nur docs/reviews/ existiert, wird es als Fallback genutzt."""
        reviews_path = tmp_path / "docs" / "reviews"
        reviews_path.mkdir(parents=True)
        legacy_md = reviews_path / "provider_landscape_review.md"
        legacy_md.write_text("# Legacy Provider-Landscape")

        result = self._resolve_provider_md(tmp_path)
        assert result is not None
        assert result == legacy_md

    def test_primary_path_takes_precedence(self, tmp_path):
        """Wenn beide existieren, gewinnt docs/comparisons/ (Primary)."""
        comparisons_path = tmp_path / "docs" / "comparisons"
        comparisons_path.mkdir(parents=True)
        primary = comparisons_path / "provider_landscape_review.md"
        primary.write_text("# Primary")

        reviews_path = tmp_path / "docs" / "reviews"
        reviews_path.mkdir(parents=True)
        (reviews_path / "provider_landscape_review.md").write_text("# Legacy")

        result = self._resolve_provider_md(tmp_path)
        assert result == primary

    def test_neither_exists_returns_none(self, tmp_path):
        """Wenn keine Datei existiert, wird None zurueckgegeben (-> Warning)."""
        result = self._resolve_provider_md(tmp_path)
        assert result is None
