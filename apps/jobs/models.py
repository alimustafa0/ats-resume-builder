import uuid

from django.conf import settings
from django.db import models


class JobDescription(models.Model):
    """A target job posting and the state of its AI extraction pipeline.

    The user supplies `raw_text` (the pasted posting); a background task then
    advances `status` and fills `structured_data` with the requirements and
    keywords Gemini extracts. Phase 4 scores a résumé against this record.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_descriptions",
    )

    title = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(blank=True)

    raw_text = models.TextField(
        help_text="The job posting text supplied by the user.",
    )
    structured_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Requirements and keywords extracted by Gemini.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(
        blank=True,
        help_text="Failure detail captured when status is FAILED.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return self.title or f"Job Description {self.pk}"