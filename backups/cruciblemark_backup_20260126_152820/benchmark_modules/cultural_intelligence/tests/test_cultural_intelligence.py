import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from benchmark_modules.cultural_intelligence.test import CulturalIntelligenceTest


class TestCulturalIntelligence(unittest.TestCase):
    def setUp(self):
        # Mocking BaseTest init process to avoid file IO
        with (
            patch("benchmark_modules.base_test.BaseTest._load_asset", return_value={}),
            patch("benchmark_modules.base_test.BaseTest._validate_asset"),
        ):
            self.tester = CulturalIntelligenceTest(Path("dummy.yaml"))

    def test_tech_localization(self):
        # Manually set asset for this test (mocking metadata structure)
        self.tester.asset = {"metadata": {"id": "cultural_intel_001"}}

        # Perfect response (All 10 terms good)
        resp_good = "Wir pushen den Commit ins Remote Repository. Nach dem Merge schlug der Build fehl (beim Bauen), wegen eines Issues im Branch. Wir müssen pullen."
        result = self.tester.score_response(resp_good)
        self.assertEqual(result["total_score"], 100)

        # "Zieh" fail (Pull translated poorly)
        resp_bad = "Wir ziehen den Zweig (Branch) und drücken (Push) es."
        result = self.tester.score_response(resp_bad)
        # Should miss 'Pull' and 'Push' and 'Branch' -> 7/10 -> 70% (assuming other words present)
        # Actually resp_bad is very short. It misses commit, remote, repo, merge, build, issue... score will be low.
        self.assertLess(result["total_score"], 50)
        self.assertIn("Branch", result["feedback"])

    def test_inclusive_job_ad(self):
        self.tester.asset = {"metadata": {"id": "cultural_intel_002"}}

        # Perfect response (Clean and Neutral)
        resp_good = "Wir suchen eine engagierte Kraft (m/w/d). Unsere Entwickler sind toll. Seien Sie mutig. Keine Beschwerden. (m/w/d)"
        result = self.tester.score_response(resp_good)
        # Check: No Ninja, No Manpower, No Craftsman, No Kill, No Dominate (-0)
        # Check: Inclusive marker (+1).
        # Score should be high.
        self.assertGreaterEqual(result["total_score"], 90)

        # Bad response (Ninja kept)
        resp_fail = "Wir suchen einen Ninja mit Manpower."
        result = self.tester.score_response(resp_fail)
        self.assertLess(result["total_score"], 90)
        self.assertIn("Ninja", result["feedback"])

    def test_agency_vibe(self):
        self.tester.asset = {"metadata": {"id": "cultural_intel_003"}}

        # Good response (No buzzwords)
        resp_good = "Wir arbeiten zusammen an guten Sachen. Unser Ansatz ändert viel. Wir gucken genau hin."
        result = self.tester.score_response(resp_good)
        self.assertEqual(result["total_score"], 100)

        # Buzzword fail
        resp_bad = "Wir nutzen Synergie für eine holistische Solution im Ecosystem."
        result = self.tester.score_response(resp_bad)
        self.assertLess(
            result["total_score"], 70
        )  # Misses Synergie, Holistisch, Solution, Ecosystem
        self.assertIn("synergy", result["feedback"].lower())

    def test_execute(self):
        # Test the execute wrapper
        self.tester.asset = {"prompt": "Translate this"}
        mock_client = MagicMock()
        mock_client.query.return_value = "Translated text"

        result = self.tester.execute("test-model", mock_client)

        self.assertEqual(result["response"], "Translated text")
        self.assertEqual(result["raw_response"], "Translated text")
        self.assertIn("execution_time", result)
        mock_client.query.assert_called_once()


if __name__ == "__main__":
    unittest.main()
