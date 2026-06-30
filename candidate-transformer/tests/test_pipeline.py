"""
Unit and integration tests for the Candidate Data Transformer ETL pipeline using standard unittest.
"""
import unittest
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models import Candidate, Location, Links, Skill, Experience, Education
from src.normalizers import PhoneNormalizer, EmailNormalizer, DateNormalizer, SkillNormalizer, LocationNormalizer
from src.merger import CandidateMatcher, CandidateMerger
from src.confidence import ConfidenceCalculator
from src.projection import OutputProjector, SchemaValidator, ValidationError


class TestPhoneNormalizer(unittest.TestCase):
    def test_normalize(self):
        normalizer = PhoneNormalizer()
        self.assertEqual(normalizer.normalize("+1-555-0101"), "+15550101")
        self.assertEqual(normalizer.normalize("555-0102"), "+15550102")
        self.assertEqual(normalizer.normalize("(555) 0103"), "+15550103")
        self.assertEqual(normalizer.normalize("invalid-phone"), "invalid-phone")
        self.assertIsNone(normalizer.normalize(""))


class TestEmailNormalizer(unittest.TestCase):
    def test_normalize(self):
        normalizer = EmailNormalizer()
        self.assertEqual(normalizer.normalize("  John.Smith@Gmail.com  "), "john.smith@gmail.com")
        self.assertIsNone(normalizer.normalize(""))


class TestDateNormalizer(unittest.TestCase):
    def test_normalize(self):
        normalizer = DateNormalizer()
        self.assertEqual(normalizer.normalize("2020-01-15"), "2020-01-15")
        self.assertEqual(normalizer.normalize("01/15/2020"), "2020-01-15")
        self.assertEqual(normalizer.normalize("Jan 15 2020"), "2020-01-15")
        self.assertIsNone(normalizer.normalize("Present"))
        
        self.assertEqual(normalizer.normalize_to_year_month("2020-01-15"), "2020-01")
        self.assertEqual(normalizer.normalize_to_year_month("2020-01"), "2020-01")
        self.assertEqual(normalizer.normalize_to_year_month("Jan 2020"), "2020-01")


class TestSkillNormalizer(unittest.TestCase):
    def test_normalize(self):
        normalizer = SkillNormalizer()
        self.assertEqual(normalizer.normalize("js"), "JavaScript")
        self.assertEqual(normalizer.normalize("K8s"), "Kubernetes")
        self.assertEqual(normalizer.normalize("python"), "Python")
        self.assertEqual(normalizer.normalize("AWS"), "AWS")
        self.assertEqual(normalizer.normalize("distributed systems"), "Distributed Systems")


class TestLocationNormalizer(unittest.TestCase):
    def test_normalize(self):
        normalizer = LocationNormalizer()
        
        loc1 = Location(city="San Francisco, CA")
        norm1 = normalizer.normalize(loc1)
        self.assertEqual(norm1.city, "San Francisco")
        self.assertEqual(norm1.region, "CA")
        self.assertEqual(norm1.country, "US")
        
        loc2 = Location(city="San Francisco, California, USA")
        norm2 = normalizer.normalize(loc2)
        self.assertEqual(norm2.city, "San Francisco")
        self.assertEqual(norm2.region, "CA")
        self.assertEqual(norm2.country, "US")
        
        loc3 = Location(city="seattle")
        norm3 = normalizer.normalize(loc3)
        self.assertEqual(norm3.city, "Seattle")
        self.assertEqual(norm3.region, "WA")
        self.assertEqual(norm3.country, "US")


class TestCandidateMatcher(unittest.TestCase):
    def test_matcher(self):
        c1 = Candidate(full_name="John Smith", emails=["john.smith@gmail.com"])
        c2 = Candidate(full_name="John S.", phones=["+15550101"])
        c3 = Candidate(full_name="J. Smith", emails=["john.smith@gmail.com"], phones=["+15550101"])
        c4 = Candidate(full_name="Alice Johnson", emails=["alice@company.com"])

        matcher = CandidateMatcher()
        groups = matcher.match_candidates([c1, c2, c3, c4])
        
        self.assertEqual(len(groups), 2)
        group_sizes = [len(g) for g in groups]
        self.assertIn(3, group_sizes)
        self.assertIn(1, group_sizes)


class TestCandidateMerger(unittest.TestCase):
    def test_merger(self):
        c_text = Candidate(
            full_name="Bob Wilson",
            emails=["bob@techmail.com"],
            headline="DevOps",
            source="Text"
        )
        c_text.add_provenance("full_name", "Text", "regex_parse")
        c_text.add_provenance("emails", "Text", "regex_parse")
        c_text.add_provenance("headline", "Text", "regex_parse")

        c_resume = Candidate(
            full_name="Robert Wilson",
            emails=["bob@techmail.com"],
            phones=["+15550104"],
            headline="Senior DevOps Engineer",
            skills=[Skill("Kubernetes", 1.0, ["Resume"])],
            source="Resume"
        )
        c_resume.add_provenance("full_name", "Resume", "direct_extract")
        c_resume.add_provenance("emails", "Resume", "direct_extract")
        c_resume.add_provenance("phones", "Resume", "direct_extract")
        c_resume.add_provenance("headline", "Resume", "direct_extract")
        c_resume.add_provenance("skills", "Resume", "direct_extract")

        merger = CandidateMerger()
        merged = merger.merge_candidates([c_text, c_resume])

        self.assertEqual(merged.full_name, "Robert Wilson")
        self.assertEqual(merged.headline, "Senior DevOps Engineer")
        self.assertIn("+15550104", merged.phones)
        self.assertIn("bob@techmail.com", merged.emails)
        self.assertEqual(len(merged.skills), 1)
        self.assertEqual(merged.skills[0].name, "Kubernetes")
        self.assertEqual(len(merged.provenance["full_name"]), 2)


class TestConfidenceCalculator(unittest.TestCase):
    def test_confidence(self):
        candidate = Candidate(
            full_name="Bob Wilson",
            emails=["bob@techmail.com"],
            phones=["+15550104"],
            source="Resume"
        )
        candidate.add_provenance("full_name", "Resume", "direct_extract")
        candidate.add_provenance("full_name", "CSV", "direct_extract")
        candidate.add_provenance("emails", "Resume", "direct_extract")
        candidate.add_provenance("phones", "Resume", "direct_extract")

        calc = ConfidenceCalculator()
        calc.calculate_confidence(candidate)

        self.assertEqual(candidate.field_confidence["full_name"], 1.0)
        self.assertEqual(candidate.field_confidence["emails"], 1.0)
        self.assertTrue(candidate.overall_confidence > 0.0)


class TestProjectorAndValidator(unittest.TestCase):
    def test_projector_and_validator(self):
        config = {
            "fields": [
                {"path": "full_name", "type": "string", "required": True},
                {"path": "emails", "type": "string[]", "required": True},
                {"path": "overall_confidence", "type": "number", "required": False}
            ],
            "include_provenance": False,
            "include_confidence": True,
            "on_missing": "null"
        }

        candidate = Candidate(
            full_name="John Smith",
            emails=["john@smith.com"]
        )
        candidate.overall_confidence = 0.95

        projector = OutputProjector(config)
        projected = projector.project(candidate)

        self.assertEqual(projected["full_name"], "John Smith")
        self.assertEqual(projected["emails"], ["john@smith.com"])
        self.assertEqual(projected["overall_confidence"], 0.95)
        self.assertNotIn("provenance", projected)

        validator = SchemaValidator(config)
        validator.validate(projected)

        projected_invalid = projected.copy()
        projected_invalid["full_name"] = None
        with self.assertRaises(ValidationError):
            validator.validate(projected_invalid)

        projected_invalid_type = projected.copy()
        projected_invalid_type["overall_confidence"] = "high"
        with self.assertRaises(ValidationError):
            validator.validate(projected_invalid_type)


if __name__ == "__main__":
    unittest.main()
