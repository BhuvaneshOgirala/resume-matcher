import streamlit as st

from analyzer import analyze_resume, extract_resume_text
from config import (
    OPENAI_API_KEY_ENV,
    OPENAI_MODEL_ENV,
    get_openai_api_key,
    get_openai_model,
)


st.set_page_config(page_title="Resume Matcher", page_icon="📄", layout="wide")
st.title("Resume Matcher")
st.write(
    "Compare a resume with a job description to see the strongest matches, "
    "missing skills, and an application recommendation."
)
st.info(
    "Text extracted from your resume and the job description are sent to OpenAI "
    "for analysis and are not stored by this app. Only submit information you "
    "are comfortable sharing."
)

with st.sidebar:
    st.header("Model settings")
    api_key = st.text_input(
        "OpenAI API key",
        value=get_openai_api_key(),
        type="password",
        help=(
            f"Set {OPENAI_API_KEY_ENV} in your environment or enter a key here. "
            "For a public app, do not add a personal key as a shared secret; "
            "visitors could use it and incur charges on your account."
        ),
    )
    model = st.text_input(
        "Model",
        value=get_openai_model(),
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
    )

if st.button("Compare", type="primary", use_container_width=True):
    if resume_file is None:
        st.error("Upload a resume file before comparing.")
    elif not job_description.strip():
        st.error("Enter a job description before comparing.")
    elif not api_key.strip():
        st.error("Enter an OpenAI API key in Model settings.")
    else:
        try:
            with st.status("Preparing resume analysis...", expanded=True) as progress:
                progress.write("Extracting text from the uploaded resume.")
                resume = extract_resume_text(
                    resume_file.name,
                    resume_file.getvalue(),
                )
                progress.write("Checking the resume and job description.")
                result = analyze_resume(
                    resume=resume,
                    job_description=job_description,
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
        else:
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
