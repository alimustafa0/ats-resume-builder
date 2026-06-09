"""Background tasks for the jobs app."""

from django.tasks import task

from apps.jobs.models import JobDescription
from apps.jobs.services.processing import process_job_description


@task()
def process_job_description_task(job_id: str) -> None:
    """Background entry point: load a JobDescription by id and run its pipeline."""
    job = JobDescription.objects.get(pk=job_id)
    process_job_description(job)