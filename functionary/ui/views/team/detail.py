from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.detail import DetailView

from core.auth import Permission
from core.models import Team, Variable
from ui.tables.team_user import TeamUserTable
from ui.tables.variables import VariableTable
from ui.views.team.utils import get_user_roles


class TeamDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team: Team = self.get_object()
        user_details = get_user_roles(team)

        # Sort users by their username
        user_details.sort(key=lambda x: x["user"].username)

        context["team_id"] = str(team.id)
        context["environments"] = team.environments.all()
        context["variable_table"] = VariableTable(
            team.vars.all()
            if self.request.user.has_perm(Permission.VARIABLE_READ, team)
            else Variable.objects.none()
        )
        context["user_table"] = TeamUserTable(user_details)
        return context

    def test_func(self):
        return self.request.user.has_perm(Permission.TEAM_READ, self.get_object())
