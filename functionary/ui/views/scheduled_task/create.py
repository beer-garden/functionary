from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse

from core.models import ScheduledTask
from ui.forms import ScheduledTaskForm, TaskParameterForm
from ui.views.generic import PermissionedCreateView
from ui.views.scheduled_task.utils import get_crontab_schedule
from ui.views.tasking_utils import add_data_values, get_tasked_object


class ScheduledTaskCreateView(PermissionedCreateView):
    """Step two view for creating a ScheduledTask"""

    model = ScheduledTask
    form_class = ScheduledTaskForm
    template_name = "forms/scheduled_task/scheduled_task_edit.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        data = request.GET.dict()
        environment_id = self.request.session.get("environment_id")

        tasked_obj, tasked_type = get_tasked_object(data, environment_id)

        task_parameter_form = TaskParameterForm(
            tasked_object=tasked_obj, initial=data, creator=request.user
        )

        add_data_values(data, environment_id, tasked_obj, tasked_type)
        data["status"] = ScheduledTask.PENDING

        scheduled_task_form = ScheduledTaskForm(
            tasked_object=tasked_obj,
            environment=data["environment"],
            initial=data,
        )

        context = {
            "form": scheduled_task_form,
            "task_parameter_form": task_parameter_form,
            "tasked_type": tasked_type.name,
            "tasked_id": tasked_obj.id,
            "breadcrumbs": [
                {"label": "Schedules", "url": reverse("ui:scheduledtask-list")},
                {"label": "Create"},
            ],
        }
        return TemplateResponse(
            request, ScheduledTaskCreateView.template_name, context=context
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        data = request.POST.dict()
        environment_id = self.request.session.get("environment_id")
        tasked_obj, tasked_type = get_tasked_object(data, environment_id)

        task_parameter_form = TaskParameterForm(
            tasked_object=tasked_obj, data=data, creator=request.user
        )
        task_parameter_form.full_clean()

        add_data_values(data, environment_id, tasked_obj, tasked_type)
        data["parameters"] = task_parameter_form.cleaned_data
        data["status"] = ScheduledTask.PENDING

        scheduled_task_form = ScheduledTaskForm(
            tasked_object=tasked_obj,
            environment=data["environment"],
            data=data,
        )

        if scheduled_task_form.is_valid():
            scheduled_task = _create_scheduled_task(
                request,
                scheduled_task_form.cleaned_data,
                task_parameter_form.cleaned_data,
            )
            return HttpResponseRedirect(
                reverse(
                    "ui:scheduledtask-detail",
                    kwargs={
                        "pk": scheduled_task.id,
                    },
                )
            )

        context = {
            "form": scheduled_task_form,
            "task_parameter_form": task_parameter_form,
            "tasked_type": tasked_type.name,
            "tasked_id": tasked_obj.id,
        }
        return self.render_to_response(context)


def _create_scheduled_task(
    request: HttpRequest, schedule_form_data: dict, task_params: dict
) -> ScheduledTask:
    """Helper function for creating scheduled task"""
    with transaction.atomic():
        scheduled_task = ScheduledTask(
            name=schedule_form_data["name"],
            environment=schedule_form_data["environment"],
            description=schedule_form_data["description"],
            tasked_object=schedule_form_data["tasked_object"],
            parameters=task_params,
            creator=request.user,
        )
        scheduled_task.save()

        crontab_schedule = get_crontab_schedule(schedule_form_data)
        scheduled_task.set_schedule(crontab_schedule)
        scheduled_task.activate()
    return scheduled_task
