# Resume Matcher

A Streamlit app that compares a resume with a job description and returns a
matching score, matching and missing skills, an apply/pass recommendation, and
three preparation tips.

## Run locally

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure your OpenAI API key using an environment variable:

   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

   Optionally set a model; the default is `gpt-4o-mini`:

   ```bash
   export OPENAI_MODEL="gpt-4o-mini"
   ```

   Alternatively, enter the API key in the app's password-masked settings field.

3. Start the app:

   ```bash
   streamlit run app.py
   ```

## Deploy on Streamlit Community Cloud

1. Create a new app and select this GitHub repository and the `main` branch.
2. Set the **Main file path** to `app.py`.
3. In the app's **Settings > Secrets**, add:

   ```toml
   OPENAI_API_KEY = "your-api-key"
   OPENAI_MODEL = "gpt-4o-mini"
   ```

Never commit API keys or add them to a public repository. The app sends the
provided resume and job description to OpenAI for analysis; do not submit
sensitive information unless you are comfortable sharing it with that service.

## Project structure

- `app.py` — Streamlit interface and result display.
- `analyzer.py` — OpenAI request, input checks, response parsing, and validation.
- `prompts.py` — Instructions for the model's resume/job analysis.
- `config.py` — Model defaults and environment configuration names.
- `.bhuvanesh.md` — Architecture notes and proposed future matching logic.
