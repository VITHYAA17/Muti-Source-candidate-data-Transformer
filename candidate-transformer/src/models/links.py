"""
Links model - professional profile links
"""
from typing import Optional, List


class Links:
    """Represents professional profile links"""
    
    def __init__(self,
                 linkedin: Optional[str] = None,
                 github: Optional[str] = None,
                 portfolio: Optional[str] = None,
                 other: Optional[List[str]] = None):
        """
        Initialize links
        
        Args:
            linkedin: LinkedIn profile URL
            github: GitHub profile URL
            portfolio: Portfolio/personal website URL
            other: List of other profile URLs
        """
        self.linkedin = linkedin
        self.github = github
        self.portfolio = portfolio
        self.other = other or []
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "linkedin": self.linkedin,
            "github": self.github,
            "portfolio": self.portfolio,
            "other": self.other
        }
    
    def __repr__(self):
        return f"Links(linkedin={bool(self.linkedin)}, github={bool(self.github)}, portfolio={bool(self.portfolio)})"
    
    def __bool__(self):
        """Check if any links exist"""
        return any([self.linkedin, self.github, self.portfolio, self.other])
