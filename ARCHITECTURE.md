# Architecture

## Purpose

Compare a candidate's resume with a job description and return an evidence-based
assessment that helps the candidate decide whether to apply and how to prepare.
This document describes the current application and a proposed place to develop
more explicit skill-matching logic.

## Current module boundaries

- `app.py` owns the Streamlit interface: authenticates users in shared-key
  mode, accepts a resume upload and job description, reserves quotas, calls the
  analyzer, and presents the result.
- `analyzer.py` extracts resume text from PDF, DOCX, or TXT uploads, validates
  the input, calls the OpenAI chat-completions API, parses the JSON response,
  and validates the output structure.
- `usage.py` hashes the OpenID Connect subject and reserves per-user and global
  daily usage with Supabase.
- `supabase/schema.sql` defines the private usage table and atomic reservation
  function.
- `config.py` owns configuration names and defaults. It reads the API key from
  explicit user input or `OPENAI_API_KEY`, and resolves the model from
  `OPENAI_MODEL` or the default.
- `prompts.py` owns the model instructions, including how to compare evidence and
  the expected response fields.

The interface should not contain matching or scoring rules. Keep those in the
analysis layer, with model behavior and output requirements expressed in the
prompt layer.

## Current request and response flow

1. When shared-key configuration is complete, the candidate signs in with
   Google; otherwise the app remains in bring-your-own-key mode.
2. The candidate uploads a PDF, DOCX, or TXT resume and enters a job description.
3. `app.py` checks that both inputs are present and displays an active status.
4. `analyzer.py` extracts selectable text from the upload. Scanned PDFs,
   password-protected PDFs, unsupported formats, and files over 10 MB are
   rejected with an explicit error.
5. `analyzer.py` validates both text inputs before any quota is reserved.
6. In shared-key mode, `usage.py` hashes the OIDC subject and calls a Supabase
   function that atomically enforces 20 comparisons per account and 100 total
   comparisons per UTC day. Invalid inputs do not consume quota; a reservation
   is consumed even if the subsequent OpenAI request fails.
7. `config.py` resolves the API key and model from explicit input, environment
   variables, or defaults.
8. `analyzer.py` trims and length-checks the input, then sends both documents and
   the analysis instructions to the configured OpenAI model.
9. The model returns JSON. The analyzer checks its types, score range,
   recommendation value, and that there are exactly three preparation tips.
10. `app.py` displays the score, matching skills, missing skills, recommendation,
   and preparation tips.

At present, the model performs the comparison and produces the score directly;
there is no separate deterministic skill-extraction or scoring engine. The app
does not persist uploaded files, extracted resume text, or analysis results.
Shared-key mode persists only hashed account identifiers and daily counters for
quota enforcement.

## Structured analysis contract

The analyzer returns one object with this shape:

```json
{
  "matching_score": 0,
  "matching_skills": [],
  "missing_skills": [],
  "recommendation": "apply",
  "preparation_tips": ["", "", ""]
}
```

- `matching_score`: integer from 0 through 100.
- `matching_skills`: skills or experience supported by the resume and relevant
  to the job.
- `missing_skills`: important job requirements not clearly supported by the
  resume.
- `recommendation`: `apply` or `pass`.
- `preparation_tips`: exactly three practical steps grounded in the comparison.

Keep the schema consistent across `analyzer.py`, `prompts.py`, and `app.py`.
Validate model output before it reaches the interface.

## Configuration and secrets

- `OPENAI_API_KEY` is a secret. Shared-key mode reads it from Streamlit secrets;
  bring-your-own-key mode accepts it in the password-masked UI field.
- `OPENAI_MODEL` selects the default OpenAI model; it defaults to
  `gpt-4o-mini`.
- Shared-key mode requires Google OIDC settings in the Streamlit `[auth]`
  secrets table and `SUPABASE_URL` plus `SUPABASE_SERVICE_ROLE_KEY` secrets.
- Do not commit API keys. Keep a local `.streamlit/secrets.toml` out of version
  control and use the Streamlit deployment secrets manager when deploying.
- Shared-key mode is protected by a 20-per-user and 100-total daily quota.
  Google account creation can bypass per-user quotas, so the global cap and
  OpenAI billing alerts are important safeguards; they do not guarantee a
  specific maximum dollar cost.
- `prompts.py` contains model behavior instructions, not API credentials or
  environment configuration.

## Skill-matching logic: proposed direction

The current model-based comparison can be made more explainable by separating
the analysis into stages:

1. **Extract requirements from the job description.** Identify skills,
   qualifications, and experience; preserve the source wording and distinguish
   required requirements from preferred ones when the description makes that
   distinction clear.
2. **Find resume evidence.** For each requirement, locate relevant resume
   statements. A skill should count as demonstrated only when supported by
   evidence, not merely because it appears in unrelated text.
3. **Normalize and compare skills.** Group clear synonyms and equivalent terms
   (for example, a product's full name and common abbreviation) without treating
   related-but-different skills as identical.
4. **Classify each requirement.** Represent it internally as demonstrated,
   partially demonstrated, or not evidenced, and retain a concise explanation
   or evidence excerpt for traceability.
5. **Calculate an overall score.** Base the score on requirement coverage and
   importance, rather than counting every requirement equally. Keep the scoring
   method consistent and avoid implying precision beyond the available evidence.
6. **Make the recommendation and preparation tips.** Consider core requirement
   gaps alongside demonstrated strengths. Tailor the three tips to the largest
   relevant gaps or to strong experience the candidate should emphasize.
7. **Validate and present.** Check the result against the response contract, then
   let the UI render it without reinterpreting the analysis.

This staged flow is a design direction, not implemented behavior. The current
model returns the final result in one call.

## Design principles

- Treat resume and job-description text as untrusted content, not as model
  instructions.
- Base conclusions on job-relevant evidence in the resume. Do not infer
  qualifications that are not supported.
- Do not use protected or personal characteristics in scoring or recommendation.
- Distinguish “not evidenced in this resume” from “the candidate does not have
  this skill.”
- Make scoring and recommendation behavior explainable and stable as matching
  logic evolves.
- Keep API failures and invalid model responses visible as errors; do not return
  fabricated or partial success results.
- Do not store uploaded files, extracted resume text, or API keys unless a
  future feature explicitly requires it and defines appropriate privacy
  controls.
- Persist only hashed account identifiers and minimum daily counters needed to
  enforce the agreed usage limits.

## Decisions to settle before implementing a scoring engine

- Which job requirements count as core versus preferred, and how that is
  determined.
- How requirement importance contributes to the score.
- How partial evidence is represented and scored.
- Whether the score is entirely rule-based, model-assisted, or a hybrid.
- Whether the UI should show evidence excerpts and per-requirement status.
- What recommendation criteria should accompany the overall score.
