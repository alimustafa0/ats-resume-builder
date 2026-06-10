from django import forms

from apps.resumes.models import Resume


class ResumeUploadForm(forms.ModelForm):
    """Single-field upload form; the model's PDF validator enforces type."""

    class Meta:
        model = Resume
        fields = ["original_file"]
        widgets = {
            "original_file": forms.ClearableFileInput(attrs={"accept": ".pdf"}),
        }