# Architecture

## Purpose

Provide a simple resume-to-job skill comparison without API keys, external
model calls, sign-in, or a paid analysis service.

## Modules

- `app.py` collects a PDF, DOCX, or TXT resume and job description, shows
  progress, and renders the structured result.
- `analyzer.py` extracts document text, matches known skill phrases and
  synonyms, calculates a deterministic score, and generates preparation tips.

## Request flow

1. The user uploads a resume and enters a job description.
2. `analyzer.py` extracts resume text locally in memory. Scanned PDFs,
   password-protected PDFs, unsupported formats, and files over 10 MB are
   rejected with an explicit error.
3. Both text inputs are trimmed and limited to 30,000 characters.
4. A curated catalog of skills and common aliases is searched in both documents
   using case-insensitive word boundaries. Only skills detected in the job
   description are scored.
5. Each recognized requirement is weighted equally unless its nearby wording
   indicates it is required (1.5x) or preferred (0.5x). The score is the
   weighted share of job skills also found in the resume, rounded to a
   percentage. `apply` is recommended at 50% or higher; otherwise `pass`.
6. The app shows matching and missing skills with three rule-based preparation
   tips.

No resume text or result is sent to an AI provider, written to an external
database, or stored by the app for later use. No API key or user account is
required. Streamlit's hosting service still processes web requests and has its
own platform resource and availability limits.

## Structured analysis contract

`analyze_resume` returns:

```json
{
  "matching_score": 0,
  "matching_skills": [],
  "missing_skills": [],
  "recommendation": "apply",
  "preparation_tips": ["", "", ""]
}
```

- `matching_score`: integer percentage from 0 through 100.
- `matching_skills`: catalog skills found in both documents.
- `missing_skills`: catalog skills found in the job description but not the
  resume.
- `recommendation`: `apply` at a score of at least 50; otherwise `pass`.
- `preparation_tips`: exactly three practical, rule-based suggestions.

## Limitations

This is literal phrase matching, not semantic analysis. Only catalog entries and
their aliases are recognized. Synonyms absent from the catalog, relevant
experience phrased differently, and contextual distinctions can be missed.
The score does not determine whether a candidate is qualified and should not be
used as a hiring decision.
