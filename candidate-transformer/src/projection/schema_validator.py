"""
Schema Validator - Validates candidate dictionaries against OutputConfig rules.
"""
from typing import Any, Dict, List
from .output_config import OutputConfig

class ValidationError(Exception):
    """Exception raised when candidate data does not conform to the schema."""
    pass

class SchemaValidator:
    """
    Validates projected candidate dictionaries against output config rules.
    """

    def __init__(self, config: OutputConfig):
        """
        Initialize the validator with OutputConfig.
        """
        self.config = config

    def validate(self, candidate_dict: Dict[str, Any]) -> None:
        """
        Validate a candidate dictionary.
        Raises ValidationError if any check fails.
        """
        fields_config = self.config.fields
        
        for f_cfg in fields_config:
            path = f_cfg.get("path")
            if not path:
                continue

            required = f_cfg.get("required", False)
            expected_type = f_cfg.get("type")

            # Check if field exists in candidate dict
            val_exists = path in candidate_dict
            val = candidate_dict.get(path)

            # Check required fields
            if required:
                if not val_exists or val is None or val == "" or val == []:
                    raise ValidationError(f"Required field '{path}' is missing or empty")

            # Skip type check if value is null and not required
            if val is None:
                continue

            # Check types
            if expected_type == "string":
                if not isinstance(val, str):
                    raise ValidationError(f"Field '{path}' must be a string, got {type(val).__name__}")
                    
            elif expected_type == "number":
                if not isinstance(val, (int, float)):
                    raise ValidationError(f"Field '{path}' must be a number, got {type(val).__name__}")
                    
            elif expected_type == "string[]":
                if not isinstance(val, list):
                    raise ValidationError(f"Field '{path}' must be a list of strings, got {type(val).__name__}")
                for idx, item in enumerate(val):
                    if not isinstance(item, str):
                        raise ValidationError(f"Field '{path}[{idx}]' must be a string, got {type(item).__name__}")
                        
            elif expected_type == "array":
                if not isinstance(val, list):
                    raise ValidationError(f"Field '{path}' must be an array (list), got {type(val).__name__}")
                
                # Check list items if specified in config
                items_config = f_cfg.get("items")
                if items_config and val:
                    for idx, item in enumerate(val):
                        if not isinstance(item, dict):
                            raise ValidationError(f"Item at '{path}[{idx}]' must be a dictionary (object)")
                        self._validate_nested_object(item, items_config, f"{path}[{idx}]")
                        
            elif expected_type == "object":
                if not isinstance(val, dict):
                    raise ValidationError(f"Field '{path}' must be an object (dict), got {type(val).__name__}")
                
                # Check object properties if specified in config
                props_config = f_cfg.get("properties")
                if props_config:
                    self._validate_nested_object(val, props_config, path)

    def validate_all(self, candidate_dicts: List[Dict[str, Any]]) -> None:
        """Validate a list of candidate dictionaries."""
        for c_dict in candidate_dicts:
            self.validate(c_dict)

    def _validate_nested_object(self, obj: Dict[str, Any], schema: Dict[str, Any], parent_path: str) -> None:
        """Helper to validate keys inside nested dicts against type rules."""
        for prop_name, prop_type in schema.items():
            if isinstance(prop_type, str):
                val = obj.get(prop_name)
                if val is None:
                    continue
                
                if prop_type == "string":
                    if not isinstance(val, str):
                        raise ValidationError(f"Nested field '{parent_path}.{prop_name}' must be a string, got {type(val).__name__}")
                elif prop_type == "number":
                    if not isinstance(val, (int, float)):
                        raise ValidationError(f"Nested field '{parent_path}.{prop_name}' must be a number, got {type(val).__name__}")
                elif prop_type == "string[]":
                    if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
                        raise ValidationError(f"Nested field '{parent_path}.{prop_name}' must be a list of strings")
