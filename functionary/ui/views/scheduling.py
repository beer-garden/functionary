from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
    QueryDict,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from core.auth import Permission
from core.models import Environment, ScheduledTask
from core.utils.scheduling import (
    create_periodic_task,
    get_function,
    get_parameters,
    is_valid_scheduled_day_of_month,
    is_valid_scheduled_day_of_week,
    is_valid_scheduled_hour,
    is_valid_scheduled_minute,
    is_valid_scheduled_month_of_year,
    update_crontab,
    update_status,
)

from ..forms.tasks import ScheduledTaskForm, TaskParameterForm, get_available_functions
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
        env = Environment.objects.get(id=self.request.session.get("environment_id"))
        if not len(get_available_functions(env)):
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
        return context


@require_POST
@login_required
def create_scheduled_task(request: HttpRequest) -> HttpResponse:
    """Handles form submission for creating a new scheduled task"""
    env = Environment.objects.get(id=request.session.get("environment_id"))
    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    func = get_function(request.POST.get("function"), env)
    if isinstance(func, HttpResponseNotFound):
        return func

    data: QueryDict = request.POST.copy()
    data["function"] = func
    data["environment"] = env
    data["status"] = ScheduledTask.PAUSED
    function_params_form = TaskParameterForm(func, data)

    # Validate function parameters
    param_errors = None
    if function_params_form.is_valid():
        data["parameters"] = function_params_form.cleaned_data
    else:
        param_errors = function_params_form.errors

    form = ScheduledTaskForm(data=data, env=env)
    if form.is_valid():
        _create_scheduled_task(
            request, form.cleaned_data, function_params_form.cleaned_data
        )
        return HttpResponseRedirect(reverse("ui:schedule-list"))

    context = {
        "form": ScheduledTaskForm(data=data, env=env),
        "errors": form.errors,
        "param_errors": param_errors,
        "function_id": str(func.id),
    }
    return render(request, "core/scheduled_task_create.html", context)


@require_POST
@login_required
def update_scheduled_task(request: HttpRequest, pk: str) -> HttpResponse:
    env = Environment.objects.get(id=request.session.get("environment_id"))
    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    scheduled_task = get_object_or_404(ScheduledTask, id=pk)
    func = get_function(request.POST.get("function"), env)
    if isinstance(func, HttpResponseNotFound):
        return func

    data: QueryDict = request.POST.copy()
    data["function"] = func
    data["environment"] = env
    function_params_form = TaskParameterForm(func, data)

    # Validate function parameters
    param_errors = None
    if function_params_form.is_valid():
        data["parameters"] = function_params_form.cleaned_data
    else:
        param_errors = function_params_form.errors

    form = ScheduledTaskForm(data=data, env=env, instance=scheduled_task)
    if form.is_valid():
        form.save()
        update_status(form.cleaned_data["status"], scheduled_task)
        update_crontab(form.cleaned_data, scheduled_task)
        return HttpResponseRedirect(reverse("ui:schedule-list"))

    """
    Return the string representation of the function and scheduled task ids
    so that the parameters can be lazy loaded via htmx.
    """
    context = {
        "form": ScheduledTaskForm(data=data, env=env),
        "errors": form.errors,
        "param_errors": param_errors,
        "scheduledtask": scheduled_task,
        "function_id": str(func.id),
        "scheduled_task_id": str(scheduled_task.id),
    }
    return render(request, "core/scheduled_task_update.html", context)


@require_GET
@login_required
def function_parameters(request: HttpRequest) -> HttpResponse:
    """Used to lazy load a function's parameters as a partial.

    Always expects a 'function_id' parameter in the request, which is the ID of the
    function object whose parameters should be rendered.
    """
    env = Environment.objects.get(id=request.session.get("environment_id"))
    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    if (function_id := request.GET.get("function", None)) in ["", None]:
        return HttpResponse("No function selected.")

    func = get_function(function_id, env)
    if isinstance(func, HttpResponseNotFound):
        return func

    """
    If the request includes the scheduled_task_id, substitute the default
    widget values for the existing ScheduledTask parameters.
    """
    existing_parameters = None
    if (scheduled_task_id := request.GET.get("scheduled_task_id", None)) is not None:
        scheduled_task = ScheduledTask.objects.get(id=scheduled_task_id)
        existing_parameters = scheduled_task.parameters

    parameters = get_parameters(func, parameter_values=existing_parameters)
    context = {"parameters": parameters}
    return render(request, "partials/function_parameters.html", context)


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


def _create_scheduled_task(request: HttpRequest, data: dict, task_params: dict):
    """Helper function for creating scheduled task"""
    scheduled_task = ScheduledTask.objects.create(
        name=data["name"],
        environment=data["environment"],
        description=data["description"],
        function=data["function"],
        parameters=task_params,
        creator=request.user,
    )

    _ = create_periodic_task(data, scheduled_task)
    scheduled_task.activate()
