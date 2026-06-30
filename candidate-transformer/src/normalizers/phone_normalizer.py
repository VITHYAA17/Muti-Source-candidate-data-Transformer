"""
Phone Normalizer - Normalizes phone numbers to E.164 format.
"""
import phonenumbers
from typing import Optional

class PhoneNormalizer:
    """
    Normalizes variations of phone numbers to standard E.164 format.
    E.g., +1-555-0101, 555-0101, (555) 0101 -> +15550101
    """

    def __init__(self, default_region: str = "US"):
        self.default_region = default_region

    def normalize(self, phone_str: str) -> Optional[str]:
        """
        Normalize phone string.
        Returns normalized string or original if parsing fails.
        """
        if not phone_str:
            return None
        
        cleaned = phone_str.strip()
        try:
            parsed = phonenumbers.parse(cleaned, self.default_region)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            pass

        # Fallback manual cleaning if phonenumbers library couldn't parse it
        digits_only = "".join(c for c in cleaned if c.isdigit())
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith("1"):
            return f"+{digits_only}"
        elif len(digits_only) == 7:
            return f"+1{digits_only}"
        elif len(digits_only) == 8 and digits_only.startswith("1"):
            return f"+{digits_only}"
        
        return cleaned
