"""
Helpers - Common utility functions for the ETL pipeline.
"""
import re
from typing import Set, Optional

def clean_phone_digits(phone_str: str) -> str:
    """
    Remove all non-digit characters from a phone number string.
    """
    if not phone_str:
        return ""
    return "".join(c for c in phone_str if c.isdigit())

def clean_email(email_str: str) -> str:
    """
    Lowercase and strip whitespace from email.
    """
    if not email_str:
        return ""
    return email_str.strip().lower()

def safe_strip(val: Optional[str]) -> str:
    """
    Safely strip a string, returning an empty string if None.
    """
    if val is None:
        return ""
    return val.strip()
