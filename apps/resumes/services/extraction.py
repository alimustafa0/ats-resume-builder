"""Resume extraction service.

Turns the raw text of a resume into structured data using Gemini's JSON mode,
bound to an explicit Pydantic schema. The schema *is* the contract: Gemini is
constrained to it on output, and we re-validate against it on input before
returning a plain dict for storage.
"""

from __future__ import annotations

import json

from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from apps.core.services.ai_client import AIClientError, generate_text


class ContactInfo(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""


class ExperienceItem(BaseModel):
    job_title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    responsibilities: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    degree: str = ""
    institution: str = ""
    start_date: str = ""
    end_date: str = ""
    details: str = ""


class ResumeData(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


_EXTRACTION_PROMPT = """You are an expert resume parser. Extract the candidate's information from the resume text below into the required structured format.

Rules:
- Use the wording from the resume; do not paraphrase job titles or skills.
- If a field is not present, leave it empty -- never invent or infer data.
- Capture every distinct work experience and education entry.

Resume text:
-----
{raw_text}
-----
"""


def extract_resume_data(raw_text: str) -> dict:
    """Extract structured resume data from raw text.

    Returns a plain dict suitable for storing in ``Resume.structured_data``.

    Raises:
        AIClientError: if the model call fails or returns unusable output.
    """
    prompt = _EXTRACTION_PROMPT.format(raw_text=raw_text)
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ResumeData,
    )

    raw_json = generate_text(prompt, config=config)

    try:
        parsed = ResumeData.model_validate_json(raw_json)
    except (ValidationError, json.JSONDecodeError) as exc:
        raise AIClientError(
            f"Gemini returned malformed resume data: {exc}"
        ) from exc

    return parsed.model_dump()