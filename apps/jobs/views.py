from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.jobs.forms import JobDescriptionForm
from apps.jobs.models import JobDescription
from apps.jobs.tasks import process_job_description_task


@login_required
def paste_job(request):
    """Save a pasted posting for the current user, enqueue extraction."""
    if request.method == "POST":
        form = JobDescriptionForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.save()
            process_job_description_task.enqueue(str(job.pk))
            return redirect("jobs:detail", pk=job.pk)
    else:
        form = JobDescriptionForm()
    return render(request, "jobs/paste.html", {"form": form})


@login_required
def job_detail(request, pk):
    job = get_object_or_404(JobDescription, pk=pk, user=request.user)
    return render(request, "jobs/detail.html", {"job": job})


@login_required
def job_status(request, pk):
    job = get_object_or_404(JobDescription, pk=pk, user=request.user)
    return render(request, "jobs/_status.html", {"job": job})