# normalizers package
from .phone_normalizer import PhoneNormalizer
from .email_normalizer import EmailNormalizer
from .date_normalizer import DateNormalizer
from .skill_normalizer import SkillNormalizer
from .location_normalizer import LocationNormalizer

__all__ = [
    "PhoneNormalizer",
    "EmailNormalizer",
    "DateNormalizer",
    "SkillNormalizer",
    "LocationNormalizer",
    "CandidateNormalizer"
]

class CandidateNormalizer:
    """Orchestrates all field normalizers on a Candidate object."""
    
    def __init__(self):
        self.phone_normalizer = PhoneNormalizer()
        self.email_normalizer = EmailNormalizer()
        self.date_normalizer = DateNormalizer()
        self.skill_normalizer = SkillNormalizer()
        self.location_normalizer = LocationNormalizer()

    def normalize(self, candidate) -> None:
        """
        Normalize all fields on a candidate in-place.
        """
        if not candidate:
            return

        # Emails
        if candidate.emails:
            normalized_emails = []
            for email in candidate.emails:
                norm_email = self.email_normalizer.normalize(email)
                if norm_email:
                    normalized_emails.append(norm_email)
            # Remove duplicates while preserving order
            candidate.emails = list(dict.fromkeys(normalized_emails))

        # Phones
        if candidate.phones:
            normalized_phones = []
            for phone in candidate.phones:
                norm_phone = self.phone_normalizer.normalize(phone)
                if norm_phone:
                    normalized_phones.append(norm_phone)
            # Remove duplicates while preserving order
            candidate.phones = list(dict.fromkeys(normalized_phones))

        # Location
        if candidate.location:
            candidate.location = self.location_normalizer.normalize(candidate.location)

        # Headline (simple trim)
        if candidate.headline:
            candidate.headline = candidate.headline.strip()

        # Skills
        if candidate.skills:
            for skill in candidate.skills:
                skill.name = self.skill_normalizer.normalize(skill.name)

        # Experience
        if candidate.experience:
            for exp in candidate.experience:
                if exp.company:
                    exp.company = exp.company.strip()
                if exp.title:
                    exp.title = exp.title.strip()
                if exp.start_date:
                    exp.start_date = self.date_normalizer.normalize_to_year_month(exp.start_date)
                if exp.end_date:
                    exp.end_date = self.date_normalizer.normalize_to_year_month(exp.end_date)
                if exp.summary:
                    exp.summary = exp.summary.strip()

        # Education
        if candidate.education:
            for edu in candidate.education:
                if edu.institution:
                    edu.institution = edu.institution.strip()
                if edu.degree:
                    edu.degree = edu.degree.strip()
                if edu.field:
                    edu.field = edu.field.strip()
                # end_year should be integer. If it's a string, cast it
                if edu.end_year is not None and not isinstance(edu.end_year, int):
                    try:
                        edu.end_year = int(edu.end_year)
                    except ValueError:
                        edu.end_year = None
