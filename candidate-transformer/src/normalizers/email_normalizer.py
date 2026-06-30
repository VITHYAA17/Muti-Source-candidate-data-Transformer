"""
Email Normalizer - Normalizes email addresses.
"""
from typing import Optional

class EmailNormalizer:
    """
    Standardizes email addresses (lowercasing and stripping whitespace).
    """

    def normalize(self, email_str: str) -> Optional[str]:
        """
        Normalize email address.
        """
        if not email_str:
            return None
        return email_str.strip().lower()
