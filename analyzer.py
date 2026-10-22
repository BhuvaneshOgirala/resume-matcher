from io import BytesIO
import json
from typing import Any, Callable, Literal, TypedDict
from zipfile import BadZipFile

from openai import OpenAI
from openai import OpenAIError

from config import get_openai_api_key, get_openai_model
from prompts import RESUME_ANALYSIS_INSTRUCTIONS

MAX_INPUT_LENGTH = 30_000
MAX_RESUME_FILE_SIZE = 10 * 1024 * 1024


class ResumeAnalysis(TypedDict):
    matching_score: int
    matching_skills: list[str]
    missing_skills: list[str]
    recommendation: Literal["apply", "pass"]
    preparation_tips: list[str]


def extract_resume_text(file_name: str, file_content: bytes) -> str:
    """Extract text from a PDF, DOCX, or plain-text resume upload."""
    if not file_content:
        raise ValueError("The uploaded resume file is empty.")
    if len(file_content) > MAX_RESUME_FILE_SIZE:
        raise ValueError("Resume files must be 10 MB or smaller.")

    extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if extension == "txt":
        try:
            text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError("The text file must use UTF-8 encoding.") from error
    elif extension == "pdf":
        try:
            from pypdf import PdfReader
            from pypdf.errors import PdfReadError
        except ImportError as error:
            raise RuntimeError("PDF uploads require the pypdf package.") from error

        try:
            reader = PdfReader(BytesIO(file_content))
            if reader.is_encrypted:
                raise ValueError("Password-protected PDF resumes are not supported.")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except PdfReadError as error:
            raise ValueError("The uploaded PDF could not be read.") from error
    elif extension == "docx":
        try:
            from docx import Document
            from docx.opc.exceptions import PackageNotFoundError
        except ImportError as error:
            raise RuntimeError("Word uploads require the python-docx package.") from error

        try:
            document = Document(BytesIO(file_content))
        except (PackageNotFoundError, BadZipFile) as error:
            raise ValueError("The uploaded Word document could not be read.") from error

        text_parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            text_parts.extend(
                cell.text for row in table.rows for cell in row.cells
            )
        text = "\n".join(text_parts)
    else:
        raise ValueError("Upload a PDF, DOCX, or TXT resume file.")

    if not text.strip():
        if extension == "pdf":
            raise ValueError(
                "No selectable text was found in the PDF. Scanned PDFs need OCR "
                "before they can be analyzed."
            )
        raise ValueError("No text was found in the uploaded resume.")
    return text


def analyze_resume(
    resume: str,
    job_description: str,
    api_key: str | None = None,
    model: str | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> ResumeAnalysis:
    """Compare a resume and job description using the configured OpenAI model."""
    resume, job_description = validate_analysis_inputs(resume, job_description)

    resolved_api_key = get_openai_api_key(api_key)
    if not resolved_api_key:
        raise ValueError(
            "Provide an OpenAI API key or configure it as OPENAI_API_KEY."
        )

    if progress_callback:
        progress_callback("Sending resume and job description to OpenAI...")
    client = OpenAI(api_key=resolved_api_key)
    try:
        response = client.chat.completions.create(
            model=get_openai_model(model),
            messages=[
                {"role": "system", "content": RESUME_ANALYSIS_INSTRUCTIONS},
                {
                    "role": "user",
                    "content": (
                        "Compare the following resume and job description.\n\n"
                        f"<resume>\n{resume}\n</resume>\n\n"
                        f"<job_description>\n{job_description}\n</job_description>"
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except OpenAIError as error:
        raise RuntimeError(
            "OpenAI could not complete the analysis. Check your API key, model name, "
            "account access, and connection, then try again."
        ) from error

    if not response.choices:
        raise RuntimeError("The model returned no analysis choices. Please try again.")
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The model returned an empty analysis. Please try again.")
    if progress_callback:
        progress_callback("Validating the structured analysis...")
    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError("The model returned an invalid analysis. Please try again.") from error
    return _validate_result(result)


def validate_analysis_inputs(resume: str, job_description: str) -> tuple[str, str]:
    """Trim and validate both documents before reserving paid analysis usage."""
    resume = resume.strip()
    job_description = job_description.strip()
    if not resume:
        raise ValueError("Resume text cannot be empty.")
    if not job_description:
        raise ValueError("Job description cannot be empty.")
    if len(resume) > MAX_INPUT_LENGTH:
        raise ValueError(f"Resume text must be {MAX_INPUT_LENGTH:,} characters or fewer.")
    if len(job_description) > MAX_INPUT_LENGTH:
        raise ValueError(
            f"Job description must be {MAX_INPUT_LENGTH:,} characters or fewer."
        )
    return resume, job_description


def _validate_result(result: Any) -> ResumeAnalysis:
    if not isinstance(result, dict):
        raise RuntimeError("The model returned an unexpected analysis format.")

    score = result.get("matching_score")
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise RuntimeError("The model returned an invalid match score.")

    matching_skills = _validate_string_list(
        result.get("matching_skills"), "matching skills"
    )
    missing_skills = _validate_string_list(result.get("missing_skills"), "missing skills")
    preparation_tips = _validate_string_list(
        result.get("preparation_tips"), "preparation tips"
    )
    if len(preparation_tips) != 3:
        raise RuntimeError("The model must return exactly three preparation tips.")

    recommendation = result.get("recommendation")
    if not isinstance(recommendation, str) or recommendation not in {"apply", "pass"}:
        raise RuntimeError("The model returned an invalid recommendation.")

    return {
        "matching_score": score,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "recommendation": recommendation,
        "preparation_tips": preparation_tips,
    }


def _validate_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise RuntimeError(f"The model returned an invalid list of {label}.")
    return [item.strip() for item in value]
