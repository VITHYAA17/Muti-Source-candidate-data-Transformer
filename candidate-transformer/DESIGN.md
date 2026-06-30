# Technical Design - Candidate Data Transformer

## Problem Statement

Eightfold ingests candidate information from multiple sources (CSV, GitHub, LinkedIn, Resume, Text) with conflicting, incomplete, and duplicated data. We need to transform this into ONE clean, canonical profile with:
- Normalized formats
- Provenance tracking (data lineage)
- Confidence scores (trust levels)
- Graceful error handling (never crash)

## Solution Architecture

### High-Level Pipeline

```
CSV → ┐
ATS → ├→ EXTRACT → NORMALIZE → DEDUP & MERGE → CONFIDENCE → OUTPUT CONFIG → VALIDATE → JSON
GitHub → │
LinkedIn → │
Resume → │
Text → ┘
```

### Phases

**Phase 1-2: Core Models**
- Define data structures for: Candidate, Skill, Experience, Education, Location, Links, Provenance
- Each candidate tracks all 13 canonical fields plus provenance per field

**Phase 3: EXTRACT - Parsers**
- `CsvParser` - Parse recruiter.csv to Candidate objects
- `JsonParser` - Parse ATS JSON with field mapping to Candidate objects
- `GitHubParser` - Parse github.json to Candidate objects
- `LinkedInParser` - Parse linkedin.json to Candidate objects
- `ResumeParser` - Extract text from resume_sample.txt via regex
- `TextParser` - Extract entities from recruiter_notes.txt via regex
- Output: `List[Candidate]` with `source` field set

**Phase 4: NORMALIZE**
- `PhoneNormalizer` - Convert all phones to E.164 format (+1-555-0101)
- `EmailNormalizer` - Lowercase all emails
- `DateNormalizer` - Convert all dates to YYYY-MM-DD format
- `SkillNormalizer` - Map skill names to canonical list (JS → JavaScript)
- `LocationNormalizer` - Parse location strings to {city, region, country} with ISO-3166

**Phase 5: DEDUP & MERGE**
- `CandidateMatcher` - Match same person across sources by email + phone
- `ConflictResolver` - Use priority to pick winning value:
  - Resume (100%) > ATS (90%) > GitHub (90%) > CSV (90%) > LinkedIn (70%) > Text (50%)
- `CandidateMerger` - Merge matched records into single Candidate

**Phase 6: CONFIDENCE**
- `ConfidenceCalculator` - Assign per-field and overall confidence
- Source confidence: Resume 1.0, ATS/GitHub/CSV 0.9, LinkedIn 0.7, Text 0.5
- Agreement bonus: +0.1 if field appears in multiple sources
- Overall = average of field confidences

**Phase 7: OUTPUT CONFIG & PROJECTION**
- Load `config/output-config.json`
- `OutputProjector` - Transform canonical to output schema
- `SchemaValidator` - Validate against schema

**Phase 8: CLI & TESTS**
- `main.py` - Orchestrate pipeline
- Test suite for each phase

### Data Model

**Candidate** (13 fields - canonical schema)
- `candidate_id` (string) - Unique identifier
- `full_name` (string)
- `emails` (string[])
- `phones` (string[]) - E.164 format
- `location` ({city, region, country}) - country as ISO-3166 alpha-2
- `links` ({linkedin, github, portfolio, other[]})
- `headline` (string | null)
- `years_experience` (number | null)
- `skills` ([{name, confidence, sources}]) - canonical names
- `experience` ([{company, title, start, end, summary}]) - dates YYYY-MM
- `education` ([{institution, degree, field, end_year}])
- `provenance` ([{field, source, method}]) - data lineage
- `overall_confidence` (number) - 0.0-1.0

**Provenance**
- `field` - which field (e.g., "full_name")
- `source` - where from (CSV, GitHub, LinkedIn, Resume, Text, ATS)
- `method` - how extracted (direct_extract, regex_parse, api_call, field_mapping)

### Matching Algorithm

1. Normalize email and phone for both candidates
2. If email matches and phone matches → same person
3. If email matches (OR phone matches) → probably same person (merge with lower confidence)
4. Otherwise → different people

### Conflict Resolution Strategy

When same person has conflicting field values from different sources:

1. Use priority order: Resume > ATS > GitHub > CSV > LinkedIn > Text
2. Pick value from highest priority source
3. Track which source was used in provenance
4. Set confidence based on source priority

Example:
```
Field: location
CSV value: "Mountain View" (priority 90, confidence 0.9)
GitHub value: "San Francisco, CA" (priority 90, confidence 0.9)
LinkedIn value: "San Francisco, CA" (priority 70, confidence 0.7)

Winner: "San Francisco, CA" (from GitHub/CSV, highest priority + agreement)
Final confidence: 0.9 + 0.1 (agreement bonus) = 1.0
```

### Normalization Rules

**Phone**
- Input formats: +1-555-0101, 555-0101, (555) 0101, +1 555 0101
- Output: E.164 format (+15550101)
- Tool: `phonenumbers` library

**Email**
- Input: "John@Gmail.com", "JOHN@GMAIL.COM"
- Output: "john@gmail.com"
- Rule: lowercase, trim whitespace

**Date**
- Input: 2020-01-15, 01/15/2020, Jan 15 2020, 2020-01
- Output: 2020-01-15 (YYYY-MM-DD)
- Tool: `python-dateutil`

**Skill**
- Map to canonical list:
  - "JS" → "JavaScript"
  - "Py", "python" → "Python"
  - "K8s", "kubernetes" → "Kubernetes"
- Case-insensitive matching

**Location**
- Input: "San Francisco, CA", "San Francisco, California, USA"
- Parse to: {city: "San Francisco", region: "CA", country: "US"}
- Country code: ISO-3166 alpha-2

### Confidence Scoring

**Source Confidence**
- Resume: 1.0 (most detailed, manual)
- ATS JSON: 0.9 (official structured)
- GitHub: 0.9 (semi-structured, public)
- CSV: 0.9 (structured, recruiter data)
- LinkedIn: 0.7 (user-maintained, less official)
- Text: 0.5 (unstructured, error-prone)

**Adjustments**
- Field agreement (appears in 2+ sources): +0.1
- Extracted via regex: -0.1
- Normalized successfully: +0.05
- Min: 0.0, Max: 1.0

**Overall Confidence** = average of all field confidences

### Error Handling

- **Missing fields**: Set to null, low confidence
- **Parse errors**: Skip invalid records, log warning
- **Conflicting data**: Use priority list, never invent data
- **Regex match failures**: Use null + low confidence
- **Never crash**: Log error, continue processing

### Output Configuration

Runtime config in `config/output-config.json` controls:
- Which fields to include
- Field renaming (e.g., "full_name" → "candidate_name")
- Per-field normalization
- Provenance/confidence inclusion
- Missing field handling

No code changes needed for different output formats!

### Edge Cases Handled

1. **Same person, different names**: "John Smith" vs "John S." → fuzzy match
2. **Phone format variations**: +1-555-0101, (555) 0101, 555-0101 → normalize
3. **Multiple emails/phones**: Keep all, set first as primary
4. **Location conflicts**: "Mountain View" vs "San Francisco" → pick by priority
5. **Skills merge**: Combine from all sources, deduplicate case-insensitively
6. **Missing fields**: Never invent, use null + low confidence
7. **Experience overlap**: Merge, handle date conflicts with priority
8. **Resume parsing**: Handle varied resume formats via regex
9. **Free text parsing**: Extract name, email, phone, skills from recruiter notes
10. **ATS field mapping**: Handle mismatched field names

## Implementation Notes

- Use `pandas` for CSV parsing
- Use `phonenumbers` for phone normalization
- Use `python-dateutil` for date parsing
- Use `PyPDF2`/`python-docx` for resume extraction
- Use `regex` for text parsing
- Track all operations with provenance
- Score all field values with confidence
- Validate output against schema
- Log all steps for debugging

## Testing Strategy

1. Unit tests per component
2. Integration tests for full pipeline
3. Sample data validation
4. Edge case testing
5. Schema validation tests
