from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Environment, Workflow
from ui.forms import WorkflowUpdateForm
from ui.tables.workflow_parameter import WorflowParameterTable
from ui.tables.workflow_step import WorflowStepTable
from ui.views.generic import PermissionedUpdateView


class WorkflowUpdateView(PermissionedUpdateView):
    """View to handle updates of Workflow details"""

    model = Workflow
    template_name = "forms/workflow/workflow_edit.html"
    form_class = WorkflowUpdateForm

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Workflow saved.")

        success_url = reverse("ui:workflow-update", kwargs={"pk": form.instance.pk})
        return HttpResponseClientRedirect(
            success_url,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["parameter_table"] = WorflowParameterTable(self.object.parameters.all())
        context["step_table"] = WorflowStepTable(
            data=self.object.ordered_steps,
            workflow_pk=self.object.pk,
        )
        context["breadcrumbs"] = [
            {
                "label": "Workflows",
                "url": reverse("ui:workflow-list"),
            },
            {"label": self.object.name},
        ]

        return context


@require_POST
@login_required
def update_status(request: HttpRequest, pk):
    """Archive or unarchive a workflow"""

    env = Environment.objects.get(id=request.session.get("environment_id"))
    if not request.user.has_perm(Permission.WORKFLOW_UPDATE, env):
        return HttpResponseForbidden()

    workflow = get_object_or_404(Workflow, pk=pk, environment=env)
    status = request.POST.get("status")

    if status == "ARCHIVED":
        workflow.deactivate()
        message = "Workflow archived"
    elif status == "ACTIVE":
        workflow.activate()
        message = "Workflow unarchived"
    else:
        return HttpResponseBadRequest("Invalid status")

    messages.success(request, message)

    # Return to the page that the user was on
    success_url = request.headers.get("Referer", "ui:workflow-list")

    return redirect(success_url)
