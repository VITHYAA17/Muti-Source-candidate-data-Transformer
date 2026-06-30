# Candidate Data Transformer

A Python-based ETL pipeline to merge candidate data from multiple sources (CSV, ATS JSON, GitHub, LinkedIn, Resume, Text) into one clean canonical profile with provenance tracking and confidence scoring.

## Overview

This application transforms messy, conflicting candidate data from multiple sources into a single unified profile following a canonical schema with:
- **Normalized formats** (E.164 phones, ISO-3166 countries, YYYY-MM dates)
- **Provenance tracking** (where each field value came from)
- **Confidence scoring** (how much to trust each field)
- **Conflict resolution** (priority-based merging)
- **Runtime configurability** (control output schema without code changes)

## Project Structure

```
candidate-transformer/
├── README.md                    ← This file
├── DESIGN.md                    ← Technical design
├── requirements.txt             ← Python dependencies
│
├── config/
│   └── output-config.json       ← Runtime output configuration
│
├── input/                       ← Sample input data
│   ├── recruiter.csv
│   ├── ats_data.json
│   ├── github.json
│   ├── linkedin.json
│   ├── resume_sample.txt
│   └── recruiter_notes.txt
│
├── output/
│   └── candidates_output.json   ← Final merged candidates
│
└── src/
    ├── main.py                  ← Entry point
    ├── models/                  ← Data structures (Phase 1-2)
    ├── parsers/                 ← Extract phase (Phase 3)
    ├── normalizers/             ← Normalize phase (Phase 4)
    ├── merger/                  ← Dedup & merge phase (Phase 5)
    ├── confidence/              ← Confidence scoring (Phase 6)
    ├── projection/              ← Output config (Phase 7)
    └── util/                    ← Utilities
└── tests/                       ← Test suite
```

## Pipeline Flow

```
INPUT SOURCES (CSV, JSON, GitHub, LinkedIn, Resume, Text)
        ↓
PHASE 3: EXTRACT (Parse all sources)
        ↓
PHASE 4: NORMALIZE (Standardize formats)
        ↓
PHASE 5: DEDUP & MERGE (Combine records, resolve conflicts)
        ↓
PHASE 6: CONFIDENCE (Calculate trust scores)
        ↓
PHASE 7: OUTPUT CONFIG (Apply runtime config)
        ↓
PHASE 8: VALIDATE (Schema validation)
        ↓
CANONICAL JSON OUTPUT (candidates_output.json)
```

## Input Sources Supported

### Structured Sources
- **Recruiter CSV Export** - structured rows (name, email, phone, company, title)
- **ATS JSON Blob** - semi-structured with field name mapping

### Unstructured Sources
- **GitHub Profile JSON** - name, bio, repositories, languages
- **LinkedIn Profile JSON** - name, headline, experience, education, skills
- **Resume Files** - PDF/DOCX text extraction and parsing
- **Recruiter Notes** - free text parsing via regex

## Default Output Schema

The canonical profile has 13 fixed fields:

```json
{
  "candidate_id": "string",
  "full_name": "string",
  "emails": ["string"],
  "phones": ["string"],              // E.164 format
  "location": {
    "city": "string",
    "region": "string",
    "country": "string"               // ISO-3166 alpha-2
  },
  "links": {
    "linkedin": "string",
    "github": "string",
    "portfolio": "string",
    "other": ["string"]
  },
  "headline": "string | null",
  "years_experience": "number | null",
  "skills": [
    {
      "name": "string",               // canonical names
      "confidence": "number",         // 0.0-1.0
      "sources": ["string"]           // where extracted from
    }
  ],
  "experience": [
    {
      "company": "string",
      "title": "string",
      "start": "YYYY-MM",
      "end": "YYYY-MM",
      "summary": "string"
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "field": "string",
      "end_year": "number"
    }
  ],
  "provenance": [
    {
      "field": "string",
      "source": "string",             // CSV, GitHub, LinkedIn, Resume, Text, ATS
      "method": "string"              // direct_extract, regex_parse, api_call
    }
  ],
  "overall_confidence": "number"      // 0.0-1.0
}
```

## Setup

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
# or
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Pipeline

```bash
python src/main.py
```

This will:
1. Parse all input sources
2. Normalize all candidate data
3. Deduplicate and merge records
4. Calculate confidence scores
5. Apply output configuration
6. Validate output schema
7. Save merged candidates to `output/candidates_output.json`

## Running Tests

```bash
python -m pytest tests/
```

## Configuration

Edit `config/output-config.json` to control output schema:
- Select which fields to include
- Rename fields
- Set normalization rules
- Toggle provenance/confidence output

Example:
```json
{
  "fields": [
    {"path": "full_name", "type": "string", "required": true},
    {"path": "phones[0]", "type": "string", "normalize": "E.164"},
    {"path": "skills[].name", "type": "string[]"}
  ],
  "include_provenance": true,
  "include_confidence": true,
  "on_missing": "null"
}
```

## Conflict Resolution Strategy

When the same candidate appears in multiple sources with conflicting field values, we use a priority order:

1. **Resume** (100% confidence) - Most detailed, manually written
2. **ATS JSON** (90% confidence) - Structured, official
3. **GitHub** (90% confidence) - Semi-structured, public
4. **CSV** (90% confidence) - Structured, recruiter data
5. **LinkedIn** (70% confidence) - User-maintained profile
6. **Text** (50% confidence) - Free text, error-prone

For example, if location conflicts:
- CSV says: "Mountain View"
- GitHub says: "San Francisco, CA"
- LinkedIn says: "San Francisco, CA"

Result: "San Francisco, CA" with confidence 0.9 (from GitHub/CSV, agreement bonus)

## Implementation Phases

- **Phase 1-2**: Core data models (Candidate, Skill, Experience, Education, Location, Links, Provenance)
- **Phase 3**: Extract - Parse all 6 input sources
- **Phase 4**: Normalize - Standardize formats (phones, emails, dates, skills, locations)
- **Phase 5**: Dedup & Merge - Match same person, resolve conflicts
- **Phase 6**: Confidence - Calculate per-field and overall confidence
- **Phase 7**: Output Config - Apply runtime configuration
- **Phase 8**: Validate & Test - Schema validation and testing

## Sample Data

The `input/` folder contains sample data:
- `recruiter.csv` - 4 candidates
- `ats_data.json` - 3 candidates (ATS format with different field names)
- `github.json` - 3 candidates with skills and bio
- `linkedin.json` - 3 candidates with experience and education
- `resume_sample.txt` - 1 resume as text
- `recruiter_notes.txt` - 1 free text candidate notes

Sample output will be in `output/candidates_output.json`

## Technical Details

See [DESIGN.md](DESIGN.md) for:
- System architecture diagram
- Data flow details
- Normalization rules
- Matching algorithm
- Confidence scoring algorithm
- Design decisions and rationale

## License

MIT License
