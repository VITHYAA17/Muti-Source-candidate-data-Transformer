"""
ATS JSON Parser - Parses ats_data.json into List[Candidate]

ATS systems export data with non-standard field names, e.g.:
  candidate_name  → full_name
  contact_email   → emails
  contact_phone   → phones
  current_employer / job_title → experience
  location_city / location_state → location

This parser uses a field-mapping table so it can adapt to different
ATS schemas without changing the core logic.
"""
import json
import uuid
import logging
from typing import List, Dict, Any

from ..models import Candidate, Experience, Location

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ATS field-name mapping  →  canonical field
# Add more aliases here when integrating a new ATS system.
# ---------------------------------------------------------------------------
FIELD_MAP: Dict[str, str] = {
    # Name
    "candidate_name": "full_name",
    "applicant_name": "full_name",
    "full_name": "full_name",
    "name": "full_name",

    # Email
    "contact_email": "emails",
    "email_address": "emails",
    "email": "emails",

    # Phone
    "contact_phone": "phones",
    "phone_number": "phones",
    "phone": "phones",

    # Company / Title (merged into experience)
    "current_employer": "company",
    "employer": "company",
    "company": "company",
    "job_title": "title",
    "current_title": "title",
    "title": "title",

    # Location parts
    "location_city": "city",
    "city": "city",
    "location_state": "region",
    "state": "region",
    "location_country": "country",
    "country": "country",

    # Years
    "years_at_company": "years_experience",
    "years_experience": "years_experience",
}


class JsonParser:
    """
    Parses an ATS JSON export (ats_data.json) into Candidate objects.

    Expects a top-level key ``"candidates"`` whose value is a list of objects.
    """

    SOURCE = "ATS"

    def parse(self, filepath: str) -> List[Candidate]:
        """
        Parse an ATS JSON file and return a list of Candidate objects.

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
            logger.error("ATS JSON file not found: %s", filepath)
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
                logger.warning("ATS record %d skipped: %s", idx, e)

        logger.info("ATS JSON parser extracted %d candidates from %s", len(candidates), filepath)
        return candidates

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_record(self, record: Dict[str, Any]):
        """Map one ATS record dict to a Candidate."""

        # Remap all keys to canonical names
        mapped = self._remap(record)

        full_name = mapped.get("full_name", "").strip()
        email = mapped.get("emails", "").strip()

        if not full_name and not email:
            logger.warning("ATS record has no name or email – skipping: %s", record)
            return None

        candidate = Candidate(
            candidate_id=str(uuid.uuid4()),
            source=self.SOURCE,
        )

        # ── Full name ──────────────────────────────────────────────────
        if full_name:
            candidate.full_name = full_name
            candidate.add_provenance("full_name", self.SOURCE, "field_mapping")

        # ── Email ─────────────────────────────────────────────────────
        if email:
            candidate.emails = [email]
            candidate.add_provenance("emails", self.SOURCE, "field_mapping")

        # ── Phone ─────────────────────────────────────────────────────
        phone = mapped.get("phones", "").strip()
        if phone:
            candidate.phones = [phone]
            candidate.add_provenance("phones", self.SOURCE, "field_mapping")

        # ── Location ──────────────────────────────────────────────────
        city = mapped.get("city", "").strip()
        region = mapped.get("region", "").strip()
        country = mapped.get("country", "").strip()
        if city or region or country:
            candidate.location = Location(
                city=city or None,
                region=region or None,
                country=country or None,
            )
            candidate.add_provenance("location", self.SOURCE, "field_mapping")

        # ── Experience (employer + title) ──────────────────────────────
        company = mapped.get("company", "").strip()
        title = mapped.get("title", "").strip()
        if company or title:
            exp = Experience(company=company or "", title=title or "")
            candidate.experience = [exp]
            candidate.add_provenance("experience", self.SOURCE, "field_mapping")

        # ── Years of experience ────────────────────────────────────────
        years = mapped.get("years_experience")
        if years is not None:
            try:
                candidate.years_experience = int(years)
                candidate.add_provenance("years_experience", self.SOURCE, "field_mapping")
            except (ValueError, TypeError):
                logger.warning("Cannot parse years_experience: %s", years)

        return candidate

    def _remap(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert ATS-specific field names to canonical names using FIELD_MAP.
        Unknown fields are carried through as-is (lowercased key).
        """
        result: Dict[str, Any] = {}
        for raw_key, value in record.items():
            canonical = FIELD_MAP.get(raw_key.lower(), raw_key.lower())
            # For multi-valued canonical targets that could clash
            # (e.g. two ATS fields both map to "full_name"), first wins.
            if canonical not in result:
                result[canonical] = value
        return result
