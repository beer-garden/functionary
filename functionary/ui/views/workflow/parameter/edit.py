from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Workflow, WorkflowParameter
from ui.views.generic import PermissionedCreateView, PermissionedUpdateView


class WorkflowParameterFormViewMixin:
    """Mixin for shared logic related to creation and update of WorkflowParameters"""

    model = WorkflowParameter
    permissioned_model = "Workflow"
    environment_through_field = "workflow"
    template_name = "forms/workflow/parameter_edit.html"
    fields = "__all__"

    def form_valid(self, form):
        """Valid form handler"""
        parameter = form.save()
        messages.success(self.request, "Workflow saved.")

        success_url = reverse(
            "ui:workflow-update", kwargs={"pk": parameter.workflow.pk}
        )
        return HttpResponseClientRedirect(success_url)

    def get_context_data(self, **kwargs):
        """Custom context which includes the Workflow"""
        context = super().get_context_data(**kwargs)
        context["workflow"] = get_object_or_404(
            Workflow, pk=self.kwargs.get("workflow_pk")
        )

        return context

    def test_func(self):
        """Permission check for access to the view"""
        workflow = get_object_or_404(Workflow, id=self.kwargs.get("workflow_pk"))
        return self.request.user.has_perm(
            self.required_permission, workflow.environment
        )


class WorkflowParameterCreateView(
    WorkflowParameterFormViewMixin, PermissionedCreateView
):
    """Create view for the WorkflowParameter model"""

    required_permission = Permission.WORKFLOW_CREATE


class WorkflowParameterUpdateView(
    WorkflowParameterFormViewMixin, PermissionedUpdateView
):
    """Update view for the WorkflowParameter model"""

    required_permission = Permission.WORKFLOW_UPDATE
    fields = ["name", "description", "parameter_type", "default", "required"]
