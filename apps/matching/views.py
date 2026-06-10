from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.services.ai_client import AIClientError
from apps.jobs.models import JobDescription
from apps.matching.models import MatchResult
from apps.matching.services.match import score_and_save
from apps.resumes.models import Resume
from apps.resumes.services.rendering import render_resume_pdf
from apps.resumes.services.tailoring import tailor_resume


def match_page(request):
    """Show the match form with completed resumes and postings."""
    resumes = Resume.objects.filter(status=Resume.Status.COMPLETED)
    jobs = JobDescription.objects.filter(status=JobDescription.Status.COMPLETED)
    return render(request, "matching/match.html", {"resumes": resumes, "jobs": jobs})


@require_POST
def run_match(request):
    """Score the chosen resume against the chosen posting (HTMX endpoint)."""
    resume = get_object_or_404(
        Resume, pk=request.POST.get("resume"), status=Resume.Status.COMPLETED
    )
    job = get_object_or_404(
        JobDescription, pk=request.POST.get("job"), status=JobDescription.Status.COMPLETED
    )
    try:
        match = score_and_save(resume, job)
    except AIClientError as exc:
        return render(request, "matching/_error.html", {"error": str(exc)})
    return render(request, "matching/_result.html", {"match": match})


@require_POST
def tailor_match(request, pk):
    """Tailor the match's resume toward its job, store it, return a preview."""
    match = get_object_or_404(MatchResult, pk=pk)
    try:
        tailored = tailor_resume(
            match.resume.structured_data, match.job_description.structured_data
        )
    except AIClientError as exc:
        return render(request, "matching/_error.html", {"error": str(exc)})
    match.tailored_data = tailored
    match.save(update_fields=["tailored_data", "updated_at"])
    return render(request, "matching/_tailored.html", {"match": match})


def download_tailored(request, pk):
    """Render the stored tailored resume as an ATS-ready PDF download."""
    match = get_object_or_404(MatchResult, pk=pk)
    if not match.tailored_data:
        return redirect("matching:match")
    pdf_bytes = render_resume_pdf(match.tailored_data)
    name = (match.tailored_data.get("contact", {}) or {}).get("full_name", "") or "resume"
    filename = f"{name.replace(' ', '_')}_tailored.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response