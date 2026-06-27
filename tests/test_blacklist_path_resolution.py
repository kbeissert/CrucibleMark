"""Test for _BLACKLIST_PATH ROOT_DIR resolution (Phase 3)."""
from pathlib import Path
from scripts.web_export import _BLACKLIST_PATH, _ROOT_DIR


class TestBlacklistPathResolution:
    def test_blacklist_path_is_absolute(self):
        """Vorher war Path('config/...') relativ zu CWD — jetzt ROOT_DIR-relativ."""
        assert _BLACKLIST_PATH.is_absolute()

    def test_blacklist_path_under_root(self):
        assert _BLACKLIST_PATH == _ROOT_DIR / "config" / "web_export_blacklist.yaml"

    def test_blacklist_path_exists(self):
        """Datei muss tatsächlich existieren (Sanity-Check)."""
        assert _BLACKLIST_PATH.exists(), f"Missing: {_BLACKLIST_PATH}"
        assert _BLACKLIST_PATH.suffix == ".yaml"
