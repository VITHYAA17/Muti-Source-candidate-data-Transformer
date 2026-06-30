"""
GitHub Parser - Parses github.json into List[Candidate]

GitHub profile fields used:
  name, email, bio, languages, github_url,
  location, company, repositories_count

Skills are derived from the 'languages' list.
Headline is built from the bio text.
"""
import json
import uuid
import logging
import re
from typing import List, Dict, Any

from ..models import Candidate, Skill, Location, Links

logger = logging.getLogger(__name__)

# Regex to pull years-of-experience hint from bio strings like
# "10+ years experience" or "8 years of experience"
_YEARS_RE = re.compile(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", re.IGNORECASE)


class GitHubParser:
    """
    Parses a GitHub-style JSON export (github.json) into Candidate objects.

    Expects a top-level key ``"candidates"`` with a list of profile objects.
    """

    SOURCE = "GitHub"

    def parse(self, filepath: str) -> List[Candidate]:
        """
        Parse a GitHub JSON file and return a list of Candidate objects.

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
            logger.error("GitHub JSON file not found: %s", filepath)
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
                logger.warning("GitHub record %d skipped: %s", idx, e)

        logger.info(
            "GitHub parser extracted %d candidates from %s", len(candidates), filepath
        )
        return candidates

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_record(self, record: Dict[str, Any]):
        """Convert one GitHub profile dict to a Candidate."""

        name = (record.get("name") or "").strip()
        email = (record.get("email") or "").strip()

        if not name and not email:
            logger.warning("GitHub record has no name or email – skipping")
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

        # ── GitHub URL → links ─────────────────────────────────────────
        github_url = (record.get("github_url") or "").strip()
        if github_url:
            candidate.links.github = github_url
            candidate.add_provenance("links", self.SOURCE, "direct_extract")

        # ── Location (raw string) ──────────────────────────────────────
        location_str = (record.get("location") or "").strip()
        if location_str:
            candidate.location = self._parse_location(location_str)
            candidate.add_provenance("location", self.SOURCE, "direct_extract")

        # ── Bio → headline + years_experience hint ─────────────────────
        bio = (record.get("bio") or "").strip()
        if bio:
            candidate.headline = bio
            candidate.add_provenance("headline", self.SOURCE, "direct_extract")

            years_match = _YEARS_RE.search(bio)
            if years_match:
                candidate.years_experience = int(years_match.group(1))
                candidate.add_provenance(
                    "years_experience", self.SOURCE, "regex_parse"
                )

        # ── Languages → skills ─────────────────────────────────────────
        languages = record.get("languages") or []
        if isinstance(languages, list):
            for lang in languages:
                lang = lang.strip() if isinstance(lang, str) else ""
                if lang:
                    skill = Skill(
                        name=lang,
                        confidence=0.9,  # GitHub source confidence
                        sources=[self.SOURCE],
                    )
                    candidate.add_skill(skill)
            if languages:
                candidate.add_provenance("skills", self.SOURCE, "direct_extract")

        return candidate

    @staticmethod
    def _parse_location(location_str: str) -> Location:
        """
        Parse strings like 'San Francisco, CA' or 'Seattle, WA' into Location.
        Full normalisation (country codes etc.) happens in LocationNormalizer.
        """
        parts = [p.strip() for p in location_str.split(",")]
        city = parts[0] if len(parts) >= 1 else None
        region = parts[1] if len(parts) >= 2 else None
        country = parts[2] if len(parts) >= 3 else None
        return Location(city=city, region=region, country=country)
