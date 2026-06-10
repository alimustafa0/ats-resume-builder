from django.shortcuts import get_object_or_404, redirect, render

from apps.jobs.forms import JobDescriptionForm
from apps.jobs.models import JobDescription
from apps.jobs.tasks import process_job_description_task


def paste_job(request):
    """Save a pasted posting, enqueue extraction, go to its detail page."""
    if request.method == "POST":
        form = JobDescriptionForm(request.POST)
        if form.is_valid():
            job = form.save()
            process_job_description_task.enqueue(str(job.pk))
            return redirect("jobs:detail", pk=job.pk)
    else:
        form = JobDescriptionForm()
    return render(request, "jobs/paste.html", {"form": form})


def job_detail(request, pk):
    """Show a posting's extraction status and parsed requirements."""
    job = get_object_or_404(JobDescription, pk=pk)
    return render(request, "jobs/detail.html", {"job": job})


def job_status(request, pk):
    """Return just the status fragment -- the endpoint HTMX polls."""
    job = get_object_or_404(JobDescription, pk=pk)
    return render(request, "jobs/_status.html", {"job": job})