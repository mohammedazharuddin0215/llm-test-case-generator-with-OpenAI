import sys
from pathlib import Path
import unittest
from unittest.mock import patch

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from generator import TestCaseGenerator


class TestGeneratorRetry(unittest.TestCase):
    def test_retry_succeeds_on_second_attempt(self):
        gen = TestCaseGenerator()

        # First call returns non-JSON, second returns valid JSON array
        bad = "I am not JSON"
        good = '[{"Functionality": "F1", "Test Summary": "S1", "Pre Condition": "", "Test Data": {}, "Test Steps": ["step1"], "Expected Result": "ok"}]'

        with patch('generator.LLMClient.generate', side_effect=[bad, good]):
            result = gen.generate_test_cases("some requirement", positive=1, negative=0, edge=0)

        # Expect parsed list from the second (good) response
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        self.assertEqual(result[0].get('Functionality'), 'F1')

    def test_retry_fails_returns_raw(self):
        gen = TestCaseGenerator()

        bad1 = "no json here"
        bad2 = "still not json"
        bad3 = "also not json"

        with patch('generator.LLMClient.generate', side_effect=[bad1, bad2, bad3]):
            result = gen.generate_test_cases("another requirement", positive=1, negative=0, edge=0)

        # When retries fail, generator returns the last raw text
        self.assertIsInstance(result, str)
        self.assertEqual(result, bad3)


if __name__ == '__main__':
    unittest.main()
