from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.edit import DeleteView

from core.auth import Permission
from core.models import Team, TeamUserRole


class TeamUserRoleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TeamUserRole

    def get_success_url(self) -> str:
        return reverse("ui:team-detail", kwargs={"pk": self.kwargs.get("team_pk")})

    def test_func(self) -> bool:
        team = get_object_or_404(Team, id=self.kwargs["team_pk"])
        return self.request.user.has_perm(Permission.TEAM_UPDATE, team)
