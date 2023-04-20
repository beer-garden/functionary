from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Workflow, WorkflowStep
from core.utils.workflow import add_step
from ui.forms import TaskParameterTemplateForm, WorkflowStepCreateForm
from ui.views.generic import PermissionedCreateView
from ui.views.tasking_utils import (
    add_data_values,
    get_package_filter,
    get_taskable_objects,
    get_tasked_object,
)


class WorkflowStepCreateView(PermissionedCreateView):
    """Create view for the WorkflowStep model"""

    model = WorkflowStep
    permissioned_model = "Workflow"
    environment_through_field = "workflow"
    form_class = WorkflowStepCreateForm
    template_name = WorkflowStepCreateForm.template_name

    def get_initial(self):
        """Populate initial form values"""
        initial = super().get_initial()
        initial["next"] = self.request.GET.get("next")
        initial["workflow"] = get_object_or_404(
            Workflow, id=self.kwargs.get("workflow_pk")
        )

        return initial

    def get_form_kwargs(self):
        """Setup kwargs for form instantiation"""
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
            data["workflow"] = get_object_or_404(
                Workflow, id=self.kwargs.get("workflow_pk")
            )
            kwargs["data"] = data

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        objects = get_taskable_objects(self.request, "function")
        context["taskable_objects"] = objects
        context["tasked_type"] = "function"
        # Create an initial filter for the modal
        context["filter"] = get_package_filter(self.request)
        context["workflow_id"] = self.kwargs.get("workflow_pk")
        return context

    def post(self, request, workflow_pk):
        """Handle WorkflowStepForm submission"""
        # Various parent class calls require the object be set
        self.object = None
        environment_id = self.request.session.get("environment_id")
        data = request.POST.dict()
        tasked_obj, tasked_type = get_tasked_object(data, environment_id)

        parameter_form = TaskParameterTemplateForm(
            tasked_object=tasked_obj, creator=request.user, data=data
        )

        add_data_values(data, environment_id, tasked_obj, tasked_type)
        step_form = self.get_form()

        if step_form.is_valid() and parameter_form.is_valid():
            cleaned = step_form.cleaned_data
            step = add_step(
                cleaned["workflow"],
                cleaned["name"],
                cleaned["tasked_object"],
                parameter_template=parameter_form.parameter_template,
                next=cleaned["next"],
            )
            messages.success(request, "Workflow saved.")

            success_url = reverse("ui:workflow-update", kwargs={"pk": step.workflow.pk})
            return HttpResponseClientRedirect(success_url)

        context = self.get_context_data()
        context["parameter_form"] = parameter_form
        context["tasked_object"] = tasked_obj

        return render(self.request, self.template_name, context)

    def test_func(self):
        """Permission check for view access"""
        workflow = get_object_or_404(
            Workflow,
            pk=self.kwargs.get("workflow_pk"),
            environment__id=self.request.session.get("environment_id"),
        )

        return self.request.user.has_perm(
            Permission.WORKFLOW_UPDATE, workflow.environment
        )
