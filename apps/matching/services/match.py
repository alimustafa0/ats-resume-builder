"""Persisting match scores."""

from __future__ import annotations

from apps.jobs.models import JobDescription
from apps.matching.models import MatchResult
from apps.matching.services.semantic import score_resume_against_job_semantic
from apps.resumes.models import Resume


def score_and_save(resume: Resume, job_description: JobDescription) -> MatchResult:
    """Score a resume against a job description and persist the result.

    Re-scoring the same pair updates the existing row. Raises AIClientError if
    the semantic pass fails.
    """
    result = score_resume_against_job_semantic(
        resume.structured_data, job_description.structured_data
    )
    match, _ = MatchResult.objects.update_or_create(
        resume=resume,
        job_description=job_description,
        defaults={
            "user": resume.user,
            "score": result["score"],
            "breakdown": result,
        },
    )
    return match