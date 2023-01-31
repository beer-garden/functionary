from core.models import Workflow
from ui.views.generic import PermissionedListView

PAGINATION_AMOUNT = 15


class WorkflowListView(PermissionedListView):
    """List view for the Workflow model"""

    model = Workflow
    queryset = Workflow.objects.select_related("creator").all()
    ordering = ["name"]
    paginate_by = PAGINATION_AMOUNT
