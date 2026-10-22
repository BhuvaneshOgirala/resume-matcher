import streamlit as st

from analyzer import analyze_resume, extract_resume_text


st.set_page_config(page_title="Resume Matcher", page_icon="📄", layout="wide")
st.title("Resume Matcher")
st.write(
    "Compare a resume with a job description to see recognized skill matches, "
    "gaps, and a practical next-step recommendation."
)
st.success(
    "Free to use: analysis runs locally in this app. No API key or sign-in is "
    "required, and resume text is not sent to an AI provider."
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

with st.expander("How the free match score works"):
    st.write(
        "The matcher runs locally and checks a built-in list of skills and common "
        "synonyms. It does not understand context as well as an AI model, so "
        "related wording may not be recognized. The score is the weighted share "
        "of recognized job-description skills found in the resume; requirements "
        "marked as required count more, while preferred skills count less. Treat "
        "the result as a quick guide, not a hiring decision."
    )

if st.button("Compare", type="primary", use_container_width=True):
    if resume_file is None:
        st.error("Upload a resume file before comparing.")
    elif not job_description.strip():
        st.error("Enter a job description before comparing.")
    else:
        try:
            with st.status("Comparing locally...", expanded=True) as progress:
                progress.write("Extracting text from the uploaded resume.")
                resume = extract_resume_text(resume_file.name, resume_file.getvalue())
                result = analyze_resume(
                    resume=resume,
                    job_description=job_description,
                    progress_callback=lambda message: progress.write(message),
                )
                progress.update(
                    label="Comparison complete",
                    state="complete",
                    expanded=False,
                )
        except (ValueError, RuntimeError) as error:
            st.error(str(error))
        else:
            st.subheader("Match results")
            score_column, recommendation_column = st.columns(2)
            score_column.metric("Recognized-skill match", f"{result['matching_score']}%")
            recommendation_column.metric(
                "Recommendation",
                result["recommendation"].capitalize(),
            )
            st.progress(result["matching_score"] / 100)

            strengths_column, missing_column = st.columns(2)
            with strengths_column:
                st.subheader("Matching skills")
                if result["matching_skills"]:
                    for skill in result["matching_skills"]:
                        st.markdown(f"- {skill}")
                else:
                    st.write("No recognized matching skills were found.")
            with missing_column:
                st.subheader("Missing skills")
                if result["missing_skills"]:
                    for skill in result["missing_skills"]:
                        st.markdown(f"- {skill}")
                else:
                    st.write("No recognized job skills appear to be missing.")

            st.subheader("Preparation tips")
            for tip in result["preparation_tips"]:
                st.markdown(f"- {tip}")
