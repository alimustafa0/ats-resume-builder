"""Job description extraction service.

Turns a job posting's raw text into structured requirements using Gemini's
JSON mode, bound to a Pydantic schema. Mirrors the resume extractor: the schema
is the contract, enforced on output and re-validated on input.
"""

from __future__ import annotations

import json

from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from apps.core.services.ai_client import AIClientError, generate_text


class JobRequirements(BaseModel):
    job_title: str = ""
    seniority: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


_EXTRACTION_PROMPT = """You are an expert technical recruiter. Extract the key requirements from the job posting below into the required structured format.

Rules:
- Use the wording from the posting; do not paraphrase skills or qualifications.
- Separate hard requirements (required_skills) from nice-to-haves (preferred_skills) using the posting's own language -- "must have" / "required" versus "preferred" / "bonus" / "nice to have".
- keywords should capture the important ATS terms a candidate is screened on: skills, tools, certifications, and domain terms.
- If a field is not present, leave it as an empty string or empty list -- never invent or infer.

Job posting:
-----
{raw_text}
-----
"""


def extract_job_data(raw_text: str) -> dict:
    """Extract structured requirements from a job posting's raw text.

    Returns a plain dict suitable for storing in ``JobDescription.structured_data``.

    Raises:
        AIClientError: if the model call fails or returns unusable output.
    """
    prompt = _EXTRACTION_PROMPT.format(raw_text=raw_text)
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=JobRequirements,
    )

    raw_json = generate_text(prompt, config=config)

    try:
        parsed = JobRequirements.model_validate_json(raw_json)
    except (ValidationError, json.JSONDecodeError) as exc:
        raise AIClientError(f"Gemini returned malformed job data: {exc}") from exc

    return parsed.model_dump()