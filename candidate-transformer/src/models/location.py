"""
Location model - structured geographic information
"""
from typing import Optional


class Location:
    """Represents a geographic location"""
    
    def __init__(self, 
                 city: Optional[str] = None,
                 region: Optional[str] = None,
                 country: Optional[str] = None):
        """
        Initialize location
        
        Args:
            city: City name (e.g., "San Francisco")
            region: Region/state code (e.g., "CA")
            country: Country code ISO-3166 alpha-2 (e.g., "US")
        """
        self.city = city
        self.region = region
        self.country = country
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "city": self.city,
            "region": self.region,
            "country": self.country
        }
    
    def to_string(self) -> str:
        """Convert to readable string format"""
        parts = [self.city, self.region, self.country]
        return ", ".join([p for p in parts if p])
    
    def __repr__(self):
        return f"Location(city={self.city}, region={self.region}, country={self.country})"
    
    def __bool__(self):
        """Check if location has any values"""
        return any([self.city, self.region, self.country])
