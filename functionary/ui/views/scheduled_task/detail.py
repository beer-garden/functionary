from django.urls import reverse

from core.models import Task
from core.models.scheduled_task import ScheduledTask
from ui.tables.scheduled_task_history import ScheduledTaskHistory
from ui.views.generic import PermissionedDetailView


class ScheduledTaskDetailView(PermissionedDetailView):
    model = ScheduledTask

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("creator", "tasked_type", "periodic_task__crontab")
            .prefetch_related("tasked_object")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scheduledtask: ScheduledTask = context["scheduledtask"]
        history = Task.objects.filter(scheduled_task=scheduledtask).order_by(
            "-created_at"
        )[:10]
        context["history_table"] = ScheduledTaskHistory(history)
        breadcrumbs = [
            {"label": "Schedules", "url": reverse("ui:scheduledtask-list")},
            {"label": scheduledtask.display_name},
        ]
        if scheduledtask.status == ScheduledTask.ARCHIVED:
            breadcrumbs.insert(
                1,
                {
                    "label": "Archive",
                    "url": reverse("ui:scheduledtask-archive-list"),
                },
            )
        context["breadcrumbs"] = breadcrumbs
        return context
