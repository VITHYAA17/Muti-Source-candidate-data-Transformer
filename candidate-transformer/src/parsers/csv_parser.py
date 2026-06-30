"""
CSV Parser - Parses recruiter.csv into List[Candidate]

Handles structured CSV rows with columns:
Name, Email, Phone, Company, Title, Location
"""
import csv
import uuid
import logging
from typing import List

from ..models import Candidate, Experience, Location

logger = logging.getLogger(__name__)


class CsvParser:
    """
    Parses recruiter CSV export into Candidate objects.

    Expected columns (case-insensitive):
        Name, Email, Phone, Company, Title, Location
    """

    SOURCE = "CSV"

    def parse(self, filepath: str) -> List[Candidate]:
        """
        Parse a CSV file and return a list of Candidate objects.

        Args:
            filepath: Path to the .csv file

        Returns:
            List of Candidate objects (one per valid row)
        """
        candidates = []

        try:
            with open(filepath, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Normalise column headers to lowercase stripped strings
                # so the parser is tolerant of minor header variations
                reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

                for row_num, row in enumerate(reader, start=2):  # row 1 is header
                    try:
                        candidate = self._parse_row(row, row_num)
                        if candidate:
                            candidates.append(candidate)
                    except Exception as e:
                        logger.warning(
                            "CSV row %d skipped due to error: %s", row_num, e
                        )

        except FileNotFoundError:
            logger.error("CSV file not found: %s", filepath)
        except Exception as e:
            logger.error("Failed to read CSV file %s: %s", filepath, e)

        logger.info("CSV parser extracted %d candidates from %s", len(candidates), filepath)
        return candidates

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_row(self, row: dict, row_num: int):
        """Parse a single CSV row into a Candidate."""

        name = self._get(row, "name")
        email = self._get(row, "email")

        # A row must have at least a name or email to be useful
        if not name and not email:
            logger.warning("CSV row %d has no name or email – skipping", row_num)
            return None

        candidate = Candidate(
            candidate_id=str(uuid.uuid4()),
            source=self.SOURCE,
        )

        # ── Full name ──────────────────────────────────────────────────
        if name:
            candidate.full_name = name.strip()
            candidate.add_provenance("full_name", self.SOURCE, "direct_extract")

        # ── Email ─────────────────────────────────────────────────────
        if email:
            candidate.emails = [email.strip()]
            candidate.add_provenance("emails", self.SOURCE, "direct_extract")

        # ── Phone ─────────────────────────────────────────────────────
        phone = self._get(row, "phone")
        if phone:
            candidate.phones = [phone.strip()]
            candidate.add_provenance("phones", self.SOURCE, "direct_extract")

        # ── Location (raw string – will be normalised later) ───────────
        location_str = self._get(row, "location")
        if location_str:
            candidate.location = self._parse_location_string(location_str.strip())
            candidate.add_provenance("location", self.SOURCE, "direct_extract")

        # ── Experience (company + title from CSV) ──────────────────────
        company = self._get(row, "company")
        title = self._get(row, "title")
        if company or title:
            exp = Experience(
                company=company.strip() if company else "",
                title=title.strip() if title else "",
            )
            candidate.experience = [exp]
            candidate.add_provenance("experience", self.SOURCE, "direct_extract")

        return candidate

    def _parse_location_string(self, location_str: str) -> Location:
        """
        Best-effort parse of a bare location string like 'Mountain View'
        or 'Seattle, WA'.  Full normalisation happens in LocationNormalizer.
        """
        parts = [p.strip() for p in location_str.split(",")]
        city = parts[0] if len(parts) >= 1 else None
        region = parts[1] if len(parts) >= 2 else None
        country = parts[2] if len(parts) >= 3 else None
        return Location(city=city, region=region, country=country)

    @staticmethod
    def _get(row: dict, key: str) -> str:
        """Safely retrieve a value from the row dict, returning '' if missing."""
        return (row.get(key) or "").strip()
