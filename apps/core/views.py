from django.shortcuts import render

from apps.jobs.models import JobDescription
from apps.matching.models import MatchResult
from apps.resumes.models import Resume


def home(request):
    """Landing page for visitors; a workspace dashboard for signed-in users."""
    context = {}
    if request.user.is_authenticated:
        resumes = Resume.objects.filter(user=request.user)
        jobs = JobDescription.objects.filter(user=request.user)
        matches = MatchResult.objects.filter(user=request.user).select_related(
            "resume", "job_description"
        )
        context = {
            "resumes": resumes[:5],
            "jobs": jobs[:5],
            "matches": matches[:5],
            "resume_count": resumes.count(),
            "job_count": jobs.count(),
            "match_count": matches.count(),
        }
    return render(request, "core/home.html", context)