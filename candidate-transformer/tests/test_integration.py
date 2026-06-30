"""
Tests for Phase 7 & 8: Output Projector, Schema Validator, and Integration flow.
"""
import os
import sys
import json
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models import Candidate, Skill
from src.projection import OutputConfig, OutputProjector, SchemaValidator, ValidationError


class TestIntegration(unittest.TestCase):
    def test_projector_and_validator(self):
        config_dict = {
            "fields": [
                {"path": "full_name", "type": "string", "required": True},
                {"path": "emails", "type": "string[]", "required": True},
                {"path": "overall_confidence", "type": "number", "required": False}
            ],
            "include_provenance": False,
            "include_confidence": True,
            "on_missing": "null"
        }
        
        config = OutputConfig(config_dict)

        candidate = Candidate(
            full_name="John Smith",
            emails=["john@smith.com"]
        )
        candidate.overall_confidence = 0.95

        projector = OutputProjector(config)
        projected = projector.project(candidate)

        self.assertEqual(projected["full_name"], "John Smith")
        self.assertEqual(projected["emails"], ["john@smith.com"])
        self.assertEqual(projected["overall_confidence"], 0.95)
        self.assertNotIn("provenance", projected)

        validator = SchemaValidator(config)
        validator.validate(projected)

        projected_invalid = projected.copy()
        projected_invalid["full_name"] = None
        with self.assertRaises(ValidationError):
            validator.validate(projected_invalid)

        projected_invalid_type = projected.copy()
        projected_invalid_type["overall_confidence"] = "high"
        with self.assertRaises(ValidationError):
            validator.validate(projected_invalid_type)

    def test_twist_configurable_projection(self):
        """
        Verify the required twist: remapping using 'from', per-field normalizations, 
        and missing values behaviors.
        """
        config_dict = {
            "fields": [
                {"path": "name", "from": "full_name", "type": "string", "required": True},
                {"path": "primary_email", "from": "emails[0]", "type": "string", "required": True},
                {"path": "phone", "from": "phones[0]", "type": "string", "normalize": "E.164"},
                {"path": "skills", "from": "skills[].name", "type": "string[]", "normalize": "canonical"},
                {"path": "missing_opt", "from": "headline", "type": "string", "required": False}
            ],
            "include_confidence": False,
            "on_missing": "omit"
        }
        config = OutputConfig(config_dict)
        
        candidate = Candidate(
            full_name="John Smith",
            emails=["john@smith.com"],
            phones=["555-0102"],
            skills=[Skill("js", 1.0, ["Resume"]), Skill("K8s", 0.9, ["Resume"])]
        )
        
        projector = OutputProjector(config)
        projected = projector.project(candidate)
        
        # Test 'from' key mappings
        self.assertEqual(projected["name"], "John Smith")
        self.assertEqual(projected["primary_email"], "john@smith.com")
        
        # Test per-field phone normalization
        self.assertEqual(projected["phone"], "+15550102")
        
        # Test per-field skill canonical mapping list projection
        self.assertEqual(projected["skills"], ["JavaScript", "Kubernetes"])
        
        # Test on_missing = "omit" for missing_opt (not included since it's None and not required)
        self.assertNotIn("missing_opt", projected)
        
        # Test on_missing = "error" for missing required field
        config_error_dict = config_dict.copy()
        config_error_dict["on_missing"] = "error"
        config_error = OutputConfig(config_error_dict)
        
        candidate_missing = Candidate(full_name="No Email")
        projector_err = OutputProjector(config_error)
        with self.assertRaises(ValidationError):
            projector_err.project(candidate_missing)

    def test_pipeline_integration(self):
        config_path = os.path.join(PROJECT_ROOT, "config", "output-config.json")
        if not os.path.exists(config_path):
            self.skipTest("output-config.json file missing")
            
        config = OutputConfig(config_path)
        self.assertTrue(len(config.fields) > 0)


if __name__ == "__main__":
    unittest.main()
