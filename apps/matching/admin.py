from django.contrib import admin

from apps.matching.models import MatchResult


@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ("__str__", "score", "resume", "job_description", "created_at")
    list_filter = ("created_at",)
    readonly_fields = ("id", "created_at", "updated_at")