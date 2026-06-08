import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class Resume(models.Model):
    """A single uploaded résumé and the full state of its parsing pipeline.

    This row is the hand-off between a synchronous upload and an asynchronous
    AI task: a view creates it and enqueues a task; the worker then advances
    `status` while filling `raw_text` (pypdf) and `structured_data` (Gemini).
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
        related_name="resumes",
        null=True,
        blank=True,
    )

    original_file = models.FileField(
        upload_to="resumes/%Y/%m/%d/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )
    original_filename = models.CharField(max_length=255, blank=True)

    raw_text = models.TextField(
        blank=True,
        help_text="Plain text extracted from the uploaded PDF by pypdf.",
    )
    structured_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured résumé data extracted by Gemini.",
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
        return self.original_filename or f"Resume {self.pk}"