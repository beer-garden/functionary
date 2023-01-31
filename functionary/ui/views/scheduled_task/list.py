from core.models.scheduled_task import ScheduledTask
from ui.views.generic import PermissionedListView

PAGINATION_AMOUNT = 15


class ScheduledTaskListView(PermissionedListView):
    model = ScheduledTask
    permissioned_model = "Task"
    paginate_by = PAGINATION_AMOUNT
