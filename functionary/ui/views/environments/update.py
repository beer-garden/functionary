from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.edit import UpdateView

from core.auth import Permission
from core.models import Environment, EnvironmentUserRole
from ui.forms.environments import EnvironmentUserRoleForm

from .utils import get_user_role


class EnvironmentUserRoleUpdateView(
    LoginRequiredMixin, UserPassesTestMixin, UpdateView
):
    model = EnvironmentUserRole
    form_class = EnvironmentUserRoleForm
    template_name = "forms/environment/environmentuserrole_update.html"

    def get_success_url(self) -> str:
        return reverse(
            "ui:environment-detail", kwargs={"pk": self.kwargs.get("environment_id")}
        )

    def get_initial(self) -> dict:
        environment_user_role: EnvironmentUserRole = self.get_object()
        initial = super().get_initial()
        role, _ = get_user_role(
            environment_user_role.user, environment_user_role.environment
        )
        initial["role"] = role.role if role else initial["role"]
        return initial

    def test_func(self) -> bool:
        environment = get_object_or_404(Environment, id=self.kwargs["environment_id"])
        return self.request.user.has_perm(Permission.ENVIRONMENT_UPDATE, environment)
