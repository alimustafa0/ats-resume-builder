"""Resume tailoring service.

Rewrites a resume's structured data to align with a specific job description --
re-emphasising and re-phrasing the candidate's *existing* experience toward the
role, without inventing anything. The output uses the same ResumeData schema as
extraction, so a tailored resume flows through the renderer unchanged.
"""

from __future__ import annotations

import json

from google.genai import types
from pydantic import ValidationError

from apps.core.services.ai_client import AIClientError, generate_text
from apps.resumes.services.extraction import ResumeData

_TAILORING_PROMPT = """You are an expert resume writer tailoring a candidate's resume for a specific job. Rewrite the resume so it speaks directly to the target role, while remaining strictly truthful.

Absolute rules -- breaking any of these makes the result useless:
- Never invent, add, or exaggerate experience, employers, job titles, dates, degrees, certifications, or skills. Every fact must already be present in the original resume.
- Keep all employers, job titles, dates, and education entries EXACTLY as written in the original. Do not alter, merge, or reorder employment history.
- Do not add skills the candidate does not already list. You may reorder skills to put the most role-relevant first, but the set must stay truthful.
- Only rephrase. Where the candidate's real work matches the job's language, you may describe it using the job's terminology -- but only when it honestly describes what they did.

What to do:
- Rewrite the professional summary to foreground the experience and strengths most relevant to this job.
- Rephrase the bullet points under each experience to emphasise the responsibilities and achievements that matter most for this role, using the original facts.
- Reorder the skills so the ones this job calls for appear first.

Target job:
-----
Title: {job_title}
Seniority: {seniority}
Required skills: {required_skills}
Preferred skills: {preferred_skills}
Key responsibilities: {responsibilities}
Keywords: {keywords}
-----

Original resume (JSON):
-----
{resume_json}
-----

Return the tailored resume in the required structured format.
"""


def tailor_resume(structured_data: dict, job_data: dict) -> dict:
    """Rewrite `structured_data` to target the role described by `job_data`.

    Returns a new structured-data dict in the ResumeData shape. Raises
    AIClientError if the model call fails or returns unusable output.
    """
    prompt = _TAILORING_PROMPT.format(
        job_title=job_data.get("job_title", ""),
        seniority=job_data.get("seniority", ""),
        required_skills=", ".join(job_data.get("required_skills", [])),
        preferred_skills=", ".join(job_data.get("preferred_skills", [])),
        responsibilities="; ".join(job_data.get("responsibilities", [])),
        keywords=", ".join(job_data.get("keywords", [])),
        resume_json=json.dumps(structured_data, ensure_ascii=False),
    )
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ResumeData,
        temperature=0.2,
    )

    raw_json = generate_text(prompt, config=config)

    try:
        parsed = ResumeData.model_validate_json(raw_json)
    except (ValidationError, json.JSONDecodeError) as exc:
        raise AIClientError(f"Gemini returned malformed tailored resume: {exc}") from exc

    return parsed.model_dump()