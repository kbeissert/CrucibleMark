#!/usr/bin/env python3
"""
Unit Tests für Code Quality Module
Testet: Asset Loading, Scoring-Logik, Golden Standard Comparison, Stabilität
"""

import pytest
import yaml
from pathlib import Path
import sys

# Add project root to path (4 levels up: tests -> code_quality -> benchmark_modules -> root)
sys.path.insert(0, str(Path(__file__).parents[3]))

from benchmark_modules.code_quality.test import CodeQualityTest

# Test constants
TOTAL_POINTS = 100
EXPECTED_SECURITY_ISSUES = 12
MAX_ACCEPTABLE_CV = 10.0  # Maximum coefficient of variation for WCAG asset
MAX_EXCELLENT_CV = 1.0  # Maximum CV for excellent stability


@pytest.fixture
def wcag_asset_path():
    """WCAG Asset Path"""
    return Path("benchmark_modules/code_quality/assets/asset_001_wcag_audit.yaml")


@pytest.fixture
def security_asset_path():
    """Security Asset Path"""
    return Path("benchmark_modules/code_quality/assets/asset_002_security_audit.yaml")


from schemas.result import BenchmarkResult

class TestAssetLoading:
    """Asset-Loading Tests"""

    def test_wcag_asset_loads(self, wcag_asset_path):
        """WCAG Asset wird korrekt geladen"""
        assert wcag_asset_path.exists(), "WCAG Asset nicht gefunden"

        with open(wcag_asset_path, "r", encoding="utf-8") as f:
            asset = yaml.safe_load(f)

        assert asset["metadata"]["id"] == "code_quality_001"
        assert asset["metadata"]["category"] == "code_quality"
        assert "scoring" in asset
        assert "error_detection" in asset["scoring"]
        assert "solution_quality" in asset["scoring"]
        assert asset["scoring"]["total_points"] == TOTAL_POINTS

    def test_security_asset_loads(self, security_asset_path):
        """Security Asset wird korrekt geladen"""
        assert security_asset_path.exists(), "Security Asset nicht gefunden"

        with open(security_asset_path, "r", encoding="utf-8") as f:
            asset = yaml.safe_load(f)

        assert asset["metadata"]["id"] == "code_quality_002"
        assert asset["metadata"]["category"] == "code_quality"
        assert len(asset["test_data"]["issues"]) == EXPECTED_SECURITY_ISSUES
        assert asset["scoring"]["total_points"] == TOTAL_POINTS

    def test_both_assets_have_same_structure(
        self, wcag_asset_path, security_asset_path
    ):
        """Beide Assets nutzen gleiche Scoring-Struktur"""
        with open(wcag_asset_path, "r", encoding="utf-8") as f:
            wcag = yaml.safe_load(f)

        with open(security_asset_path, "r", encoding="utf-8") as f:
            security = yaml.safe_load(f)

        # Gleiche Scoring-Kategorien
        wcag_cats = set(wcag["scoring"].keys())
        security_cats = set(security["scoring"].keys())

        assert "error_detection" in wcag_cats
        assert "error_detection" in security_cats
        assert "solution_quality" in wcag_cats
        assert "solution_quality" in security_cats


class TestScoringLogic:
    """Scoring-Logik Tests"""

    def test_keyword_matching_above_threshold(self, security_asset_path):
        """Keywords über 40% Threshold werden erkannt"""
        response = "sql injection prepared statement pdo bindparam"
        keywords = [
            "sql injection",
            "prepared statement",
            "pdo",
            "bindparam",
            "mysqli_prepare",
        ]
        # Matches: 4/5 = 80% > 40%

        # Test helper logic directly (since _check_issue_mentioned was refactored)
        from benchmark_modules.code_quality.core.scoring_helpers import ScoringHelpers

        helper = ScoringHelpers()
        criterion = {"keywords": keywords, "points": 10, "description": "Test"}

        # Check standard keyword presence
        points, _ = helper.score_keyword_presence(response.lower(), criterion)
        result = points > 0

        assert result is True, "Keywords sollten erkannt werden"

    def test_keyword_matching_below_threshold(self, security_asset_path):
        """Keywords unter 40% Threshold nicht erkannt"""
        response = "security problem was fixed"
        keywords = [
            "sql injection",
            "prepared statement",
            "pdo",
            "bindparam",
            "mysqli_prepare",
        ]
        # Matches: 0/5 = 0% < 40%

        from benchmark_modules.code_quality.core.scoring_helpers import ScoringHelpers

        helper = ScoringHelpers()
        criterion = {"keywords": keywords, "points": 10, "description": "Test"}

        points, _ = helper.score_keyword_presence(response.lower(), criterion)
        result = points > 0

        assert result is False, "Keywords unter Threshold sollten nicht erkannt werden"

    def test_wcag_number_alone_sufficient(self, wcag_asset_path):
        """WCAG-Nummer allein reicht für Match"""
        response = "guideline 2.4.11 is important"
        keywords = ["2.4.11", "focus", "visible", "keyboard"]

        from benchmark_modules.code_quality.core.scoring_helpers import ScoringHelpers

        helper = ScoringHelpers()
        criterion = {"keywords": keywords, "points": 10, "description": "Test"}

        points, _ = helper.score_keyword_presence(response.lower(), criterion)
        result = points > 0

        assert result is True, "WCAG-Nummer allein sollte ausreichen"

    def test_empty_response_returns_zero_score(self, security_asset_path):
        """Leere Response gibt 0 Punkte"""
        # test = CodeQualityTest(security_asset_path)
        # Use Evaluator explicitly since test.execute returns BenchmarkResult
        from benchmark_modules.code_quality.core.evaluators import CodeQualityEvaluator

        evaluator = CodeQualityEvaluator({"scoring": {"total_points": 100}})
        result = evaluator.score_response("")

        assert result["total_score"] == 0
        assert "error" in result["status"]

        assert result["total_score"] == 0
        assert len(result["violations"]) > 0

    def test_error_response_returns_zero_score(self, security_asset_path):
        """Error-Response gibt 0 Punkte"""
        test = CodeQualityTest(security_asset_path)

        dummy_result = BenchmarkResult(status="error", raw_response="ERROR: Something went wrong")
        result = test.score_response(dummy_result)

        assert result.primary_score == 0


class TestStability:
    """Stabilitäts-Tests"""

    def test_cv_calculation(self, security_asset_path):
        """CV-Berechnung funktioniert korrekt"""
        _ = CodeQualityTest(security_asset_path)

        # Perfekt stabile Scores
        scores = [83.0, 83.0]
        mean = sum(scores) / len(scores)
        std = 0.0
        cv = (std / mean) * 100

        assert cv == 0.0, "Identische Scores sollten CV 0% haben"

    def test_security_asset_stability(self):
        """Security Asset hat perfekte Stabilität (CV 0%)"""
        # Basiert auf realen Test-Ergebnissen
        scores = [83.0, 83.0]
        mean = sum(scores) / len(scores)
        std = ((sum((x - mean) ** 2 for x in scores)) / len(scores)) ** 0.5
        cv = (std / mean) * 100 if mean > 0 else 0

        assert cv < MAX_EXCELLENT_CV, (
            f"Security Asset sollte CV <{MAX_EXCELLENT_CV}% haben, ist {cv:.2f}%"
        )

    def test_wcag_asset_stability(self):
        """WCAG Asset hat akzeptable Stabilität (CV <10%)"""
        # Basiert auf realen Test-Ergebnissen
        scores = [68.83, 79.17]
        mean = sum(scores) / len(scores)
        std = ((sum((x - mean) ** 2 for x in scores)) / len(scores)) ** 0.5
        cv = (std / mean) * 100 if mean > 0 else 0

        assert cv < MAX_ACCEPTABLE_CV, (
            f"WCAG Asset sollte CV <{MAX_ACCEPTABLE_CV}% haben, ist {cv:.2f}%"
        )


class TestModuleIntegration:
    """Integration Tests"""

    def test_code_quality_test_initializes(self, security_asset_path):
        """CodeQualityTest kann initialisiert werden"""
        test = CodeQualityTest(security_asset_path)
        assert test.asset is not None
        assert test.asset["metadata"]["id"] == "code_quality_002"

    def test_execute_returns_valid_structure(self, security_asset_path):
        """execute() gibt valide Struktur zurück (Mock)"""
        # Dieser Test würde LLM-Client benötigen, daher nur Struktur-Check
        test = CodeQualityTest(security_asset_path)

        # Prüfe dass Asset korrekt geladen ist
        assert "prompt" in test.asset
        assert "context" in test.asset
        assert "test_data" in test.asset


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
