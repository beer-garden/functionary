from core.models.scheduled_task import ScheduledTask
from ui.views.generic import PermissionedListView


class ScheduledTaskListView(PermissionedListView):
    model = ScheduledTask
    permissioned_model = "Task"
    template_name = "core/scheduling_list.html"
