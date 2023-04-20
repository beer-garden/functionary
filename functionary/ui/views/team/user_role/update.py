from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.edit import UpdateView
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Team, TeamUserRole
from ui.forms.teams import TeamUserRoleForm


class TeamUserRoleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TeamUserRole
    form_class = TeamUserRoleForm
    template_name = "forms/team/teamuserrole_update.html"

    def get_success_url(self) -> str:
        return reverse("ui:team-detail", kwargs={"pk": self.kwargs.get("team_pk")})

    def form_valid(self, form):
        """Valid form handler"""
        form.save()
        return HttpResponseClientRedirect(self.get_success_url())

    def test_func(self) -> bool:
        team = get_object_or_404(Team, id=self.kwargs["team_pk"])
        return self.request.user.has_perm(Permission.TEAM_UPDATE, team)
