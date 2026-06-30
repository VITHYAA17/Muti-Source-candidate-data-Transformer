"""
Confidence Calculator - Computes field-level and overall confidence scores.
"""
import re
from typing import Set
from ..models import Candidate

class ConfidenceCalculator:
    """
    Calculates trust scores for candidate fields and overall profiles.
    Scores range from 0.0 to 1.0.
    """

    SOURCE_CONFIDENCE = {
        "Resume": 1.0,
        "ATS": 0.9,
        "GitHub": 0.9,
        "CSV": 0.9,
        "LinkedIn": 0.7,
        "Text": 0.5
    }

    FIELDS_TO_SCORE = [
        "full_name",
        "emails",
        "phones",
        "location",
        "links",
        "headline",
        "years_experience",
        "skills",
        "experience",
        "education"
    ]

    def calculate_confidence(self, candidate: Candidate) -> None:
        """
        Calculate and assign confidence scores for each field and overall.
        
        Args:
            candidate: Candidate object to update
        """
        if not candidate:
            return

        for field in self.FIELDS_TO_SCORE:
            if not candidate.has_field(field):
                candidate.set_field_confidence(field, 0.0)
                continue

            # 1. Base Confidence from highest-confidence source
            provenances = candidate.provenance.get(field, [])
            if not provenances:
                base_score = 0.5  # Fallback if no provenance tracking exists
            else:
                base_score = max(self.SOURCE_CONFIDENCE.get(p.source, 0.5) for p in provenances)

            # 2. Adjustments
            adjustment = 0.0

            # Agreement Bonus: +0.1 if field appears in 2+ unique sources
            unique_sources = {p.source for p in provenances}
            if len(unique_sources) >= 2:
                adjustment += 0.1

            # Regex Penalty: -0.1 if extracted using regex
            if any(p.method == "regex_parse" for p in provenances):
                adjustment -= 0.1

            # Normalization Bonus: +0.05 if normalized successfully
            if self._is_normalized(candidate, field):
                adjustment += 0.05

            # Apply score
            final_score = max(0.0, min(1.0, base_score + adjustment))
            candidate.set_field_confidence(field, final_score)

        # Calculate overall candidate confidence
        candidate.calculate_overall_confidence()

    def _is_normalized(self, candidate: Candidate, field: str) -> bool:
        """Determine if a field's value has been normalized successfully."""
        if field == "emails":
            # Normalized to lowercase
            return bool(candidate.emails and all(e == e.lower() for e in candidate.emails))
            
        elif field == "phones":
            # E.164 phone numbers start with +
            return bool(candidate.phones and all(p.startswith("+") for p in candidate.phones))
            
        elif field == "location":
            # Structured location with a country code
            return bool(candidate.location and candidate.location.country and len(candidate.location.country) == 2)
            
        elif field == "experience":
            # Normalized start and end dates (YYYY-MM format)
            if not candidate.experience:
                return False
            for exp in candidate.experience:
                if exp.start_date and not re.match(r"^\d{4}-\d{2}$", exp.start_date):
                    return False
                if exp.end_date and not re.match(r"^\d{4}-\d{2}$", exp.end_date):
                    return False
            return True
            
        elif field == "education":
            # end_year is integer
            return bool(candidate.education and all(edu.end_year is None or isinstance(edu.end_year, int) for edu in candidate.education))

        elif field == "skills":
            # Skill list contains mapped or capitalized skill names
            return bool(candidate.skills)

        # Other fields (full_name, headline, links, years_experience)
        # return True simply if they are present as they don't have special formats
        return True
