"""
Text Parser - Parses recruiter_notes.txt into a Candidate

Handles completely free-form recruiter notes using regex entity extraction.

Entities extracted:
  - Name (labeled "Candidate:")
  - Email
  - Phone
  - Location
  - Current company / title (labeled "Currently:")
  - Skills (labeled "Skills:" line or comma-separated list)
  - Education (labeled "BS/MS/PhD ... from ... (YYYY)")
  - Years of experience (from body text)
  - Experience entries (bullet lines under "Experience:")

Returns a list for API consistency (always 0 or 1 element).
"""
import re
import uuid
import logging
from typing import List, Optional

from ..models import Candidate, Skill, Experience, Education, Location

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled regexes
# ---------------------------------------------------------------------------

_NAME_RE     = re.compile(r"^Candidate[:\s]+(.+)$", re.IGNORECASE | re.MULTILINE)
_EMAIL_RE    = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
_PHONE_RE    = re.compile(
    r"(\+?1[\s\-.]?)?"
    r"(\(?\d{3}\)?[\s\-.]?)"
    r"(\d{3,4}[\s\-.]?\d{3,4})"
)
_LOCATION_RE = re.compile(r"^Location[:\s]+(.+)$", re.IGNORECASE | re.MULTILINE)

# "Currently: Senior Backend Engineer at Netflix (2021-Present)"
_CURRENT_JOB_RE = re.compile(
    r"Currently[:\s]+(?P<title>.+?)\s+at\s+(?P<company>.+?)(?:\s+\((?P<start>\d{4})",
    re.IGNORECASE,
)

# Bullet experience lines: "- Previous: Backend Engineer at LinkedIn (2018-2021)"
_PREV_EXP_RE = re.compile(
    r"[-•]\s*(?:Previously?|Earlier|Current)[:\s]+(?P<title>.+?)\s+at\s+(?P<company>.+?)"
    r"(?:\s+\((?P<start>\d{4})[-–](?P<end>Present|\d{4})\))?",
    re.IGNORECASE,
)

# Skills line: "Java, Python, Go, ..."
_SKILLS_SECTION_RE = re.compile(
    r"Skills[:\s]*\n(?P<skills>[^\n]+)", re.IGNORECASE
)
_SKILL_SPLIT_RE = re.compile(r"[,;|•]+")

# Education: "BS Computer Science from UC Berkeley (2015)"
_EDU_RE = re.compile(
    r"(?P<degree>BS|MS|PhD|MBA|BA|MA|B\.S\.|M\.S\.|B\.A\.|M\.A\.)\s+"
    r"(?P<field>[^from\n]+?)\s+from\s+(?P<institution>[^\n(]+)"
    r"(?:\s+\((?P<year>\d{4})\))?",
    re.IGNORECASE,
)

# Years experience
_YEARS_RE = re.compile(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", re.IGNORECASE)


class TextParser:
    """
    Parses a free-text recruiter notes file into a Candidate object.
    """

    SOURCE = "Text"

    def parse(self, filepath: str) -> List[Candidate]:
        """
        Parse a recruiter notes text file.

        Args:
            filepath: Path to the .txt file

        Returns:
            List containing 0 or 1 Candidate objects
        """
        try:
            with open(filepath, encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            logger.error("Text file not found: %s", filepath)
            return []
        except Exception as e:
            logger.error("Failed to read text file %s: %s", filepath, e)
            return []

        candidate = self._parse_text(text)
        if candidate:
            logger.info("Text parser extracted candidate: %s", candidate.full_name)
            return [candidate]
        return []

    # ------------------------------------------------------------------
    # Private: main parse
    # ------------------------------------------------------------------

    def _parse_text(self, text: str):
        """Extract entities from free-form recruiter notes."""

        candidate = Candidate(
            candidate_id=str(uuid.uuid4()),
            source=self.SOURCE,
        )

        # ── Name ────────────────────────────────────────────────────────
        name_match = _NAME_RE.search(text)
        if name_match:
            candidate.full_name = name_match.group(1).strip()
            candidate.add_provenance("full_name", self.SOURCE, "regex_parse")

        # ── Email ───────────────────────────────────────────────────────
        emails = _EMAIL_RE.findall(text)
        if emails:
            candidate.emails = list(dict.fromkeys(emails))
            candidate.add_provenance("emails", self.SOURCE, "regex_parse")

        # ── Phone ───────────────────────────────────────────────────────
        phones = [m.group(0).strip() for m in _PHONE_RE.finditer(text)]
        if phones:
            candidate.phones = list(dict.fromkeys(phones))
            candidate.add_provenance("phones", self.SOURCE, "regex_parse")

        # ── Location ────────────────────────────────────────────────────
        loc_match = _LOCATION_RE.search(text)
        if loc_match:
            candidate.location = self._parse_location(loc_match.group(1).strip())
            candidate.add_provenance("location", self.SOURCE, "regex_parse")

        # ── Years of experience ─────────────────────────────────────────
        years_match = _YEARS_RE.search(text)
        if years_match:
            candidate.years_experience = int(years_match.group(1))
            candidate.add_provenance("years_experience", self.SOURCE, "regex_parse")

        # ── Skills ─────────────────────────────────────────────────────
        skills_match = _SKILLS_SECTION_RE.search(text)
        if skills_match:
            skill_line = skills_match.group("skills")
            for part in _SKILL_SPLIT_RE.split(skill_line):
                name = part.strip()
                if name and len(name) > 1:
                    skill = Skill(name=name, confidence=0.5, sources=[self.SOURCE])
                    candidate.add_skill(skill)
            candidate.add_provenance("skills", self.SOURCE, "regex_parse")

        # ── Current job ─────────────────────────────────────────────────
        experiences: List[Experience] = []
        current_match = _CURRENT_JOB_RE.search(text)
        if current_match:
            start_year = current_match.group("start")
            experiences.append(
                Experience(
                    company=current_match.group("company").strip(),
                    title=current_match.group("title").strip(),
                    start_date=f"{start_year}-01" if start_year else None,
                    end_date=None,   # current role
                )
            )

        # ── Previous jobs ───────────────────────────────────────────────
        for match in _PREV_EXP_RE.finditer(text):
            company = match.group("company").strip()
            title   = match.group("title").strip()
            start   = match.group("start")
            end_raw = match.group("end")
            end     = None if (not end_raw or end_raw.lower() == "present") else end_raw

            # Avoid duplicating the current role captured above
            if any(e.company == company and e.title == title for e in experiences):
                continue

            experiences.append(
                Experience(
                    company=company,
                    title=title,
                    start_date=f"{start}-01" if start else None,
                    end_date=f"{end}-01" if end else None,
                )
            )

        if experiences:
            candidate.experience = experiences
            candidate.add_provenance("experience", self.SOURCE, "regex_parse")

        # ── Education ───────────────────────────────────────────────────
        edu_match = _EDU_RE.search(text)
        if edu_match:
            end_year = edu_match.group("year")
            candidate.education = [
                Education(
                    institution=edu_match.group("institution").strip(),
                    degree=edu_match.group("degree").strip(),
                    field=edu_match.group("field").strip(),
                    end_year=int(end_year) if end_year else None,
                )
            ]
            candidate.add_provenance("education", self.SOURCE, "regex_parse")

        # ── Headline from summary paragraph ────────────────────────────
        # Extract the first "Summary:" paragraph as the headline
        summary_match = re.search(
            r"^Summary[:\s]*\n(?P<body>.+?)(?:\n\n|\Z)",
            text, re.IGNORECASE | re.DOTALL | re.MULTILINE,
        )
        if summary_match:
            summary_text = summary_match.group("body").strip()
            # Use first sentence only as headline
            first_sentence = re.split(r"[.\n]", summary_text)[0].strip()
            if first_sentence:
                candidate.headline = first_sentence
                candidate.add_provenance("headline", self.SOURCE, "regex_parse")

        # Require at least a name or email
        if not candidate.full_name and not candidate.emails:
            logger.warning("Text file produced no name/email – discarding")
            return None

        return candidate

    # ------------------------------------------------------------------
    # Private helper
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_location(location_str: str) -> Location:
        """Parse 'San Jose, California' style strings to Location."""
        parts = [p.strip() for p in location_str.split(",")]
        city    = parts[0] if len(parts) >= 1 else None
        region  = parts[1] if len(parts) >= 2 else None
        country = parts[2] if len(parts) >= 3 else None
        return Location(city=city, region=region, country=country)
