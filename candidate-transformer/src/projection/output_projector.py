"""
Output Projector - Transforms canonical Candidate objects into JSON-ready dictionaries based on runtime configuration.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union
from ..models import Candidate

logger = logging.getLogger(__name__)

class OutputProjector:
    """
    Applies projection rules from a configuration file/dictionary to Candidates.
    Controls which fields are returned, their names, and inclusion of metadata.
    """

    def __init__(self, config_source: Union[str, Dict[str, Any]]):
        """
        Initialize the projector.
        
        Args:
            config_source: Path to JSON config file or config dictionary
        """
        if isinstance(config_source, str):
            try:
                with open(config_source, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.error("Failed to load output config from %s: %s", config_source, e)
                # Fallback empty config
                self.config = {"fields": [], "include_provenance": True, "include_confidence": True, "on_missing": "null"}
        else:
            self.config = config_source

    def project(self, candidate: Candidate) -> Dict[str, Any]:
        """
        Project a single candidate object into a dictionary.
        
        Args:
            candidate: Candidate object to project
            
        Returns:
            Projected dictionary representing the candidate
        """
        output = {}
        fields_config = self.config.get("fields", [])
        include_provenance = self.config.get("include_provenance", True)
        include_confidence = self.config.get("include_confidence", True)
        on_missing = self.config.get("on_missing", "null")

        for f_cfg in fields_config:
            path = f_cfg.get("path")
            if not path:
                continue

            # Skip provenance/confidence if globally disabled
            if path == "provenance" and not include_provenance:
                continue
            if path == "overall_confidence" and not include_confidence:
                continue

            # Extract raw value
            val = self._extract_value(candidate, path)

            # Handle missing fields
            if self._is_empty(val):
                if on_missing == "omit":
                    continue
                else:
                    output[path] = None
                    continue

            output[path] = val

        return output

    def project_all(self, candidates: List[Candidate]) -> List[Dict[str, Any]]:
        """Project a list of candidate objects."""
        return [self.project(c) for c in candidates]

    def _extract_value(self, candidate: Candidate, path: str) -> Any:
        """Helper to extract nested value from Candidate based on path name."""
        if path == "candidate_id":
            return candidate.candidate_id
        elif path == "full_name":
            return candidate.full_name
        elif path == "emails":
            return candidate.emails
        elif path == "phones":
            return candidate.phones
        elif path == "location":
            if candidate.location and (candidate.location.city or candidate.location.region or candidate.location.country):
                return candidate.location.to_dict()
            return None
        elif path == "links":
            if candidate.links and (candidate.links.linkedin or candidate.links.github or candidate.links.portfolio or candidate.links.other):
                return candidate.links.to_dict()
            return None
        elif path == "headline":
            return candidate.headline
        elif path == "years_experience":
            return candidate.years_experience
        elif path == "skills":
            return [s.to_dict() for s in candidate.skills] if candidate.skills else []
        elif path == "experience":
            return [e.to_dict() for e in candidate.experience] if candidate.experience else []
        elif path == "education":
            return [ed.to_dict() for ed in candidate.education] if candidate.education else []
        elif path == "provenance":
            # Flatten dict to list
            prov_list = []
            for plist in candidate.provenance.values():
                for p in plist:
                    prov_list.append(p.to_dict())
            return prov_list
        elif path == "overall_confidence":
            return candidate.overall_confidence
        return None

    def _is_empty(self, val: Any) -> bool:
        """Check if value is missing/empty."""
        if val is None:
            return True
        if isinstance(val, (list, dict)) and not val:
            return True
        return False
