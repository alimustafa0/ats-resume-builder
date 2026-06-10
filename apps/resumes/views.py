from django.shortcuts import get_object_or_404, redirect, render

from apps.resumes.forms import ResumeUploadForm
from apps.resumes.models import Resume
from apps.resumes.tasks import process_resume_task


def upload_resume(request):
    """Save an uploaded resume, enqueue parsing, and go to its detail page."""
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.original_filename = request.FILES["original_file"].name
            resume.save()
            process_resume_task.enqueue(str(resume.pk))
            return redirect("resumes:detail", pk=resume.pk)
    else:
        form = ResumeUploadForm()
    return render(request, "resumes/upload.html", {"form": form})


def resume_detail(request, pk):
    """Show a resume's processing status and, once ready, its parsed summary."""
    resume = get_object_or_404(Resume, pk=pk)
    return render(request, "resumes/detail.html", {"resume": resume})