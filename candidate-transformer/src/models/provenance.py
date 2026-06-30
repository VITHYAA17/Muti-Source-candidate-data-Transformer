"""
Provenance model - tracks data lineage
Where each field value came from and how it was extracted
"""
from typing import Optional
from datetime import datetime


class Provenance:
    """Tracks where each field value came from"""
    
    def __init__(self, 
                 field: str, 
                 source: str, 
                 method: str, 
                 extraction_date: Optional[datetime] = None):
        """
        Initialize provenance tracking
        
        Args:
            field: Field name (e.g., "full_name")
            source: Data source (CSV, GitHub, LinkedIn, Resume, Text, ATS)
            method: Extraction method (direct_extract, regex_parse, api_call, field_mapping)
            extraction_date: When the data was extracted
        """
        self.field = field
        self.source = source
        self.method = method
        self.extraction_date = extraction_date or datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "field": self.field,
            "source": self.source,
            "method": self.method,
            "extraction_date": self.extraction_date.isoformat()
        }
    
    def __repr__(self):
        return f"Provenance(field={self.field}, source={self.source}, method={self.method})"
    
    def __eq__(self, other):
        if isinstance(other, Provenance):
            return (self.field == other.field and 
                    self.source == other.source and 
                    self.method == other.method)
        return False
