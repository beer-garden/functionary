from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.models import Environment, Package


class EnvironmentListView(ListView):
    model = Environment

    def get_queryset(self):
        """Sorts based on team name, then env name."""

        return (super().get_queryset().order_by('team__name', 'name'))


class EnvironmentDetailView(DetailView):
    model = Environment

    def get_context_data(self, **kwargs):
        print(f"self: {dir(self)!r}")
        teams = [self.get_object().team]
        context = super().get_context_data(**kwargs)
        context["packages"] = Package.objects.filter(environment=self.get_object())
        context["teams"] = teams
        return context