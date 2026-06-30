"""
Experience model - professional work experience
"""
from typing import Optional
from datetime import datetime


class Experience:
    """Represents a professional work experience"""
    
    def __init__(self, 
                 company: str,
                 title: str,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 summary: Optional[str] = None):
        """
        Initialize experience
        
        Args:
            company: Company/employer name
            title: Job title
            start_date: Start date (format: YYYY-MM)
            end_date: End date (format: YYYY-MM) or None if current
            summary: Job description/summary
        """
        self.company = company
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.summary = summary
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "company": self.company,
            "title": self.title,
            "start": self.start_date,
            "end": self.end_date,
            "summary": self.summary
        }
    
    def is_current(self) -> bool:
        """Check if this is current employment"""
        return self.end_date is None
    
    def __repr__(self):
        return f"Experience(company={self.company}, title={self.title}, current={self.is_current()})"
