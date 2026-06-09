"""Resume processing orchestration.

The end-to-end pipeline for a single resume: extract text from the PDF, send
it to Gemini for structured extraction, and persist the result while advancing
the status lifecycle. This is plain business logic -- callable directly in a
shell or a test, with the background task as a thin wrapper around it.
"""

from __future__ import annotations

from apps.core.services.text_extraction import extract_text_from_pdf
from apps.resumes.models import Resume
from apps.resumes.services.extraction import extract_resume_data


def process_resume(resume: Resume) -> None:
    """Run the full extraction pipeline for one resume, updating its status.

    Advances status to PROCESSING, then COMPLETED on success, or FAILED with a
    stored error message on any failure. Safe to re-run.
    """
    resume.status = Resume.Status.PROCESSING
    resume.error_message = ""
    resume.save(update_fields=["status", "error_message", "updated_at"])

    try:
        with resume.original_file.open("rb") as fh:
            raw_text = extract_text_from_pdf(fh)

        structured_data = extract_resume_data(raw_text)

        resume.raw_text = raw_text
        resume.structured_data = structured_data
        resume.status = Resume.Status.COMPLETED
        resume.save(
            update_fields=["raw_text", "structured_data", "status", "updated_at"]
        )
    except Exception as exc:
        # Persist the failure so the row never stays stuck in PROCESSING,
        # then re-raise so the worker logs the full traceback.
        resume.status = Resume.Status.FAILED
        resume.error_message = str(exc)
        resume.save(update_fields=["status", "error_message", "updated_at"])
        raise