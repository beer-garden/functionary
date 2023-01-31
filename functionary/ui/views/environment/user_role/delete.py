from django.urls import reverse

from core.models import EnvironmentUserRole
from ui.views.generic import PermissionedDeleteView


class EnvironmentUserRoleDeleteView(PermissionedDeleteView):
    model = EnvironmentUserRole
    permissioned_model = "Environment"

    def get_success_url(self) -> str:
        environment_user_role: EnvironmentUserRole = self.get_object()
        return reverse(
            "ui:environment-detail", kwargs={"pk": environment_user_role.environment.id}
        )
