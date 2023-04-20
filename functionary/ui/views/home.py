from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import RedirectView


class HomeView(LoginRequiredMixin, RedirectView):
    pattern_name = "ui:task-list"
