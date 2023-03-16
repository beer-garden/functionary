from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, PermissionDenied
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Function, WorkflowStep
from core.utils.workflow import move_step
from ui.forms import TaskParameterTemplateForm, WorkflowStepUpdateForm
from ui.views.generic import PermissionedUpdateView


class WorkflowStepUpdateView(PermissionedUpdateView):
    """Update view for WorkflowStep model"""

    model = WorkflowStep
    permissioned_model = "Workflow"
    environment_through_field = "workflow"
    form_class = WorkflowStepUpdateForm
    template_name = WorkflowStepUpdateForm.template_name

    def get_context_data(self, **kwargs):
        """Custom context"""
        context = super().get_context_data(**kwargs)
        context["parameter_form"] = TaskParameterTemplateForm(
            self.get_object().function, initial=self.object.parameter_template
        )

        return context

    def get_form_kwargs(self):
        """Setup kwargs for form instantiation"""
        kwargs = super().get_form_kwargs()
        kwargs["environment"] = self.request.session["environment_id"]

        return kwargs

    def post(self, request, workflow_pk, pk):
        """Handle WorkflowStepForm submission"""
        # Various parent class calls require the object be set
        self.object = self.get_object()

        function = Function.objects.get(id=self.request.POST.get("function"))
        parameter_form = TaskParameterTemplateForm(
            tasked_object=function, data=self.request.POST
        )
        step_form = self.get_form()

        if step_form.is_valid() and parameter_form.is_valid():
            step_form.instance.parameter_template = parameter_form.parameter_template
            step = step_form.save()

            success_url = reverse("ui:workflow-detail", kwargs={"pk": step.workflow.pk})

            return HttpResponseClientRedirect(success_url)
        else:
            context = self.get_context_data()
            context["parameter_form"] = parameter_form

            return render(self.request, self.template_name, context)


@require_POST
@login_required
def move_workflow_step(request: HttpRequest, workflow_pk: UUID, pk: UUID):
    step = get_object_or_404(WorkflowStep, workflow=workflow_pk, pk=pk)
    new_next_step = None

    if not request.user.has_perm(Permission.WORKFLOW_UPDATE, step.workflow.environment):
        raise PermissionDenied()

    if next := request.POST.get("next"):
        try:
            new_next_step = WorkflowStep.objects.get(workflow=workflow_pk, pk=next)
        except (ValueError, WorkflowStep.DoesNotExist):
            raise BadRequest(f"{next} is not a valid next value for this WorkflowStep")

    move_step(step, new_next_step)

    context = {"workflow": step.workflow}
    return render(request, "partials/workflows/step_list.html", context)
