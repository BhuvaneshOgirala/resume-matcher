from collections.abc import Mapping

import httpx
import streamlit as st
from postgrest.exceptions import APIError

from analyzer import (
    analyze_resume,
    extract_resume_text,
    validate_analysis_inputs,
)
from config import (
    OPENAI_API_KEY_ENV,
    OPENAI_MODEL_ENV,
    get_openai_api_key,
    get_openai_model,
)
from usage import DAILY_GLOBAL_LIMIT, DAILY_USER_LIMIT, reserve_daily_comparison


st.set_page_config(page_title="Resume Matcher", page_icon="📄", layout="wide")
st.title("Resume Matcher")
st.write(
    "Compare a resume with a job description to see the strongest matches, "
    "missing skills, and an application recommendation."
)
st.info(
    "Text extracted from your resume and the job description are sent to OpenAI "
    "for analysis. Resume text is not stored by this app. Only a hashed account "
    "identifier and daily usage counts are saved for rate limiting. Only submit "
    "information you are comfortable sending to OpenAI."
)

auth_settings = st.secrets.get("auth", {})
supabase_url = st.secrets.get("SUPABASE_URL", "")
supabase_service_role_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")
shared_api_key = get_openai_api_key(st.secrets.get(OPENAI_API_KEY_ENV))
model = get_openai_model(st.secrets.get(OPENAI_MODEL_ENV))
shared_mode_ready = (
    isinstance(auth_settings, Mapping)
    and all(
        isinstance(auth_settings.get(key), str) and auth_settings.get(key).strip()
        for key in (
            "redirect_uri",
            "cookie_secret",
            "client_id",
            "client_secret",
            "server_metadata_url",
        )
    )
    and isinstance(supabase_url, str)
    and bool(supabase_url.strip())
    and isinstance(supabase_service_role_key, str)
    and bool(supabase_service_role_key.strip())
    and bool(shared_api_key)
)

user_subject: str | None = None
if shared_mode_ready:
    if not st.user.is_logged_in:
        st.write("Sign in to compare your resume using the shared model.")
        st.button("Continue with Google", on_click=st.login)
        st.stop()

    subject_claim = st.user.get("sub")
    if not isinstance(subject_claim, str) or not subject_claim.strip():
        st.error("Google sign-in did not provide an account identifier.")
        st.stop()
    user_subject = subject_claim

with st.sidebar:
    if shared_mode_ready:
        st.header("Account")
        user_email = st.user.get("email")
        if isinstance(user_email, str) and user_email:
            st.write(f"Signed in as {user_email}")
        st.caption(
            f"Up to {DAILY_USER_LIMIT} comparisons per account per UTC day. "
            f"The app also has a shared limit of {DAILY_GLOBAL_LIMIT} per day."
        )
        st.button("Sign out", on_click=st.logout)
        api_key = shared_api_key
    else:
        st.header("Model settings")
        st.warning(
            "Shared-key sign-in is not configured yet. Enter your own API key "
            "until the owner finishes setup."
        )
        api_key = st.text_input(
            "OpenAI API key",
            value="",
            type="password",
            help=(
                f"Set {OPENAI_API_KEY_ENV} in your environment or enter a key here. "
                "Never share an API key in chat or commit it to the repository."
            ),
        )
        model = st.text_input(
            "Model",
            value=model,
            help=f"Set {OPENAI_MODEL_ENV} to change the default model.",
        )

resume_column, job_column = st.columns(2)
with resume_column:
    resume_file = st.file_uploader(
        "Upload resume",
        type=["pdf", "docx", "txt"],
        help=(
            "PDF, DOCX, or TXT; maximum 10 MB. Scanned PDFs must have selectable "
            "text (OCR) before upload."
        ),
    )
with job_column:
    job_description = st.text_area(
        "Job description",
        placeholder="Paste the job description here...",
        height=360,
        max_chars=30_000,
    )

if st.button("Compare", type="primary", use_container_width=True):
    if resume_file is None:
        st.error("Upload a resume file before comparing.")
    elif not job_description.strip():
        st.error("Enter a job description before comparing.")
    elif not api_key.strip():
        st.error("Enter an OpenAI API key in Model settings.")
    else:
        result = None
        quota_message = None
        try:
            with st.status("Preparing resume analysis...", expanded=True) as progress:
                progress.write("Extracting text from the uploaded resume.")
                resume = extract_resume_text(resume_file.name, resume_file.getvalue())
                resume, validated_job_description = validate_analysis_inputs(
                    resume,
                    job_description,
                )

                if shared_mode_ready and user_subject:
                    progress.write("Checking your daily usage allowance.")
                    reservation = reserve_daily_comparison(
                        user_subject,
                        supabase_url,
                        supabase_service_role_key,
                    )
                    if not reservation["allowed"]:
                        if reservation["limit_reason"] == "global":
                            quota_message = (
                                "The app has reached its daily comparison limit. "
                                "Please try again tomorrow (UTC)."
                            )
                        else:
                            quota_message = (
                                f"You have reached your {DAILY_USER_LIMIT}-comparison "
                                "daily limit. "
                                "Please try again tomorrow (UTC)."
                            )
                        progress.update(
                            label="Daily comparison limit reached",
                            state="error",
                            expanded=False,
                        )
                    else:
                        progress.write(
                            f"{reservation['user_remaining']} comparisons remain "
                            f"for your account today; "
                            f"{reservation['global_remaining']} remain for the app."
                        )

                if not quota_message:
                    progress.write("Sending the resume and job description for analysis.")
                    result = analyze_resume(
                        resume=resume,
                        job_description=validated_job_description,
                        api_key=api_key.strip(),
                        model=model.strip(),
                        progress_callback=lambda message: progress.update(
                            label=message,
                            state="running",
                        ),
                    )
                    progress.update(
                        label="Analysis complete",
                        state="complete",
                        expanded=False,
                    )
        except (ValueError, RuntimeError) as error:
            progress.update(label="Analysis failed", state="error")
            st.error(str(error))
        except (APIError, httpx.HTTPError):
            progress.update(label="Usage check failed", state="error")
            st.error(
                "The app could not verify the daily usage limit. No analysis "
                "was sent; please try again later."
            )
        if quota_message:
            st.warning(quota_message)
        elif result is not None:
            st.subheader("Match results")
            score_column, recommendation_column = st.columns(2)
            score_column.metric("Match score", f"{result['matching_score']}%")
            recommendation = result["recommendation"].capitalize()
            recommendation_column.metric("Recommendation", recommendation)
            st.progress(result["matching_score"] / 100)

            strengths_column, missing_column = st.columns(2)
            with strengths_column:
                st.subheader("Matching skills")
                if result["matching_skills"]:
                    for skill in result["matching_skills"]:
                        st.markdown(f"- {skill}")
                else:
                    st.write("No clear matching skills were identified.")
            with missing_column:
                st.subheader("Missing skills")
                if result["missing_skills"]:
                    for skill in result["missing_skills"]:
                        st.markdown(f"- {skill}")
                else:
                    st.write("No notable missing skills were identified.")

            st.subheader("Preparation tips")
            for tip in result["preparation_tips"]:
                st.markdown(f"- {tip}")
