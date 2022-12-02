from core.models import Workflow
from ui.views.view_base import PermissionedEnvironmentListView

PAGINATION_AMOUNT = 10


class WorkflowListView(PermissionedEnvironmentListView):
    """List view for the Workflow model"""

    model = Workflow
    queryset = Workflow.objects.select_related("creator").all()
    order_by_fields = ["name"]
    paginate_by = PAGINATION_AMOUNT
