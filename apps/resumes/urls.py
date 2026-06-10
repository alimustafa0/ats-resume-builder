from django.urls import path

from apps.resumes import views

app_name = "resumes"

urlpatterns = [
    path("resumes/upload/", views.upload_resume, name="upload"),
    path("resumes/<uuid:pk>/", views.resume_detail, name="detail"),
]