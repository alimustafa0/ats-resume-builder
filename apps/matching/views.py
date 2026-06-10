from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.core.services.ai_client import AIClientError
from apps.jobs.models import JobDescription
from apps.matching.services.match import score_and_save
from apps.resumes.models import Resume


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