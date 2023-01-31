from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView

from core.models import Environment

PAGINATION_AMOUNT = 15


class EnvironmentListView(LoginRequiredMixin, ListView):
    model = Environment
    paginate_by = PAGINATION_AMOUNT

    def get_queryset(self):
        """Sorts based on team name, then env name."""
        return self.request.user.environments.select_related("team")
