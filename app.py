import streamlit as st

from analyzer import analyze_resume
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

with st.sidebar:
    st.header("Model settings")
    api_key = st.text_input(
        "OpenAI API key",
        value=get_openai_api_key(),
        type="password",
        help=(
            f"Set {OPENAI_API_KEY_ENV} in your environment or Streamlit secrets, "
            "or enter a key here. The app does not save it."
        ),
    )
    model = st.text_input(
        "Model",
        value=get_openai_model(),
        help=f"Set {OPENAI_MODEL_ENV} to change the default model.",
    )

resume_column, job_column = st.columns(2)
with resume_column:
    resume = st.text_area(
        "Resume",
        placeholder="Paste the resume text here...",
        height=360,
    )
with job_column:
    job_description = st.text_area(
        "Job description",
        placeholder="Paste the job description here...",
        height=360,
    )

if st.button("Compare", type="primary", use_container_width=True):
    if not resume.strip():
        st.error("Enter resume text before comparing.")
    elif not job_description.strip():
        st.error("Enter a job description before comparing.")
    elif not api_key.strip():
        st.error("Enter an OpenAI API key in Model settings.")
    else:
        try:
            with st.status("Preparing resume analysis...", expanded=True) as progress:
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
