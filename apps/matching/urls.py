from django.urls import path

from apps.matching import views

app_name = "matching"

urlpatterns = [
    path("match/", views.match_page, name="match"),
    path("match/run/", views.run_match, name="run"),
]