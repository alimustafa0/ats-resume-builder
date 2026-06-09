"""Resume processing orchestration."""

from __future__ import annotations

from apps.core.services.processing import processing_lifecycle
from apps.core.services.text_extraction import extract_text_from_pdf
from apps.resumes.models import Resume
from apps.resumes.services.extraction import extract_resume_data


def process_resume(resume: Resume) -> None:
    """Run the full extraction pipeline for one resume, updating its status."""
    with processing_lifecycle(resume):
        with resume.original_file.open("rb") as fh:
            resume.raw_text = extract_text_from_pdf(fh)
        resume.structured_data = extract_resume_data(resume.raw_text)