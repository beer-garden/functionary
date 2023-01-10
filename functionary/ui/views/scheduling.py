from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
    QueryDict,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_celery_beat.models import CrontabSchedule

from core.auth import Permission
from core.models import Environment, Function, ScheduledTask
from core.utils.scheduling import (
    get_or_create_crontab_schedule,
    is_valid_scheduled_day_of_month,
    is_valid_scheduled_day_of_week,
    is_valid_scheduled_hour,
    is_valid_scheduled_minute,
    is_valid_scheduled_month_of_year,
)
from ui.forms import ScheduledTaskForm, TaskParameterForm

from .view_base import (
    PermissionedEnvironmentListView,
    PermissionedFormCreateView,
    PermissionedFormUpdateView,
)


class ScheduledTaskListView(PermissionedEnvironmentListView):
    model = ScheduledTask
    template_name = "core/scheduled_task_list.html"


class ScheduledTaskCreateView(PermissionedFormCreateView):
    model = ScheduledTask
    form_class = ScheduledTaskForm
    success_url = "/schedule_list"
    template_name = "core/scheduled_task_create.html"

    def get(self, *args, **kwargs):
        environment_id = self.request.session.get("environment_id")
        if not Function.objects.filter(package__environment=environment_id).exists():
            messages.warning(
                self.request,
                "No available functions to schedule in current environment.",
            )
            return redirect("ui:schedule-list")
        return super().get(*args, **kwargs)

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        kwargs["env"] = Environment.objects.get(
            id=self.request.session.get("environment_id")
        )
        return kwargs


class ScheduledTaskUpdateView(PermissionedFormUpdateView):
    model = ScheduledTask
    form_class = ScheduledTaskForm
    success_url = "/schedule_list"
    template_name = "core/scheduled_task_update.html"

    def get_form_kwargs(self) -> dict:
        """Add session environment to form kwargs to initialize available functions"""
        kwargs = super().get_form_kwargs()
        kwargs["env"] = Environment.objects.get(
            id=self.request.session.get("environment_id")
        )
        return kwargs

    def get_initial(self):
        """Use existing ScheduledTask to fill in existing values in the form"""
        initial = super().get_initial()
        scheduled_task: ScheduledTask = self.get_object()
        crontab = scheduled_task.periodic_task.crontab
        initial["scheduled_minute"] = crontab.minute
        initial["scheduled_hour"] = crontab.hour
        initial["scheduled_day_of_week"] = crontab.day_of_week
        initial["scheduled_day_of_month"] = crontab.day_of_month
        initial["scheduled_month_of_year"] = crontab.month_of_year
        return initial

    def get_context_data(self, **kwargs) -> dict:
        """Add function_id and scheduled_task_id to context

        This is used for lazy loading the function parameters.
        """
        context = super().get_context_data(**kwargs)
        scheduled_task: ScheduledTask = self.get_object()
        context["function_id"] = str(scheduled_task.function.id)
        context["scheduled_task_id"] = str(scheduled_task.id)
        context["parameter_form"] = TaskParameterForm(
            function=scheduled_task.function, initial=scheduled_task.parameters
        )
        return context


@require_POST
@login_required
def create_scheduled_task(request: HttpRequest) -> HttpResponse:
    """Handles form submission for creating a new scheduled task"""
    env = Environment.objects.get(id=request.session.get("environment_id"))

    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    function_id = request.POST.get("function")
    function = get_object_or_404(Function, id=function_id, package__environment=env)

    data: QueryDict = request.POST.copy()
    data["function"] = function
    data["environment"] = env
    data["status"] = ScheduledTask.PAUSED
    function_params_form = TaskParameterForm(function, data)

    # Validate function parameters
    param_errors = None
    if function_params_form.is_valid():
        data["parameters"] = function_params_form.cleaned_data
    else:
        # TODO: Refactor this. Just re-render the task param form instead
        # of setting a param_errors variable
        data["parameters"] = function_params_form.cleaned_data
        param_errors = function_params_form.errors

    form = ScheduledTaskForm(data=data, env=env)
    if form.is_valid():
        _create_scheduled_task(
            request, form.cleaned_data, function_params_form.cleaned_data
        )
        return HttpResponseRedirect(reverse("ui:schedule-list"))

    context = {
        "form": form,
        "parameter_form": function_params_form,
        "errors": form.errors,
        "param_errors": param_errors,
        "function_id": str(function.id),
    }
    return render(request, "core/scheduled_task_create.html", context)


@require_POST
@login_required
def update_scheduled_task(request: HttpRequest, pk: str) -> HttpResponse:
    """Handles form submission for updating a scheduled task"""
    env = Environment.objects.get(id=request.session.get("environment_id"))

    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    scheduled_task = get_object_or_404(ScheduledTask, id=pk)
    function_id = request.POST.get("function")
    function = get_object_or_404(Function, id=function_id, package__environment=env)

    data: QueryDict = request.POST.copy()
    data["function"] = function
    data["environment"] = env
    function_params_form = TaskParameterForm(function, data)

    # Validate function parameters
    param_errors = None
    if function_params_form.is_valid():
        data["parameters"] = function_params_form.cleaned_data
    else:
        param_errors = function_params_form.errors

    form = ScheduledTaskForm(data=data, env=env, instance=scheduled_task)
    if form.is_valid():
        form.save()
        scheduled_task.set_status(form.cleaned_data["status"])
        crontab_schedule = _get_crontab_schedule(form.cleaned_data)
        scheduled_task.set_schedule(crontab_schedule)

        return HttpResponseRedirect(reverse("ui:schedule-list"))

    # Return the string representation of the function and scheduled task ids
    # so that the parameters can be lazy loaded via htmx.
    context = {
        "form": ScheduledTaskForm(data=data, env=env),
        "errors": form.errors,
        "param_errors": param_errors,
        "scheduledtask": scheduled_task,
        "function_id": str(function.id),
        "scheduled_task_id": str(scheduled_task.id),
    }
    return render(request, "core/scheduled_task_update.html", context)


@require_POST
@login_required
def crontab_minute_param(request: HttpRequest) -> HttpResponse:
    if not is_valid_scheduled_minute(request.POST.get("scheduled_minute")):
        return render(request, "partials/crontab_invalid.html", {"field": "Minute"})
    return HttpResponse("")


@require_POST
@login_required
def crontab_hour_param(request: HttpRequest) -> HttpResponse:
    if not is_valid_scheduled_hour(request.POST.get("scheduled_hour")):
        return render(request, "partials/crontab_invalid.html", {"field": "Hour"})
    return HttpResponse("")


@require_POST
@login_required
def crontab_day_of_week_param(request: HttpRequest) -> HttpResponse:
    if not is_valid_scheduled_day_of_week(request.POST.get("scheduled_day_of_week")):
        return render(
            request, "partials/crontab_invalid.html", {"field": "Day of week"}
        )
    return HttpResponse("")


@require_POST
@login_required
def crontab_day_of_month_param(request: HttpRequest) -> HttpResponse:
    if not is_valid_scheduled_day_of_month(request.POST.get("scheduled_day_of_month")):
        return render(
            request, "partials/crontab_invalid.html", {"field": "Day of month"}
        )
    return HttpResponse("")


@require_POST
@login_required
def crontab_month_of_year_param(request: HttpRequest) -> HttpResponse:
    if not is_valid_scheduled_month_of_year(
        request.POST.get("scheduled_month_of_year")
    ):
        return render(
            request, "partials/crontab_invalid.html", {"field": "Month of year"}
        )
    return HttpResponse("")


def _create_scheduled_task(
    request: HttpRequest, schedule_form_data: dict, task_params: dict
):
    """Helper function for creating scheduled task

    By this point, the parameters have been validated against the schema,
    and the fields have been validated, so we can just create the object.
    """
    with transaction.atomic():
        scheduled_task = ScheduledTask.objects.create(
            name=schedule_form_data["name"],
            environment=schedule_form_data["environment"],
            description=schedule_form_data["description"],
            function=schedule_form_data["function"],
            parameters=task_params,
            creator=request.user,
        )
        crontab_schedule = _get_crontab_schedule(schedule_form_data)
        scheduled_task.set_schedule(crontab_schedule)
        scheduled_task.activate()


def _get_crontab_schedule(schedule_form_data: dict) -> CrontabSchedule:
    """Retrieve or create a CrontabSchedule for the provided ScheduledTaskForm data"""
    minute = schedule_form_data.get("scheduled_minute")
    hour = schedule_form_data.get("scheduled_hour")
    day_of_month = schedule_form_data.get("scheduled_day_of_month")
    month_of_year = schedule_form_data.get("scheduled_month_of_year")
    day_of_week = schedule_form_data.get("scheduled_day_of_week")

    return get_or_create_crontab_schedule(
        minute, hour, day_of_month, month_of_year, day_of_week
    )
