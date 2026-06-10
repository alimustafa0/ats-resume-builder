import uuid

from django.conf import settings
from django.db import models


class MatchResult(models.Model):
    """A scored match between a resume and a job description."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="match_results",
        null=True,
        blank=True,
    )
    resume = models.ForeignKey(
        "resumes.Resume",
        on_delete=models.CASCADE,
        related_name="match_results",
    )
    job_description = models.ForeignKey(
        "jobs.JobDescription",
        on_delete=models.CASCADE,
        related_name="match_results",
    )

    score = models.FloatField(default=0.0)
    breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full required/preferred matched/missing detail from the scorer.",
    )

    tailored_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Resume structured data rewritten toward this job.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["resume", "job_description"],
                name="unique_resume_job_match",
            ),
        ]
        indexes = [models.Index(fields=["-score"])]

    def __str__(self) -> str:
        return f"Match {self.score} ({self.resume_id} vs {self.job_description_id})"