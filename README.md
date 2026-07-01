Candidate Data Transformer
A Python-based ETL pipeline to merge candidate data from multiple sources (CSV, ATS JSON, GitHub, LinkedIn, Resume, Text) into one clean canonical profile with provenance tracking, confidence scoring, runtime custom remapping/projections, and an interactive local UI dashboard.

Overview
This application transforms messy, conflicting candidate data from multiple sources into a single unified profile following a canonical schema with:

Normalized formats (E.164 phones, ISO-3166 countries, YYYY-MM dates, canonical skills)
Provenance tracking (tracks field-level data lineage)
Confidence scoring (per-field and overall profile trust scoring)
Conflict resolution (priority-based merging)
Runtime configurability (control output schema path selection, remapping, format normalization, and validation rules without code changes)
Interactive UI Dashboard (local dashboard to trigger pipeline runs and visualize candidate profiles and lineage)
Project Structure
candidate-transformer/
├── README.md                          ← This file
├── DESIGN.md                          ← Technical design (Architecture and Policies)
├── Vithyaa_2005ckv_Eightfold.pdf      ← Generated One-Page Design Document
├── requirements.txt                   ← Python dependencies
├── generate_pdf.py                    ← Compiles Vithyaa_2005ckv_Eightfold.pdf design document
│
├── config/
│   ├── output-config.json             ← Default canonical output schema configuration
│   └── custom-config.json             ← Custom output configuration (remaps, E.164/canonical formats)
│
├── input/                             ← Raw inputs (structured & unstructured)
│   ├── recruiter.csv
│   ├── ats_data.json
│   ├── github.json
│   ├── linkedin.json
│   ├── resume_sample.txt
│   └── recruiter_notes.txt
│
├── output/                            ← Generated JSON formats
│   ├── candidates_output.json         ← Standard canonical merged profile output
│   └── custom_candidates_output.json  ← Reshaped projected custom profile output
│
└── src/
    ├── main.py                        ← ETL pipeline orchestrator entrypoint
    ├── ui_server.py                   ← Lightweight web API server hosting the dashboard UI
    ├── static/
    │   └── index.html                 ← Interactive glassmorphic dashboard UI
    ├── models/                        ← In-memory canonical model structures
    ├── parsers/                       ← Multi-format extractor parsers
    ├── normalizers/                   ← String format normalizers
    ├── merger/                        ← Disjoint-set match and priority conflict merger
    ├── confidence/                    ← Trust confidence scoring calculator
    ├── projection/                    ← Schema projection and Validation layer
    └── util/                          ← Helpers and utilities
└── tests/                             ← Modular test suites
    ├── test_parsers.py
    ├── test_normalizers.py
    ├── test_merger.py
    ├── test_confidence.py
    └── test_integration.py
Setup & Installation
Prerequisites
Python 3.8+
pip
Installation
Clone and navigate to the project directory:
cd candidate-transformer
Create a virtual environment:
python -m venv venv
source venv/Scripts/activate  # On Windows
# or
source venv/bin/activate  # On macOS/Linux
Install dependencies:
pip install -r requirements.txt
How to Run
1. Run the ETL Pipeline (CLI)
To run the full pipeline synchronously and generate both the default canonical JSON (output/candidates_output.json) and custom config pass (output/custom_candidates_output.json):

python src/main.py
2. Launch the Web UI Dashboard
To run the web interface locally:

python src/ui_server.py
Open http://localhost:8000/ in your browser. The dashboard lets you:

Trigger the ETL pipeline from the UI.
Filter candidates by name or skill search queries.
Inspect circular trust meters and technical skill badges.
Track where each field value came from dynamically in the Provenance table.
3. Run the Modular Test Suite
To run all 18 modular unit and integration tests:

python -m unittest discover -s tests -p "test_*.py"
4. Compile the Design PDF Document
To recompile the single-page PDF document deliverable:

python generate_pdf.py
Required Twist — Configurable Projection Output
Our projection engine matches configuration requirements exactly. By editing the configuration in config/custom-config.json, you can:

Reshape structure: Use the "from" key to remap nested paths (e.g. "from": "emails[0]" mapping to "primary_email", or "from": "skills[].name" to export skill names as list of strings).
Format Normalization: Use the "normalize" key under path config (e.g. "normalize": "E.164" for phone standardizations, or "normalize": "canonical" for skills).
Toggle Metadata: Enable/disable confidence and provenance objects dynamically.
Graceful Nulls/Omissions/Errors: Handled by "on_missing" set to "null" (outputs None), "omit" (skips keys), or "error" (raises ValidationError).
Example projection output configuration (custom-config.json):

{
  "fields": [
    { "path": "full_name", "type": "string", "required": true },
    { "path": "primary_email", "from": "emails[0]", "type": "string", "required": true },
    { "path": "phone", "from": "phones[0]", "type": "string", "normalize": "E.164" },
    { "path": "skills", "from": "skills[].name", "type": "string[]", "normalize": "canonical" }
  ],
  "include_confidence": true,
  "on_missing": "null"
}
Conflict Resolution & Confidence Metrics
When the same candidate appears across multiple inputs, we merge properties by tracking priorities:

Resume (Trust 1.0)
ATS JSON (Trust 0.9)
GitHub (Trust 0.9)
CSV (Trust 0.9)
LinkedIn (Trust 0.7)
Text notes (Trust 0.5)
Adjustments are applied dynamically:

Field Agreement: +0.1 if the value appears identically across 2 or more sources.
Regex Extraction Penalty: -0.1 for unstructured extractions.
Normalization Bonus: +0.05 for successfully parsed locations/phones.
Min/Max bounds: [0.0, 1.0].
License
MIT License
