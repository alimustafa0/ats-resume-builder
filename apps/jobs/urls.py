from django.urls import path

from apps.jobs import views

app_name = "jobs"

urlpatterns = [
    path("jobs/new/", views.paste_job, name="new"),
    path("jobs/<uuid:pk>/", views.job_detail, name="detail"),
    path("jobs/<uuid:pk>/status/", views.job_status, name="status"),
]