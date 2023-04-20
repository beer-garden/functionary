from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import FormView
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Operation
from core.models import Environment
from ui.forms import ScheduledTaskWizardForm
from ui.views.generic import PermissionedViewMixin
from ui.views.tasking_utils import (
    add_data_values,
    get_package_filter,
    get_taskable_objects,
    get_tasked_object,
)


class ScheduleCreateView(PermissionedViewMixin, FormView):
    """Wizard view for setting the name and Function or Workflow
    for a new ScheduledTask"""

    form_class = ScheduledTaskWizardForm
    template_name = "forms/scheduled_task/create_modal.html"
    permissioned_model = "ScheduledTask"
    post_action = Operation.CREATE

    def get_context_data(self, **kwargs):
        """Initial render defaults to scheduling Functions"""
        context = super().get_context_data(**kwargs)
        context["filter"] = get_package_filter(self.request)

        tasked_type = kwargs.get("tasked_type", "function")
        objects = get_taskable_objects(self.request, tasked_type)

        context["taskable_objects"] = objects
        context["tasked_type"] = tasked_type
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        environment = get_object_or_404(
            Environment, id=self.request.session.get("environment_id")
        )
        data = getattr(self.request, self.request.method, {})
        kwargs["environment"] = environment
        kwargs["tasked_type"] = data.get("tasked_type", "function")
        return kwargs

    def post(self, request):
        environment_id = self.request.session.get("environment_id")
        data = request.POST.copy()

        tasked_obj = None
        tasked_type = request.POST["tasked_type"]
        try:
            tasked_obj, tasked_type = get_tasked_object(data, environment_id)
        except ValidationError:
            pass
        add_data_values(data, environment_id, tasked_obj, tasked_type)

        wizard_form = ScheduledTaskWizardForm(
            data["environment"],
            tasked_type,
            data=data,
        )
        if wizard_form.is_valid():
            success_url = (
                reverse("ui:scheduledtask-create")
                + f"?name={data['name']}&tasked_id={tasked_obj.id}"
                + f"&tasked_type={tasked_type.name}"
            )

            return HttpResponseClientRedirect(success_url)

        context = {
            "form": wizard_form,
        }
        # Get tasked_type out of the POST, get_tasked_object
        # converted the local to a ContentType for the form earlier
        tasked_type = request.POST.get("tasked_type", "function")
        objects = get_taskable_objects(request, tasked_type)

        context["taskable_objects"] = objects
        context["tasked_type"] = tasked_type

        return TemplateResponse(
            request=self.request,
            context=context,
            template="forms/scheduled_task/scheduled_task_create.html",
        )
