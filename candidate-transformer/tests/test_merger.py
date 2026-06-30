"""
Tests for Phase 5: Matcher, Conflict Resolver, and Merger.
"""
import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models import Candidate, Skill
from src.merger import CandidateMatcher, ConflictResolver, CandidateMerger


class TestMerger(unittest.TestCase):
    def test_candidate_matcher(self):
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

    def test_conflict_resolver(self):
        c_low = Candidate(full_name="Bob W.", source="Text")
        c_high = Candidate(full_name="Robert Wilson", source="Resume")
        
        resolver = ConflictResolver()
        winner = resolver.resolve_field([c_high, c_low], "full_name")
        self.assertEqual(winner, "Robert Wilson")

    def test_candidate_merger(self):
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


if __name__ == "__main__":
    unittest.main()
