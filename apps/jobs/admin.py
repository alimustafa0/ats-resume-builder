from django.contrib import admin

from apps.jobs.models import JobDescription


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "company", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "company", "raw_text")
    readonly_fields = ("id", "created_at", "updated_at")