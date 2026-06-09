"""Background tasks for the resumes app."""

from django.tasks import task

from apps.resumes.models import Resume
from apps.resumes.services.processing import process_resume


@task()
def process_resume_task(resume_id: str) -> None:
    """Background entry point: load a Resume by id and run its pipeline."""
    resume = Resume.objects.get(pk=resume_id)
    process_resume(resume)