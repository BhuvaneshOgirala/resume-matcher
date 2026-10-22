# Resume Matcher

A Streamlit application that compares a resume with a job description and
provides an evidence-based match score, matching and missing skills, an
apply/pass recommendation, and three practical preparation tips.

This project is intended as a candidate self-assessment aid. It is not a hiring
decision system, and its model-generated assessment may be incomplete or
incorrect.

## Features

- Compare resume text against a job description.
- Show a match score, relevant skills, and important skills not evidenced by
  the resume.
- Recommend whether to consider applying.
- Suggest three role-specific preparation steps.
- Validate the model response before displaying it.

## Requirements

- Python 3.10 or later.
- An OpenAI API key.

## Run locally

1. Clone the repository and enter its directory:

   ```bash
   git clone https://github.com/BhuvaneshOgirala/resume-matcher.git
   cd resume-matcher
   ```

2. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Configure your OpenAI API key. Either set it in your shell:

   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

   Or enter it in the password-masked API key field in the app. Never commit an
   API key to the repository.

4. Optionally set `OPENAI_MODEL` to choose a different model. The default is
   `gpt-4o-mini`.

5. Start Streamlit:

   ```bash
   streamlit run app.py
   ```

## Deploy on Streamlit Community Cloud

1. Create an app from this GitHub repository and select the `main` branch.
2. Set **Main file path** to `app.py`.
3. Leave the OpenAI key unset for a public deployment so visitors supply their
   own key in the app. For a private deployment only, the app's **Settings >
   Secrets** can contain:

   ```toml
   OPENAI_API_KEY = "your-api-key"
   OPENAI_MODEL = "gpt-4o-mini"
   ```

For a public app, do **not** add your personal API key as a shared app secret:
any visitor could use it and incur charges on your account. Leave the secret
unset so users enter their own key in the app, or add access controls and usage
limits before configuring a shared key. Never put secrets in GitHub, including
in a public repository's files or commit history.

## Privacy and limitations

Resume text and job-description text are sent to OpenAI to produce the analysis.
Only submit information you are comfortable sending to that service. The app
does not persist the resume or analysis in its own storage. Match scores and
recommendations are model-generated guidance, not guarantees of job suitability
or hiring outcomes. This public demo has no user authentication or request
limits; keep API keys private and use your own key when trying the app.

## Project structure

| File | Responsibility |
| --- | --- |
| `app.py` | Streamlit inputs, progress status, and analysis results. |
| `analyzer.py` | Input checks, OpenAI request, response parsing, and schema validation. |
| `prompts.py` | Model instructions and analysis criteria. |
| `config.py` | Model defaults and configuration/environment-variable names. |
| `ARCHITECTURE.md` | Current architecture and planned matching approach. |
