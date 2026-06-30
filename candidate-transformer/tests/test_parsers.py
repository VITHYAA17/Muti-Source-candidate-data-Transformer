"""
Tests for Phase 3: Parsers (CSV, ATS JSON, GitHub, LinkedIn, Resume, Text).
"""
import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.parsers import CsvParser, JsonParser, GitHubParser, LinkedInParser, ResumeParser, TextParser


class TestParsers(unittest.TestCase):
    def setUp(self):
        self.input_dir = os.path.join(PROJECT_ROOT, "input")

    def test_csv_parser(self):
        path = os.path.join(self.input_dir, "recruiter.csv")
        if not os.path.exists(path):
            self.skipTest("recruiter.csv input not found")
        candidates = CsvParser().parse(path)
        self.assertEqual(len(candidates), 4)
        for c in candidates:
            self.assertEqual(c.source, "CSV")
            self.assertTrue(c.full_name)

    def test_json_parser(self):
        path = os.path.join(self.input_dir, "ats_data.json")
        if not os.path.exists(path):
            self.skipTest("ats_data.json input not found")
        candidates = JsonParser().parse(path)
        self.assertEqual(len(candidates), 3)
        for c in candidates:
            self.assertEqual(c.source, "ATS")
            self.assertTrue(c.full_name)

    def test_github_parser(self):
        path = os.path.join(self.input_dir, "github.json")
        if not os.path.exists(path):
            self.skipTest("github.json input not found")
        candidates = GitHubParser().parse(path)
        self.assertEqual(len(candidates), 3)
        for c in candidates:
            self.assertEqual(c.source, "GitHub")
            self.assertTrue(c.full_name)

    def test_linkedin_parser(self):
        path = os.path.join(self.input_dir, "linkedin.json")
        if not os.path.exists(path):
            self.skipTest("linkedin.json input not found")
        candidates = LinkedInParser().parse(path)
        self.assertEqual(len(candidates), 3)
        for c in candidates:
            self.assertEqual(c.source, "LinkedIn")
            self.assertTrue(c.full_name)

    def test_resume_parser(self):
        path = os.path.join(self.input_dir, "resume_sample.txt")
        if not os.path.exists(path):
            self.skipTest("resume_sample.txt input not found")
        candidates = ResumeParser().parse(path)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].full_name, "Bob Wilson")
        self.assertEqual(candidates[0].source, "Resume")

    def test_text_parser(self):
        path = os.path.join(self.input_dir, "recruiter_notes.txt")
        if not os.path.exists(path):
            self.skipTest("recruiter_notes.txt input not found")
        candidates = TextParser().parse(path)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].full_name, "David Lee")
        self.assertEqual(candidates[0].source, "Text")


if __name__ == "__main__":
    unittest.main()
