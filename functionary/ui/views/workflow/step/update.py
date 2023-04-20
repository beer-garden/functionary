import json
from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, PermissionDenied
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Workflow, WorkflowStep
from core.utils.workflow import move_step, reorder_steps
from ui.forms import TaskParameterTemplateForm, WorkflowStepUpdateForm
from ui.tables.workflow_step import WorflowStepTable
from ui.views.generic import PermissionedUpdateView
from ui.views.tasking_utils import (
    get_package_filter,
    get_taskable_objects,
    get_tasked_object,
)


class WorkflowStepUpdateView(PermissionedUpdateView):
    """Update view for WorkflowStep model"""

    model = WorkflowStep
    permissioned_model = "Workflow"
    environment_through_field = "workflow"
    form_class = WorkflowStepUpdateForm
    template_name = WorkflowStepUpdateForm.template_name

    def get_initial(self):
        """Populate initial form values"""
        initial = super().get_initial()
        initial["name"] = self.get_object().name
        initial["next"] = self.request.GET.get("next")
        initial["workflow"] = get_object_or_404(
            Workflow, id=self.kwargs.get("workflow_pk")
        )

        return initial

    def get_form_kwargs(self):
        """Setup kwargs for form instantiation"""
        step = self.get_object()
        kwargs = super().get_form_kwargs()
        kwargs["environment"] = self.request.session["environment_id"]
        if self.request.method == "POST":
            tasked_obj, tasked_type = get_tasked_object(
                self.request.POST, kwargs["environment"]
            )
            data = kwargs["data"].dict()
            data["tasked_object"] = tasked_obj
            # Convert tasked_type back to ContentType for the model
            data["tasked_type"] = tasked_type
            kwargs["data"] = data
        else:
            kwargs["data"] = {
                "name": step.name,
                "tasked_object": step.tasked_object,
                "tasked_type": step.tasked_type,
            }

        return kwargs

    def get_context_data(self, **kwargs):
        """Custom context"""
        context = super().get_context_data(**kwargs)
        tasked_object = self.get_object().tasked_object
        tasked_type = self.object.tasked_type.name
        objects = get_taskable_objects(self.request, tasked_type)

        context["parameter_form"] = TaskParameterTemplateForm(
            tasked_object,
            creator=self.request.user,
            initial=self.object.parameter_template,
        )
        context["tasked_type"] = tasked_type
        context["tasked_object"] = tasked_object
        # Create an initial filter for the modal
        context["filter"] = get_package_filter(self.request)
        context["taskable_objects"] = objects

        return context

    def post(self, request, workflow_pk, pk):
        """Handle WorkflowStepForm submission"""
        # Various parent class calls require the object be set
        self.object = self.get_object()

        environment_id = self.request.session.get("environment_id")

        data = request.POST.dict()
        tasked_obj, _ = get_tasked_object(data, environment_id)

        parameter_form = TaskParameterTemplateForm(
            tasked_object=tasked_obj, creator=request.user, data=data
        )
        step_form = self.get_form()

        if step_form.is_valid() and parameter_form.is_valid():
            step_form.instance.parameter_template = parameter_form.parameter_template
            step = step_form.save()
            messages.success(request, "Workflow saved.")

            success_url = reverse("ui:workflow-update", kwargs={"pk": step.workflow.pk})
            return HttpResponseClientRedirect(success_url)

        # Pass in step_form, otherwise the form gets created again
        context = self.get_context_data(form=step_form)
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
    messages.success(request, "Workflow saved.")

    context = {
        "workflow": step.workflow,
        "step_table": WorflowStepTable(
            step.workflow.ordered_steps, workflow_pk=workflow_pk
        ),
    }
    response = render(request, "partials/workflows/step_table.html", context)
    response["HX-Trigger"] = json.dumps({"showMessages": {}})

    return response


@require_POST
@login_required
def reorder_workflow_steps(request: HttpRequest, workflow_pk: UUID):
    step_ids = request.POST.getlist("step_ids")
    workflow = get_object_or_404(
        Workflow,
        id=workflow_pk,
    )

    if not request.user.has_perm(Permission.WORKFLOW_UPDATE, workflow.environment):
        raise PermissionDenied()

    try:
        reorder_steps(step_ids=step_ids, workflow=workflow)
        messages.success(request, "Workflow saved.")
    except Exception:
        messages.error(request, "Sorry, something went wrong! Please try again.")

    context = {
        "workflow": workflow,
        "step_table": WorflowStepTable(
            data=workflow.ordered_steps, workflow_pk=workflow_pk
        ),
    }
    response = render(request, "partials/workflows/step_table.html", context)
    response["HX-Trigger"] = json.dumps({"showMessages": {}})

    return response
