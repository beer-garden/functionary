import json

from django.urls import reverse

from core.models.scheduled_task import ScheduledTask
from ui.tables.schedule_task import ScheduledTaskFilter, ScheduledTaskTable
from ui.views.generic import PermissionedListView


class ScheduledTaskListView(PermissionedListView):
    """List view for the ScheduledTask model"""

    model = ScheduledTask
    ordering = ["name"]
    table_class = ScheduledTaskTable
    template_name = "core/scheduledtask_list.html"
    filterset_class = ScheduledTaskFilter
    queryset = ScheduledTask.active_objects.select_related(
        "environment",
        "creator",
        "most_recent_task",
        "periodic_task",
        "tasked_type",
    ).prefetch_related("tasked_object")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [{"label": "Schedules"}]

        return context

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        response["HX-Trigger-After-Swap"] = json.dumps({"loadPopovers": {}})

        return response


class ScheduledTaskArchiveListView(ScheduledTaskListView):
    """List view for archived ScheduledTasks"""

    template_name = "core/scheduledtask_archive.html"
    queryset = (
        ScheduledTask.objects.filter(status=ScheduledTask.ARCHIVED)
        .select_related(
            "environment",
            "creator",
            "most_recent_task",
            "periodic_task",
            "tasked_type",
        )
        .prefetch_related("tasked_object")
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"label": "Schedules", "url": reverse("ui:scheduledtask-list")},
            {"label": "Archive"},
        ]

        return context
