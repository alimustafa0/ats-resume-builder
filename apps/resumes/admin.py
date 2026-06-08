from django.contrib import admin

from apps.resumes.models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("original_filename", "raw_text")
    readonly_fields = ("id", "created_at", "updated_at")