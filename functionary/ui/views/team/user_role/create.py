from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import CreateView
from django_htmx.http import HttpResponseClientRedirect
from rapidfuzz import process

from core.auth import Permission
from core.models import Team, TeamUserRole, User
from ui.forms.teams import TeamUserRoleForm


class TeamUserRoleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TeamUserRole
    form_class = TeamUserRoleForm
    template_name = "forms/team/teamuserrole_create.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["team_id"] = self.kwargs.get("team_pk")
        return context

    def get_success_url(self) -> str:
        return reverse("ui:team-detail", kwargs={"pk": self.kwargs.get("team_pk")})

    def form_valid(self, form):
        """Valid form handler"""
        form.save()
        return HttpResponseClientRedirect(self.get_success_url())

    def test_func(self) -> bool:
        team = get_object_or_404(Team, id=self.kwargs["team_pk"])
        return self.request.user.has_perm(Permission.TEAM_UPDATE, team)


# NOTE: Enventually move this method somewhere more appropriate
@require_GET
@login_required
def get_users(request: HttpRequest) -> HttpResponse:
    username = request.GET.get("user")
    users = User.objects.all()

    if username == "":
        context = {"usernames": [], "username": username}
        return render(request, "partials/teams/user_list.html", context)

    results = process.extract(
        username, [user.username for user in users], score_cutoff=50
    )

    context = {"usernames": [result[0] for result in results], "username": username}
    return render(request, "partials/teams/user_list.html", context)
