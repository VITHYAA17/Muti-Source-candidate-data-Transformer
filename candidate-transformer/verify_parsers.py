"""Quick verification script for all parsers."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.parsers import CsvParser, JsonParser, GitHubParser, LinkedInParser, ResumeParser, TextParser

csv_candidates  = CsvParser().parse('input/recruiter.csv')
ats_candidates  = JsonParser().parse('input/ats_data.json')
gh_candidates   = GitHubParser().parse('input/github.json')
li_candidates   = LinkedInParser().parse('input/linkedin.json')
res_candidates  = ResumeParser().parse('input/resume_sample.txt')
txt_candidates  = TextParser().parse('input/recruiter_notes.txt')

all_candidates = (csv_candidates + ats_candidates + gh_candidates +
                  li_candidates + res_candidates + txt_candidates)

print(f"CSV      : {len(csv_candidates)} candidates")
print(f"ATS JSON : {len(ats_candidates)} candidates")
print(f"GitHub   : {len(gh_candidates)} candidates")
print(f"LinkedIn : {len(li_candidates)} candidates")
print(f"Resume   : {len(res_candidates)} candidates")
print(f"Text     : {len(txt_candidates)} candidates")
print(f"TOTAL    : {len(all_candidates)} raw candidate objects")
print()
for c in all_candidates:
    name = (c.full_name or "(no name)").ljust(25)
    print(f"  [{c.source:10}] {name} | emails={c.emails} | skills={len(c.skills)} | exp={len(c.experience)}")
