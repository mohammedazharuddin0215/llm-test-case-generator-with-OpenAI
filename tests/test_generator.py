import os
import sys
import unittest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from generator import generate_data, TestCaseGenerator
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Python path: {sys.path}")
    raise

class TestGenerator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = TestCaseGenerator()

    def test_generate_data(self):
        """Test the generate_data function"""
        result = generate_data()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
    def test_test_case_generator(self):
        """Test the TestCaseGenerator class"""
        requirement = "User login functionality"
        result = self.generator.generate_test_cases(requirement)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)

if __name__ == "__main__":
    unittest.main()