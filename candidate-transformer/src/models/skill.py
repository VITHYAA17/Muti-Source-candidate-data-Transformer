"""
Skill model - professional skills with confidence tracking
"""
from typing import Optional, List


class Skill:
    """Represents a professional skill"""
    
    def __init__(self, 
                 name: str,
                 confidence: float = 0.0,
                 sources: Optional[List[str]] = None):
        """
        Initialize skill
        
        Args:
            name: Skill name (should be canonicalized)
            confidence: Confidence score 0.0-1.0
            sources: List of sources where this skill was found
        """
        self.name = name
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp to 0.0-1.0
        self.sources = sources or []
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "confidence": self.confidence,
            "sources": self.sources
        }
    
    def add_source(self, source: str):
        """Add a source if not already present"""
        if source not in self.sources:
            self.sources.append(source)
    
    def __repr__(self):
        return f"Skill(name={self.name}, confidence={self.confidence})"
    
    def __eq__(self, other):
        """Compare by canonical name (case-insensitive)"""
        if isinstance(other, Skill):
            return self.name.lower() == other.name.lower()
        return False
    
    def __hash__(self):
        """Hash by canonical name"""
        return hash(self.name.lower())
