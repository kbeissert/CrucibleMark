#!/usr/bin/env python3
"""
Unit Tests für UX Writing Module
Testet: Asset Loading, Scoring-Logik, Struktur
"""

import pytest
import yaml
from pathlib import Path
import sys

# Add project root to path (4 levels up: tests -> ux_writing -> benchmark_modules -> root)
sys.path.insert(0, str(Path(__file__).parents[3]))

from benchmark_modules.ux_writing.test import UXWritingTest

# Test constants
TOTAL_POINTS = 100


@pytest.fixture
def error_messages_asset_path():
    """Error Messages Asset Path"""
    return Path("benchmark_modules/ux_writing/assets/asset_001_error_messages.yaml")


@pytest.fixture
def button_labels_asset_path():
    """Button Labels Asset Path"""
    return Path("benchmark_modules/ux_writing/assets/asset_002_button_labels.yaml")


class TestAssetLoading:
    """Asset-Loading Tests"""

    def test_error_messages_asset_loads(self, error_messages_asset_path):
        """Error Messages Asset wird korrekt geladen"""
        assert error_messages_asset_path.exists(), "Error Messages Asset nicht gefunden"

        with open(error_messages_asset_path, "r", encoding="utf-8") as f:
            asset = yaml.safe_load(f)

        assert asset["metadata"]["id"] == "ux_writing_001"
        assert asset["metadata"]["category"] == "ux_writing"
        assert "scoring" in asset
        assert "error_detection" in asset["scoring"]
        assert "solution_quality" in asset["scoring"]
        assert asset["scoring"]["total_points"] == TOTAL_POINTS

    def test_button_labels_asset_loads(self, button_labels_asset_path):
        """Button Labels Asset wird korrekt geladen"""
        assert button_labels_asset_path.exists(), "Button Labels Asset nicht gefunden"

        with open(button_labels_asset_path, "r", encoding="utf-8") as f:
            asset = yaml.safe_load(f)

        assert asset["metadata"]["id"] == "ux_writing_002"
        assert asset["metadata"]["category"] == "ux_writing"
        assert asset["scoring"]["total_points"] == TOTAL_POINTS

    def test_instantiation(self, error_messages_asset_path):
        """Testet, ob die Klasse korrekt instanziiert werden kann"""
        test = UXWritingTest(error_messages_asset_path)
        assert test.asset["metadata"]["id"] == "ux_writing_001"
        assert isinstance(test, UXWritingTest)
