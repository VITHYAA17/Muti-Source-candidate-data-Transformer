"""
Output Projector - Transforms canonical Candidate objects using OutputConfig.
"""
import re
from typing import Any, Dict, List, Union
from ..models import Candidate
from .output_config import OutputConfig
from .schema_validator import ValidationError
from ..normalizers import PhoneNormalizer, SkillNormalizer

class OutputProjector:
    """
    Applies projection rules from an OutputConfig to Candidate profiles.
    Supports field remapping (using the "from" property), per-field normalization,
    and missing values behavior (null, omit, or error).
    """

    def __init__(self, config: OutputConfig):
        """
        Initialize the projector.
        """
        self.config = config
        self.phone_normalizer = PhoneNormalizer()
        self.skill_normalizer = SkillNormalizer()

    def project(self, candidate: Candidate) -> Dict[str, Any]:
        """
        Project a single Candidate object into a dictionary.
        """
        output = {}
        fields_config = self.config.fields
        include_provenance = self.config.include_provenance
        include_confidence = self.config.include_confidence
        on_missing = self.config.on_missing

        for f_cfg in fields_config:
            path = f_cfg.get("path")
            source_path = f_cfg.get("from")
            required = f_cfg.get("required", False)
            norm_type = f_cfg.get("normalize")

            if not path:
                continue

            # Skip metadata fields if globally disabled
            if path == "provenance" and not include_provenance:
                continue
            if path == "overall_confidence" and not include_confidence:
                continue

            # 1. Resolve raw value from source path or path
            lookup_path = source_path if source_path else path
            val = self._resolve_path(candidate, lookup_path)

            # 2. Apply per-field normalization if specified
            if val and norm_type:
                val = self._apply_normalization(val, norm_type)

            # 3. Handle missing values
            if self._is_empty(val):
                if required or on_missing == "error":
                    raise ValidationError(f"Required projected field '{path}' is missing or empty")
                elif on_missing == "omit":
                    continue
                else:  # "null" is default
                    output[path] = None
                    continue

            output[path] = val

        return output

    def project_all(self, candidates: List[Candidate]) -> List[Dict[str, Any]]:
        """Project a list of candidate objects."""
        return [self.project(c) for c in candidates]

    def _resolve_path(self, candidate: Candidate, path: str) -> Any:
        """
        Extracts values based on direct/nested/indexed paths.
        E.g., "emails[0]"
        E.g., "skills[].name"
        E.g., "location.city"
        """
        if not path:
            return None

        # 1. Array index lookup like "emails[0]" or "phones[0]"
        match_idx = re.match(r"^(\w+)\[(\d+)\]$", path)
        if match_idx:
            attr = match_idx.group(1)
            idx = int(match_idx.group(2))
            val_list = getattr(candidate, attr, None)
            if val_list and isinstance(val_list, list) and len(val_list) > idx:
                return val_list[idx]
            return None

        # 2. Nested array mapping like "skills[].name"
        if "[]" in path:
            parts = path.split("[].")
            base_attr = parts[0]
            sub_attr = parts[1] if len(parts) > 1 else None
            
            base_val = getattr(candidate, base_attr, None)
            if not base_val or not isinstance(base_val, list):
                return []
                
            if sub_attr:
                mapped_list = []
                for item in base_val:
                    # Check if it has the attribute (e.g. s.name)
                    if hasattr(item, sub_attr):
                        mapped_list.append(getattr(item, sub_attr))
                    elif isinstance(item, dict) and sub_attr in item:
                        mapped_list.append(item[sub_attr])
                return mapped_list
            return base_val

        # 3. Nested object path like "location.city"
        if "." in path:
            parts = path.split(".")
            val = candidate
            for p in parts:
                if hasattr(val, p):
                    val = getattr(val, p)
                elif isinstance(val, dict) and p in val:
                    val = val[p]
                else:
                    return None
            return val

        # 4. Standard mapping for structured model conversions
        if path == "location":
            if candidate.location and (candidate.location.city or candidate.location.region or candidate.location.country):
                return candidate.location.to_dict()
            return None
        elif path == "links":
            if candidate.links and (candidate.links.linkedin or candidate.links.github or candidate.links.portfolio or candidate.links.other):
                return candidate.links.to_dict()
            return None
        elif path == "skills":
            return [s.to_dict() for s in candidate.skills] if candidate.skills else []
        elif path == "experience":
            return [e.to_dict() for e in candidate.experience] if candidate.experience else []
        elif path == "education":
            return [ed.to_dict() for ed in candidate.education] if candidate.education else []
        elif path == "provenance":
            prov_list = []
            for plist in candidate.provenance.values():
                for p in plist:
                    prov_list.append(p.to_dict())
            return prov_list

        # Direct attribute lookup
        if hasattr(candidate, path):
            return getattr(candidate, path)
            
        return None

    def _apply_normalization(self, val: Any, norm_type: str) -> Any:
        """Applies normalization of type E164 or canonical to strings/lists."""
        norm_type_clean = norm_type.replace(".", "").lower() # e.g. E.164 -> e164
        
        if norm_type_clean == "e164":
            if isinstance(val, list):
                return [self.phone_normalizer.normalize(x) for x in val if x]
            elif isinstance(val, str):
                return self.phone_normalizer.normalize(val)
                
        elif norm_type_clean == "canonical":
            if isinstance(val, list):
                return [self.skill_normalizer.normalize(x) for x in val if x]
            elif isinstance(val, str):
                return self.skill_normalizer.normalize(val)
                
        return val

    def _is_empty(self, val: Any) -> bool:
        """Check if value is missing/empty."""
        if val is None:
            return True
        if isinstance(val, (list, dict)) and not val:
            return True
        if isinstance(val, str) and not val.strip():
            return True
        return False
