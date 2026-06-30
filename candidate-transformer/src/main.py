"""
Candidate Data Transformer - Main ETL Pipeline Orchestrator.
"""
import json
import logging
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.parsers import CsvParser, JsonParser, GitHubParser, LinkedInParser, ResumeParser, TextParser
from src.normalizers import CandidateNormalizer
from src.merger import CandidateMatcher, CandidateMerger
from src.confidence import ConfidenceCalculator
from src.projection import OutputConfig, OutputProjector, SchemaValidator

# Set up logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main_pipeline")

def run_etl():
    """
    Runs the full ETL pipeline:
    Extract -> Normalize -> Merge -> Confidence -> Project -> Validate -> Load.
    """
    logger.info("Starting Candidate Data Transformer ETL Pipeline...")

    # Define paths
    input_dir = os.path.join(PROJECT_ROOT, "input")
    config_path = os.path.join(PROJECT_ROOT, "config", "output-config.json")
    output_path = os.path.join(PROJECT_ROOT, "output", "candidates_output.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 1. EXTRACT
    logger.info("Stage 1: Extracting raw candidate profiles from sources...")
    
    parsers = {
        "CSV": (CsvParser(), os.path.join(input_dir, "recruiter.csv")),
        "ATS": (JsonParser(), os.path.join(input_dir, "ats_data.json")),
        "GitHub": (GitHubParser(), os.path.join(input_dir, "github.json")),
        "LinkedIn": (LinkedInParser(), os.path.join(input_dir, "linkedin.json")),
        "Resume": (ResumeParser(), os.path.join(input_dir, "resume_sample.txt")),
        "Text": (TextParser(), os.path.join(input_dir, "recruiter_notes.txt")),
    }

    raw_candidates = []
    for source_name, (parser, filepath) in parsers.items():
        if not os.path.exists(filepath):
            logger.warning("Input file not found, skipping source %s: %s", source_name, filepath)
            continue
        try:
            parsed = parser.parse(filepath)
            logger.info("Extracted %d records from %s", len(parsed), source_name)
            raw_candidates.extend(parsed)
        except Exception as e:
            logger.error("Failed to parse source %s: %s", source_name, e)

    logger.info("Total raw candidates extracted: %d", len(raw_candidates))
    if not raw_candidates:
        logger.error("No candidate data extracted. Exiting pipeline.")
        return

    # 2. NORMALIZE
    logger.info("Stage 2: Normalizing candidate fields...")
    normalizer = CandidateNormalizer()
    for c in raw_candidates:
        normalizer.normalize(c)

    # 3. DEDUP & MERGE
    logger.info("Stage 3: Matching and merging duplicate profiles...")
    matcher = CandidateMatcher()
    merger = CandidateMerger()

    groups = matcher.match_candidates(raw_candidates)
    logger.info("Matched into %d unique candidate profiles", len(groups))

    merged_candidates = []
    for idx, group in enumerate(groups, start=1):
        merged = merger.merge_candidates(group)
        merged_candidates.append(merged)
        logger.info("Group %d merged: %s (from %d sources)", idx, merged.full_name, len(group))

    # 4. CONFIDENCE SCORING
    logger.info("Stage 4: Calculating confidence scores...")
    confidence_calc = ConfidenceCalculator()
    for mc in merged_candidates:
        confidence_calc.calculate_confidence(mc)

    # 5. OUTPUT CONFIG & PROJECTION
    logger.info("Stage 5: Applying output configuration & projection...")
    if not os.path.exists(config_path):
        logger.error("Output configuration file not found at %s. Exiting.", config_path)
        return

    # Load configuration wrapper
    config = OutputConfig(config_path)

    projector = OutputProjector(config)
    projected_profiles = projector.project_all(merged_candidates)

    # 6. SCHEMA VALIDATION
    logger.info("Stage 6: Validating schema correctness...")
    validator = SchemaValidator(config)
    try:
        validator.validate_all(projected_profiles)
        logger.info("Schema validation passed successfully for all profiles!")
    except Exception as e:
        logger.error("Schema validation failed: %s", e)

    # 7. LOAD (Save final output)
    logger.info("Stage 7: Loading (saving) canonical profiles...")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(projected_profiles, f, indent=2, ensure_ascii=False)
        logger.info("ETL pipeline complete! Final output written to: %s", output_path)
    except Exception as e:
        logger.error("Failed to write output to file: %s", e)

    # 8. CUSTOM CONFIG RUN (Deliverable: default + custom config)
    custom_config_path = os.path.join(PROJECT_ROOT, "config", "custom-config.json")
    custom_output_path = os.path.join(PROJECT_ROOT, "output", "custom_candidates_output.json")
    if os.path.exists(custom_config_path):
        logger.info("Running custom configuration pass...")
        try:
            custom_config = OutputConfig(custom_config_path)
            custom_projector = OutputProjector(custom_config)
            custom_projected = custom_projector.project_all(merged_candidates)
            
            custom_validator = SchemaValidator(custom_config)
            custom_validator.validate_all(custom_projected)
            
            with open(custom_output_path, "w", encoding="utf-8") as f:
                json.dump(custom_projected, f, indent=2, ensure_ascii=False)
            logger.info("Custom configuration pass complete! Custom output written to: %s", custom_output_path)
        except Exception as e:
            logger.error("Custom config pass failed: %s", e)

if __name__ == "__main__":
    run_etl()
