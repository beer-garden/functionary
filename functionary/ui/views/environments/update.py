from django.urls import reverse

from core.models import EnvironmentUserRole
from ui.forms.environments import EnvironmentUserRoleForm
from ui.views.generic import PermissionedUpdateView

from .utils import get_user_role


class EnvironmentUserRoleUpdateView(PermissionedUpdateView):
    model = EnvironmentUserRole
    permissioned_model = "Environment"
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
