from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.auth import Permission
from core.models import Environment, ScheduledTask
from ui.forms import ScheduledTaskForm, TaskParameterForm
from ui.views.generic import PermissionedUpdateView
from ui.views.scheduled_task.utils import get_crontab_schedule


class ScheduledTaskUpdateView(PermissionedUpdateView):
    model = ScheduledTask
    form_class = ScheduledTaskForm
    template_name = "forms/scheduled_task/scheduled_task_edit.html"

    def get_success_url(self) -> str:
        return reverse(
            "ui:scheduledtask-detail", kwargs={"pk": self.kwargs.get(self.pk_url_kwarg)}
        )

    def get_initial(self) -> dict:
        initial = super().get_initial()
        scheduled_task: ScheduledTask = self.get_object()
        crontab = scheduled_task.periodic_task.crontab
        initial["scheduled_minute"] = crontab.minute
        initial["scheduled_hour"] = crontab.hour
        initial["scheduled_day_of_month"] = crontab.day_of_month
        initial["scheduled_month_of_year"] = crontab.month_of_year
        initial["scheduled_day_of_week"] = crontab.day_of_week
        initial["parameters"] = scheduled_task.parameters
        return initial

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        scheduled_task: ScheduledTask = context["scheduledtask"]
        context["update"] = True
        context["task_parameter_form"] = TaskParameterForm(
            tasked_object=scheduled_task.tasked_object,
            initial=scheduled_task.parameters,
            creator=self.request.user,
        )
        context["tasked_type"] = scheduled_task.tasked_type.name
        context["tasked_id"] = scheduled_task.tasked_object.id
        context["breadcrumbs"] = [
            {
                "label": "Schedules",
                "url": reverse("ui:scheduledtask-list"),
            },
            {"label": scheduled_task.display_name},
        ]
        return context

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        kwargs["tasked_object"] = kwargs["instance"].tasked_object
        kwargs["environment"] = self.get_environment()
        return kwargs

    def post(self, request: HttpRequest, **kwargs) -> HttpResponse:
        scheduled_task: ScheduledTask = self.get_object()
        data: dict = request.POST.dict()
        data["tasked_object"] = scheduled_task.tasked_object
        data["tasked_id"] = scheduled_task.tasked_object.id
        data["tasked_type"] = ContentType.objects.get_for_model(
            scheduled_task.tasked_object
        )

        task_parameter_form = TaskParameterForm(
            scheduled_task.tasked_object,
            data=data,
            initial=scheduled_task.parameters,
            creator=request.user,
        )
        task_parameter_form.full_clean()

        if not task_parameter_form.is_valid():
            form = self.get_form()
        else:
            data["environment"] = self.get_environment()
            data["parameters"] = task_parameter_form.cleaned_data
            form = ScheduledTaskForm(
                tasked_object=scheduled_task.tasked_object,
                environment=data["environment"],
                instance=scheduled_task,
                data=data,
            )
            if form.is_valid():
                form.save()
                scheduled_task.set_status(form.cleaned_data["status"])
                crontab_schedule = get_crontab_schedule(form.cleaned_data)
                scheduled_task.set_schedule(crontab_schedule)

                return HttpResponseRedirect(self.get_success_url())

        context = {
            "scheduledtask": scheduled_task,
            "update": True,
            "form": form,
            "task_parameter_form": task_parameter_form,
            "tasked_type": scheduled_task.tasked_type.name,
            "tasked_id": scheduled_task.tasked_object.id,
        }
        return self.render_to_response(context)


@require_POST
@login_required
def update_status(request: HttpRequest, pk):
    """Update just the status of a scheduled task"""

    env = Environment.objects.get(id=request.session.get("environment_id"))
    if not request.user.has_perm(Permission.SCHEDULEDTASK_UPDATE, env):
        return HttpResponseForbidden()

    status = request.POST["status"]
    scheduled_task = get_object_or_404(ScheduledTask, pk=pk, environment=env)

    try:
        scheduled_task.set_status(status)
    except ValueError:
        return HttpResponseBadRequest("Invalid status")

    messages.success(request, "Schedule status updated.")

    # Return to the page that the user was on
    success_url = request.headers.get("Referer", "ui:scheduledtask-list")

    return redirect(success_url)
