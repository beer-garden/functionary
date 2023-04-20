from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect

from core.models import EnvironmentUserRole
from ui.forms.environments import EnvironmentUserRoleForm
from ui.views.generic import PermissionedUpdateView


class EnvironmentUserRoleUpdateView(PermissionedUpdateView):
    model = EnvironmentUserRole
    permissioned_model = "Environment"
    form_class = EnvironmentUserRoleForm
    template_name = "forms/environment/environmentuserrole_update.html"

    def get_success_url(self) -> str:
        return reverse(
            "ui:environment-detail", kwargs={"pk": self.kwargs.get("environment_pk")}
        )

    def form_valid(self, form):
        """Valid form handler"""
        form.save()
        return HttpResponseClientRedirect(self.get_success_url())
