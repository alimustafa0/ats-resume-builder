from django import forms

from apps.jobs.models import JobDescription


class JobDescriptionForm(forms.ModelForm):
    """Paste form for a posting; raw_text is required by the model."""

    class Meta:
        model = JobDescription
        fields = ["title", "company", "raw_text"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g. Senior Python Engineer"}),
            "company": forms.TextInput(attrs={"placeholder": "Company (optional)"}),
            "raw_text": forms.Textarea(
                attrs={"rows": 14, "placeholder": "Paste the full job description here..."}
            ),
        }
        labels = {"raw_text": "Job description"}