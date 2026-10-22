# Resume Matcher

A Streamlit application that compares a resume with a job description and
provides an evidence-based match score, matching and missing skills, an
apply/pass recommendation, and three practical preparation tips.

This project is intended as a candidate self-assessment aid. It is not a hiring
decision system, and its model-generated assessment may be incomplete or
incorrect.

## Live demo

Try the [Resume Matcher app](https://resume-matcher-bhuvanesh.streamlit.app/).
When shared-key mode is configured, visitors sign in with Google instead of
entering an OpenAI API key.

## Features

- Upload a PDF, DOCX, or TXT resume and compare it against a job description.
- Show a match score, relevant skills, and important skills not evidenced by
  the resume.
- Recommend whether to consider applying.
- Suggest three role-specific preparation steps.
- Use Google sign-in and enforce daily per-account and app-wide usage limits
  when shared-key mode is enabled.
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

1. Create a Supabase project and run [`supabase/schema.sql`](./supabase/schema.sql)
   in its SQL Editor. This creates private daily usage counters and a database
   function that atomically enforces both limits.
2. Create a Google OAuth client for a **Web application**. Add this authorized
   redirect URI in Google Cloud:

   ```text
   https://resume-matcher-bhuvanesh.streamlit.app/oauth2callback
   ```

   Configure the OAuth consent screen and publish it for the intended audience;
   while it is in testing mode, only listed test users can sign in.
3. In Streamlit Community Cloud, open the app's **Settings > Secrets** and add
   the following values, replacing every placeholder. Keep the Supabase
   **service-role** key and OpenAI key private:

   ```toml
   OPENAI_API_KEY = "your-openai-api-key"
   OPENAI_MODEL = "gpt-4o-mini"
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_SERVICE_ROLE_KEY = "your-supabase-service-role-key"

   [auth]
   redirect_uri = "https://resume-matcher-bhuvanesh.streamlit.app/oauth2callback"
   cookie_secret = "a-long-random-secret"
   client_id = "your-google-oauth-client-id"
   client_secret = "your-google-oauth-client-secret"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
   ```

   Generate a strong cookie secret locally (for example, `openssl rand -hex 32`).
   Never paste keys into chat, commit them, or place them in source files.
4. Shared-key mode activates only after all OpenAI, Google OIDC, and Supabase
   secrets are present. Until then, the app continues to request each visitor's
   own API key and does not use an incomplete shared-key configuration.

The shared key is billed to the app owner. Google sign-in is not an absolute
barrier to creating multiple accounts, so the app also enforces a maximum of 20
comparisons per account and 100 across all accounts per UTC day. Each attempted
analysis consumes quota once the usage reservation is made, including attempts
that later fail at OpenAI. Configure OpenAI billing alerts and spending limits
as an additional safeguard. Daily usage storage contains only a hashed Google
account identifier, date, and counters; resume and job-description text are not
stored by this app. Old usage records are automatically removed after 30 days.

## Privacy and limitations

Text extracted from uploaded resumes and job-description text are sent to OpenAI
to produce the analysis. The app accepts PDF, DOCX, and UTF-8 TXT files up to
10 MB; scanned PDFs without selectable text are not supported. Only submit
information you are comfortable sending to that service. The app does not
persist resume text or analysis results. Shared-key mode stores a hashed
account identifier and daily usage counters for quota enforcement. Match scores
and recommendations are model-generated guidance, not guarantees of job
suitability or hiring outcomes.

## Project structure

| File | Responsibility |
| --- | --- |
| `app.py` | Streamlit inputs, sign-in, quota enforcement, progress, and results. |
| `analyzer.py` | Resume text extraction, input checks, OpenAI request, response parsing, and schema validation. |
| `usage.py` | Hashes signed-in identities and reserves daily quota through Supabase. |
| `supabase/schema.sql` | Private usage-counter table and atomic daily quota function. |
| `prompts.py` | Model instructions and analysis criteria. |
| `config.py` | Model defaults and configuration/environment-variable names. |
| `ARCHITECTURE.md` | Current architecture and planned matching approach. |
