"""
Date Normalizer - Standardizes dates to YYYY-MM-DD or YYYY-MM format.
"""
import re
from typing import Optional
from dateutil import parser

class DateNormalizer:
    """
    Standardizes candidate dates using dateutil parser.
    """

    def normalize(self, date_str: str) -> Optional[str]:
        """
        Normalize standard date format to YYYY-MM-DD.
        """
        if not date_str:
            return None
        
        cleaned = date_str.strip().lower()
        if cleaned in ["present", "current", "now", "present)", "current)"]:
            return None
            
        try:
            # Parse using dateutil
            dt = parser.parse(date_str)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

        # Regex fallback for YYYY-MM
        match_ym = re.search(r"\b(\d{4})[-–/](\d{2})\b", date_str)
        if match_ym:
            return f"{match_ym.group(1)}-{match_ym.group(2)}-01"

        # Regex fallback for YYYY
        match_y = re.search(r"\b(\d{4})\b", date_str)
        if match_y:
            return f"{match_y.group(1)}-01-01"

        return date_str

    def normalize_to_year_month(self, date_str: str) -> Optional[str]:
        """
        Normalize dates specifically for resume/experience start and end dates (YYYY-MM).
        """
        if not date_str:
            return None
            
        cleaned = date_str.strip().lower()
        if cleaned in ["present", "current", "now", "present)", "current)"]:
            return None

        # If it is already in format YYYY-MM or YYYY-MM-DD, try to extract YYYY-MM directly
        match_ym = re.match(r"^(\d{4})[-–/](\d{2})", date_str)
        if match_ym:
            return f"{match_ym.group(1)}-{match_ym.group(2)}"

        normalized = self.normalize(date_str)
        if normalized and len(normalized) >= 7:
            # Check if it has YYYY-MM-DD structure
            if re.match(r"^\d{4}-\d{2}-\d{2}$", normalized):
                return normalized[:7]
            
        return normalized
