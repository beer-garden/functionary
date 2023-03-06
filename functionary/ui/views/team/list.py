from django.contrib.auth.mixins import LoginRequiredMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from core.models import Team
from ui.tables.team import TeamFilter, TeamTable

PAGINATION_AMOUNT = 15


class TeamListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = Team
    table_class = TeamTable
    paginate_by = PAGINATION_AMOUNT
    template_name = "default_list.html"
    filterset_class = TeamFilter
