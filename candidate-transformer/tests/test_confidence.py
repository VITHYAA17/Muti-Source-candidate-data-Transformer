"""
Tests for Phase 6: Confidence Calculator.
"""
import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models import Candidate
from src.confidence import ConfidenceCalculator


class TestConfidence(unittest.TestCase):
    def test_confidence_calculator(self):
        candidate = Candidate(
            full_name="Bob Wilson",
            emails=["bob@techmail.com"],
            phones=["+15550104"],
            source="Resume"
        )
        candidate.add_provenance("full_name", "Resume", "direct_extract")
        candidate.add_provenance("full_name", "CSV", "direct_extract")  # Agreement bonus
        candidate.add_provenance("emails", "Resume", "direct_extract")
        candidate.add_provenance("phones", "Resume", "direct_extract")

        calc = ConfidenceCalculator()
        calc.calculate_confidence(candidate)

        self.assertEqual(candidate.field_confidence["full_name"], 1.0)
        self.assertEqual(candidate.field_confidence["emails"], 1.0)
        self.assertTrue(candidate.overall_confidence > 0.0)


if __name__ == "__main__":
    unittest.main()
