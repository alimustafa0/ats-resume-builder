from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.resumes.forms import ResumeUploadForm
from apps.resumes.models import Resume
from apps.resumes.tasks import process_resume_task


@login_required
def upload_resume(request):
    """Save an uploaded resume for the current user, enqueue parsing."""
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.original_filename = request.FILES["original_file"].name
            resume.save()
            process_resume_task.enqueue(str(resume.pk))
            return redirect("resumes:detail", pk=resume.pk)
    else:
        form = ResumeUploadForm()
    return render(request, "resumes/upload.html", {"form": form})


@login_required
def resume_detail(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    return render(request, "resumes/detail.html", {"resume": resume})


@login_required
def resume_status(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    return render(request, "resumes/_status.html", {"resume": resume})