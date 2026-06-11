from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import CreateView

from apps.accounts.forms import CustomUserCreationForm


class SignupView(CreateView):
    """Create an account and log the new user straight in."""

    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response