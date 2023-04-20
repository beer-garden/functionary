import json

from core.models import Task
from ui.tables.task import TaskListFilter, TaskListTable

from ..generic import PermissionedListView


class TaskListView(PermissionedListView):
    model = Task
    queryset = Task.objects.select_related(
        "tasked_type",
        "creator",
        "workflow_run_step",
        "workflow_run_step__workflow_task",
    ).prefetch_related(
        "tasked_object", "workflow_run_step__workflow_task__tasked_object"
    )
    ordering = ["-created_at"]
    table_class = TaskListTable
    filterset_class = TaskListFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [{"label": "Tasking"}]

        return context

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        response["HX-Trigger-After-Swap"] = json.dumps({"loadPopovers": {}})

        return response
