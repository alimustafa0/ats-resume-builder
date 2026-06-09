"""Job description processing orchestration."""

from __future__ import annotations

from apps.core.services.processing import processing_lifecycle
from apps.jobs.models import JobDescription
from apps.jobs.services.extraction import extract_job_data


def process_job_description(job: JobDescription) -> None:
    """Run the extraction pipeline for one job description, updating its status."""
    with processing_lifecycle(job):
        job.structured_data = extract_job_data(job.raw_text)