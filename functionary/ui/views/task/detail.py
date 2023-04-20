import csv

import django_tables2 as tables
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, ValidationError
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from core.auth import Permission
from core.models import Environment, Task, Workflow
from ui.tables.task_output import TaskOutputTable

from ..generic import PermissionedDetailView


def _detect_csv(result):
    """Attempt to determine if the provided result is a valid CSV"""
    try:
        csv.Sniffer().sniff(result, delimiters=",")
    except Exception:
        return False

    return True


def _format_csv_table(result: str) -> dict:
    """Convert a string of CSV into a format suitable for table rendering"""
    data = []
    for row in csv.DictReader(result.splitlines()):
        data.append(row)

    formatted_result = {
        "headers": list(data[0].keys()),
        "data": data,
    }

    return formatted_result


def _format_json_table(result: list) -> dict:
    """Convert a JSON list into a format suitable for table rendering"""
    headers = [key for key in result[0].keys()]

    return {"headers": headers, "data": result}


def _format_table(result):
    """Convert a result to a table friendly format

    This will take in a "string" or "json" result and return
    the headers and a list of rows for the data. A result_type of
    string is assumed to be csv formatted data - a csv reader
    parses the data into the resulting header and data.

    A result type of json should be of the following format:
    [
        {"prop1":"value1", "prop2":"value2"},
        {"prop1":"value3", "prop2":"value4"}
    ]
    The headers are derived from the keys of the first entry in the list.
    """
    if type(result) is str:
        return _format_csv_table(result)
    elif type(result) is list and len(result) > 0:
        return _format_json_table(result)
    else:
        raise ValueError("Unable to convert result to table")


def _show_output_selector(result):
    """Determines if the output format selector should be rendered"""
    result_type = type(result)

    if result_type is list:
        # Don't offer a table for a list of non-dictionaries
        show_selector = result and type(result[0]) is dict
    elif result_type is str:
        show_selector = _detect_csv(result)
    else:
        show_selector = False

    return show_selector


def _format_result(result, format):
    """Inspects the task result and formats the result data for in the desired format
    as appropriate"""
    output_format = "table"
    formatted_result = None
    format_error = None

    match format:
        case "display_raw":
            if type(result) in [list, dict]:
                output_format = "json"
            else:
                output_format = "string"
        case "display_table":
            try:
                formatted_result = _format_table(result)
            except Exception:
                format_error = "Result data is unsuitable for table output"
        case _:
            raise BadRequest("Invalid display format")

    return output_format, format_error, formatted_result


def _get_workflow_steps(task: Task) -> dict:
    """Builds the context for workflow step"""
    steps = task.steps.select_related("step_task").order_by("step_order")
    step_details = []

    for step in steps:
        details = {
            "step": step,
            "name": step.step_name,
            "status": step.step_task.status if step.step_task else "PENDING",
            "task": step.step_task,
            "finished": step.step_task and step.step_task.finished,
        }
        match details["status"]:
            case "PENDING":
                details["icon"] = (
                    "fa-spinner fa-fade animation" if not task.finished else ""
                )
            case "IN_PROGRESS":
                details["icon"] = "fa-spinner fa-spin animation"
            case "COMPLETE":
                details["icon"] = "fa-circle-check"
            case "ERROR":
                details["icon"] = "fa-circle-exclamation"

        step_details.append(details)

    return step_details


def _get_result_context(context: dict, format: str) -> dict:
    task: Task = context["task"]

    output_format, format_error, formatted_result = _format_result(task.result, format)
    if not format_error and output_format == "table":
        extra_columns = []
        for header in formatted_result["headers"]:
            extra_columns.append(
                (header, tables.Column(verbose_name=header, accessor=header))
            )
        context["task_output_table"] = TaskOutputTable(
            formatted_result["data"], extra_columns=extra_columns
        )

    context["show_output_selector"] = (
        False if not task.finished else _show_output_selector(task.result)
    )
    context["format_error"] = format_error
    context["formatted_result"] = formatted_result
    context["output_format"] = output_format

    if task.tasked_type.model_class() == Workflow:
        context["steps"] = _get_workflow_steps(task)
        context["poll_step"] = len(context["steps"])
        if not task.finished:
            for step in context["steps"]:
                # get the first step that isn't in a final state
                if not step["finished"]:
                    context["poll_step"] = step["step"].step_order
                    break

    return context


class TaskDetailView(PermissionedDetailView):
    model = Task

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("environment", "creator", "taskresult", "environment__team")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        format = (
            self.request.GET["output"]
            if "output" in self.request.GET
            else "display_raw"
        )
        context["breadcrumbs"] = [
            {
                "label": "Tasking",
                "url": reverse("ui:task-list"),
            },
            {"label": self.object.tasked_object.display_name},
        ]

        return _get_result_context(context, format)


class TaskResultsView(PermissionedDetailView):
    """View for retrieving the results in a given output format."""

    model = Task

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "environment",
                "taskresult",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return _get_result_context(context, self.request.GET["output"])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()

        if "poll" in request.GET:
            context["last"] = int(request.GET.get("last", 1))
            return render(request, "partials/task/result_poll.html", context=context)

        return render(request, "partials/task/task_result_block.html", context=context)


@require_GET
@login_required
def get_task_log(request: HttpRequest, pk: str) -> HttpResponse:
    env = Environment.objects.get(id=request.session.get("environment_id"))
    if not request.user.has_perm(Permission.TASK_READ, env):
        return HttpResponseForbidden()

    try:
        # Use try/except in case of invalid task_id uuid format
        task = get_object_or_404(Task, id=pk, environment=env)
    except ValidationError:
        return HttpResponseNotFound("Unknown task submitted.")

    if task.tasked_type.model == "workflow":
        context = {"log": task.log}
        return render(request, "partials/log_block.html", context)
    else:
        show_output_selector = (
            False if not task.finished else _show_output_selector(task.result)
        )

        context = {
            "task": task,
            "show_output_selector": show_output_selector,
            "output_format": "log",
        }
        return render(request, "partials/task/task_result_block.html", context)
