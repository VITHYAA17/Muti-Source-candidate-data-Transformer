"""
Education model - academic background
"""
from typing import Optional


class Education:
    """Represents a candidate's education"""
    
    def __init__(self, 
                 institution: str,
                 degree: Optional[str] = None,
                 field: Optional[str] = None,
                 end_year: Optional[int] = None):
        """
        Initialize education
        
        Args:
            institution: School/university name
            degree: Degree type (B.S., M.S., PhD, etc.)
            field: Field of study
            end_year: Graduation year (YYYY format)
        """
        self.institution = institution
        self.degree = degree
        self.field = field
        self.end_year = end_year
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "institution": self.institution,
            "degree": self.degree,
            "field": self.field,
            "end_year": self.end_year
        }
    
    def __repr__(self):
        return f"Education(institution={self.institution}, degree={self.degree}, field={self.field})"
