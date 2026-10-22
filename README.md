# Resume Matcher

A free Streamlit app that compares an uploaded resume with a job description.
It runs a built-in skill and synonym matcher locally, so users do not need an
API key, account, or paid AI service.

The results are a quick, rule-based guide—not a semantic assessment or hiring
decision. The skill catalog is finite, and exact wording/context can affect
which skills are recognized.

## Live demo

Try the [Resume Matcher app](https://resume-matcher-bhuvanesh.streamlit.app/).
Upload a PDF, DOCX, or TXT resume, paste a job description, and select
**Compare**. No sign-in or API key is required.

## Features

- Extract resume text from selectable-text PDFs, DOCX, and UTF-8 TXT files.
- Compare recognized skills and common synonyms from a built-in catalog.
- Weight job requirements marked as required more heavily and preferred skills
  less heavily.
- Show a match score, matching skills, missing skills, recommendation, and
  three preparation tips.
- Keep resume and job-description text in the running app process; no AI API
  request or external database is used.

## Run locally

Requirements: Python 3.10 or later.

```bash
git clone https://github.com/BhuvaneshOgirala/resume-matcher.git
cd resume-matcher
python -m pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

Create an app from this repository, select the `main` branch, and set the main
file path to `app.py`. No secrets, OAuth setup, database, or API configuration
is needed. Streamlit Community Cloud's own availability and resource limits
still apply.

## Privacy and limitations

Resume text is extracted and analyzed locally by the app code and is not sent to
OpenAI or another model API. The app does not persist uploaded resumes or
analysis results. As with any hosted website, the hosting provider processes
requests, and uploaded file bytes are handled temporarily in the app process.
The app accepts PDF, DOCX, and UTF-8 TXT files up to 10 MB; scanned PDFs without
selectable text are not supported.

The analyzer only recognizes skills and synonyms in its built-in catalog. It
does not interpret meaning, infer equivalent experience, or understand
surrounding context. Match scores and recommendations are approximate guidance,
not guarantees of job suitability or hiring outcomes.

## Project structure

| File | Responsibility |
| --- | --- |
| `app.py` | Streamlit inputs, progress, and comparison results. |
| `analyzer.py` | Local skill matching, score calculation, tips, and resume text extraction. |
| `requirements.txt` | Streamlit and document extraction dependencies. |
| `ARCHITECTURE.md` | Current architecture and matching behavior. |
