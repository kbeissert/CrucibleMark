import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from benchmark_modules.cultural_intelligence.test import CulturalIntelligenceTest

class TestCulturalIntelligence(unittest.TestCase):
    def setUp(self):
        # Mocking BaseTest init process to avoid file IO
        with patch('benchmark_modules.base_test.BaseTest._load_asset', return_value={}), \
             patch('benchmark_modules.base_test.BaseTest._validate_asset'):
            self.tester = CulturalIntelligenceTest(Path("dummy.yaml"))

    def test_tech_localization(self):
        # Manually set asset for this test
        self.tester.asset = {'id': 'cultural_intel_001'}
        
        # Perfect response
        resp_good = "English: Pull Request, Merge Request. German: Abbrechen, Absenden."
        result = self.tester.score_response(resp_good)
        self.assertEqual(result['total_score'], 100)

        # "Zieh-Anfrage" fail
        resp_bad = "Zieh-Anfrage, Abbrechen, Absenden"
        result = self.tester.score_response(resp_bad)
        self.assertLess(result['total_score'], 100)
        self.assertIn("Zieh-Anfrage", result['feedback'])

    def test_inclusive_job_ad(self):
        self.tester.asset = {'id': 'cultural_intel_002'}

        # Perfect response
        resp_good = "Wir suchen einen Software Engineer (m/w/d). Unsere Entwickler*innen sind toll."
        result = self.tester.score_response(resp_good)
        self.assertEqual(result['total_score'], 100) # 30 + 40 + 30 = 100

        # Missing m/w/d
        resp_med = "Wir suchen einen Software Engineer. Unsere Entwickler*innen sind toll."
        result = self.tester.score_response(resp_med)
        self.assertEqual(result['total_score'], 70)

    def test_agency_vibe(self):
        self.tester.asset = {'id': 'cultural_intel_003'}
        
        # Good response
        resp_good = "Hey, checkt unsere Vibes. Wir freuen uns auf euch."
        result = self.tester.score_response(resp_good)
        self.assertEqual(result['total_score'], 100)

        # Formal fail
        resp_bad = "Sehr geehrte Damen und Herren, wir freuen uns auf Sie."
        result = self.tester.score_response(resp_bad)
        self.assertEqual(result['total_score'], 0) # Penalty for 'Sie' wipes score

    def test_execute(self):
        # Test the execute wrapper
        self.tester.asset = {'input_text': 'Translate this'}
        mock_client = MagicMock()
        mock_client.query.return_value = "Translated text"
        
        result = self.tester.execute("test-model", mock_client)
        
        self.assertEqual(result['response'], "Translated text")
        self.assertIn('execution_time', result)
        mock_client.query.assert_called_once()


if __name__ == '__main__':
    unittest.main()
