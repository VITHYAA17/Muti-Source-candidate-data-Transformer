"""
Main Candidate model - core data structure with all 13 canonical fields
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from .skill import Skill
from .experience import Experience
from .education import Education
from .location import Location
from .links import Links
from .provenance import Provenance


class Candidate:
    """
    Core candidate data model with all 13 canonical fields.
    Tracks provenance (where data came from) and confidence scores.
    """
    
    def __init__(self, 
                 candidate_id: Optional[str] = None,
                 full_name: Optional[str] = None,
                 emails: Optional[List[str]] = None,
                 phones: Optional[List[str]] = None,
                 location: Optional[Location] = None,
                 links: Optional[Links] = None,
                 headline: Optional[str] = None,
                 years_experience: Optional[int] = None,
                 skills: Optional[List[Skill]] = None,
                 experience: Optional[List[Experience]] = None,
                 education: Optional[List[Education]] = None,
                 source: Optional[str] = None):
        """
        Initialize candidate with all canonical fields
        
        Args:
            candidate_id: Unique identifier
            full_name: Full name
            emails: List of email addresses
            phones: List of phone numbers (should be normalized to E.164)
            location: Location object {city, region, country}
            links: Links object {linkedin, github, portfolio, other}
            headline: Professional headline
            years_experience: Years of experience
            skills: List of Skill objects
            experience: List of Experience objects
            education: List of Education objects
            source: Data source (CSV, GitHub, LinkedIn, Resume, Text, ATS)
        """
        # Canonical fields (13 total)
        self.candidate_id = candidate_id
        self.full_name = full_name
        self.emails = emails or []
        self.phones = phones or []
        self.location = location or Location()
        self.links = links or Links()
        self.headline = headline
        self.years_experience = years_experience
        self.skills = skills or []
        self.experience = experience or []
        self.education = education or []
        
        # Metadata
        self.source = source  # CSV, GitHub, LinkedIn, Resume, Text, ATS
        
        # Provenance tracking: field_name → List[Provenance]
        self.provenance: Dict[str, List[Provenance]] = {}
        
        # Confidence scores: field_name → confidence (0.0-1.0)
        self.field_confidence: Dict[str, float] = {}
        self.overall_confidence: float = 0.0
    
    def add_provenance(self, field: str, source: str, method: str):
        """
        Track where a field value came from
        
        Args:
            field: Field name
            source: Data source
            method: Extraction method
        """
        if field not in self.provenance:
            self.provenance[field] = []
        self.provenance[field].append(Provenance(field, source, method))
    
    def set_field_confidence(self, field: str, confidence: float):
        """
        Set confidence score for a field
        
        Args:
            field: Field name
            confidence: Confidence score 0.0-1.0
        """
        self.field_confidence[field] = max(0.0, min(1.0, confidence))
    
    def calculate_overall_confidence(self):
        """Calculate overall confidence as average of field confidences"""
        if not self.field_confidence:
            self.overall_confidence = 0.0
        else:
            self.overall_confidence = sum(self.field_confidence.values()) / len(self.field_confidence)
    
    def has_field(self, field_name: str) -> bool:
        """Check if a field has a value"""
        field_map = {
            'candidate_id': self.candidate_id,
            'full_name': self.full_name,
            'emails': self.emails,
            'phones': self.phones,
            'location': bool(self.location),
            'links': bool(self.links),
            'headline': self.headline,
            'years_experience': self.years_experience,
            'skills': bool(self.skills),
            'experience': bool(self.experience),
            'education': bool(self.education),
        }
        return bool(field_map.get(field_name))
    
    def add_skill(self, skill: Skill):
        """Add skill, avoiding duplicates (case-insensitive)"""
        for existing_skill in self.skills:
            if existing_skill == skill:
                # Merge sources
                for source in skill.sources:
                    existing_skill.add_source(source)
                # Use higher confidence
                existing_skill.confidence = max(existing_skill.confidence, skill.confidence)
                return
        self.skills.append(skill)
    
    def to_dict(self, 
                include_provenance: bool = True, 
                include_confidence: bool = True) -> dict:
        """
        Convert candidate to dictionary (canonical format)
        
        Args:
            include_provenance: Include provenance tracking
            include_confidence: Include confidence scores
            
        Returns:
            Dictionary with all candidate data
        """
        data = {
            "candidate_id": self.candidate_id,
            "full_name": self.full_name,
            "emails": self.emails,
            "phones": self.phones,
            "location": self.location.to_dict() if self.location else None,
            "links": self.links.to_dict() if self.links else None,
            "headline": self.headline,
            "years_experience": self.years_experience,
            "skills": [s.to_dict() for s in self.skills],
            "experience": [e.to_dict() for e in self.experience],
            "education": [ed.to_dict() for ed in self.education]
        }
        
        if include_provenance:
            data["provenance"] = [
                prov.to_dict() 
                for prov_list in self.provenance.values() 
                for prov in prov_list
            ]
        
        if include_confidence:
            data["field_confidence"] = self.field_confidence
            data["overall_confidence"] = self.overall_confidence
        
        return data
    
    def __repr__(self):
        email_str = self.emails[0] if self.emails else 'N/A'
        return f"Candidate(name={self.full_name}, email={email_str}, source={self.source})"
