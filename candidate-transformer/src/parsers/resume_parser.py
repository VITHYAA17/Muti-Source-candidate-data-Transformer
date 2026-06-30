"""
Resume Parser - Parses resume_sample.txt into a Candidate

Handles plain-text resume files using regex extraction.
Sections recognised:
  - Contact block  (Name, Email, Phone, Location)
  - Professional Summary / Objective
  - Professional Experience  (company, title, dates)
  - Technical Skills
  - Education
  - Certifications (stored as skills)

Designed to be forgiving: it never raises on missing sections.
"""
import re
import uuid
import logging
from typing import List, Optional

from ..models import Candidate, Skill, Experience, Education, Location, Links

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled regexes
# ---------------------------------------------------------------------------

# Contact block
_NAME_RE     = re.compile(r"^Name[:\s]+(.+)$", re.IGNORECASE | re.MULTILINE)
_EMAIL_RE    = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
_PHONE_RE    = re.compile(
    r"(\+?1[\s\-.]?)?"           # optional country code
    r"(\(?\d{3}\)?[\s\-.]?)"     # area code
    r"(\d{3,4}[\s\-.]?\d{3,4})" # rest of number
)
_LOCATION_RE = re.compile(r"^Location[:\s]+(.+)$", re.IGNORECASE | re.MULTILINE)

# LinkedIn / GitHub URLs
_LINKEDIN_RE  = re.compile(r"linkedin\.com/in/[\w\-]+", re.IGNORECASE)
_GITHUB_RE    = re.compile(r"github\.com/[\w\-]+", re.IGNORECASE)
_PORTFOLIO_RE = re.compile(r"https?://(?!linkedin|github)[\w\-.]+\.\w{2,}", re.IGNORECASE)

# Section splitter – lines that look like section headers in ALL CAPS or Title Case
_SECTION_RE = re.compile(
    r"^(PROFESSIONAL SUMMARY|OBJECTIVE|PROFESSIONAL EXPERIENCE|WORK EXPERIENCE|"
    r"TECHNICAL SKILLS|SKILLS|EDUCATION|CERTIFICATIONS?|CONTACT)"
    r"\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Experience entry: "Company - Title (YYYY-Present)" or "Company - Title (YYYY-YYYY)"
_EXP_TITLE_RE = re.compile(
    r"^(?P<company>.+?)\s*[-–]\s*(?P<title>.+?)"
    r"\s*\((?P<start>\d{4})[-–](?P<end>Present|\d{4})\)",
    re.IGNORECASE | re.MULTILINE,
)

# Education: "B.S. Computer Science\nUniversity ..., Graduated: YYYY"
_EDU_DEGREE_RE = re.compile(
    r"^(?P<degree>B\.?S\.?|M\.?S\.?|Ph\.?D\.?|MBA|B\.?A\.?|M\.?A\.?)[\s,]+(?P<field>[^\n]+)$",
    re.IGNORECASE | re.MULTILINE,
)
_EDU_INSTITUTION_RE = re.compile(
    r"^(?P<institution>University .+?|.+? University|.+? College|.+? Institute)[,\s]*"
    r"(?:.*?Graduated:\s*(?P<year>\d{4}))?",
    re.IGNORECASE | re.MULTILINE,
)
_EDU_YEAR_RE = re.compile(r"Graduated[:\s]+(\d{4})", re.IGNORECASE)

# Skill lines: comma- or bullet-separated
_SKILL_SPLIT_RE = re.compile(r"[,;|•\-]+")

# Years of experience from summary
_YEARS_RE = re.compile(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", re.IGNORECASE)


class ResumeParser:
    """
    Parses a plain-text resume file into a single Candidate object.

    Returns a list for API consistency with other parsers (always length 0 or 1).
    """

    SOURCE = "Resume"

    def parse(self, filepath: str) -> List[Candidate]:
        """
        Parse a resume file (TXT, PDF, or DOCX).

        Args:
            filepath: Path to the resume file

        Returns:
            List containing 0 or 1 Candidate objects
        """
        import os
        ext = os.path.splitext(filepath)[1].lower()
        text = ""
        try:
            if ext == ".pdf":
                import PyPDF2
                logger.info("Extracting text from PDF resume: %s", filepath)
                with open(filepath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    pages_text = []
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            pages_text.append(page_text)
                    text = "\n".join(pages_text)
            elif ext == ".docx":
                import docx
                logger.info("Extracting text from Word document resume: %s", filepath)
                doc = docx.Document(filepath)
                paragraphs = [p.text for p in doc.paragraphs]
                text = "\n".join(paragraphs)
            else:
                logger.info("Reading plain-text resume: %s", filepath)
                with open(filepath, encoding="utf-8") as f:
                    text = f.read()
        except FileNotFoundError:
            logger.error("Resume file not found: %s", filepath)
            return []
        except Exception as e:
            logger.error("Failed to read resume %s: %s", filepath, e)
            return []

        candidate = self._parse_text(text)
        if candidate:
            logger.info("Resume parser extracted candidate: %s", candidate.full_name)
            return [candidate]
        return []

    # ------------------------------------------------------------------
    # Private: main parse
    # ------------------------------------------------------------------

    def _parse_text(self, text: str):
        """Parse raw resume text into a Candidate."""
        candidate = Candidate(
            candidate_id=str(uuid.uuid4()),
            source=self.SOURCE,
        )

        sections = self._split_sections(text)

        # ── Contact block ───────────────────────────────────────────────
        self._extract_contact(text, candidate)

        # ── Professional summary → headline + years_experience ──────────
        summary_text = sections.get("professional summary", "") or sections.get("objective", "")
        if summary_text:
            candidate.headline = summary_text.strip()
            candidate.add_provenance("headline", self.SOURCE, "regex_parse")
            years_match = _YEARS_RE.search(summary_text)
            if years_match:
                candidate.years_experience = int(years_match.group(1))
                candidate.add_provenance("years_experience", self.SOURCE, "regex_parse")

        # ── Skills ─────────────────────────────────────────────────────
        skills_text = sections.get("technical skills", "") or sections.get("skills", "")
        if skills_text:
            self._extract_skills(skills_text, candidate)

        # ── Experience ─────────────────────────────────────────────────
        exp_text = (
            sections.get("professional experience", "")
            or sections.get("work experience", "")
        )
        if exp_text:
            self._extract_experience(exp_text, candidate)

        # ── Education ──────────────────────────────────────────────────
        edu_text = sections.get("education", "")
        if edu_text:
            self._extract_education(edu_text, candidate)

        # Require at least a name or email
        if not candidate.full_name and not candidate.emails:
            logger.warning("Resume produced no name/email – discarding")
            return None

        return candidate

    # ------------------------------------------------------------------
    # Private: section splitter
    # ------------------------------------------------------------------

    def _split_sections(self, text: str) -> dict:
        """
        Split resume text into named sections.
        Returns dict  { section_header_lower: section_body_text }
        """
        sections: dict = {}
        matches = list(_SECTION_RE.finditer(text))

        for i, match in enumerate(matches):
            header = match.group(0).strip().lower()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections[header] = text[start:end].strip()

        return sections

    # ------------------------------------------------------------------
    # Private: contact
    # ------------------------------------------------------------------

    def _extract_contact(self, text: str, candidate: Candidate):
        # Name: look for "Name: ..." line first, fall back to first non-blank line
        name_match = _NAME_RE.search(text)
        if name_match:
            candidate.full_name = name_match.group(1).strip()
        else:
            # First meaningful non-empty line (before any all-caps section header)
            for line in text.splitlines():
                line = line.strip()
                if line and not _SECTION_RE.match(line) and len(line.split()) >= 2:
                    candidate.full_name = line
                    break

        if candidate.full_name:
            candidate.add_provenance("full_name", self.SOURCE, "regex_parse")

        # Email
        emails = _EMAIL_RE.findall(text)
        if emails:
            candidate.emails = list(dict.fromkeys(emails))  # deduplicate, preserve order
            candidate.add_provenance("emails", self.SOURCE, "regex_parse")

        # Phone
        phones = [m.group(0).strip() for m in _PHONE_RE.finditer(text)]
        if phones:
            candidate.phones = list(dict.fromkeys(phones))
            candidate.add_provenance("phones", self.SOURCE, "regex_parse")

        # Location line
        loc_match = _LOCATION_RE.search(text)
        if loc_match:
            candidate.location = self._parse_location(loc_match.group(1).strip())
            candidate.add_provenance("location", self.SOURCE, "regex_parse")

        # Links
        linkedin_match = _LINKEDIN_RE.search(text)
        github_match   = _GITHUB_RE.search(text)
        portfolio_match = _PORTFOLIO_RE.search(text)

        if linkedin_match:
            candidate.links.linkedin = "https://" + linkedin_match.group(0)
            candidate.add_provenance("links", self.SOURCE, "regex_parse")
        if github_match:
            candidate.links.github = "https://" + github_match.group(0)
            if not linkedin_match:
                candidate.add_provenance("links", self.SOURCE, "regex_parse")
        if portfolio_match:
            candidate.links.portfolio = portfolio_match.group(0)

    # ------------------------------------------------------------------
    # Private: skills
    # ------------------------------------------------------------------

    def _extract_skills(self, text: str, candidate: Candidate):
        """
        Extract skills from a skills section.
        Handles sub-headings like "Cloud Platforms: AWS, Azure, GCP"
        and plain comma/bullet lists.
        """
        # Strip sub-headings (anything before a colon)
        lines = text.splitlines()
        skill_names: List[str] = []

        for line in lines:
            # "Category: skill1, skill2, ..."
            if ":" in line:
                _, _, rest = line.partition(":")
                line = rest

            parts = _SKILL_SPLIT_RE.split(line)
            for part in parts:
                name = part.strip()
                if name and len(name) > 1:
                    skill_names.append(name)

        for name in skill_names:
            skill = Skill(name=name, confidence=1.0, sources=[self.SOURCE])
            candidate.add_skill(skill)

        if skill_names:
            candidate.add_provenance("skills", self.SOURCE, "regex_parse")

    # ------------------------------------------------------------------
    # Private: experience
    # ------------------------------------------------------------------

    def _extract_experience(self, text: str, candidate: Candidate):
        """
        Extract work experience entries.
        Pattern: "Company - Title (YYYY-YYYY)" or "Company - Title (YYYY-Present)"
        """
        experiences = []
        for match in _EXP_TITLE_RE.finditer(text):
            company = match.group("company").strip()
            title   = match.group("title").strip()
            start   = match.group("start")
            end_raw = match.group("end")
            end     = None if end_raw.lower() == "present" else end_raw

            # Extract lines after the header as summary (up to next blank line)
            after = text[match.end():]
            summary_lines = []
            for line in after.splitlines():
                line = line.strip()
                if not line:
                    break
                if line.startswith("-") or line.startswith("•"):
                    summary_lines.append(line.lstrip("-•").strip())

            experiences.append(
                Experience(
                    company=company,
                    title=title,
                    start_date=f"{start}-01" if start else None,
                    end_date=f"{end}-01" if end else None,
                    summary="; ".join(summary_lines) if summary_lines else None,
                )
            )

        if experiences:
            candidate.experience = experiences
            candidate.add_provenance("experience", self.SOURCE, "regex_parse")

    # ------------------------------------------------------------------
    # Private: education
    # ------------------------------------------------------------------

    def _extract_education(self, text: str, candidate: Candidate):
        """Extract education entries from the education section."""
        edu_list = []

        degree_match = _EDU_DEGREE_RE.search(text)
        inst_match   = _EDU_INSTITUTION_RE.search(text)
        year_match   = _EDU_YEAR_RE.search(text)

        if inst_match:
            edu_list.append(
                Education(
                    institution=inst_match.group("institution").strip(),
                    degree=degree_match.group("degree").strip() if degree_match else None,
                    field=degree_match.group("field").strip() if degree_match else None,
                    end_year=int(year_match.group(1)) if year_match else None,
                )
            )

        if edu_list:
            candidate.education = edu_list
            candidate.add_provenance("education", self.SOURCE, "regex_parse")

    # ------------------------------------------------------------------
    # Private: location helper
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_location(location_str: str) -> Location:
        parts = [p.strip() for p in location_str.split(",")]
        city   = parts[0] if len(parts) >= 1 else None
        region = parts[1] if len(parts) >= 2 else None
        country = parts[2] if len(parts) >= 3 else None
        return Location(city=city, region=region, country=country)
