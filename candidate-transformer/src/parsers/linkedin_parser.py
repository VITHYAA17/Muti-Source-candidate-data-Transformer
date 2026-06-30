"""
LinkedIn Parser - Parses linkedin.json into List[Candidate]

LinkedIn profile fields used:
  name, email, headline, profile_url, skills,
  location, current_company, current_title,
  years_experience, experience[], education[]
"""
import json
import uuid
import logging
from typing import List, Dict, Any, Optional

from ..models import Candidate, Skill, Experience, Education, Location, Links

logger = logging.getLogger(__name__)


class LinkedInParser:
    """
    Parses a LinkedIn-style JSON export (linkedin.json) into Candidate objects.

    Expects a top-level key ``"candidates"`` with a list of profile objects.
    """

    SOURCE = "LinkedIn"

    def parse(self, filepath: str) -> List[Candidate]:
        """
        Parse a LinkedIn JSON file and return a list of Candidate objects.

        Args:
            filepath: Path to the .json file

        Returns:
            List of Candidate objects
        """
        candidates = []

        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error("LinkedIn JSON file not found: %s", filepath)
            return candidates
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in %s: %s", filepath, e)
            return candidates

        raw_list = data.get("candidates", [])
        if not isinstance(raw_list, list):
            logger.error("Expected 'candidates' list in %s", filepath)
            return candidates

        for idx, record in enumerate(raw_list):
            try:
                candidate = self._parse_record(record)
                if candidate:
                    candidates.append(candidate)
            except Exception as e:
                logger.warning("LinkedIn record %d skipped: %s", idx, e)

        logger.info(
            "LinkedIn parser extracted %d candidates from %s",
            len(candidates),
            filepath,
        )
        return candidates

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_record(self, record: Dict[str, Any]):
        """Convert one LinkedIn profile dict to a Candidate."""

        name = (record.get("name") or "").strip()
        email = (record.get("email") or "").strip()

        if not name and not email:
            logger.warning("LinkedIn record has no name or email – skipping")
            return None

        candidate = Candidate(
            candidate_id=str(uuid.uuid4()),
            source=self.SOURCE,
        )

        # ── Full name ──────────────────────────────────────────────────
        if name:
            candidate.full_name = name
            candidate.add_provenance("full_name", self.SOURCE, "direct_extract")

        # ── Email ─────────────────────────────────────────────────────
        if email:
            candidate.emails = [email]
            candidate.add_provenance("emails", self.SOURCE, "direct_extract")

        # ── Headline ──────────────────────────────────────────────────
        headline = (record.get("headline") or "").strip()
        if headline:
            candidate.headline = headline
            candidate.add_provenance("headline", self.SOURCE, "direct_extract")

        # ── LinkedIn URL → links ───────────────────────────────────────
        profile_url = (record.get("profile_url") or "").strip()
        if profile_url:
            candidate.links.linkedin = profile_url
            candidate.add_provenance("links", self.SOURCE, "direct_extract")

        # ── Location ──────────────────────────────────────────────────
        location_str = (record.get("location") or "").strip()
        if location_str:
            candidate.location = self._parse_location(location_str)
            candidate.add_provenance("location", self.SOURCE, "direct_extract")

        # ── Years of experience ────────────────────────────────────────
        years = record.get("years_experience")
        if years is not None:
            try:
                candidate.years_experience = int(years)
                candidate.add_provenance(
                    "years_experience", self.SOURCE, "direct_extract"
                )
            except (ValueError, TypeError):
                logger.warning("Cannot parse years_experience: %s", years)

        # ── Skills ────────────────────────────────────────────────────
        skills_raw = record.get("skills") or []
        if isinstance(skills_raw, list):
            for skill_name in skills_raw:
                skill_name = skill_name.strip() if isinstance(skill_name, str) else ""
                if skill_name:
                    skill = Skill(
                        name=skill_name,
                        confidence=0.7,   # LinkedIn source confidence
                        sources=[self.SOURCE],
                    )
                    candidate.add_skill(skill)
            if skills_raw:
                candidate.add_provenance("skills", self.SOURCE, "direct_extract")

        # ── Work experience ────────────────────────────────────────────
        experiences = self._parse_experience(record.get("experience") or [])
        if experiences:
            candidate.experience = experiences
            candidate.add_provenance("experience", self.SOURCE, "direct_extract")

        # ── Education ─────────────────────────────────────────────────
        education_list = self._parse_education(record.get("education") or [])
        if education_list:
            candidate.education = education_list
            candidate.add_provenance("education", self.SOURCE, "direct_extract")

        return candidate

    def _parse_experience(self, raw_list: list) -> List[Experience]:
        """Parse the LinkedIn experience array."""
        result = []
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            company = (item.get("company") or "").strip()
            title = (item.get("title") or "").strip()
            if not company and not title:
                continue

            # LinkedIn stores dates like "2019-06-01"; we keep only YYYY-MM
            start = self._trim_date(item.get("start_date"))
            end = self._trim_date(item.get("end_date"))

            result.append(
                Experience(
                    company=company,
                    title=title,
                    start_date=start,
                    end_date=end,
                )
            )
        return result

    def _parse_education(self, raw_list: list) -> List[Education]:
        """Parse the LinkedIn education array."""
        result = []
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            institution = (item.get("institution") or "").strip()
            if not institution:
                continue

            degree = (item.get("degree") or "").strip() or None
            field = (item.get("field") or "").strip() or None
            grad_year = item.get("graduation_year")
            end_year = int(grad_year) if grad_year else None

            result.append(
                Education(
                    institution=institution,
                    degree=degree,
                    field=field,
                    end_year=end_year,
                )
            )
        return result

    @staticmethod
    def _trim_date(raw_date) -> Optional[str]:
        """
        Trim a full ISO date string '2019-06-01' down to 'YYYY-MM'.
        Returns None for null / invalid values.
        """
        if not raw_date or not isinstance(raw_date, str):
            return None
        parts = raw_date.strip().split("-")
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}"
        return raw_date.strip() or None

    @staticmethod
    def _parse_location(location_str: str) -> Location:
        """Parse 'San Francisco, CA' style strings to Location."""
        parts = [p.strip() for p in location_str.split(",")]
        city = parts[0] if len(parts) >= 1 else None
        region = parts[1] if len(parts) >= 2 else None
        country = parts[2] if len(parts) >= 3 else None
        return Location(city=city, region=region, country=country)
