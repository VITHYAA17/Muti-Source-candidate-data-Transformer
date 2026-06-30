"""
Tests for Phase 4: Normalizers.
"""
import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models import Location
from src.normalizers import PhoneNormalizer, EmailNormalizer, DateNormalizer, SkillNormalizer, LocationNormalizer


class TestNormalizers(unittest.TestCase):
    def test_phone_normalizer(self):
        normalizer = PhoneNormalizer()
        self.assertEqual(normalizer.normalize("+1-555-0101"), "+15550101")
        self.assertEqual(normalizer.normalize("555-0102"), "+15550102")
        self.assertEqual(normalizer.normalize("(555) 0103"), "+15550103")
        self.assertEqual(normalizer.normalize("invalid-phone"), "invalid-phone")
        self.assertIsNone(normalizer.normalize(""))

    def test_email_normalizer(self):
        normalizer = EmailNormalizer()
        self.assertEqual(normalizer.normalize("  Jane.Doe@Gmail.com  "), "jane.doe@gmail.com")
        self.assertIsNone(normalizer.normalize(""))

    def test_date_normalizer(self):
        normalizer = DateNormalizer()
        self.assertEqual(normalizer.normalize("2020-01-15"), "2020-01-15")
        self.assertEqual(normalizer.normalize("01/15/2020"), "2020-01-15")
        self.assertEqual(normalizer.normalize("Jan 15 2020"), "2020-01-15")
        self.assertIsNone(normalizer.normalize("Present"))
        
        self.assertEqual(normalizer.normalize_to_year_month("2020-01-15"), "2020-01")
        self.assertEqual(normalizer.normalize_to_year_month("Jan 2020"), "2020-01")

    def test_skill_normalizer(self):
        normalizer = SkillNormalizer()
        self.assertEqual(normalizer.normalize("js"), "JavaScript")
        self.assertEqual(normalizer.normalize("K8s"), "Kubernetes")
        self.assertEqual(normalizer.normalize("python"), "Python")
        self.assertEqual(normalizer.normalize("AWS"), "AWS")
        self.assertEqual(normalizer.normalize("distributed systems"), "Distributed Systems")

    def test_location_normalizer(self):
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


if __name__ == "__main__":
    unittest.main()
