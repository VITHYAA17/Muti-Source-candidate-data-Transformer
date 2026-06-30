"""
PDF Generator - Compiles the Technical Design One-Pager into a professional single-page PDF.
Uses ReportLab to build the document dynamically.
"""
import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def build_pdf(filename: str):
    # Setup document with small margins to guarantee it fits on a single page
    margin = 32 # 0.45 inch margins
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    styles = getSampleStyleSheet()
    
    # Custom compact styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1e3a8a"), # Dark Blue
        spaceAfter=3
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#4b5563"), # Slate Grey
        spaceAfter=10
    )
    
    section_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#1d4ed8"), # Indigo Blue
        spaceBefore=6,
        spaceAfter=4,
        borderPadding=2
    )
    
    body_style = ParagraphStyle(
        'BodyTextCompact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1f2937"), # Charcoal
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'BulletCompact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1f2937"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=2
    )

    story = []

    # Document Header
    story.append(Paragraph("Eightfold Engineering Intern (Jul-Dec 2026) Assignment", title_style))
    story.append(Paragraph("<b>Multi-Source Candidate Data Transformer</b> — Vithyaa | 2005ckv@gmail.com", meta_style))

    # Divider line
    divider = Table([[""]], colWidths=[548])
    divider.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor("#cbd5e1")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 4))

    # 1. Pipeline Step Breakdown
    story.append(Paragraph("1. ETL Pipeline Step Breakdown", section_style))
    story.append(Paragraph(
        "The system processes multiple disparate source files sequentially, executing these clean structural phases: "
        "<b>Extract</b> (parsers ingest CSV rows, JSON arrays, API-like structures, text resumes, and recruiter notes) &rarr; "
        "<b>Normalize</b> (standardizes schema layouts and formats in-place) &rarr; "
        "<b>Merge & Dedup</b> (clusters duplicate profiles and merges fields) &rarr; "
        "<b>Confidence</b> (assigns precision scores per field and overall profile) &rarr; "
        "<b>Project-to-Output</b> (reshapes fields and resolves remapping configurations) &rarr; "
        "<b>Validate</b> (validates schema types and required rules before loading).",
        body_style
    ))

    # 2. Canonical Schema and Normalization Rules
    story.append(Paragraph("2. Canonical Schema & Normalized Formats", section_style))
    story.append(Paragraph(
        "A Candidate record encapsulates 13 fields (UUID, name, emails, phones, location, links, headline, years_experience, skills, experience, education, provenance tracking, and overall trust score). Selected normalization formats are:",
        body_style
    ))
    story.append(Paragraph("&bull; <b>Phones:</b> E.164 formatting (e.g. +15550101) utilizing <i>phonenumbers</i> library with a robust custom length fallback check.", bullet_style))
    story.append(Paragraph("&bull; <b>Dates:</b> Standardized YYYY-MM-DD (general dates) and YYYY-MM (professional history) formats parsed with <i>python-dateutil</i>.", bullet_style))
    story.append(Paragraph("&bull; <b>Location:</b> Standardized country codes (ISO-3166-1 alpha-2) and region (state abbreviations like CA) using string parsers.", bullet_style))
    story.append(Paragraph("&bull; <b>Skills:</b> Canonical mapping dictionary standardizing colloquialisms (e.g., JS &rarr; JavaScript, K8s &rarr; Kubernetes).", bullet_style))

    # 3. Merger, Conflict-Resolution & Confidence Policy
    story.append(Paragraph("3. Match Keys, Merger, & Confidence Scoring", section_style))
    story.append(Paragraph(
        "<b>Duplicate Matching:</b> Candidates are matched if they share at least one email (case-insensitive) or phone number (digits-only comparison). Matches are resolved using a disjoint-set (union-find) clustering algorithm to group transitive links.<br/>"
        "<b>Conflict Resolution:</b> Field values are resolved using source hierarchy ranking: <b>Resume (60) &gt; ATS = GitHub = CSV (50) &gt; LinkedIn (30) &gt; Text (10)</b>. Higher priority source values overwrite lower ones. Nested structures (skills, experience, and education) are merged, deduplicated, and unified.<br/>"
        "<b>Confidence Scoring:</b> Trust scores (0.0 to 1.0) are computed at field level. Base score matches highest source confidence: Resume = 1.0, ATS/GitHub/CSV = 0.9, LinkedIn = 0.7, Text = 0.5. Adjustments: Field agreement bonus (+0.1 if seen in &ge;2 sources), regex extraction penalty (-0.1 if from notes/resumes), and normalization bonus (+0.05). Overall confidence is the mathematical average of populated fields.",
        body_style
    ))

    # 4. Configurable Output & Projection Layer
    story.append(Paragraph("4. Runtime Custom-Output Projection & Schema Validation", section_style))
    story.append(Paragraph(
        "To enforce runtime schema reshaping without code alterations, the pipeline includes a <b>Projection Layer</b>. "
        "It supports remapping via the 'from' configuration attribute (e.g., mapping custom 'primary_email' from index 'emails[0]', extracting lists like 'skills[].name', or nested lookups like 'location.city'). "
        "It dynamically applies per-field formats during projection, handles metadata display flags (provenance and overall_confidence toggle), and obeys 'on_missing' directives (setting values to null, omitting keys, or raising a ValidationError on missing fields). "
        "After projection, the dictionary is evaluated by the SchemaValidator against rules to confirm type correctness.",
        body_style
    ))

    # 5. Edge Cases & Descope Strategy
    story.append(Paragraph("5. Critical Edge Cases & Descoped Areas", section_style))
    story.append(Paragraph("&bull; <b>Mock Phone Formats:</b> Shorter mock formats (7/8 digits in CSV/Notes) are mapped safely to +1 E.164 using a customized digit checks fallback.", bullet_style))
    story.append(Paragraph("&bull; <b>Nested Experience Merging:</b> Experience entries are clustered by company/title case-insensitively, merging dates and summary contents from the highest priority candidates.", bullet_style))
    story.append(Paragraph("&bull; <b>Circular Matching Dependencies:</b> Solved via disjoint-set clustering preventing matching loops and ensuring consistent merged identities.", bullet_style))
    story.append(Paragraph("&bull; <b>Descoped Under Time Pressure:</b> Abstract semantic translation of names (e.g., 'Robert' vs 'Bob' fuzzy matches), parallel map-reduce distributed execution, and deep NLP entity parsing (opted for optimized regular expressions for reliability and scale).", bullet_style))

    # Build PDF
    doc.build(story)
    print(f"PDF successfully generated: {filename}")

if __name__ == "__main__":
    output_filename = "Vithyaa_2005ckv_Eightfold.pdf"
    build_pdf(output_filename)
