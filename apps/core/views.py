from django.shortcuts import render


def home(request):
    """Landing page."""
    return render(request, "core/home.html")